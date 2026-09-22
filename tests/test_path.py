"""Universal agent path + Windguru probe."""

from __future__ import annotations

from guru.core.path import agent_path_payload, probe_windguru


def test_agent_path_payload() -> None:
    path = agent_path_payload()
    assert path["id"] == "local_guru_cli"
    assert "guru" in path["commands"]["weekend"]
    assert path["rule"] == "agent_runs_all_commands"


def test_probe_windguru_shape() -> None:
    result = probe_windguru()
    assert "reachable" in result
    assert result["host"] == "www.windguru.cz"
    assert "ok" in result
