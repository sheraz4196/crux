import typer
from crux.config.manager import load
from crux.render.renderer import Renderer
from crux.core.text import safe_text


def context(ctx, no_color=False):
    config = load()
    renderer = Renderer(no_color or bool((ctx.obj or {}).get('no_color')), theme=config.data['general']['theme'])
    for warning in config.warnings:
        typer.echo(f'Warning: {safe_text(warning)}', err=True)
    return renderer, config


def fail(exc):
    typer.echo(f'Error: {safe_text(exc)}', err=True)
    raise typer.Exit(1)
