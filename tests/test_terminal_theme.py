import subprocess
from unittest.mock import patch

import pytest

from crux.integrations.terminal_theme import sync_gnome_profile


def test_profile_sync_preserves_preferences_and_original_backup(tmp_path, monkeypatch):
    monkeypatch.setenv('GNOME_TERMINAL_SERVICE', ':1.123')
    profile = 'b1dcc9dd-5262-4d8d-a863-c897e6d979b9'
    original = "[/]\nfont='Custom Font 12'\nscrollbar-policy='always'\n"
    state = {'background': '#122738', 'original': original}
    writes = []

    def run(args, **kwargs):
        if args[1] == 'dump':
            output = state['original']
        elif args[1] == 'load':
            writes.append(kwargs['input'])
            state['original'] = kwargs['input']
            output = ''
        elif args[-1] == 'default':
            output = repr(profile)
        else:
            output = repr(state['background'])
        return subprocess.CompletedProcess(args, 0, stdout=output, stderr='')

    with patch('crux.integrations.terminal_theme.shutil.which', return_value='/usr/bin/tool'), patch('crux.integrations.terminal_theme.subprocess.run', side_effect=run):
        assert sync_gnome_profile('cobalt', tmp_path)
        state['background'] = '#f5f7fa'
        assert sync_gnome_profile('light', tmp_path)
    assert (tmp_path / f'gnome-terminal-{profile}.backup.ini').read_text() == original
    assert "background-color='#122738'" in writes[0]
    assert "cursor-background-color='#ffc600'" in writes[0]
    assert 'use-theme-colors=false' in writes[0]
    assert "background-color='#f5f7fa'" in writes[1]
    assert all('font=' not in body and 'scrollbar-policy=' not in body for body in writes)


def test_other_terminals_do_not_change_desktop_profile(tmp_path):
    with patch('crux.integrations.terminal_theme.subprocess.run') as run:
        assert not sync_gnome_profile('cobalt', tmp_path)
    run.assert_not_called()


def test_dconf_failed_commit_is_reported(tmp_path, monkeypatch):
    monkeypatch.setenv('GNOME_TERMINAL_SERVICE', ':1.123')
    with patch('crux.integrations.terminal_theme.shutil.which', return_value='/usr/bin/tool'), patch('crux.integrations.terminal_theme.subprocess.run', return_value=subprocess.CompletedProcess([], 0, stdout='', stderr='failed to commit changes: Permission denied')):
        with pytest.raises(RuntimeError, match='Permission denied'):
            sync_gnome_profile('cobalt', tmp_path)
    assert not list(tmp_path.iterdir())


@pytest.fixture
def gnome_state(tmp_path, monkeypatch):
    import configparser
    monkeypatch.setenv('GNOME_TERMINAL_SERVICE', ':1.123')
    profile = 'b1dcc9dd-5262-4d8d-a863-c897e6d979b9'
    # Some original color keys are unset; restoration must reset those keys.
    state = {'background-color': "'#abcdef'", 'font': "'Original Font 12'", 'scrollbar-policy': "'always'"}
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        if args[1] == 'dump':
            output = '[/]\n' + ''.join(f'{k}={v}\n' for k, v in state.items())
        elif args[1] == 'load':
            parser = configparser.ConfigParser(interpolation=None)
            parser.read_string(kwargs['input'])
            state.update(dict(parser['/']))
            output = ''
        elif args[1] == 'reset':
            state.pop(args[-1].rsplit('/', 1)[-1], None)
            output = ''
        elif args[1] == 'write':
            state[args[-2].rsplit('/', 1)[-1]] = args[-1]
            output = ''
        elif args[-1] == 'default':
            output = repr(profile)
        else:
            output = state[args[-1]]
        return subprocess.CompletedProcess(args, 0, stdout=output, stderr='')
    monkeypatch.setattr('crux.integrations.terminal_theme.shutil.which', lambda name: '/usr/bin/' + name)
    monkeypatch.setattr('crux.integrations.terminal_theme.subprocess.run', run)
    return state, calls, profile


def test_restore_only_owned_colors_and_repeat(tmp_path, gnome_state):
    from crux.integrations.terminal_theme import restore_gnome_profile
    state, calls, profile = gnome_state
    sync_gnome_profile('cobalt', tmp_path)
    backup = tmp_path / f'gnome-terminal-{profile}.backup.ini'
    original = backup.read_bytes()
    state['font'] = "'New User Font 14'"
    state['scrollbar-policy'] = "'never'"
    assert restore_gnome_profile(tmp_path, dry_run=True)
    assert state['background-color'] == "'#122738'"
    assert restore_gnome_profile(tmp_path)
    assert state == {'background-color': "'#abcdef'", 'font': "'New User Font 14'", 'scrollbar-policy': "'never'"}
    before = len([a for a in calls if a[1] in ('reset', 'write')])
    assert restore_gnome_profile(tmp_path)
    assert len([a for a in calls if a[1] in ('reset', 'write')]) == before
    assert backup.read_bytes() == original


def test_restore_refuses_newer_colors_and_legacy_backup(tmp_path, gnome_state):
    from crux.integrations.terminal_theme import restore_gnome_profile
    state, calls, profile = gnome_state
    sync_gnome_profile('light', tmp_path)
    state['foreground-color'] = "'#userchange'"
    before = dict(state)
    with pytest.raises(RuntimeError, match='newer settings'):
        restore_gnome_profile(tmp_path)
    assert state == before
    assert not any(a[1] in ('reset', 'write') for a in calls)
    (tmp_path / f'gnome-terminal-{profile}.applied.json').unlink()
    with pytest.raises(RuntimeError, match='manual'):
        restore_gnome_profile(tmp_path)


@pytest.mark.parametrize('value', ['', 'invalid-uuid'])
def test_invalid_profile_does_not_write(tmp_path, monkeypatch, value):
    monkeypatch.setenv('GNOME_TERMINAL_SERVICE', ':1.123')
    with patch('crux.integrations.terminal_theme.shutil.which', return_value='tool'), patch('crux.integrations.terminal_theme.subprocess.run', return_value=subprocess.CompletedProcess([], 0, stdout=value, stderr='')) as run:
        with pytest.raises(RuntimeError, match='valid default profile'):
            sync_gnome_profile('cobalt', tmp_path)
    assert run.call_count == 1 and not list(tmp_path.iterdir())


def test_missing_dependencies_and_non_gnome_restore(tmp_path, monkeypatch):
    from crux.integrations.terminal_theme import restore_gnome_profile
    assert not restore_gnome_profile(tmp_path)
    monkeypatch.setenv('GNOME_TERMINAL_SERVICE', ':1.123')
    with patch('crux.integrations.terminal_theme.shutil.which', return_value=None):
        with pytest.raises(RuntimeError, match='gsettings and dconf'):
            restore_gnome_profile(tmp_path)


def test_restore_failed_write_preserves_recovery_data(tmp_path, gnome_state, monkeypatch):
    from crux.integrations.terminal_theme import restore_gnome_profile
    state, calls, profile = gnome_state
    sync_gnome_profile('dark', tmp_path)
    files = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    from crux.integrations import terminal_theme
    run = terminal_theme.subprocess.run
    def fail_write(args, **kwargs):
        if args[1] in ('write', 'reset'):
            return subprocess.CompletedProcess(args, 1, stdout='', stderr='Permission denied')
        return run(args, **kwargs)
    monkeypatch.setattr(terminal_theme.subprocess, 'run', fail_write)
    with pytest.raises(RuntimeError, match='Permission denied'):
        restore_gnome_profile(tmp_path)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == files


def test_state_atomic_write_failure_and_symlink_refusal(tmp_path, gnome_state):
    state, calls, profile = gnome_state
    with patch('crux.core.storage.os.replace', side_effect=PermissionError('state denied')):
        with pytest.raises(PermissionError):
            sync_gnome_profile('cobalt', tmp_path)
    backup = tmp_path / f'gnome-terminal-{profile}.backup.ini'
    assert backup.exists()
    assert not list(tmp_path.glob('.crux-*'))
    backup.unlink()
    target = tmp_path / 'untouched'
    try:
        backup.symlink_to(target)
    except OSError:
        pytest.skip('symlink creation unavailable')
    before = len(calls)
    with pytest.raises(ValueError, match='symlink'):
        sync_gnome_profile('light', tmp_path)
    assert not target.exists() and len(calls) == before + 2


def test_cli_restore_disables_prompt_palette(gnome_state):
    from crux.config.manager import load
    from crux.cli.main import app
    from typer.testing import CliRunner
    path = load().path
    sync_gnome_profile('cobalt', path.parent)
    result = CliRunner().invoke(app, ['theme', '--restore-profile'])
    assert result.exit_code == 0, result.output
    assert '\x1b' not in result.stdout
    assert not load().data['general']['terminal_palette']


@pytest.mark.parametrize('text', ['not json', '[]', '{"profile": "wrong", "colors": {}}'])
def test_corrupt_ownership_state_refused(tmp_path, gnome_state, text):
    from crux.integrations.terminal_theme import restore_gnome_profile
    state, calls, profile = gnome_state
    sync_gnome_profile('cobalt', tmp_path)
    (tmp_path / f'gnome-terminal-{profile}.applied.json').write_text(text)
    before = dict(state)
    with pytest.raises(RuntimeError):
        restore_gnome_profile(tmp_path)
    assert state == before
    assert not any(a[1] in ('reset', 'write') for a in calls)


def test_sync_timeout_and_malformed_backup(tmp_path, monkeypatch):
    monkeypatch.setenv('GNOME_TERMINAL_SERVICE', ':1.123')
    with patch('crux.integrations.terminal_theme.shutil.which', return_value='tool'), patch('crux.integrations.terminal_theme.subprocess.run', side_effect=subprocess.TimeoutExpired('gsettings', 5)):
        with pytest.raises(RuntimeError, match='timed out'):
            sync_gnome_profile('cobalt', tmp_path)
    assert not list(tmp_path.iterdir())
