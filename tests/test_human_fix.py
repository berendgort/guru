"""Rare human UI fix recipes."""

from __future__ import annotations

from guru.core.human_fix import human_fix_payload, pick_human_fix


def test_human_fix_recipes_have_clear_steps() -> None:
    payload = human_fix_payload()
    assert "Automate everything first" in payload["policy"]
    recipes = payload["recipes"]
    assert "Settings → Data controls → Work network access" in recipes[
        "chatgpt_work_network"
    ]["say_to_rider"]
    assert "Agent internet" in recipes["codex_cloud_environment"]["say_to_rider"]
    assert "/config" in recipes["claude_network_settings"]["say_to_rider"]
    assert "windguru.cz" in recipes["codex_cloud_environment"]["say_to_rider"]
    assert "new chat" in recipes["restart_after_unlock"]["say_to_rider"].lower()


def test_pick_human_fix() -> None:
    assert pick_human_fix() is None
    restart = pick_human_fix(after_unlock=True)
    assert restart is not None
    assert restart["id"] == "restart_after_unlock"
    work = pick_human_fix(still_blocked=True, host_hint="ChatGPT Work")
    assert work is not None
    assert work["id"] == "chatgpt_work_network"
    claude = pick_human_fix(still_blocked=True, host_hint="claude code")
    assert claude is not None
    assert claude["id"] == "claude_network_settings"
