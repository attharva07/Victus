import socket
from types import SimpleNamespace

import psutil
import victus.domains.system.system_plugin as system_plugin
from victus.core.schemas import Approval
from victus.domains.system.system_plugin import PROCESS_PERMISSION_NOTE, SystemPlugin


class DummyProc:
    def __init__(self, name: str) -> None:
        self._name = name

    def name(self) -> str:
        return self._name


def _conn(status: str, l_ip: str | None, l_port: int | None, r_ip: str | None = None, r_port: int | None = None, pid: int | None = None):
    laddr = SimpleNamespace(ip=l_ip, port=l_port) if l_ip is not None else None
    raddr = SimpleNamespace(ip=r_ip, port=r_port) if r_ip is not None else None
    return SimpleNamespace(type=socket.SOCK_STREAM, status=status, laddr=laddr, raddr=raddr, pid=pid)


def test_net_connections_gracefully_handles_access_denied(monkeypatch):
    plugin = SystemPlugin()
    connection = _conn("ESTABLISHED", "127.0.0.1", 5000, "1.1.1.1", 80, pid=321)

    monkeypatch.setattr(system_plugin.psutil, "net_connections", lambda kind=None: [connection])

    def proc_factory(pid):
        raise psutil.AccessDenied(pid=pid, name=None)

    monkeypatch.setattr(system_plugin.psutil, "Process", proc_factory)

    result = plugin.execute("net_connections", {}, Approval(approved=True, policy_signature="sig"))

    assert result["ok"] is True
    assert result["action"] == "net_connections"
    record = result["data"][0]
    assert record["process_name"] is None
    assert PROCESS_PERMISSION_NOTE in result["notes"]


def test_exposure_snapshot_groups_listeners(monkeypatch):
    plugin = SystemPlugin()
    listener_a = _conn("LISTEN", "0.0.0.0", 8080, pid=42)
    listener_b = _conn("LISTEN", "127.0.0.1", 8080, pid=42)
    active = _conn("ESTABLISHED", "127.0.0.1", 1234, "8.8.8.8", 53, pid=99)

    monkeypatch.setattr(system_plugin.psutil, "net_connections", lambda kind=None: [listener_a, listener_b, active])
    monkeypatch.setattr(system_plugin.psutil, "Process", lambda pid: DummyProc("server" if pid == 42 else "client"))

    result = plugin.execute("exposure_snapshot", {}, Approval(approved=True, policy_signature="sig"))

    assert result["ok"] is True
    assert result["action"] == "exposure_snapshot"
    services = result["data"]["listening"]
    assert len(services) == 1
    entry = services[0]
    assert entry["local_port"] == 8080
    assert entry["pid"] == 42
    assert set(entry["local_ips"]) == {"0.0.0.0", "127.0.0.1"}
    assert entry["protocols"] == ["tcp"]


def test_access_overview_combines_outputs(monkeypatch):
    plugin = SystemPlugin()
    net_result = {
        "ok": True,
        "action": "net_connections",
        "data": [
            {
                "proto": "tcp",
                "state": "ESTABLISHED",
                "local_ip": "127.0.0.1",
                "local_port": 4000,
                "remote_ip": "9.9.9.9",
                "remote_port": 443,
                "pid": 1,
                "process_name": "alpha",
            },
            {
                "proto": "tcp",
                "state": "LISTEN",
                "local_ip": "0.0.0.0",
                "local_port": 22,
                "remote_ip": None,
                "remote_port": None,
                "pid": 1,
                "process_name": "alpha",
            },
        ],
        "notes": ["note-1"],
    }

    exposure_result = {
        "ok": True,
        "action": "exposure_snapshot",
        "data": {"listening": [], "rdp_enabled": None},
        "notes": ["note-2"],
    }

    local_devices = {
        "ok": True,
        "action": "local_devices",
        "data": {"usb": {}, "bluetooth": {}},
        "notes": [],
    }

    monkeypatch.setattr(plugin, "_net_connections", lambda: net_result)
    monkeypatch.setattr(plugin, "_exposure_snapshot", lambda connections_result=None: exposure_result)
    monkeypatch.setattr(plugin, "_local_devices", lambda: local_devices)

    result = plugin.execute("access_overview", {}, Approval(approved=True, policy_signature="sig"))

    assert result["ok"] is True
    assert result["action"] == "access_overview"
    summary = result["data"]["summary"]
    assert summary["established"] == 1
    assert summary["listening"] == 1
    assert summary["unique_remote_ips"] == 1
    assert {"note-1", "note-2"}.issubset(set(result["notes"]))
    assert result["data"]["top_processes"][0]["connection_count"] == 2
