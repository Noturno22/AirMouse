import ctypes
import os
import socket
import subprocess
import sys
import time
import webbrowser
import winreg

CREATE_NO_WINDOW = 0x08000000
WM_CLOSE = 0x0010


def _windows_with_title(hint):
    user32 = ctypes.windll.user32
    found = []

    def _cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n > 0:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                if hint.lower() in buf.value.lower():
                    found.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
    )
    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return found


def _find_browser():
    candidates = []
    for exe in ("chrome.exe", "msedge.exe", "firefox.exe"):
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                key = winreg.OpenKey(
                    root,
                    rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}",
                )
                val = winreg.QueryValueEx(key, None)[0]
                winreg.CloseKey(key)
                if val and os.path.isfile(val):
                    candidates.append(val)
                    break
            except OSError:
                continue
    local_chrome = os.path.expandvars(
        r"%LocalAppData%\Google\Chrome\Application\chrome.exe"
    )
    if os.path.isfile(local_chrome):
        candidates.append(local_chrome)
    for c in candidates:
        if c.endswith(("chrome.exe", "msedge.exe")):
            return c
    return candidates[0] if candidates else None


class Assistant3D:
    """Gere o assistente 3D barehands (server local + janela app do browser)."""

    def __init__(self, server_dir, url, window_hint="barehands", port=8794):
        self.server_dir = server_dir
        self.url = url
        self.window_hint = window_hint
        self.port = int(port)

    def server_up(self):
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=0.25):
                return True
        except OSError:
            return False

    def _launch_server(self):
        script = os.path.join(self.server_dir, "server.py")
        if not os.path.isfile(script):
            return False
        py = sys.executable
        pyw = py.replace("python.exe", "pythonw.exe")
        exe = pyw if os.path.isfile(pyw) else py
        try:
            subprocess.Popen(
                [exe, script],
                cwd=self.server_dir,
                creationflags=CREATE_NO_WINDOW,
            )
        except Exception:
            return False
        deadline = time.time() + 12.0
        while time.time() < deadline:
            if self.server_up():
                return True
            time.sleep(0.2)
        return False

    def is_open(self):
        return len(_windows_with_title(self.window_hint)) > 0

    def open(self):
        if not self.is_open():
            if not self.server_up() and not self._launch_server():
                webbrowser.open(self.url)
                return "ASSISTENTE (navegador)"
            exe = _find_browser()
            if exe:
                subprocess.Popen(
                    [exe, "--app=" + self.url, "--window-size=1280,860"],
                    creationflags=CREATE_NO_WINDOW,
                )
                return "ASSISTENTE 3D"
            webbrowser.open(self.url)
            return "ASSISTENTE (navegador)"
        return "JA ABERTO"

    def close(self):
        wins = _windows_with_title(self.window_hint)
        for hwnd in wins:
            try:
                ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            except Exception:
                pass
        return len(wins)

    def toggle(self):
        if self.is_open():
            n = self.close()
            return f"ASSISTENTE FECHADO ({n})" if n else "FECHAR ASSISTENTE"
        return self.open()
