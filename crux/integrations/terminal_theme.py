"""Persist GNOME Terminal colours before the shell's first prompt is drawn."""
import os
import shutil
import subprocess
from uuid import UUID

from crux.render.theme import TERMINAL_THEMES


def sync_gnome_profile(name, backup_directory):
    """Update the default GNOME profile, preserving its original settings once.

    Other emulators continue to use OSC colours. This runs only on theme
    selection, never on the prompt path. dconf loads the colours together in
    one transaction, leaving fonts, scrolling and other preferences intact.
    """
    if not os.environ.get("GNOME_TERMINAL_SERVICE"):
        return False
    if not shutil.which("gsettings") or not shutil.which("dconf"):
        raise RuntimeError("GNOME profile colours need gsettings and dconf installed.")

    def run(args, **kwargs):
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=5, **kwargs)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(f"Could not update GNOME Terminal profile: {exc}") from exc
        # dconf may report a failed commit on stderr with a zero exit status.
        if result.returncode or result.stderr.strip():
            raise RuntimeError(f"Could not update GNOME Terminal profile: {result.stderr.strip() or 'command failed'}")
        return result.stdout

    profile = run(["gsettings", "get", "org.gnome.Terminal.ProfilesList", "default"]).strip().strip("'")
    try:
        profile = str(UUID(profile))
    except ValueError as exc:
        raise RuntimeError("GNOME Terminal has no valid default profile.") from exc
    path = f"/org/gnome/terminal/legacy/profiles:/:{profile}/"
    original = run(["dconf", "dump", path])
    backup_directory.mkdir(parents=True, exist_ok=True)
    backup = backup_directory / f"gnome-terminal-{profile}.backup.ini"
    try:
        with backup.open("x", encoding="utf-8") as stream:
            stream.write(original)
    except FileExistsError:
        pass
    palette = TERMINAL_THEMES[name]
    settings = {
        "background-color": repr(palette["background"]),
        "foreground-color": repr(palette["foreground"]),
        "palette": repr(list(palette["ansi"])),
        "cursor-background-color": repr(palette["cursor"]),
        "cursor-foreground-color": repr(palette["background"]),
        "cursor-colors-set": "true",
        "bold-color-same-as-fg": "true",
        "use-theme-colors": "false",
    }
    body = "[/]\n" + "".join(f"{key}={value}\n" for key, value in settings.items())
    run(["dconf", "load", path], input=body)
    schema = f"org.gnome.Terminal.Legacy.Profile:{path}"
    actual = run(["gsettings", "get", schema, "background-color"]).strip().strip("'")
    if actual.lower() != palette["background"]:
        raise RuntimeError("GNOME Terminal did not save the selected background colour.")
    return True
