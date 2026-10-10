import io
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from crux.cli.main import app
from crux.cli.cat import detect_lexer, read_source


@pytest.mark.parametrize('name,source,language', [
    ('app.py', 'def greet():\n    return "hello"\n', 'Python'),
    ('app.js', 'const answer = 42;\n', 'JavaScript'),
    ('config.json', '{"answer": 42}', 'JSON'),
    ('README.md', '# Hello\n', 'Markdown'),
    ('notes.unknown', 'some notes', 'Text only'),
    ('script', '#!/bin/bash\necho hello\n', 'Bash'),
])
def test_file_detection_and_rendering(tmp_path, name, source, language):
    path = tmp_path / name
    path.write_text(source, encoding='utf-8')
    assert detect_lexer(path, source).name == language
    result = CliRunner().invoke(app, ['view', str(path)])
    assert result.exit_code == 0, result.output
    assert name in result.output and language in result.output
    assert '\x1b' not in result.output


def test_preserve_indentation_and_escape_controls(tmp_path):
    path = tmp_path / '[bold]demo.py'
    path.write_bytes(b'\xef\xbb\xbfdef f():\r\n\treturn "\x1b]0;bad\x07"\r\n')
    source = read_source(path)
    assert source.startswith('def f():\n\treturn')
    assert '\x1b' not in source and '\\x1b' in source and '\\x07' in source
    result = CliRunner().invoke(app, ['view', str(path)])
    assert '[bold]demo.py' in result.output


def test_errors_empty_file_and_multiple_files(tmp_path):
    empty = tmp_path / 'empty.txt'
    empty.touch()
    binary = tmp_path / 'binary'
    binary.write_bytes(b'\x00\x01')
    large = tmp_path / 'large'
    large.write_bytes(b'a' * (2 * 1024 * 1024 + 1))
    result = CliRunner().invoke(app, ['view', str(binary), str(empty), str(large), str(tmp_path / 'missing')])
    assert result.exit_code == 1
    assert 'Binary file' in result.output
    assert '(empty file)' in result.output and '0 lines' in result.output
    assert '2 MiB' in result.output and 'missing' in result.output


def test_cobalt_highlighting_and_no_color(tmp_path, monkeypatch):
    from crux.cli.cat import view
    from crux.config.manager import load
    from typer.main import get_command
    import typer

    class Terminal(io.StringIO):
        encoding = 'utf-8'
        def isatty(self): return True

    monkeypatch.setenv('TERM', 'xterm-256color')
    monkeypatch.setenv('COLORTERM', 'truecolor')
    monkeypatch.delenv('NO_COLOR', raising=False)
    config = load().path
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('[general]\ntheme="cobalt"\n')
    path = tmp_path / 'app.py'
    path.write_text('def greet():\n    return "hello"\n')
    ctx = typer.Context(get_command(app), obj={})
    terminal = Terminal()
    with patch('sys.stdout', terminal):
        view(ctx, [path], no_color=False)
    output = terminal.getvalue()
    assert '38;2;255;157;0' in output  # Cobalt orange keywords
    assert '38;2;165;255;144' in output  # Cobalt green strings
    monkeypatch.setenv('NO_COLOR', '')
    terminal = Terminal()
    with patch('sys.stdout', terminal):
        view(ctx, [path], no_color=False)
    assert '\x1b' not in terminal.getvalue()
