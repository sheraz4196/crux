import json
import subprocess
import sys
from typer.testing import CliRunner
from crux.cli.main import app

runner = CliRunner()


def test_commands(tmp_path, monkeypatch):
    # Typer forces terminal styling under GITHUB_ACTIONS, even in captured help.
    # Exercise captured-output behavior independently of the CI host settings.
    import typer.rich_utils
    monkeypatch.setattr(typer.rich_utils, "FORCE_TERMINAL", None)
    for args in (['--version'], ['--help'], ['config'], ['doctor', '--json'], ['_ls', str(tmp_path)], ['_tree', str(tmp_path)], ['_git', '--help'], ['init', '--help'], ['uninstall', '--help']):
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.output
        assert '\x1b' not in result.output
    assert json.loads(runner.invoke(app, ['doctor', '--json']).output)['system']


def test_errors_and_literal_names(tmp_path):
    (tmp_path / '[bold]name').touch()
    result = runner.invoke(app, ['_ls', str(tmp_path), '--no-color'])
    assert '[bold]name' in result.output
    assert runner.invoke(app, ['_ls', str(tmp_path / 'missing')]).exit_code == 1
    assert runner.invoke(app, ['_tree', '--depth', '-1']).exit_code != 0
    assert runner.invoke(app, ['_git', 'status', str(tmp_path)]).exit_code == 1


def test_tree_bounds(tmp_path):
    child = tmp_path / 'child'
    child.mkdir()
    (child / 'deep').touch()
    result = runner.invoke(app, ['_tree', str(tmp_path), '--depth', '1'])
    assert 'child' in result.output and 'deep' not in result.output
    for i in range(4): (tmp_path / str(i)).touch()
    assert 'truncated' in runner.invoke(app, ['_tree', str(tmp_path), '--max-entries', '1']).output


def test_real_cli():
    result = subprocess.run([sys.executable, '-m', 'crux', '--version'], capture_output=True, text=True)
    assert result.returncode == 0 and '0.1.0' in result.stdout
    result = subprocess.run([sys.executable, '-m', 'crux', 'prompt', '--status', '7'], capture_output=True, text=True)
    assert result.returncode == 0 and 'exit 7' in result.stdout


def test_management_commands_and_theme(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
    monkeypatch.setenv('APPDATA', str(tmp_path))
    from crux.config.manager import load
    path = load().path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('# keep me\n[general]\nicons = false\n[prompt]\nshow_git = false\n')
    result = runner.invoke(app, ['theme', 'light'])
    assert result.exit_code == 0, result.output
    assert '\x1b' not in result.output
    assert load().data['general']['theme'] == 'light'
    assert not load().data['general']['icons']
    assert '# keep me' in path.read_text()
    before = path.read_text()
    assert runner.invoke(app, ['theme', 'missing']).exit_code == 1
    assert path.read_text() == before
    help_output = runner.invoke(app, ['--help']).output
    assert 'theme' in help_output and 'install' in help_output
    for name in ('ls', 'tree', 'git'):
        assert runner.invoke(app, [name]).exit_code != 0


def test_theme_applies_to_terminal(monkeypatch):
    import io
    from unittest.mock import patch
    from crux.cli.theme import theme
    import typer

    class Terminal(io.StringIO):
        def isatty(self): return True

    monkeypatch.setenv('TERM', 'xterm-256color')
    monkeypatch.delenv('NO_COLOR', raising=False)
    from typer.main import get_command
    ctx = typer.Context(get_command(app))
    ctx.obj = {}
    for name, background in [('light', '#f5f7fa'), ('default', '#171b24'), ('light', '#f5f7fa'), ('dark', '#171b24'), ('monochrome', '#181818')]:
        terminal = Terminal()
        with patch('sys.stdout', terminal):
            theme(ctx, name)
        output = terminal.getvalue()
        assert f'\x1b]11;{background}\x1b\\' in output
        assert '\x1b]10;' in output and '\x1b]12;' in output and '\x1b]4;' in output
        assert f'Theme changed to {name}.' in output
    for env, value in [('NO_COLOR', ''), ('TERM', 'dumb')]:
        with monkeypatch.context() as scoped:
            scoped.setenv(env, value)
            terminal = Terminal()
            with patch('sys.stdout', terminal):
                theme(ctx, 'light')
            assert '\x1b' not in terminal.getvalue()
    ctx.obj = {'no_color': True}
    terminal = Terminal()
    with patch('sys.stdout', terminal):
        theme(ctx, 'light')
    assert '\x1b' not in terminal.getvalue()
