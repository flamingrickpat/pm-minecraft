"""Exercise durable server epochs without substituting a world or tool."""
import pytest

from mcmcp.body_fence import BodyFence


def test_restart_invalidates_a_retained_active_token(tmp_path):
    path = tmp_path / "body-epoch.json"
    token = {"epoch": 7, "owner": "retained", "session": "first", "active": True}
    fence = BodyFence(path)
    fence.commit(token)
    restarted = BodyFence(path)
    assert restarted.state["epoch"] == 7
    assert restarted.state["interrupted"] == "mcp_restart"
    with pytest.raises(PermissionError, match="Stale Minecraft body epoch"):
        restarted.validate("minecraft_rotate", token)
    replacement = {**token, "epoch": 8, "session": "replacement"}
    restarted.commit(replacement)
    restarted.validate("minecraft_rotate", replacement)
    with pytest.raises(PermissionError):
        restarted.validate("minecraft_rotate", token)


def test_active_ownership_rejects_unowned_mutation_but_permits_reads(tmp_path):
    fence = BodyFence(tmp_path / "epoch.json")
    token = {"epoch": 1, "owner": "worker", "session": "owned", "active": True}
    fence.commit(token)
    fence.validate("minecraft_observe", None)
    with pytest.raises(PermissionError, match="active lease token"):
        fence.validate("minecraft_rotate", None)
    with pytest.raises(PermissionError, match="Stale Minecraft body epoch"):
        fence.validate("minecraft_rotate", {**token, "session": "other"})
    fence.commit({**token, "active": False})
    with pytest.raises(PermissionError):
        fence.validate("minecraft_rotate", token)
