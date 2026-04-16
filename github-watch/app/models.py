from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RepoTarget:
    group: str
    owner: str
    repo: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def key(self) -> str:
        return f"{self.owner}_{self.repo}"


@dataclass
class TimeRange:
    start: str
    end: str


@dataclass
class NormalizedRepoData:
    repo: str
    group: str
    fetched_at: str
    time_range: TimeRange
    commits: list[dict[str, Any]] = field(default_factory=list)
    pull_requests: list[dict[str, Any]] = field(default_factory=list)
    issues: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "group": self.group,
            "fetched_at": self.fetched_at,
            "time_range": {
                "start": self.time_range.start,
                "end": self.time_range.end,
            },
            "commits": self.commits,
            "pull_requests": self.pull_requests,
            "issues": self.issues,
            "errors": self.errors,
        }
from dataclasses import dataclass


@dataclass(frozen=True)
class RepoTarget:
    group: str
    owner: str
    repo: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"
