"""Read-only DuckDB / Parquet query connection for the published website data."""
from __future__ import annotations

from functools import lru_cache
import os
from threading import Lock

from ..runtime import RuntimeConfigurationError, catalog_path

class DatabaseConfigurationError(RuntimeConfigurationError):
    """A local deployment configuration issue with no credential detail."""


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
        self.path = catalog_path()
        if not self.path.is_file():
            raise DatabaseConfigurationError('The DuckDB service snapshot is not configured.')
        from .duckdb_collation import initialize, text_key, text_list, json_distinct_list
        try:
            initialize()
        except locale.Error:
            raise DatabaseConfigurationError('The PostgreSQL-compatible en_US.utf8 collation is unavailable.') from None
        self.connection = duckdb.connect(str(self.path), read_only=True, config={
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
    return DuckDBEngine()


_engine_lock = Lock()


def engine():
    # lru_cache alone may execute a cache miss more than once concurrently.
    with _engine_lock:
        return _cached_engine()


engine.cache_info = _cached_engine.cache_info
engine.cache_clear = _cached_engine.cache_clear


def query(sql: str, params: dict | None = None) -> list[dict]:
    return engine().query(sql, params or {})


def one(sql: str, params: dict | None = None) -> dict | None:
    rows = query(sql, params)
    return rows[0] if rows else None
