"""
gui_harness.action.clipboard — clipboard operations.

Includes: set_clipboard, get_clipboard.
"""

from __future__ import annotations

import platform
import subprocess

SYSTEM = platform.system()


def set_clipboard(text):
    """Set clipboard content."""
    if SYSTEM == "Darwin":
        p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE,
                              env={"LANG": "en_US.UTF-8"})
        p.communicate(text.encode("utf-8"))
    elif SYSTEM == "Windows":
        subprocess.run(["clip"], input=text.encode("utf-16le"), check=True)
    else:
        _linux_set_clipboard(text)


def _linux_set_clipboard(text: str) -> None:
    import shutil
    data = text.encode("utf-8")
    if shutil.which("xclip"):
        subprocess.run(["xclip", "-selection", "clipboard"],
                       input=data, check=True)
    elif shutil.which("xsel"):
        subprocess.run(["xsel", "--clipboard", "--input"],
                       input=data, check=True)
    elif shutil.which("wl-copy"):
        subprocess.run(["wl-copy"], input=data, check=True)
    else:
        raise RuntimeError(
            "No clipboard tool found on Linux. "
            "Install xclip, xsel, or wl-clipboard."
        )


def _linux_get_clipboard() -> str:
    import shutil
    if shutil.which("xclip"):
        r = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                            capture_output=True, text=True, encoding="utf-8")
        return r.stdout
    elif shutil.which("xsel"):
        r = subprocess.run(["xsel", "--clipboard", "--output"],
                            capture_output=True, text=True, encoding="utf-8")
        return r.stdout
    elif shutil.which("wl-paste"):
        r = subprocess.run(["wl-paste", "--no-newline"],
                            capture_output=True, text=True, encoding="utf-8")
        return r.stdout
    else:
        raise RuntimeError(
            "No clipboard tool found on Linux. "
            "Install xclip, xsel, or wl-clipboard."
        )


def get_clipboard():
    """Get clipboard content."""
    if SYSTEM == "Darwin":
        r = subprocess.run(["pbpaste"], capture_output=True, text=True,
                            encoding="utf-8")
        return r.stdout
    elif SYSTEM == "Windows":
        r = subprocess.run(["powershell", "-command", "Get-Clipboard"],
                            capture_output=True, text=True, encoding="utf-8")
        return r.stdout.strip()
    else:
        return _linux_get_clipboard()
