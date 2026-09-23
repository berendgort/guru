"""HTTP client -- curl_cffi + Chrome impersonation, polite spacing, retries."""

from __future__ import annotations

__all__ = (
    "Client",
    "DEFAULT_IMPERSONATE",
    "IAPI_CZ",
    "IAPI_NET",
    "REQUEST_TIMEOUT",
    "get_client",
)

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
from guru.search.polite import (
    cache_get,
    cache_key,
    cache_set,
    check_circuit,
    is_ip_forbidden,
    trip_circuit,
    wait_turn,
)

DEFAULT_IMPERSONATE = os.environ.get("GURU_IMPERSONATE", "chrome")
REQUEST_TIMEOUT = float(os.environ.get("GURU_TIMEOUT", "30"))

IAPI_CZ = "https://www.windguru.cz/int/iapi.php"
IAPI_NET = "https://www.windguru.net/int/iapi.php"


def _retryable_http(exc: BaseException) -> bool:
    """Don't burn retries on allowlist / IP ban / hard 4xx (except 429)."""
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

    def get_json(
        self,
        *,
        params: dict[str, Any],
        referer: str,
        base: str = IAPI_CZ,
        use_cache: bool = True,
    ) -> Any:
        check_circuit()
        key = cache_key(base, params)
        if use_cache:
            hit = cache_get(key)
            if hit is not None:
                return hit
        data = self._get_json_live(params=params, referer=referer, base=base)
        if use_cache:
            cache_set(key, data)
        return data

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.0, min=1.0, max=8),
        retry=retry_if_exception(_retryable_http),
        reraise=True,
    )
    def _get_json_live(
        self,
        *,
        params: dict[str, Any],
        referer: str,
        base: str,
    ) -> Any:
        check_circuit()
        wait_turn()
        headers = {
            "Referer": referer,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
        }
        resp = self._session.get(
            base, params=params, headers=headers, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code >= 400:
            body = (resp.text or "")[:400]
            if is_ip_forbidden(resp.status_code, body):
                trip_circuit()
                raise GuruHTTPError(
                    "Windguru Forbidden (IP ban / anti-scrape). Stop hammering; "
                    "circuit open. Mail vh@windguru.cz with your IP if personal "
                    "use. Official API coming.",
                    status_code=resp.status_code,
                )
            if resp.status_code == 403 and (
                "allowlist" in body.lower()
                or "not allowed" in body.lower()
                or "blocked" in body.lower()
            ):
                raise GuruHTTPError(
                    "Windguru gated in this runtime (allowlist). Agent: check "
                    "doctor.network.unlock_already_done -- unlock once if "
                    "false; if true show restart_after_unlock or "
                    "fallback_cursor (never /config domains again).",
                    status_code=resp.status_code,
                )
            raise GuruHTTPError(
                f"HTTP {resp.status_code} for {params.get('q')}: {body[:200]}",
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
