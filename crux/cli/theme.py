"""Inspect and persist the display theme without losing unrelated TOML."""
import typer
from crux.cli.main import app
from crux.core.text import safe_text
from crux.cli.common import fail
from crux.config.manager import load, update
from crux.render.theme import THEMES, terminal_sequences
from crux.core.terminal import detect
from crux.integrations.terminal_theme import sync_gnome_profile, restore_gnome_profile


@app.command()
def theme(ctx: typer.Context, name: str = typer.Argument(None), sync_profile: bool = typer.Option(False, '--sync-profile', help='Also save GNOME Terminal default-profile colors when output is redirected.'), restore_profile: bool = typer.Option(False, '--restore-profile', help='Restore backed-up GNOME colors only if no newer color changes exist.'), reset_terminal: bool = typer.Option(False, '--reset-terminal', help='Disable prompt palette writes and reset OSC colors to emulator defaults.')):
    """Show the current theme, or select default, dark, light, cobalt, or monochrome."""
    config = load()
    if restore_profile is True or reset_terminal is True:
        if name is not None or sync_profile is True or (restore_profile is True and reset_terminal is True):
            fail(ValueError('Choose a theme name, --restore-profile, or --reset-terminal separately.'))
        try:
            if restore_profile is True and not restore_gnome_profile(config.path.parent, dry_run=True):
                fail(ValueError('GNOME recovery requires a GNOME Terminal session; other profiles are unchanged.'))
            update({'general.terminal_palette': False}, config.path)
            if restore_profile is True:
                restore_gnome_profile(config.path.parent)
        except (OSError, RuntimeError, ValueError) as exc:
            fail(exc)
        color = detect(no_color=bool((ctx.obj or {}).get('no_color'))).color
        if color:
            typer.echo(''.join(f'\x1b]{code}\x1b\\' for code in (104, 110, 111, 112)), nl=False)
        if restore_profile is True:
            typer.echo('GNOME colors restored; prompt palette writes disabled.')
        else:
            typer.echo('Palette writes disabled; emulator reset requested.' if color else 'Palette writes disabled; rerun --reset-terminal in a color-capable terminal to request emulator defaults.')
        return
    if name is None:
        typer.echo(f"Theme: {config.data['general']['theme']}\nAvailable: {', '.join(THEMES)}")
        return
    if name not in THEMES:
        fail(ValueError(f"Unknown theme: {name}. Choose {', '.join(THEMES)}."))
    path = config.path
    try:
        update({'general.theme': name, 'general.terminal_palette': True}, path)
    except (OSError, ValueError) as exc:
        fail(exc)
    color = detect(no_color=bool((ctx.obj or {}).get('no_color'))).color
    if color or sync_profile is True:
        try:
            if sync_gnome_profile(name, path.parent):
                typer.echo('GNOME Terminal default-profile colours updated.')
        except (RuntimeError, OSError, ValueError) as exc:
            typer.echo(f'Warning: {safe_text(exc)}', err=True)
    if color:
        typer.echo(terminal_sequences(name), nl=False)
    typer.echo(f'Theme changed to {name}.')
