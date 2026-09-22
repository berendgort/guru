"""Capture live Windguru iapi responses into fixtures/."""

from __future__ import annotations

import json
from pathlib import Path

from curl_cffi import requests as curl_requests

from guru.search.client import IAPI_CZ, get_client

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures"

SCENARIOS = [
    ("search_castelldefels", {"q": "search_spots", "search": "castelldefels"}, "https://www.windguru.cz/"),
    ("forecast_spot_201", {"q": "forecast_spot", "id_spot": 201}, "https://www.windguru.cz/201"),
    ("forecast_spot_48309", {"q": "forecast_spot", "id_spot": 48309}, "https://www.windguru.cz/48309"),
    ("model_info_full", {"q": "model_info_full"}, "https://www.windguru.cz/"),
    ("forecast_201_gfs", {"q": "forecast", "id_spot": 201, "id_model": 3}, "https://www.windguru.cz/201"),
]


def _write_simplemap_nl_subset() -> None:
    session = curl_requests.Session(impersonate="chrome")
    headers = {
        "Referer": "https://www.windguru.cz/map/spot/",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }
    resp = session.get(
        IAPI_CZ,
        params={"q": "spots", "opt": "simplemap", "WGCACHEABLE": 1800},
        headers=headers,
        timeout=120,
    )
    data = resp.json()
    subset = []
    for row in data.get("spots") or []:
        lat, lon = float(row[2]), float(row[3])
        if 50.5 <= lat <= 54.0 and 3.0 <= lon <= 7.5:
            subset.append(row)
    path = OUT / "spots_simplemap_nl.json"
    path.write_text(
        json.dumps(
            {"count": len(subset), "spots": subset, "_note": "NL bbox subset of simplemap"},
            indent=2,
        )
    )
    print(f"wrote {path} ({len(subset)} spots)")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    client = get_client()
    for name, params, referer in SCENARIOS:
        data = client.get_json(params=params, referer=referer, base=IAPI_CZ)
        path = OUT / f"{name}.json"
        path.write_text(json.dumps(data, indent=2))
        print(f"wrote {path}")
    _write_simplemap_nl_subset()


if __name__ == "__main__":
    main()
