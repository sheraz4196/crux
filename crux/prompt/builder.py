import os
from pathlib import Path
from crux.config.manager import load
from crux.core.environment import virtual_environment
from crux.core.git import in_repository, status
from crux.core.text import safe_text
from crux.core.terminal import detect
from crux.render.theme import PROMPT_COLORS, terminal_sequences


def build(exit_status=0, path=None, configuration=None, shell="plain"):
    path = Path(path or Path.cwd()).resolve()
    config = (configuration or load()).data
    if not config["prompt"]["enabled"]:
        return "> "
    home = Path.home()
    label = "~" + str(path)[len(str(home)):] if path == home or home in path.parents else str(path)
    parts = [(label, "path")]
    if config["prompt"]["show_git"] and config["git"]["enabled"] and in_repository(path):
        try:
            git = status(path, timeout=0.03)
            parts.append((f"{git.branch} {'*' if git.changes else 'clean'}", "git"))
            if git.ahead or git.behind:
                parts.append((f"+{git.ahead}/-{git.behind}", "git"))
        except ValueError:
            pass
    if config["prompt"]["show_python"] and (venv := virtual_environment()):
        parts.append((f"({venv})", "environment"))
    if config["prompt"]["show_node"] and (path / "package.json").is_file():
        # No version subprocess on every prompt; expose the project environment.
        parts.append(("node project", "environment"))
    if exit_status:
        parts.append((f"exit {exit_status}", "error"))
    if shell == "plain":
        return safe_text("  ".join(value for value, _ in parts)) + "\n> "
    capabilities = detect()
    palette = PROMPT_COLORS.get(config["general"]["theme"], PROMPT_COLORS["default"])
    # Prompt output is captured by the shell, so stdout itself is not a TTY.
    color = os.environ.get("TERM") != "dumb" and "NO_COLOR" not in os.environ

    def control(sequence):
        if shell == "bash":
            return "\x01" + sequence + "\x02"
        if shell == "zsh":
            return "%{" + sequence + "%}"
        return sequence

    def paint(value, role):
        value = safe_text(value)
        if shell == "zsh":
            value = value.replace("%", "%%")
        code = palette.get(role)
        if not color or not code:
            return value
        return control(f"\x1b[{code}m") + value + control("\x1b[0m")

    top, bottom, arrow, separator = ("╭─", "╰─", "❯", " · ") if capabilities.unicode else ("+-", "+-", ">", " | ")
    content = paint(separator, "frame").join(paint(value, role) for value, role in parts)
    terminal = control(terminal_sequences(config["general"]["theme"])) if color else ""
    return terminal + paint(top, "frame") + " " + content + "\n" + paint(bottom, "frame") + " " + paint(arrow, "error" if exit_status else "arrow") + " "
