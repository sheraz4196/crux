"""Inspect and persist the display theme without losing unrelated TOML."""
import os
import re
import tempfile
import tomllib
import typer
from crux.cli.main import app
from crux.cli.common import fail
from crux.config.manager import load
from crux.render.theme import THEMES, terminal_sequences
from crux.core.terminal import detect


@app.command()
def theme(ctx: typer.Context, name: str = typer.Argument(None)):
    """Show the current theme, or select default, dark, light, or monochrome."""
    config = load()
    if name is None:
        typer.echo(f"Theme: {config.data['general']['theme']}\nAvailable: {', '.join(THEMES)}")
        return
    if name not in THEMES:
        fail(ValueError(f"Unknown theme: {name}. Choose {', '.join(THEMES)}."))
    path = config.path
    try:
        if path.is_symlink():
            raise ValueError('Refusing to replace a symlinked configuration.')
        text = path.read_text(encoding='utf-8') if path.exists() else ''
        tomllib.loads(text)  # Refuse malformed files rather than overwriting them.
        section = re.search(r'^\[general\][ \t]*(?:#.*)?\n(?P<body>.*?)(?=^\[|\Z)', text, re.M | re.S)
        setting = f'theme = "{name}"\n'
        if section:
            body = section.group('body')
            if re.search(r'^theme\s*=', body, re.M):
                body = re.sub(r'^theme\s*=.*(?:\n|$)', setting, body, count=1, flags=re.M)
            else:
                body = setting + body
            text = text[:section.start('body')] + body + text[section.end('body'):]
        else:
            text += ('\n' if text and not text.endswith('\n') else '') + '[general]\n' + setting
        parsed = tomllib.loads(text)
        if parsed.get('general', {}).get('theme') != name:
            raise ValueError('Cannot safely update this TOML layout; use a [general] section.')
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix='.crux-', dir=path.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(text)
            if path.exists():
                os.chmod(temporary, path.stat().st_mode)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    except (OSError, ValueError) as exc:
        fail(exc)
    if detect(no_color=bool((ctx.obj or {}).get('no_color'))).color:
        typer.echo(terminal_sequences(name), nl=False)
    typer.echo(f'Theme changed to {name}.')
