"""Model id map — extend only from live Network captures (see docs/WIRE.md)."""

from __future__ import annotations

MODELS: dict[str, int] = {
    "gfs": 3,
    "gfs13": 3,
    "icon": 117,
    "nam": 52,
    "wrf": 109,
    "arome": 107,
    "harmonie": 21,
    "ecmwf": 45,
}

MODEL_NAMES: dict[int, str] = {v: k for k, v in MODELS.items()}


def resolve_model(model: str | int) -> tuple[int, str]:
    if isinstance(model, int):
        return model, MODEL_NAMES.get(model, str(model))
    key = model.strip().lower()
    if key.isdigit():
        mid = int(key)
        return mid, MODEL_NAMES.get(mid, key)
    if key not in MODELS:
        raise ValueError(f"Unknown model {model!r}. Known: {', '.join(sorted(MODELS))}")
    return MODELS[key], key
