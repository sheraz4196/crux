import json
import subprocess
import sys
from typer.testing import CliRunner
from crux.cli.main import app

runner = CliRunner()


def test_commands(tmp_path):
    for args in (['--version'], ['--help'], ['config'], ['doctor', '--json'], ['ls', str(tmp_path)], ['tree', str(tmp_path)], ['git', '--help'], ['init', '--help'], ['uninstall', '--help']):
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.output
        assert '\x1b' not in result.output
    assert json.loads(runner.invoke(app, ['doctor', '--json']).output)['system']


def test_errors_and_literal_names(tmp_path):
    (tmp_path / '[bold]name').touch()
    result = runner.invoke(app, ['ls', str(tmp_path), '--no-color'])
    assert '[bold]name' in result.output
    assert runner.invoke(app, ['ls', str(tmp_path / 'missing')]).exit_code == 1
    assert runner.invoke(app, ['tree', '--depth', '-1']).exit_code != 0
    assert runner.invoke(app, ['git', 'status', str(tmp_path)]).exit_code == 1


def test_tree_bounds(tmp_path):
    child = tmp_path / 'child'
    child.mkdir()
    (child / 'deep').touch()
    result = runner.invoke(app, ['tree', str(tmp_path), '--depth', '1'])
    assert 'child' in result.output and 'deep' not in result.output
    for i in range(4): (tmp_path / str(i)).touch()
    assert 'truncated' in runner.invoke(app, ['tree', str(tmp_path), '--max-entries', '1']).output


def test_real_cli():
    result = subprocess.run([sys.executable, '-m', 'crux', '--version'], capture_output=True, text=True)
    assert result.returncode == 0 and '0.1.0' in result.stdout
    result = subprocess.run([sys.executable, '-m', 'crux', 'prompt', '--status', '7'], capture_output=True, text=True)
    assert result.returncode == 0 and 'exit 7' in result.stdout
