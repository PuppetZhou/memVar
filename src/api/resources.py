"""Relocatable locations for unchanged service files outside the query engine."""
from functools import lru_cache
import os
from pathlib import Path

import yaml

WEB = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def configuration() -> dict:
    configured = os.environ.get('MEMVAR_RESOURCES_CONFIG')
    path = Path(configured) if configured else WEB / 'config/resources.yaml'
    if not path.is_absolute():
        path = WEB / path
    try:
        return yaml.safe_load(path.read_text()) or {}
    except (OSError, yaml.YAMLError):
        return {}


def resource_path(key: str, environment: str, default: str | None = None) -> Path:
    value = os.environ.get(environment) or configuration().get(key) or default
    if not value:
        raise ValueError(f'{key} resource location is not configured')
    path = Path(value).expanduser()
    return (path if path.is_absolute() else WEB / path).resolve()
