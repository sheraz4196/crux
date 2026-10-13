"""Inspect and edit validated settings while retaining unrelated TOML."""
import json
import typer
from crux.cli.main import app
from crux.core.text import safe_text
from crux.cli.common import context, fail
from crux.config.manager import DEFAULTS, default_value, load, parse_value, update

subapp = typer.Typer(help='Inspect or edit configuration.', invoke_without_command=True)
app.add_typer(subapp, name='config')


@subapp.callback()
def show(ctx: typer.Context, json_output: bool = typer.Option(False, '--json'), no_color: bool = typer.Option(False, '--no-color')):
    if ctx.invoked_subcommand:
        return
    renderer, config = context(ctx, no_color)
    if json_output:
        typer.echo(json.dumps(config.data, indent=2))
        return
    renderer.line(f'Configuration: {config.path}', 'primary')
    for section, values in config.data.items():
        renderer.line(f'[{section}]', 'secondary')
        for key, value in values.items():
            renderer.line(f'  {key} = {value}')


@subapp.command('get')
def get(key: str):
    """Print the effective value of SECTION.KEY as a JSON scalar."""
    try:
        default_value(key)
        section, name = key.split('.')
        config = load()
        for warning in config.warnings:
            typer.echo(f'Warning: {safe_text(warning)}', err=True)
        typer.echo(json.dumps(config.data[section][name]))
    except ValueError as exc:
        fail(exc)


@subapp.command('set')
def set_value(key: str, value: str):
    """Persist a validated value; booleans accept true or false."""
    try:
        path = update({key: parse_value(key, value)})
        typer.echo(f'Updated {key}: {path}')
    except (OSError, ValueError) as exc:
        fail(exc)


@subapp.command('reset')
def reset(key: str = typer.Argument(None), yes: bool = typer.Option(False, '--yes', '-y')):
    """Reset one setting, or confirm resetting all known settings to defaults."""
    try:
        settings = {key: default_value(key)} if key else {
            f'{section}.{name}': value for section, values in DEFAULTS.items() for name, value in values.items()
        }
        if key is None and not yes:
            typer.confirm('Reset all CRUX settings to defaults? Unrelated TOML is retained.', abort=True)
        path = update(settings)
        typer.echo(f'Reset {key or "all CRUX settings"}: {path}')
    except (OSError, ValueError) as exc:
        fail(exc)
