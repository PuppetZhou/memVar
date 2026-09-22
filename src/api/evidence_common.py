"""Shared validation and small field projections for evidence endpoints."""
import base64
import json
import math
from fastapi import HTTPException
from .db import one

def require_protein(accession):
    if not one("SELECT accession FROM web.protein WHERE accession=:accession", {"accession": accession}):
        raise HTTPException(404, "Protein not found")


def cursor_read(cursor, context):
    if not cursor:
        return None
    try:
        if len(cursor) > 4096:
            raise ValueError()
        data = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        if data[0] != context:
            raise ValueError()
        value = data[1]
        if context[0] == "variants":
            valid = isinstance(value, list) and len(value) == 3 and all(isinstance(v, str) for v in value)
        elif context[0] in ("qtl", "expression"):
            valid = isinstance(value, list) and len(value) == 2 and all(type(v) is int and v >= 0 for v in value)
        else:
            valid = isinstance(value, str)
        if not valid:
            raise ValueError()
        return data[1]
    except (ValueError, TypeError, IndexError, KeyError, UnicodeDecodeError):
        raise HTTPException(400, "Invalid cursor for these filters")


def cursor_write(value, context):
    return base64.urlsafe_b64encode(json.dumps([context, value], separators=(",", ":")).encode()).decode().rstrip("=")


def clean(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value if value not in ("", "-", ".", "NA", "NaN") else None


def fields(data, names):
    return [{"label": k, "value": clean(data.get(k))} for k in names if clean(data.get(k)) is not None]
