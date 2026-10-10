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
