"""One SQLAlchemy pool, bound parameters and a dedicated read-only database login.

Provision once with ``python -m Web.src.api.db --setup-reader``. Runtime reads
only .api.env (or MEMVAR_DATABASE_URL), never the import administrator secret.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import os
from pathlib import Path
import secrets

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

WEB = Path(__file__).resolve().parents[2]


class DatabaseConfigurationError(RuntimeError):
    """A local deployment configuration issue with no credential detail."""


def read_env(path: Path) -> dict[str, str]:
    return dict(line.split('=', 1) for line in path.read_text().splitlines()
                if '=' in line and not line.lstrip().startswith('#'))


@lru_cache(maxsize=1)
def engine():
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


def query(sql: str, params: dict | None = None) -> list[dict]:
    with engine().connect() as conn:
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
        for schema in ['web', 'web_variant', 'web_variant_sequence', 'web_clinvar_snv', 'web_context', 'web_disease']:
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
