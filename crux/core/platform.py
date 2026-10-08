import os
import platform
from pathlib import Path


def system_info():
    return {"OS": platform.system(), "Architecture": platform.machine()}


def config_path():
    if platform.system() == "Windows":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return root / "CRUX" / "config.toml"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "crux" / "config.toml"
