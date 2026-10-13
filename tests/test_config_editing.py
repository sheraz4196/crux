import os
import tomllib
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner
from crux.cli.main import app
from crux.config.manager import DEFAULTS, load, update

runner = CliRunner()


def test_get_set_reset_preserve_unknown_and_comments():
    path = load().path
    path.parent.mkdir(parents=True)
    path.write_text('# personal\n[general] # group\nicons = false # icon preference\n[prompt]\nshow_git = false\n[other]\nmessage = "keep # literal"\n')
    assert runner.invoke(app, ['config', 'get', 'general.theme']).stdout.strip() == '"default"'
    assert runner.invoke(app, ['config', 'set', 'general.theme', 'cobalt']).exit_code == 0
    assert runner.invoke(app, ['config', 'set', 'prompt.show_git', 'true']).exit_code == 0
    assert runner.invoke(app, ['config', 'reset', 'general.icons']).exit_code == 0
    assert '# personal' in path.read_text() and '# icon preference' in path.read_text()
    assert tomllib.loads(path.read_text())['other']['message'] == 'keep # literal'
    before = path.read_bytes()
    assert runner.invoke(app, ['config', 'reset'], input='n\n').exit_code != 0
    assert path.read_bytes() == before
    assert runner.invoke(app, ['config', 'reset', '--yes']).exit_code == 0
    assert load().data == DEFAULTS
    assert tomllib.loads(path.read_text())['other']['message'] == 'keep # literal'


@pytest.mark.parametrize('key,value', [('unknown.key', 'true'), ('general.icons', '1'), ('prompt.show_git', 'yes'), ('general.theme', 'missing')])
def test_invalid_values_do_not_create_file(key, value):
    assert runner.invoke(app, ['config', 'set', key, value]).exit_code == 1
    assert not load().path.exists()
    assert runner.invoke(app, ['config', 'get', 'unknown.key']).exit_code == 1
    assert runner.invoke(app, ['config', 'reset', 'unknown.key']).exit_code == 1


@pytest.mark.parametrize('text', ['bad toml !', 'general = {icons = false}\n', '[general]\n"icons" = false\n', '[general]\ntheme = """default\n"""\n'])
def test_refuse_unsafe_layout_without_modification(tmp_path, text):
    path = tmp_path / 'config'
    path.write_text(text)
    with pytest.raises(ValueError):
        update({'general.icons': True, 'general.theme': 'cobalt'}, path)
    assert path.read_text() == text


def test_atomic_failure_and_mode(tmp_path):
    path = tmp_path / 'config'
    path.write_text('[general]\nicons = false\n')
    if os.name != 'nt':
        path.chmod(0o640)
    with patch('crux.core.storage.os.replace', side_effect=PermissionError('denied')):
        with pytest.raises(PermissionError):
            update({'general.icons': True}, path)
    assert path.read_text() == '[general]\nicons = false\n'
    assert not list(tmp_path.glob('.crux-*'))
    update({'general.icons': True}, path)
    if os.name != 'nt':
        assert path.stat().st_mode & 0o777 == 0o640


def test_missing_file_header_at_eof_and_symlink(tmp_path):
    path = tmp_path / 'nested' / 'config'
    update({'prompt.show_git': False}, path)
    assert not load(path).data['prompt']['show_git']
    path.write_text('[general]')
    update({'general.icons': False}, path)
    assert not load(path).data['general']['icons']
    link = tmp_path / 'link'
    try:
        link.symlink_to(path)
    except OSError:
        pytest.skip('symlink creation unavailable')
    before = path.read_bytes()
    with pytest.raises(ValueError, match='symlink'):
        update({'general.icons': True}, link)
    assert path.read_bytes() == before


def test_permission_error_is_actionable():
    with patch('crux.config.manager.update', side_effect=PermissionError('denied')):
        # Patch the imported CLI binding rather than a real personal directory.
        with patch('crux.cli.config.update', side_effect=PermissionError('denied')):
            result = runner.invoke(app, ['config', 'set', 'general.icons', 'false'])
    assert result.exit_code == 1 and 'denied' in result.output and 'Traceback' not in result.output
