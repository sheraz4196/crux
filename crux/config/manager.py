import copy
import tomllib
from dataclasses import dataclass
from pathlib import Path
from crux.core.platform import config_path

DEFAULTS = {
    "general": {"theme": "default", "icons": True, "animations": False},
    "prompt": {"enabled": True, "show_git": True, "show_python": True, "show_node": True},
    "ls": {"show_icons": True, "show_sizes": True},
    "git": {"enabled": True},
}


@dataclass
class Configuration:
    data: dict
    path: Path
    warnings: list[str]


def load(path=None):
    path = Path(path) if path else config_path()
    data = copy.deepcopy(DEFAULTS)
    warnings = []
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return Configuration(data, path, warnings)
    except (OSError, ValueError) as exc:
        return Configuration(data, path, [f"Cannot read configuration: {exc}; using defaults."])
    for section, values in raw.items():
        if section not in data or not isinstance(values, dict):
            warnings.append(f"Unknown or invalid configuration section: {section}")
            continue
        for key, value in values.items():
            if key not in data[section] or type(value) is not type(data[section][key]):
                warnings.append(f"Invalid configuration setting: {section}.{key}")
            elif key == "theme" and value != "default":
                warnings.append(f"Unknown theme {value}; using default.")
            else:
                data[section][key] = value
    return Configuration(data, path, warnings)
