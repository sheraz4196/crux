from pathlib import Path
import typer
from crux.cli.main import app
from crux.cli.common import context, fail
from crux.core.git import status as git_status

subapp = typer.Typer(help='Present local Git information.')
app.add_typer(subapp, name='_git', hidden=True)


@subapp.command()
def status(ctx: typer.Context, path: Path = typer.Argument(Path('.')), no_color: bool = typer.Option(False, '--no-color')):
    """Show branch, ahead/behind counts and staged/unstaged changes."""
    renderer, config = context(ctx, no_color)
    if not config.data['git']['enabled']:
        renderer.line('Git integration is disabled.')
        return
    try:
        result = git_status(path)
    except ValueError as exc:
        fail(exc)
    renderer.line(f'Branch: {result.branch}', 'git')
    renderer.line(f'Ahead: {result.ahead}  Behind: {result.behind}')
    renderer.line('Changes (index / working tree):' if result.changes else 'Working tree clean', 'warning' if result.changes else 'success')
    for code, name in result.changes:
        renderer.line(f'  {code}  {name}')
    renderer.line(f'{len(result.changes)} changed files', 'muted')
