"""Semantic styles, prompt colours, and terminal-wide palettes."""
ROLES = {
    "primary": "bold bright_cyan", "secondary": "cyan", "success": "green",
    "warning": "yellow", "error": "bold red", "muted": "dim cyan",
    "directory": "bold bright_blue", "file": "white", "git": "magenta",
    "prompt": "bright_green",
}

THEMES = {
    "default": ROLES,
    "dark": ROLES,
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
PROMPT_COLORS["dark"] = PROMPT_COLORS["default"]

# ANSI slots 0–7 and their bright counterparts 8–15. Keep light-theme
# colours dark enough to read against its background, including bold text.
TERMINAL_THEMES = {
    "default": {
        "background": "#171b24", "foreground": "#e6edf3", "cursor": "#e6edf3",
        "ansi": ("#202632", "#f07178", "#8bd49c", "#e5c07b",
                 "#82aaff", "#c792ea", "#89ddff", "#c8d3e0",
                 "#7f8c9f", "#ff8b92", "#a3e6b5", "#ffe19c",
                 "#a6c8ff", "#dfb5ff", "#b3edff", "#ffffff"),
    },
    "light": {
        "background": "#f5f7fa", "foreground": "#24292f", "cursor": "#24292f",
        "ansi": ("#24292f", "#b42332", "#246b36", "#805500",
                 "#2456a6", "#7936a6", "#176575", "#4b5563",
                 "#667085", "#a2192b", "#195c2b", "#704800",
                 "#17478f", "#692b91", "#0e5868", "#343b45"),
    },
    "monochrome": {
        "background": "#181818", "foreground": "#e0e0e0", "cursor": "#ffffff",
        "ansi": ("#181818",) + ("#bcbcbc",) * 7 + ("#808080",) + ("#e0e0e0",) * 7,
    },
}
TERMINAL_THEMES["dark"] = TERMINAL_THEMES["default"]


def terminal_sequences(name):
    """Set default text, background, cursor and all sixteen ANSI colours.

    OSC sequences use ST terminators and contain only our fixed palette data.
    Callers decide whether their output is an interactive terminal or a shell
    prompt, and honour NO_COLOR before emitting these controls.
    """
    theme = TERMINAL_THEMES.get(name, TERMINAL_THEMES["default"])
    def osc(value):
        return f"\x1b]{value}\x1b\\"
    result = "".join(osc(f"{code};{theme[role]}") for code, role in
                     ((10, "foreground"), (11, "background"), (12, "cursor")))
    result += osc("4;" + ";".join(f"{index};{value}" for index, value in enumerate(theme["ansi"])))
    return result
