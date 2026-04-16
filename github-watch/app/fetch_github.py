import datetime as dt
import logging
import time
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)


class GitHubClient:
    def __init__(self, token: str, base_url: str, request_sleep_seconds: float = 1.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.request_sleep_seconds = max(0.0, request_sleep_seconds)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def _request_with_retry(self, path: str, params: dict[str, Any], max_retries: int = 3) -> list[dict[str, Any]]:
        url = f"{self.base_url}{path}"
        for attempt in range(1, max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                    reset_ts = int(response.headers.get("X-RateLimit-Reset", "0"))
                    sleep_seconds = max(5, reset_ts - int(time.time()))
                    LOGGER.warning("Hit GitHub rate limit, sleeping %s seconds", sleep_seconds)
                    time.sleep(min(sleep_seconds, 120))
                    continue
                response.raise_for_status()
                time.sleep(self.request_sleep_seconds)
                return response.json()
            except requests.RequestException as exc:
                LOGGER.warning("GitHub request failed (%s/%s): %s", attempt, max_retries, exc)
                if attempt == max_retries:
                    raise
                time.sleep(2 * attempt)
        return []

    def fetch_recent(self, owner: str, repo: str, since_utc: dt.datetime) -> dict[str, list[dict[str, Any]]]:
        since_iso = since_utc.replace(microsecond=0).isoformat() + "Z"
        LOGGER.info("Fetching repo=%s/%s since=%s", owner, repo, since_iso)
        pulls = self._request_with_retry(
            f"/repos/{owner}/{repo}/pulls",
            {"state": "all", "sort": "updated", "direction": "desc", "per_page": 100},
        )
        issues = self._request_with_retry(
            f"/repos/{owner}/{repo}/issues",
            {"state": "all", "sort": "updated", "direction": "desc", "since": since_iso, "per_page": 100},
        )
        commits = self._request_with_retry(
            f"/repos/{owner}/{repo}/commits",
            {"since": since_iso, "per_page": 100},
        )

        def _is_recent(item: dict[str, Any]) -> bool:
            updated = item.get("updated_at") or item.get("created_at")
            if not updated:
                return False
            updated_dt = dt.datetime.fromisoformat(updated.replace("Z", "+00:00"))
            return updated_dt >= since_utc

        pulls_recent = [x for x in pulls if _is_recent(x)]
        issues_recent = [x for x in issues if _is_recent(x) and "pull_request" not in x]
        commits_recent = commits

        return {"pulls": pulls_recent, "issues": issues_recent, "commits": commits_recent}
