import typer
from crux.config.manager import load
from crux.render.renderer import Renderer


def context(ctx, no_color=False):
    renderer = Renderer(no_color or bool((ctx.obj or {}).get('no_color')))
    config = load()
    for warning in config.warnings:
        typer.echo(f'Warning: {warning}', err=True)
    return renderer, config


def fail(exc):
    typer.echo(f'Error: {exc}', err=True)
    raise typer.Exit(1)
