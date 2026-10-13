import json
from pathlib import Path
import typer
from crux.cli.main import app
from crux.cli.common import context, fail
from crux.core.filesystem import scan, entry_data


@app.command('tree')
@app.command('_tree', hidden=True)
def tree(ctx: typer.Context, path: Path = typer.Argument(Path('.')), depth: int = typer.Option(3, '--depth', min=0, max=100), hidden: bool = typer.Option(False, '--hidden', '-a'), no_color: bool = typer.Option(False, '--no-color'), max_entries: int = typer.Option(1000, '--max-entries', min=1), json_output: bool = typer.Option(False, '--json')):
    """Show a bounded tree; directory symlinks are never followed."""
    renderer, config = context(ctx, no_color)
    if not path.is_dir():
        fail(ValueError(f'Not an accessible directory: {path}'))
    records = []
    errors = []
    count = 0
    truncated = False
    unicode = renderer.capabilities.unicode
    icons = config.data['general']['icons']
    def visit(directory, prefix, level):
        nonlocal count, truncated
        if level >= depth:
            return
        try:
            entries = scan(directory, hidden)
        except OSError as exc:
            if level == 0:
                raise
            errors.append({'path': str(directory), 'error': str(exc)})
            if not json_output:
                renderer.line(prefix + f'[unavailable: {exc}]', 'warning')
            return
        for index, entry in enumerate(entries):
            if count >= max_entries:
                truncated = True
                return
            count += 1
            last = index == len(entries) - 1
            branch = ('└── ' if last else '├── ') if unicode else ('`-- ' if last else '|-- ')
            records.append({**entry_data(entry), 'relative_path': str(entry.path.relative_to(path)), 'depth': level + 1})
            if not json_output:
                renderer.line(prefix + branch + renderer.icon(entry.directory, icons) + entry.path.name + ('/' if entry.directory else '') + (' [symlink]' if entry.symlink else ''), 'directory' if entry.directory else 'file')
            if entry.directory and not entry.symlink:
                visit(entry.path, prefix + ('    ' if last else '│   ' if unicode else '|   '), level + 1)
    if not json_output:
        renderer.line(str(path) + '/', 'directory')
    try:
        if not path.is_symlink():
            visit(path, '', 0)
    except OSError as exc:
        fail(exc)
    if json_output:
        typer.echo(json.dumps({'schema_version': 1, 'path': str(path), 'symlink': path.is_symlink(), 'entries': records, 'errors': errors, 'count': count, 'depth': depth, 'max_entries': max_entries, 'truncated': truncated}, indent=2))
        return
    if truncated:
        renderer.line(f'[truncated at {max_entries} entries]', 'warning')
