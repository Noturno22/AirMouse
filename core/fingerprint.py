"""Hardware fingerprint -> deterministic machine_id (SHA-256)."""
import hashlib
import subprocess


def _read_machine_guid() -> str:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Cryptography") as k:
            val, _ = winreg.QueryValueEx(k, "MachineGuid")
            return str(val)
    except Exception:
        return ""


def _wmic(namespace_class: str) -> str:
    try:
        out = subprocess.run(
            ["wmic", namespace_class, "get", "SerialNumber"],
            capture_output=True, text=True, timeout=8).stdout
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        return lines[-1] if len(lines) > 1 else ""
    except Exception:
        return ""


def collect_components() -> dict:
    return {
        "machine_guid": _read_machine_guid(),
        "disk_serial": _wmic("diskdrive"),
        "board_uuid": _wmic("baseboard"),
    }


def machine_id() -> str:
    comps = collect_components()
    joined = "|".join(f"{k}={comps[k]}" for k in sorted(comps))
    return hashlib.sha256(joined.encode()).hexdigest()
