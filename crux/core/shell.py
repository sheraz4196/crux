import os
from pathlib import Path
from crux.core.platform import system_info


def detect_shell():
    if os.environ.get("PSModulePath"):
        return "powershell"
    shell = Path(os.environ.get("SHELL", "")).stem.lower()
    if shell:
        return shell
    return "cmd" if system_info()["OS"] == "Windows" else "unknown"


def profile_path(shell):
    home = Path.home()
    if shell == "bash":
        return home / ".bashrc"
    if shell == "zsh":
        return Path(os.environ.get("ZDOTDIR", home)) / ".zshrc"
    raise ValueError("Use --profile with PowerShell's $PROFILE path. Fish and cmd integration are not supported in v0.1.")
