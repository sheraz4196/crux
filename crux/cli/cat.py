"""Readable source files without changing native cat's stream semantics."""
import stat
from pathlib import Path

import typer
from pygments.lexers import guess_lexer_for_filename, guess_lexer, TextLexer
from pygments.util import ClassNotFound
from rich import box
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from crux.cli.main import app
from crux.cli.common import context
from crux.core.text import safe_text
from crux.render.code import syntax_theme

MAX_FILE_BYTES = 2 * 1024 * 1024


def read_source(path):
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('The viewer requires a regular text file; use native cat for streams/devices.')
    with path.open('rb') as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError('File exceeds the 2 MiB viewer limit; use native cat for large files.')
    encoding = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    try:
        source = data.decode(encoding)
    except UnicodeError as exc:
        raise ValueError('File is not UTF-8 or BOM-marked UTF-16 text; use native cat for raw output.') from exc
    if '\x00' in source:
        raise ValueError('Binary file; use native cat for raw output.')
    # Preserve indentation and line breaks, but never execute embedded terminal
    # controls (including escape sequences and bidirectional control characters).
    source = ''.join(c if c in '\n\r\t' or c.isprintable() else safe_text(c) for c in source)
    source = source.replace('\r\n', '\n').replace('\r', '\\x0d')
    return source


def detect_lexer(path, source):
    options = {'stripnl': False, 'ensurenl': False}
    try:
        return guess_lexer_for_filename(path.name, source[:8192], **options)
    except ClassNotFound:
        if source.startswith('#!'):
            try:
                return guess_lexer(source[:8192], **options)
            except ClassNotFound:
                pass
        return TextLexer(**options)


@app.command('view')
@app.command('_cat', hidden=True)
def view(ctx: typer.Context, paths: list[Path] = typer.Argument(...), no_color: bool = typer.Option(False, '--no-color')):
    """Show text/code files with syntax colours, line numbers and wrapping."""
    renderer, config = context(ctx, no_color)
    failed = False
    for path in paths:
        try:
            source = read_source(path)
        except (OSError, ValueError) as exc:
            typer.echo(f'Error: {safe_text(path)}: {safe_text(exc)}', err=True)
            failed = True
            continue
        lexer = detect_lexer(path, source)
        lines = len(source.splitlines())
        title = Text(safe_text(path.name), style='primary')
        separator = ' · ' if renderer.capabilities.unicode else ' | '
        subtitle = Text(f'{lexer.name}{separator}{lines} {"line" if lines == 1 else "lines"}', style='muted')
        content = Syntax(source, lexer, theme=syntax_theme(config.data['general']['theme']),
                         line_numbers=True, word_wrap=True, tab_size=4,
                         background_color='default', padding=(0, 1)) if source else Text('(empty file)', style='muted')
        renderer.console.print(Panel(content, title=title, title_align='left', subtitle=subtitle,
                                     subtitle_align='right', border_style='muted',
                                     box=box.ROUNDED if renderer.capabilities.unicode else box.ASCII))
    if failed:
        raise typer.Exit(1)
