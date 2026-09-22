"""MCP tool smoke (no live network)."""

from __future__ import annotations

from guru.mcp.server import instruct, list_models_tool, resolve_spot_tool
from guru.models.forecast import Spot
from guru.search.exceptions import GuruAmbiguousError


def test_instruct_tool() -> None:
    payload = instruct()
    assert payload["ok"] is True
    assert payload["data"]["preset"] == "WINDGURU_DEFAULT"


def test_list_models_tool() -> None:
    payload = list_models_tool()
    assert payload["ok"] is True
    assert any(row["id"] == 3 for row in payload["data"])


def test_resolve_spot_tool_ambiguous(monkeypatch) -> None:
    def boom(spot: str, *, pick: int | None = None) -> Spot:
        raise GuruAmbiguousError(
            "ambiguous",
            candidates=[Spot(id=1, name="A"), Spot(id=2, name="B")],
        )

    monkeypatch.setattr("guru.mcp.server.resolve_spot", boom)
    payload = resolve_spot_tool("slufter")
    assert payload["ok"] is False
    assert payload["error_type"] == "ambiguous"
    assert len(payload["candidates"]) == 2
