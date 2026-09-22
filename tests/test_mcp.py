"""MCP tool smoke (no live network)."""

from __future__ import annotations

from guru.models.forecast import Spot
from guru.search.exceptions import GuruAmbiguousError


class _FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, name: str):
        def deco(fn):
            self.tools[name] = fn
            return fn

        return deco


def _tools() -> dict[str, object]:
    from guru.core.envelope import error_payload, success_payload
    from guru.mcp.tools_forecast import register as register_forecast
    from guru.mcp.tools_profile import register as register_profile
    from guru.search.exceptions import GuruError

    mcp = _FakeMcp()
    catch = (GuruError, ValueError, OSError)
    register_profile(mcp, catch=catch, ok=success_payload, err=error_payload)  # type: ignore[arg-type]
    register_forecast(mcp, catch=catch, ok=success_payload, err=error_payload)  # type: ignore[arg-type]
    return mcp.tools


def test_instruct_tool() -> None:
    payload = _tools()["instruct"]()  # type: ignore[operator]
    assert payload["ok"] is True
    assert payload["data"]["preset"] == "WINDGURU_DEFAULT"


def test_list_models_tool() -> None:
    payload = _tools()["list_models"]()  # type: ignore[operator]
    assert payload["ok"] is True
    assert any(row["id"] == 3 for row in payload["data"])


def test_resolve_spot_tool_ambiguous(monkeypatch) -> None:
    tools = _tools()

    def boom(spot: str, *, pick: int | None = None) -> Spot:
        raise GuruAmbiguousError(
            "ambiguous",
            candidates=[Spot(id=1, name="A"), Spot(id=2, name="B")],
        )

    monkeypatch.setattr("guru.mcp.tools_forecast.resolve_spot", boom)
    payload = tools["resolve_spot"]("slufter")  # type: ignore[operator]
    assert payload["ok"] is False
    assert payload["error_type"] == "ambiguous"
    assert len(payload["candidates"]) == 2
