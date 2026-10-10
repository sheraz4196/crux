"""Semantic output styles and lightweight ANSI prompt palettes."""
ROLES = {
    "primary": "bold bright_cyan", "secondary": "cyan", "success": "green",
    "warning": "yellow", "error": "bold red", "muted": "dim cyan",
    "directory": "bold bright_blue", "file": "white", "git": "magenta",
    "prompt": "bright_green",
}

THEMES = {
    "default": ROLES,
    "light": {
        "primary": "bold blue", "secondary": "magenta", "success": "green",
        "warning": "dark_orange", "error": "bold red", "muted": "dim blue",
        "directory": "bold magenta", "file": "blue", "git": "blue",
        "prompt": "magenta",
    },
    "monochrome": {role: "bold" if role in ("primary", "directory") else "default" for role in ROLES},
}

# No Rich import on the prompt startup path. Values are standard SGR codes.
PROMPT_COLORS = {
    "default": {"path": "1;96", "git": "95", "environment": "93", "error": "1;91", "frame": "90", "arrow": "1;92"},
    "light": {"path": "1;34", "git": "35", "environment": "36", "error": "1;31", "frame": "34", "arrow": "1;35"},
    "monochrome": {},
}
