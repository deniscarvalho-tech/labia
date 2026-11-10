"""site-data/versions.json: a linha do tempo das versões, lida pela página de portfólio."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from labia.contracts.common import SCHEMA_VERSION, Strict
from labia.contracts.summary import HeadlineCard


class VersionLinks(Strict):
    github_release: str | None = None
    hf_model: str | None = None
    hf_dataset: str | None = None
    space: str | None = None
    article: str | None = None
    panel: str | None = None


class Version(Strict):
    version: str
    date: date
    title: str
    status: Literal["planned", "in_progress", "released"]
    changes: list[str]
    headline: list[HeadlineCard]
    links: VersionLinks


class VersionsFile(Strict):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    is_sample: bool
    generated_at: datetime
    versions: list[Version]
