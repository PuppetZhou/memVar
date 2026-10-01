"""Read-only PostgreSQL compatibility and DuckDB / Parquet query connections.

Select the candidate with MEMVAR_QUERY_BACKEND=duckdb and MEMVAR_DUCKDB_PATH.
The historical --setup-reader command is manual PostgreSQL provisioning only;
normal API startup never invokes it or reads administrator credentials.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import os
from pathlib import Path
import secrets
from threading import Lock

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

WEB = Path(__file__).resolve().parents[2]


class DatabaseConfigurationError(RuntimeError):
    """A local deployment configuration issue with no credential detail."""


def read_env(path: Path) -> dict[str, str]:
    return dict(line.split('=', 1) for line in path.read_text().splitlines()
                if '=' in line and not line.lstrip().startswith('#'))


def backend() -> str:
    value = os.environ.get('MEMVAR_QUERY_BACKEND', 'postgresql').lower()
    if value not in {'postgresql', 'duckdb'}:
        raise DatabaseConfigurationError('MEMVAR_QUERY_BACKEND must be postgresql or duckdb.')
    return value


@lru_cache(maxsize=512)
def parameter_names(sql: str) -> frozenset[str]:
    import sqlglot
    from sqlglot import exp
    return frozenset(p.name for p in sqlglot.parse_one(sql, read='postgres').find_all(exp.Placeholder))


def decode_value(value, dtype):
    if value is None:
        return None
    if dtype == 'JSON':
        import json
        return json.loads(value)
    if dtype == 'FLOAT':
        # psycopg receives PostgreSQL's shortest round-trippable float4 text.
        # DuckDB Python widens float32 to float64: restore that API expression.
        import numpy as np
        return float(str(np.float32(value)))
    if dtype.endswith('[]'):
        return [decode_value(item, dtype[:-2]) for item in value]
    return value


class DuckDBEngine:
    """One read-only database handle; independent cursors for concurrent requests.

    DuckDB cursors share the catalog but have separate execution state. Closing
    each cursor after use prevents request threads from sharing active results.
    """
    def __init__(self):
        import duckdb
        import locale
        path_value = os.environ.get('MEMVAR_DUCKDB_PATH')
        if not path_value:
            import yaml
            try:
                path_value = yaml.safe_load((WEB / 'config/duckdb.yaml').read_text())['catalog']
            except (OSError, KeyError, TypeError, yaml.YAMLError):
                raise DatabaseConfigurationError('The DuckDB service snapshot is not configured.') from None
        path = Path(path_value).expanduser()
        if not path.is_absolute():
            path = WEB / path
        self.path = path.resolve()
        if not path.is_file():
            raise DatabaseConfigurationError('The DuckDB service snapshot is not configured.')
        from .duckdb_collation import initialize, text_key, text_list, json_distinct_list
        try:
            initialize()
        except locale.Error:
            raise DatabaseConfigurationError('The PostgreSQL-compatible en_US.utf8 collation is unavailable.') from None
        self.connection = duckdb.connect(str(path), read_only=True, config={
            'threads': os.environ.get('MEMVAR_DUCKDB_THREADS', '4'),
            'memory_limit': os.environ.get('MEMVAR_DUCKDB_MEMORY_LIMIT', '4GB'),
        })
        self.connection.create_function('memvar_pg_text_key', text_key, ['VARCHAR'], 'BLOB')
        self.connection.create_function('memvar_pg_text_list', text_list, ['VARCHAR[]'], 'VARCHAR[]')
        self.connection.create_function('memvar_pg_json_distinct_list', json_distinct_list, ['VARCHAR'], 'JSON')

    @lru_cache(maxsize=65536)
    def source_record_files(self, record_id: str):
        import json
        locator = self.path.parent / 'source-record-files.json'
        if not locator.is_file():
            return None
        if not hasattr(self, '_record_locator'):
            content = json.loads(locator.read_text())
            if content.get('format_version') != 1 or content.get('relation') != 'web_variant.variant_source_record' or content.get('key') != 'record_id':
                raise DatabaseConfigurationError('The source-record file locator is incompatible with this snapshot.')
            manifest = json.loads((self.path.parent / 'manifest.json').read_text())
            source = next((item for item in manifest['objects'] if item['schema']=='web_variant' and item['name']=='variant_source_record'), None)
            if source is None or content.get('snapshot_id') != manifest.get('snapshot_id') or content.get('rows') != source.get('rows'):
                raise DatabaseConfigurationError('The source-record file locator does not belong to this snapshot.')
            self._record_locator = content['files']
        files = []
        for entry in self._record_locator:
            low, high = entry['min_record_id'], entry['max_record_id']
            # Missing statistics are unknown, never evidence for exclusion.
            if low is None or high is None or low <= record_id <= high:
                path = (self.path.parent / entry['path']).resolve()
                if self.path.parent not in path.parents:
                    raise DatabaseConfigurationError('The source-record locator contains an invalid file path.')
                files.append(str(path))
        # Unknown / orphan keys keep the original full-view lookup behavior.
        return files or None

    def query(self, sql: str, params: dict) -> list[dict]:
        from .duckdb_sql import translate
        translated = translate(sql)
        with self.connection.cursor() as cursor:
            # DuckDB rejects extra bound values; PostgreSQL ignores them.
            names = parameter_names(sql)
            cursor.execute(translated, {key: value for key, value in params.items() if key in names})
            columns = cursor.description
            return [{column[0]: decode_value(value, str(column[1]))
                     for column, value in zip(columns, row)} for row in cursor.fetchall()]

    def dispose(self):
        self.source_record_files.cache_clear()
        self.connection.close()


@lru_cache(maxsize=1)
def _cached_engine():
    if backend() == 'duckdb':
        return DuckDBEngine()
    url = os.environ.get('MEMVAR_DATABASE_URL')
    try:
        if url:
            url = make_url(url)
            if url.get_backend_name() not in {'postgresql', 'postgres'}:
                raise DatabaseConfigurationError('A PostgreSQL connection is required.')
            url = url.set(drivername='postgresql+psycopg')
        else:
            cfg = read_env(WEB / 'data/.api.env')
            url = URL.create('postgresql+psycopg', username=cfg['PGUSER'],
                             password=cfg['PGPASSWORD'], host=cfg['PGHOST'],
                             port=int(cfg['PGPORT']), database=cfg['PGDATABASE'])
    except (OSError, KeyError, ValueError):
        raise DatabaseConfigurationError('The read-only database connection is not configured.') from None
    return create_engine(url, pool_size=5, max_overflow=2, pool_timeout=10,
                         pool_pre_ping=True, hide_parameters=True,
                         connect_args={'connect_timeout': 5,
                           'options': '-c default_transaction_read_only=on -c statement_timeout=15000 -c application_name=memvar_api'})


_engine_lock = Lock()


def engine():
    # lru_cache alone may execute a cache miss more than once concurrently.
    with _engine_lock:
        return _cached_engine()


engine.cache_info = _cached_engine.cache_info
engine.cache_clear = _cached_engine.cache_clear


def query(sql: str, params: dict | None = None) -> list[dict]:
    current = engine()
    if isinstance(current, DuckDBEngine):
        return current.query(sql, params or {})
    with current.connect() as conn:
        return [dict(row) for row in conn.execute(text(sql), params or {}).mappings()]


def one(sql: str, params: dict | None = None) -> dict | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def setup_reader():
    import psycopg
    from psycopg import sql
    import yaml

    config = yaml.safe_load((WEB / 'config/database.yaml').read_text())
    admin = read_env(WEB / config['credentials_file'])
    secret_path = WEB / 'data/.api.env'
    if secret_path.exists():
        reader = read_env(secret_path)
        password = reader['PGPASSWORD']
    else:
        password = secrets.token_urlsafe(32)
    role = 'memvar_api'
    with psycopg.connect(host=config['host'], port=config['port'], dbname=config['database'],
                        user=admin['POSTGRES_USER'], password=admin['POSTGRES_PASSWORD']) as conn:
        # The unlocated-PTM detail query exposes existing candidate associations.
        # This small partial index avoids scanning all mapped PTM records.
        conn.execute('CREATE INDEX IF NOT EXISTS ptm_record_candidate_accessions_gin '
                     'ON web.ptm_record USING gin(candidate_accessions) WHERE accession IS NULL')
        if not conn.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (role,)).fetchone():
            conn.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role), sql.Literal(password)))
        else:
            conn.execute(sql.SQL('ALTER ROLE {} LOGIN PASSWORD {}').format(sql.Identifier(role), sql.Literal(password)))
        conn.execute(sql.SQL('ALTER ROLE {} SET default_transaction_read_only=on').format(sql.Identifier(role)))
        conn.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(config['database']), sql.Identifier(role)))
        for schema in ['web', 'web_variant', 'web_variant_sequence', 'web_clinvar_snv', 'web_classification', 'web_context', 'web_disease', 'web_paxdb', 'web_alphagenome', 'web_avi', 'web_mane']:
            if not conn.execute('SELECT 1 FROM pg_namespace WHERE nspname=%s', (schema,)).fetchone():
                continue
            conn.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO {}').format(sql.Identifier(schema), sql.Identifier(role)))
            conn.execute(sql.SQL('GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}').format(sql.Identifier(schema), sql.Identifier(role)))
            conn.execute(sql.SQL('ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT SELECT ON TABLES TO {}').format(sql.Identifier(schema), sql.Identifier(role)))
    if not secret_path.exists():
        fd = os.open(secret_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'w') as fh:
            fh.write(f"PGHOST={config['host']}\nPGPORT={config['port']}\nPGDATABASE={config['database']}\nPGUSER={role}\nPGPASSWORD={password}\n")
    secret_path.chmod(0o600)
    print('Read-only API role configured; credentials saved with mode 0600.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--setup-reader', action='store_true', required=True)
    parser.parse_args()
    setup_reader()
