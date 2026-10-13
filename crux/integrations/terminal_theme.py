"""Guarded persistence and recovery of GNOME Terminal's managed colors."""
import ast
import configparser
import json
import os
import shutil
import subprocess
from uuid import UUID

from crux.core.storage import atomic_write
from crux.render.theme import TERMINAL_THEMES

MANAGED_KEYS = (
    'background-color', 'foreground-color', 'palette', 'cursor-background-color',
    'cursor-foreground-color', 'cursor-colors-set', 'bold-color-same-as-fg', 'use-theme-colors',
)


def _run(args, **kwargs):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=5, **kwargs)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f'Could not update GNOME Terminal profile: {exc}') from exc
    if result.returncode or result.stderr.strip():
        raise RuntimeError(f'Could not update GNOME Terminal profile: {result.stderr.strip() or "command failed"}')
    return result.stdout


def _profile():
    if not os.environ.get('GNOME_TERMINAL_SERVICE'):
        return None
    if not shutil.which('gsettings') or not shutil.which('dconf'):
        raise RuntimeError('GNOME profile colors need gsettings and dconf installed.')
    value = _run(['gsettings', 'get', 'org.gnome.Terminal.ProfilesList', 'default']).strip().strip("'")
    try:
        profile = str(UUID(value))
    except ValueError as exc:
        raise RuntimeError('GNOME Terminal has no valid default profile.') from exc
    return profile, f'/org/gnome/terminal/legacy/profiles:/:{profile}/'


def _colors(text):
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    try:
        parser.read_string(text)
    except configparser.Error as exc:
        raise RuntimeError('Invalid GNOME backup/state; no restoration attempted.') from exc
    section = dict(parser['/']) if parser.has_section('/') else {}
    return {key: section.get(key) for key in MANAGED_KEYS}


def _read(path):
    if path.is_symlink():
        raise ValueError(f'Refusing symlinked recovery data: {path}')
    return path.read_text(encoding='utf-8')


def sync_gnome_profile(name, backup_directory):
    profile = _profile()
    if profile is None:
        return False
    profile_id, path = profile
    original = _run(['dconf', 'dump', path])
    _colors(original)  # Validate the recovery data before changing anything.
    backup_directory.mkdir(parents=True, exist_ok=True)
    backup = backup_directory / f'gnome-terminal-{profile_id}.backup.ini'
    if backup.exists() or backup.is_symlink():
        _colors(_read(backup))
    else:
        # Exclusive creation keeps the very first backup. Do not replace it.
        with backup.open('x', encoding='utf-8') as stream:
            stream.write(original)
    state_path = backup_directory / f'gnome-terminal-{profile_id}.applied.json'
    if state_path.is_symlink():
        raise ValueError('Refusing symlinked GNOME recovery state.')
    palette = TERMINAL_THEMES[name]
    settings = {
        'background-color': repr(palette['background']),
        'foreground-color': repr(palette['foreground']),
        'palette': repr(list(palette['ansi'])),
        'cursor-background-color': repr(palette['cursor']),
        'cursor-foreground-color': repr(palette['background']),
        'cursor-colors-set': 'true', 'bold-color-same-as-fg': 'true', 'use-theme-colors': 'false',
    }
    body = '[/]\n' + ''.join(f'{key}={value}\n' for key, value in settings.items())
    _run(['dconf', 'load', path], input=body)
    schema = f'org.gnome.Terminal.Legacy.Profile:{path}'
    actual = _run(['gsettings', 'get', schema, 'background-color']).strip().strip("'")
    if actual.lower() != palette['background']:
        raise RuntimeError('GNOME Terminal did not save the selected background color.')
    applied = _colors(_run(['dconf', 'dump', path]))
    def normalized(value):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value
    if any(value is None or normalized(value) != normalized(settings[key]) for key, value in applied.items()):
        raise RuntimeError('Could not verify applied GNOME colors; preserve backup for manual recovery.')
    atomic_write(state_path, json.dumps({'profile': profile_id, 'colors': applied}, indent=2))
    return True


def restore_gnome_profile(backup_directory, dry_run=False):
    """Restore only owned keys if they still match our last verified write.

    Never load the full backup: unrelated settings may have changed since sync.
    An older backup without ownership state requires manual recovery instead.
    """
    profile = _profile()
    if profile is None:
        return False
    profile_id, path = profile
    backup = backup_directory / f'gnome-terminal-{profile_id}.backup.ini'
    state_path = backup_directory / f'gnome-terminal-{profile_id}.applied.json'
    try:
        original = _colors(_read(backup))
        state = json.loads(_read(state_path))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f'No valid verified recovery state. Keep {backup} and restore colors manually: {exc}') from exc
    if not isinstance(state, dict) or state.get('profile') != profile_id or not isinstance(state.get('colors'), dict):
        raise RuntimeError('Invalid GNOME ownership state; no changes made.')
    expected = state['colors']
    if set(expected) != set(MANAGED_KEYS) or any(not isinstance(v, str) for v in expected.values()):
        raise RuntimeError('Invalid GNOME ownership colors; no changes made.')
    current = _colors(_run(['dconf', 'dump', path]))
    if current == original:
        return True  # Already restored, also lets the CLI disable prompt palettes.
    if current != expected:
        raise RuntimeError('GNOME colors changed since CRUX last applied them; refusing to overwrite newer settings. Keep the backup for manual recovery.')
    if dry_run:
        return True
    for key, value in original.items():
        if value is None:
            _run(['dconf', 'reset', path + key])
        else:
            _run(['dconf', 'write', path + key, value])
    if _colors(_run(['dconf', 'dump', path])) != original:
        raise RuntimeError('GNOME color restoration did not verify; backup and ownership state retained.')
    return True
