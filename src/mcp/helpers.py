"""Parsing and validation helpers for MCP server configuration."""

from collections.abc import Iterable
from pathlib import Path
from typing import TypeGuard
from urllib.parse import urlsplit

import yaml


def read_yaml(path: Path) -> object:
    """Read and parse a YAML document from disk."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"Could not read MCP config {path}: {error}") from error
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML in MCP config {path}: {error}") from error


def read_server_entries(document: object, path: Path) -> list[object]:
    """Extract the server list from the top-level config mapping."""
    if not _is_string_mapping(document) or set(document) != {"servers"}:
        raise ValueError(f"MCP config {path} must contain only a 'servers' key")

    entries = document["servers"]
    if not _is_list(entries):
        raise TypeError(f"'servers' in {path} must be a list")
    return entries


def parse_server_entry(entry: object, index: int, path: Path) -> tuple[str, str]:
    """Validate a YAML entry and return its server name and URL."""
    if not _is_string_mapping(entry) or set(entry) != {"name", "url"}:
        raise ValueError(
            f"Server entry {index} in {path} must contain 'name' and 'url'"
        )

    name, url = entry["name"], entry["url"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"Server entry {index} in {path} has an empty name")

    name = name.strip()
    if not isinstance(url, str):
        raise TypeError(f"MCP server {name!r} in {path} must have a URL")
    if not is_http_url(url):
        raise ValueError(
            f"MCP server {name!r} URL must be an absolute HTTP or HTTPS URL"
        )
    return name, url


def is_http_url(url: str) -> bool:
    """Return whether a URL has an HTTP(S) scheme and a valid host."""
    try:
        parsed_url = urlsplit(url)
        return parsed_url.scheme in {"http", "https"} and bool(parsed_url.hostname)
    except ValueError:
        return False


def validate_unique_names(names: Iterable[str], path: Path) -> None:
    """Reject duplicate names so the manager can index every server uniquely."""
    seen = set()
    for name in names:
        if name in seen:
            raise ValueError(f"Duplicate MCP server name {name!r} in {path}")
        seen.add(name)


def _is_string_mapping(value: object) -> TypeGuard[dict[str, object]]:
    """Narrow an untrusted YAML mapping to string keys and object values."""
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _is_list(value: object) -> TypeGuard[list[object]]:
    """Narrow an untrusted YAML sequence to a list of dynamically typed values."""
    return isinstance(value, list)
