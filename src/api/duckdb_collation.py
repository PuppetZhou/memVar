"""PostgreSQL snapshot text ordering (libc en_US.utf8), without a PG runtime.

The source database uses a deterministic libc collation. Deployment must provide
that locale; initialization occurs once, before request worker threads run.
"""
from functools import lru_cache
import locale
from threading import Lock

_lock = Lock()
_ready = False


def initialize():
    global _ready
    with _lock:
        if not _ready:
            locale.setlocale(locale.LC_COLLATE, 'en_US.utf8')
            _ready = True


@lru_cache(maxsize=65536)
def text_key(value: str) -> bytes:
    # Fixed-width codepoints preserve Python / libc transformed-string order.
    # Deterministic PG collations break equal locale weights by original bytes.
    return locale.strxfrm(value).encode('utf-32-be', errors='surrogatepass') + b'\x00\x00\x00\x00' + value.encode('utf-8')


def text_list(values):
    if values is None:
        return None
    return sorted(values, key=lambda value: (value is None, text_key(value) if value is not None else b''))


def json_value_key(value):
    # PostgreSQL 17 jsonb B-tree order; object storage keys are byte-length then
    # byte-order, while string values use the source database's text collation.
    # https://www.postgresql.org/docs/17/datatype-json.html#JSON-INDEXING
    if isinstance(value, dict):
        keys = sorted(value, key=lambda key: (len(key.encode('utf-8')), key.encode('utf-8')))
        return (5, len(keys), tuple((text_key(key), json_value_key(value[key])) for key in keys))
    if isinstance(value, list):
        return (-1,) if not value else (4, len(value), tuple(json_value_key(item) for item in value))
    if isinstance(value, bool):
        return (3, value)
    if isinstance(value, (int, float)):
        return (2, value)
    if isinstance(value, str):
        return (1, text_key(value))
    return (0,)


def json_distinct_list(value):
    import json
    if value is None:
        return None
    return json.dumps(sorted(json.loads(value), key=json_value_key), ensure_ascii=False, separators=(',', ':'))
