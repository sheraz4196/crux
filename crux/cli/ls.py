from pathlib import Path
import typer
from crux.cli.main import app
from crux.cli.common import context, fail
from crux.core.filesystem import scan, human_size


@app.command('_ls', hidden=True)
def listing(ctx: typer.Context, path: Path = typer.Argument(Path('.')), hidden: bool = typer.Option(False, '--hidden', '-a'), long: bool = typer.Option(False, '--long', '-l'), size: bool = typer.Option(False, '--size'), no_color: bool = typer.Option(False, '--no-color')):
    """List a directory, with optional hidden entries and file sizes."""
    renderer, config = context(ctx, no_color)
    try:
        entries = scan(path, hidden)
    except OSError as exc:
        fail(exc)
    for entry in entries:
        label = renderer.icon(entry.directory, config.data['general']['icons'] and config.data['ls']['show_icons']) + entry.path.name + ('/' if entry.directory else '')
        if entry.symlink:
            label += ' [symlink]'
        if not entry.directory and (long or size or config.data['ls']['show_sizes']):
            label += '  ' + human_size(entry.size)
        if entry.error:
            label += ' [unavailable]'
        renderer.line(label, 'directory' if entry.directory else 'file')
    directories = sum(e.directory for e in entries)
    renderer.line(f'{directories} directories, {len(entries)-directories} files', 'muted')
