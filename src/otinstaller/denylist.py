"""Denylist management: loading and checking tools against denylist."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from otinstaller.registry import RegistryError, Tool


@dataclass(frozen=True)
class Denylist:
    capabilities: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    repos: tuple[str, ...] = ()


def load_denylist(path: Path) -> Denylist:
    if not path.exists():
        return Denylist()
    try:
        with path.open() as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise RegistryError(f"invalid YAML in denylist: {e}") from e

    if content is None:
        return Denylist()

    def as_tuple(key: str) -> tuple[str, ...]:
        val = content.get(key, [])
        if not isinstance(val, list):
            raise RegistryError(f"denylist.{key} must be a list")
        return tuple(str(v) for v in val)

    return Denylist(
        capabilities=as_tuple("capabilities"),
        topics=as_tuple("topics"),
        keywords=as_tuple("keywords"),
        repos=as_tuple("repos"),
    )


def check_tool(tool: Tool, denylist: Denylist) -> str | None:
    for cap in tool.capabilities:
        if cap in denylist.capabilities:
            return f"capability: {cap}"

    for topic in tool.topics:
        if topic in denylist.topics:
            return f"topic: {topic}"

    name_desc = f"{tool.name} {tool.description}".lower()
    for keyword in denylist.keywords:
        if keyword.lower() in name_desc:
            return f"keyword: {keyword}"

    if tool.repo:
        for repo in denylist.repos:
            if repo.lower() == tool.repo.lower():
                return f"repo: {repo}"

    return None


def filter_tools(
    tools: list[Tool], denylist: Denylist
) -> tuple[list[Tool], list[tuple[Tool, str]]]:
    allowed = []
    denied = []
    for tool in tools:
        reason = check_tool(tool, denylist)
        if reason:
            denied.append((tool, reason))
        else:
            allowed.append(tool)
    return allowed, denied
