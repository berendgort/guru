"""Pure TOML upsert helpers."""

from __future__ import annotations

from guru.core.toml_edit import remove_assignment_in_section, upsert_toml_table


def test_upsert_appends_table() -> None:
    text, changed = upsert_toml_table("", "features.network_proxy.domains", {"a.com": "allow"})
    assert changed is True
    assert "[features.network_proxy.domains]" in text
    assert '"a.com" = "allow"' in text


def test_bool_to_table_upgrade() -> None:
    raw = '[features]\nnetwork_proxy = true\n'
    stripped = remove_assignment_in_section(raw, "features", "network_proxy")
    assert "network_proxy = true" not in stripped
    text, _ = upsert_toml_table(stripped, "features.network_proxy", {"enabled": True})
    text, _ = upsert_toml_table(text, "features.network_proxy.domains", {"x.com": "allow"})
    assert "enabled = true" in text
    assert '"x.com" = "allow"' in text
