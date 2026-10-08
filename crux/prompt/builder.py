import os
from pathlib import Path
from crux.config.manager import load
from crux.core.environment import virtual_environment
from crux.core.git import in_repository, status
from crux.core.text import safe_text


def build(exit_status=0, path=None, configuration=None):
    path = Path(path or Path.cwd()).resolve()
    config = (configuration or load()).data
    if not config["prompt"]["enabled"]:
        return "> "
    home = Path.home()
    label = "~" + str(path)[len(str(home)):] if path == home or home in path.parents else str(path)
    parts = [label]
    if config["prompt"]["show_git"] and config["git"]["enabled"] and in_repository(path):
        try:
            git = status(path, timeout=0.03)
            parts.append(f"{git.branch} {'*' if git.changes else 'clean'}")
            if git.ahead or git.behind:
                parts.append(f"+{git.ahead}/-{git.behind}")
        except ValueError:
            pass
    if config["prompt"]["show_python"] and (venv := virtual_environment()):
        parts.append(f"({venv})")
    if config["prompt"]["show_node"] and (path / "package.json").is_file():
        # No version subprocess on every prompt; expose the project environment.
        parts.append("node project")
    if exit_status:
        parts.append(f"exit {exit_status}")
    return safe_text("  ".join(parts)) + "\n> "
