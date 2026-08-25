"""Release-scoped validators for safe API response revalidation."""

from __future__ import annotations

from hashlib import sha256
import os

from fastapi import Request


REVALIDATE_CACHE_CONTROL = "public, max-age=0, must-revalidate"
NO_STORE_CACHE_CONTROL = "no-store"


def normalized_route(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return str(path) if isinstance(path, str) else "<unmatched>"


def application_release() -> str | None:
    value = os.environ.get("MEMVAR_APP_RELEASE", "").strip()
    return value or None


def release_etag(release_id: str, app_release: str, request: Request) -> str:
    identity = "\n".join((release_id, app_release, request.url.path, request.url.query))
    return f'"{sha256(identity.encode("utf-8")).hexdigest()}"'


def if_none_match_matches(value: str | None, etag: str) -> bool:
    if value is None:
        return False
    return any(
        candidate.strip() == "*" or candidate.strip().removeprefix("W/") == etag
        for candidate in value.split(",")
    )
