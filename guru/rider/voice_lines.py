"""Session / weekend copy builders (pure)."""

from __future__ import annotations

from guru.rider.voice_pick import call_label, joke

__all__ = (
    "advice_summary",
    "checklist",
    "far_drive_note",
    "hour_bits",
    "incomplete_advice_summary",
    "slot_line",
    "thinking_headers",
    "weekend_incomplete",
    "weekend_summary",
)


def advice_summary(
    overall: str,
    *,
    start: str,
    end: str,
    wind_kn: float,
    gust_kn: float | None,
    stars: str,
    kite: str,
    suit: str,
    session_h: float,
    sport: str,
    level: str,
) -> str:
    if overall == "no":
        return (
            f"{call_label('no')} -- no sendable {sport} window for {level} "
            f"in this forecast. {joke(about='dead_zone', seed=sport)} "
            "Stay on the beach, protect the quiver."
        )
    if overall == "incomplete":
        return (
            f"{call_label('incomplete')} -- drop your quiver + home range "
            f"once (level required) before I call a session. "
            f"{joke(about='intake', seed='advice')}"
        )
    star_bit = f" · {stars}" if stars and stars != "-" else ""
    gust = f" gust {gust_kn:g}" if gust_kn is not None else ""
    punch = (
        joke(about="send", seed=f"{start}:{kite}")
        if overall == "go"
        else joke(about="soft", seed=f"{start}:{kite}")
    )
    return (
        f"{call_label(overall)} · {start}-{end} · {wind_kn:g} kt{gust}"
        f"{star_bit} · rig {kite} · {suit} · {session_h:g}h session -- {punch}"
    )


def incomplete_advice_summary(missing: list[str]) -> str:
    return (
        f"{call_label('incomplete')} -- need your setup before gear calls. "
        f"Missing: {', '.join(missing)}. {joke(about='intake', seed='missing')}"
    )


def _norm(raw: str) -> str:
    return raw.strip().lower().replace(" ", "")


def hour_bits(
    *,
    quality: str,
    sport_foil_light: bool,
    gap: float | None,
    ideal: float | None,
    owned: float | None,
    owned_suit: str | None,
    rec_suit: str | None,
    session_hours: float,
    beginner_strong: bool,
) -> list[str]:
    bits: list[str] = []
    if quality == "smooth":
        bits.append("glassy power")
    elif quality == "gusty":
        bits.append("gusty -- warn; sized on average (not the spike)")
    elif quality == "ok":
        bits.append("clean enough")
    if sport_foil_light:
        bits.append("foil light-wind still rides")
    if gap is not None and abs(gap) > 2.0:
        bits.append(f"quiver gap {gap:+.1f} m2 vs ideal {ideal}")
    elif owned is not None and ideal is not None:
        bits.append(f"rig {owned:g} m2 (sweet spot ~{ideal:g})")
    if owned_suit and rec_suit and _norm(owned_suit) != _norm(rec_suit):
        bits.append(
            f"suit: your {owned_suit}, chart wants {rec_suit} ({session_hours:g}h)"
        )
    elif owned_suit:
        bits.append(f"suit {owned_suit} ({session_hours:g}h session)")
    if beginner_strong:
        bits.append("juiced for a beginner -- take it easy")
    return bits


def far_drive_note(existing: str | None = None) -> str:
    extra = (
        "long haul needs a clear SEND IT, not a soft maybe "
        "(no flaky-test road trips)"
    )
    if existing:
        return f"{existing}; {extra}"
    return extra


def weekend_summary(
    *,
    overall: str,
    lead_weekday: str | None,
    lead_name: str | None,
    lead_drive: float | str | None,
    lead_line: str | None,
    plan_days: str | None,
    top_name: str | None = None,
    top_id: int | None = None,
    top_drive: float | str | None = None,
    top_line: str | None = None,
) -> str:
    call = call_label(overall)
    if lead_weekday and lead_name and lead_line and plan_days:
        bit = joke(
            about="send" if overall == "go" else "soft",
            seed=f"{lead_weekday}:{lead_name}",
        )
        return (
            f"{call} · next: {lead_weekday} {lead_name} "
            f"~{lead_drive if lead_drive is not None else '?'} km -- {lead_line} "
            f"| plan: {plan_days} -- {bit}"
        )
    if top_name is not None and top_line:
        bit = joke(
            about="send" if overall == "go" else "soft",
            seed=f"{top_id}:{top_name}",
        )
        return (
            f"{call}: {top_name} ({top_id}) "
            f"~{top_drive if top_drive is not None else '?'} km -- {top_line} -- {bit}"
        )
    return (
        f"{call_label('no')} -- dead zone in your drive range this window. "
        f"{joke(about='dead_zone', seed='weekend')}"
    )


def weekend_incomplete(missing: list[str]) -> str:
    return (
        f"{call_label('incomplete')} -- need quiver + home range before I map "
        f"sessions. Missing: {', '.join(missing)}. "
        f"{joke(about='intake', seed='weekend')}"
    )


def slot_line(
    *,
    verdict: str,
    start: str,
    end: str,
    wind_kn: float,
    gust_kn: float | None,
    stars: str | None,
    kite: str,
    agree: int,
) -> str:
    gust = f" gust {gust_kn:g}" if gust_kn is not None else ""
    star_bit = f" · {stars}" if stars and stars != "-" else ""
    return (
        f"{call_label(verdict)} · {start}-{end} · {wind_kn:g} kt{gust}"
        f"{star_bit} · rig {kite} · {agree}/3 models locked"
    )


def checklist(*, gusty: bool, drive_km: float | None = None) -> list[str]:
    # Beach 5-min check stays in agent voice (not CLI checklist preach).
    items = [
        "Size for average wind; gusty -> warn (beginners stay SOFT CALL)",
        "Side-shore / side-on preferred; offshore = advanced-only if known",
        "Models must agree on GO before a long haul",
    ]
    if gusty:
        items.append("Gusty session -- more depower / shorter send, not auto downsize")
    if drive_km is not None and drive_km > 150:
        items.append(
            f"Long haul (~{drive_km:.0f} km) -> need ≥2h continuous SEND IT"
        )
    return items


def thinking_headers(*, hours: int, top_models: int, range_label: str | None) -> list[str]:
    bits = [
        "Long haul only on clear SEND IT with ≥2h continuous GO",
        f"Scan with top {top_models} models; horizon = what those models return "
        f"(~{hours}h default) -- beyond that we have not hacked time yet",
        joke(about="general", seed=f"think:{hours}:{top_models}"),
    ]
    if range_label:
        bits.insert(0, f"Home range: {range_label}")
    return bits
