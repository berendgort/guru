"""Model id aliases -- extend only from live Network captures (see docs/WIRE.md)."""

from __future__ import annotations

__all__ = (
    "MODELS",
    "MODEL_NAMES",
    "list_models",
    "resolve_model",
)

MODELS: dict[str, int] = {
    "gfs": 3,
    "gfs13": 3,
    "nam": 4,
    "wrf": 21,
    "icon7": 43,
    "icon": 45,
    "icon13": 45,
    "arome": 52,
    "aromehd": 52,
    "harmonie": 57,
    "gdps": 59,
    "zephr": 64,
    "zephyr": 64,
    "aladin": 107,
    "harmdk": 109,
    "ifs": 117,
    "icon_ifs": 117,
}

MODEL_NAMES: dict[int, str] = {}
for _alias, _mid in MODELS.items():
    MODEL_NAMES.setdefault(_mid, _alias)


def resolve_model(model: str | int) -> tuple[int, str]:
    if isinstance(model, int):
        return model, MODEL_NAMES.get(model, str(model))
    key = model.strip().lower()
    if key.isdigit():
        mid = int(key)
        return mid, MODEL_NAMES.get(mid, key)
    if key not in MODELS:
        known = ", ".join(sorted(MODELS))
        raise ValueError(f"Unknown model {model!r}. Known: {known}")
    return MODELS[key], key


def list_models() -> list[dict[str, str | int | list[str]]]:
    by_id: dict[int, list[str]] = {}
    for alias, mid in MODELS.items():
        by_id.setdefault(mid, []).append(alias)
    return [
        {
            "id": mid,
            "aliases": sorted(aliases),
            "primary": MODEL_NAMES.get(mid, str(mid)),
        }
        for mid, aliases in sorted(by_id.items())
    ]
