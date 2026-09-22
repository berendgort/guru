"""XDG rider profile load/save (``~/.config/guru/profile.json``)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from guru.models.profile import RiderProfile, parse_level, parse_sport


def config_dir() -> Path:
    override = os.environ.get("GURU_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / "guru"
    return Path.home() / ".config" / "guru"


def profile_path() -> Path:
    return config_dir() / "profile.json"


def load_profile() -> RiderProfile:
    path = profile_path()
    if not path.is_file():
        return RiderProfile()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid profile at {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid profile at {path}: expected object")
    return RiderProfile.model_validate(raw)


def save_profile(profile: RiderProfile) -> Path:
    path = profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(profile.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def update_profile(**updates: Any) -> RiderProfile:
    """Merge non-None updates into the stored profile and save."""
    current = load_profile()
    cleaned = _normalize_updates(updates)
    merged = current.merge(**cleaned)
    save_profile(merged)
    return merged


def _normalize_updates(updates: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "sport" in updates and updates["sport"] is not None:
        out["sport"] = parse_sport(updates["sport"])
    if "level" in updates and updates["level"] is not None:
        out["level"] = parse_level(updates["level"])
    if "weight_kg" in updates and updates["weight_kg"] is not None:
        out["weight_kg"] = float(updates["weight_kg"])
    if "kites_m2" in updates and updates["kites_m2"] is not None:
        out["kites_m2"] = list(updates["kites_m2"])
    if "boards" in updates and updates["boards"] is not None:
        out["boards"] = list(updates["boards"])
    if "wetsuits" in updates and updates["wetsuits"] is not None:
        out["wetsuits"] = list(updates["wetsuits"])
    if "home_spots" in updates and updates["home_spots"] is not None:
        out["home_spots"] = [int(x) for x in updates["home_spots"]]
    if "home_lat" in updates and updates["home_lat"] is not None:
        out["home_lat"] = float(updates["home_lat"])
    if "home_lon" in updates and updates["home_lon"] is not None:
        out["home_lon"] = float(updates["home_lon"])
    if "drive_km" in updates and updates["drive_km"] is not None:
        out["drive_km"] = float(updates["drive_km"])
    if "range_label" in updates and updates["range_label"] is not None:
        out["range_label"] = str(updates["range_label"])
    if "session_hours" in updates and updates["session_hours"] is not None:
        out["session_hours"] = float(updates["session_hours"])
    return out


def parse_float_list(raw: str | None) -> list[float] | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return []
    return [float(part.strip()) for part in text.replace(";", ",").split(",") if part.strip()]


def parse_str_list(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return []
    return [part.strip() for part in text.replace(";", ",").split(",") if part.strip()]


def profile_payload(profile: RiderProfile | None = None) -> dict[str, Any]:
    """Envelope-friendly profile view with readiness + first-pass intake."""
    from guru.rider.intake import intake_payload

    p = profile if profile is not None else load_profile()
    missing = p.missing_fields()
    range_missing = p.missing_range_fields()
    need_intake = bool(missing or range_missing)
    return {
        "profile": p.model_dump(mode="json"),
        "path": str(profile_path()),
        "ready": p.is_ready(),
        "range_ready": p.is_range_ready(),
        "missing": missing,
        "missing_range": range_missing,
        "first_pass": need_intake,
        "intake": intake_payload(needed=need_intake),
        "setup_hint": (
            None
            if not need_intake
            else "guru setup --intake '<user key=value paste>' --json"
        ),
        "range_hint": (
            None
            if not range_missing
            else (
                "guru setup --home-lat 41.39 --home-lon 2.17 --drive-km 200 "
                '--range-label "Trabucador → Leucate" --json'
            )
        ),
    }


__all__ = [
    "config_dir",
    "load_profile",
    "parse_float_list",
    "parse_str_list",
    "profile_path",
    "profile_payload",
    "save_profile",
    "update_profile",
]
