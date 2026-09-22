"""HTTP client — curl_cffi + Chrome impersonation, retries, env timeouts."""

from __future__ import annotations

import os
from typing import Any

from curl_cffi import requests as curl_requests
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from guru.search.exceptions import GuruHTTPError, GuruParseError

DEFAULT_IMPERSONATE = os.environ.get("GURU_IMPERSONATE", "chrome")
REQUEST_TIMEOUT = float(os.environ.get("GURU_TIMEOUT", "30"))

IAPI_CZ = "https://www.windguru.cz/int/iapi.php"
IAPI_NET = "https://www.windguru.net/int/iapi.php"


def _retryable_http(exc: BaseException) -> bool:
    """Don't burn retries on allowlist / hard 4xx (except 429)."""
    if isinstance(exc, GuruHTTPError):
        status = exc.status_code
        if status is None:
            return True
        if status == 429 or status >= 500:
            return True
        return False
    if isinstance(exc, GuruParseError):
        return False
    return True


class Client:
    def __init__(self) -> None:
        self._session = curl_requests.Session(impersonate=DEFAULT_IMPERSONATE)

    def close(self) -> None:
        self._session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception(_retryable_http),
        reraise=True,
    )
    def get_json(
        self,
        *,
        params: dict[str, Any],
        referer: str,
        base: str = IAPI_CZ,
    ) -> Any:
        headers = {
            "Referer": referer,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        }
        resp = self._session.get(
            base, params=params, headers=headers, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code >= 400:
            body = (resp.text or "")[:200]
            if resp.status_code == 403 and (
                "allowlist" in body.lower()
                or "not allowed" in body.lower()
                or "blocked" in body.lower()
            ):
                raise GuruHTTPError(
                    "Yo — this chat can't peek at the wind charts (gated). "
                    "Run guru unlock on the laptop or ask in Cursor for a live SEND IT.",
                    status_code=resp.status_code,
                )
            raise GuruHTTPError(
                f"HTTP {resp.status_code} for {params.get('q')}: {body}",
                status_code=resp.status_code,
            )
        try:
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise GuruParseError(
                f"Non-JSON for {params.get('q')}: {resp.text[:200]}"
            ) from exc
        if isinstance(data, dict) and data.get("return") == "error":
            raise GuruHTTPError(str(data.get("message") or data))
        return data


_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = Client()
    return _client
