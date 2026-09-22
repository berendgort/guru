"""Capture live Windguru iapi responses into fixtures/."""

from __future__ import annotations

import json
from pathlib import Path

from guru.search.client import IAPI_CZ, get_client

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures"

SCENARIOS = [
    ("search_castelldefels", {"q": "search_spots", "search": "castelldefels"}, "https://www.windguru.cz/"),
    ("forecast_spot_201", {"q": "forecast_spot", "id_spot": 201}, "https://www.windguru.cz/201"),
    ("forecast_201_gfs", {"q": "forecast", "id_spot": 201, "id_model": 3}, "https://www.windguru.cz/201"),
]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    client = get_client()
    for name, params, referer in SCENARIOS:
        data = client.get_json(params=params, referer=referer, base=IAPI_CZ)
        path = OUT / f"{name}.json"
        path.write_text(json.dumps(data, indent=2))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
