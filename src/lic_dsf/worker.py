"""Foreground calculation worker with its own parent and lifetime guards."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time


def write_result(path, data):
    fd, temporary = tempfile.mkstemp(prefix=".result-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle, allow_nan=False, sort_keys=True)
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def parent_probe(parent_pid):
    if parent_pid <= 1 or os.getppid() != parent_pid:
        raise ValueError("calculation_parent_unavailable")
    if os.name != "nt":
        return lambda: os.getppid() == parent_pid, lambda: None
    # A handle refers to the original process even if Windows later reuses its PID.
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x00100000, False, parent_pid)
    if not handle:
        raise ValueError("calculation_parent_unavailable")
    return lambda: kernel.WaitForSingleObject(handle, 0) == 0x102, lambda: kernel.CloseHandle(handle)


def start_guard(request, directory):
    remaining = float(request["deadline_utc"]) - time.time()
    if not 0 < remaining <= 601:
        raise ValueError("calculation_deadline_invalid")
    deadline = time.monotonic() + remaining
    alive, close = parent_probe(int(request["parent_pid"]))
    stopped = threading.Event()
    def watch():
        try:
            while not stopped.wait(0.2):
                code = None
                try:
                    if not alive():
                        code = "calculation_parent_lost"
                    elif time.monotonic() >= deadline:
                        code = "calculation_deadline_exceeded"
                except Exception:
                    code = "calculation_guard_unreadable"
                if code:
                    try:
                        write_result(directory / "error.json", {"code": code})
                    finally:
                        # Exit only this task-owned foreground leaf; no persisted PID cleanup.
                        os._exit(124)
        finally:
            close()
    threading.Thread(target=watch, daemon=True, name="calculation-lifetime").start()
    return stopped


def main(request_path):
    request_path = Path(request_path)
    stopped = None
    try:
        request = json.loads(request_path.read_text())
        stopped = start_guard(request, request_path.parent)
        from . import calculate
        result = calculate(request["workbook"], request["scenario"], expected_sha256=request["workbook_sha256"])
        write_result(request_path.parent / "result.json", result)
        return 0
    except Exception as exc:
        code = str(exc)
        if not code or len(code) > 200 or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789_" for c in code):
            code = "calculation_failed"
        write_result(request_path.parent / "error.json", {"code": code})
        return 1
    finally:
        if stopped is not None:
            stopped.set()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
