from __future__ import annotations

import datetime as dt
import logging
import time
from typing import Any

import requests

from app.models import RepoTarget

LOGGER = logging.getLogger(__name__)


class GitHubClient:
    def __init__(
        self,
        token: str,
        base_url: str,
        request_sleep_seconds: float = 1.0,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.request_sleep_seconds = max(0.0, request_sleep_seconds)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.session = requests.Session()
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.session.headers.update(headers)

    def _request_json(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        url = f"{self.base_url}{path}"
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout_seconds)
                if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                    reset_ts = int(response.headers.get("X-RateLimit-Reset", "0"))
                    wait_seconds = max(5, reset_ts - int(time.time()))
                    LOGGER.warning("Rate limit reached, sleep %s seconds", wait_seconds)
                    time.sleep(min(wait_seconds, 120))
                    continue
                response.raise_for_status()
                payload = response.json()
                time.sleep(self.request_sleep_seconds)
                if isinstance(payload, list):
                    return payload
                return []
            except requests.RequestException as exc:
                LOGGER.warning("GitHub API failed (%s/%s): %s", attempt, self.max_retries, exc)
                if attempt == self.max_retries:
                    raise
                time.sleep(2 * attempt)
        return []

    def _fetch_pr_files(self, target: RepoTarget, pr_number: int) -> list[str]:
        try:
            files = self._request_json(
                f"/repos/{target.owner}/{target.repo}/pulls/{pr_number}/files",
                {"per_page": 100},
            )
            return [f.get("filename", "") for f in files if isinstance(f, dict)]
        except Exception as exc:
            LOGGER.warning("Fetch PR files failed for %s#%s: %s", target.full_name, pr_number, exc)
            return []

    def fetch_recent(self, target: RepoTarget, since_utc: dt.datetime, until_utc: dt.datetime) -> dict[str, Any]:
        since_iso = since_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        until_iso = until_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        LOGGER.info("Fetch %s since=%s", target.full_name, since_iso)
        commits = self._request_json(
            f"/repos/{target.owner}/{target.repo}/commits",
            {"since": since_iso, "per_page": 100},
        )
        pull_requests = self._request_json(
            f"/repos/{target.owner}/{target.repo}/pulls",
            {"state": "all", "sort": "updated", "direction": "desc", "per_page": 100},
        )
        issues = self._request_json(
            f"/repos/{target.owner}/{target.repo}/issues",
            {"state": "all", "sort": "updated", "direction": "desc", "since": since_iso, "per_page": 100},
        )

        def _in_range(ts: str | None) -> bool:
            if not ts:
                return False
            moment = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return since_utc <= moment <= until_utc

        pulls_recent = []
        for item in pull_requests:
            if _in_range(item.get("updated_at") or item.get("created_at")):
                number = item.get("number")
                if isinstance(number, int):
                    item["changed_files"] = self._fetch_pr_files(target, number)
                pulls_recent.append(item)

        issues_recent = [
            item
            for item in issues
            if "pull_request" not in item and _in_range(item.get("updated_at") or item.get("created_at"))
        ]

        return {
            "repo": target.full_name,
            "domain": target.domain,
            "group": target.group,
            "since": since_iso,
            "until": until_iso,
            "commits": commits,
            "pull_requests": pulls_recent,
            "issues": issues_recent,
        }
