ROLES = {"primary": "bold cyan", "secondary": "cyan", "success": "green", "warning": "yellow", "error": "red", "muted": "dim", "directory": "bold blue", "file": "default", "git": "magenta", "prompt": "cyan"}

THEMES = {
    "default": ROLES,
    "light": {**ROLES, "primary": "bold blue", "secondary": "blue", "directory": "bold magenta", "prompt": "blue"},
    "monochrome": {role: "bold" if role in ("primary", "directory") else "default" for role in ROLES},
}
