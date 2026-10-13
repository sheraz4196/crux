import copy
import tomllib
from dataclasses import dataclass
from pathlib import Path
from crux.core.platform import config_path
from crux.render.theme import THEMES

DEFAULTS = {
    "general": {"theme": "default", "icons": True, "animations": False, "terminal_palette": True},
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
            elif key == "theme" and value not in THEMES:
                warnings.append(f"Unknown theme {value}; using default.")
            else:
                data[section][key] = value
    return Configuration(data, path, warnings)


def default_value(key):
    parts = key.split('.')
    if len(parts) != 2 or parts[0] not in DEFAULTS or parts[1] not in DEFAULTS[parts[0]]:
        raise ValueError(f'Unknown setting: {key}. Use SECTION.KEY from crux config.')
    return DEFAULTS[parts[0]][parts[1]]


def parse_value(key, value):
    expected = default_value(key)
    if isinstance(expected, bool):
        if value.lower() not in ('true', 'false'):
            raise ValueError(f'{key} requires true or false.')
        return value.lower() == 'true'
    if key == 'general.theme' and value not in THEMES:
        raise ValueError(f'Unknown theme: {value}. Choose {", ".join(THEMES)}.')
    return value


def update(settings, path=None):
    """Edit simple table assignments and verify every unrelated parsed value.

    Refuse alternate TOML layouts this bounded editor cannot preserve. A reset
    is a single atomic write rather than a sequence of partially applied edits.
    """
    import json
    import re
    from crux.core.storage import atomic_write

    path = Path(path) if path else config_path()
    if path.is_symlink():
        raise ValueError('Refusing to replace a symlinked configuration.')
    text = path.read_text(encoding='utf-8') if path.exists() else ''
    expected = tomllib.loads(text)
    for key, value in settings.items():
        default = default_value(key)
        if type(value) is not type(default):
            raise ValueError(f'Invalid type for {key}.')
        if key == 'general.theme' and value not in THEMES:
            raise ValueError(f'Unknown theme: {value}.')
        section, name = key.split('.')
        if section in expected and not isinstance(expected[section], dict):
            raise ValueError(f'Cannot safely edit [{section}]; use a TOML table.')
        expected.setdefault(section, {})[name] = value
        encoded = str(value).lower() if isinstance(value, bool) else json.dumps(value)
        table = re.search(r'^\[' + section + r'\][ \t]*(?:#[^\n]*)?(?:\n|$)(?P<body>.*?)(?=^\[|\Z)', text, re.M | re.S)
        if table:
            body = table.group('body')
            assignment = re.compile(r'^([ \t]*' + name + r'[ \t]*=[ \t]*)([^\n]*)(\n|$)', re.M)
            match = assignment.search(body)
            if match:
                comment = re.search(r'[ \t]+#.*$', match.group(2))
                suffix = comment.group() if comment else ''
                body = assignment.sub(lambda m: m.group(1) + encoded + suffix + m.group(3), body, count=1)
            else:
                body = f'{name} = {encoded}\n' + body
            header = text[table.start():table.start('body')]
            if not header.endswith('\n'):
                header += '\n'
            text = text[:table.start()] + header + body + text[table.end('body'):]
        else:
            text += ('\n' if text and not text.endswith('\n') else '') + f'[{section}]\n{name} = {encoded}\n'
        try:
            parsed = tomllib.loads(text)
        except ValueError as exc:
            raise ValueError(f'Cannot safely update {key}; use a [{section}] table with simple assignments.') from exc
        if parsed != expected:
            raise ValueError(f'Cannot safely update {key}; unrelated TOML would change.')
    atomic_write(path, text)
    return path
