import json
import typer
from crux.cli.main import app
from crux.cli.common import context


@app.command('config')
def show(ctx: typer.Context, json_output: bool = typer.Option(False, '--json'), no_color: bool = typer.Option(False, '--no-color')):
    """Inspect effective TOML configuration without modifying it."""
    renderer, config = context(ctx, no_color)
    if json_output:
        typer.echo(json.dumps(config.data, indent=2))
        return
    renderer.line(f'Configuration: {config.path}', 'primary')
    for section, values in config.data.items():
        renderer.line(f'[{section}]', 'secondary')
        for key, value in values.items():
            renderer.line(f'  {key} = {value}')
