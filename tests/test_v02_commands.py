import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner
from crux.cli.main import app
from crux.core.diagnostics import integration_health
from crux.integrations.manager import edit_profile

from test_core import repo  # noqa: F401 -- shared real-Git fixture

runner = CliRunner()


@pytest.mark.parametrize('name,private', [('ls', '_ls'), ('tree', '_tree')])
def test_public_private_equivalence_and_help(tmp_path, name, private):
    (tmp_path / 'source').touch()
    assert runner.invoke(app, [name, str(tmp_path)]).stdout == runner.invoke(app, [private, str(tmp_path)]).stdout
    assert runner.invoke(app, [name, '--help']).exit_code == 0
    assert runner.invoke(app, [name, str(tmp_path / 'missing')]).exit_code == 1
    assert runner.invoke(app, [name, '--unsupported']).exit_code != 0


def test_public_git_and_private(repo):
    path, git = repo
    (path / 'name with spaces').touch()
    git('mv', 'tracked', 'new name')
    public = runner.invoke(app, ['git', 'status', str(path)])
    assert public.exit_code == 0 and 'tracked -> new name' in public.stdout
    assert 'name with spaces' in public.stdout
    assert public.stdout == runner.invoke(app, ['_git', 'status', str(path)]).stdout


def test_listing_json_raw_names_and_counts(tmp_path):
    (tmp_path / 'dir').mkdir()
    (tmp_path / '.hidden').touch()
    (tmp_path / '[bold]literal').write_bytes(b'abc')
    result = runner.invoke(app, ['ls', str(tmp_path), '--json'])
    assert result.exit_code == 0 and '\x1b' not in result.stdout
    data = json.loads(result.stdout)
    assert data['schema_version'] == 1 and data['directories'] == 1 and data['files'] == 1
    assert data['entries'][0]['name'] == 'dir'
    assert data['entries'][1]['size'] == 3 and data['entries'][1]['name'] == '[bold]literal'
    assert len(json.loads(runner.invoke(app, ['ls', str(tmp_path), '--json', '-a']).stdout)['entries']) == 3
    if __import__('os').name != 'nt':
        name = 'control\x1b[2J'
        (tmp_path / name).touch()
        assert name in [e['name'] for e in json.loads(runner.invoke(app, ['ls', str(tmp_path), '--json']).stdout)['entries']]
        assert '\x1b' not in runner.invoke(app, ['ls', str(tmp_path)]).stdout


def test_tree_json_bounds_and_symlink(tmp_path):
    child = tmp_path / 'child'
    child.mkdir()
    (child / 'deep').touch()
    data = json.loads(runner.invoke(app, ['tree', str(tmp_path), '--depth', '0', '--json']).stdout)
    assert data['count'] == 0 and not data['truncated']
    data = json.loads(runner.invoke(app, ['tree', str(tmp_path), '--depth', '1', '--json']).stdout)
    assert data['count'] == 1 and data['entries'][0]['depth'] == 1
    (tmp_path / 'other').touch()
    data = json.loads(runner.invoke(app, ['tree', str(tmp_path), '--max-entries', '1', '--json']).stdout)
    assert data['count'] == 1 and data['truncated']
    link = child / 'cycle'
    try:
        link.symlink_to(tmp_path, target_is_directory=True)
    except OSError:
        pytest.skip('symlink creation unavailable')
    data = json.loads(runner.invoke(app, ['tree', str(tmp_path), '--json']).stdout)
    assert data['count'] == 4
    assert next(e for e in data['entries'] if e['name'] == 'cycle')['symlink']
    root = json.loads(runner.invoke(app, ['tree', str(link), '--json']).stdout)
    assert root['symlink'] and root['count'] == 0


def test_tree_inaccessible_child_json(tmp_path):
    from crux.core.filesystem import scan
    child = tmp_path / 'child'
    child.mkdir()
    def selective(path, hidden):
        if path == child:
            raise PermissionError('denied')
        return scan(path, hidden)
    with patch('crux.cli.tree.scan', side_effect=selective):
        result = runner.invoke(app, ['tree', str(tmp_path), '--json'])
    assert result.exit_code == 0
    assert json.loads(result.stdout)['errors'] == [{'path': str(child), 'error': 'denied'}]


def test_doctor_schema_profile_health_and_no_writes(tmp_path):
    profile = tmp_path / 'profile'
    result = runner.invoke(app, ['doctor', '--shell', 'bash', '--profile', str(profile), '--json'])
    data = json.loads(result.stdout)
    assert not profile.exists()
    assert {'system', 'shell', 'terminal', 'tools', 'virtual_environment', 'configuration', 'warnings'} <= data.keys()
    assert data['crux']['version'] and data['integration']['status'] == 'not installed'
    assert {'session', 'gsettings', 'dconf'} == data['gnome_profile_sync'].keys()
    edit_profile(profile, 'bash', keep_prompt=True)
    before = profile.read_bytes()
    data = json.loads(runner.invoke(app, ['doctor', '--shell', 'bash', '--profile', str(profile), '--json']).stdout)
    assert data['integration']['status'] == 'installed' and data['integration']['prompt_preserved']
    assert profile.read_bytes() == before
    profile.write_text('# >>> crux >>>\nbroken\n')
    assert integration_health('bash', profile)['status'] == 'invalid'
    assert integration_health('fish')['status'] == 'unsupported'
    assert integration_health('powershell')['status'] == 'profile required'
    profile.write_text('# >>> crux >>>\nunalias git ls tree cat\n# <<< crux <<<\n')
    assert integration_health('bash', profile)['status'] == 'legacy integration'


def test_palette_reset_no_redirected_controls_and_prompt_opt_out(tmp_path):
    from crux.config.manager import load
    from crux.prompt.builder import build
    result = runner.invoke(app, ['theme', '--reset-terminal'])
    assert result.exit_code == 0 and '\x1b' not in result.stdout
    config = load()
    assert not config.data['general']['terminal_palette']
    with patch.dict('os.environ', {'TERM': 'xterm'}, clear=True):
        assert '\x1b]' not in build(path=tmp_path, configuration=config, shell='bash')
    assert runner.invoke(app, ['theme', 'cobalt']).exit_code == 0
    assert load().data['general']['terminal_palette']
    assert runner.invoke(app, ['theme', 'light', '--reset-terminal']).exit_code == 1
    assert runner.invoke(app, ['theme', '--restore-profile']).exit_code == 1


def test_json_hidden_tree_and_entry_metadata_failure(tmp_path):
    (tmp_path / '.hidden').touch()
    assert json.loads(runner.invoke(app, ['tree', str(tmp_path), '--json']).stdout)['count'] == 0
    assert json.loads(runner.invoke(app, ['tree', str(tmp_path), '--json', '-a']).stdout)['count'] == 1
    with patch.object(Path, 'lstat', side_effect=PermissionError('metadata denied')):
        data = json.loads(runner.invoke(app, ['ls', str(tmp_path), '--json', '-a']).stdout)
    assert data['entries'][0]['size'] is None and data['entries'][0]['error'] == 'metadata denied'


def test_reset_terminal_controls_only_when_appropriate(monkeypatch):
    import io
    import typer
    from typer.main import get_command
    from crux.cli.theme import theme
    class Terminal(io.StringIO):
        def isatty(self):
            return True
    ctx = typer.Context(get_command(app))
    ctx.obj = {}
    monkeypatch.setenv('TERM', 'xterm')
    monkeypatch.delenv('NO_COLOR', raising=False)
    stream = Terminal()
    with patch('sys.stdout', stream):
        theme(ctx, None, reset_terminal=True)
    for code in (104, 110, 111, 112):
        assert f'\x1b]{code}\x1b\\' in stream.getvalue()
    monkeypatch.setenv('NO_COLOR', '')
    stream = Terminal()
    with patch('sys.stdout', stream):
        theme(ctx, None, reset_terminal=True)
    assert '\x1b' not in stream.getvalue()


def test_errors_and_configuration_warnings_escape_terminal_controls(tmp_path):
    from crux.config.manager import load
    result = runner.invoke(app, ['tree', str(tmp_path / 'missing\x1b[2J')])
    assert result.exit_code == 1 and '\x1b' not in result.output
    result = runner.invoke(app, ['config', 'set', 'unknown.\x1b[2J', 'false'])
    assert result.exit_code == 1 and '\x1b' not in result.output
    path = load().path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('[general]\ntheme = "\\u001b[2J"\n')
    for command in (['config'], ['config', 'get', 'general.theme'], ['doctor', '--json']):
        result = runner.invoke(app, command)
        assert result.exit_code == 0 and '\x1b' not in result.output
