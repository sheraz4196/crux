import io
import json
import os
import subprocess
import time
from pathlib import Path
from unittest.mock import patch
import pytest
from crux.config.manager import load
from crux.core.filesystem import scan, human_size
from crux.core.platform import config_path, system_info
from crux.core.terminal import detect
from crux.core.environment import virtual_environment, tool_version, duplicate_paths
from crux.core.git import status, in_repository
from crux.core.text import safe_text
from crux.prompt.builder import build


def test_platform(monkeypatch, tmp_path):
    assert system_info()['Architecture']
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
    with patch('platform.system', return_value='Linux'):
        assert config_path() == tmp_path / 'crux/config.toml'
    monkeypatch.setenv('APPDATA', str(tmp_path))
    with patch('platform.system', return_value='Windows'):
        assert config_path() == tmp_path / 'CRUX/config.toml'


def test_terminal(monkeypatch):
    stream = io.StringIO()
    assert not detect(stream).color
    class Terminal(io.StringIO):
        encoding = 'utf-8'
        def isatty(self): return True
    stream = Terminal()
    monkeypatch.delenv('NO_COLOR', raising=False)
    monkeypatch.setenv('TERM', 'xterm')
    monkeypatch.setenv('COLORTERM', 'truecolor')
    assert detect(stream).truecolor and detect(stream).unicode
    assert not detect(stream, True).color
    monkeypatch.setenv('NO_COLOR', '')
    assert not detect(stream).color
    class Ascii(Terminal): encoding = 'ascii'
    assert not detect(Ascii()).unicode


def test_configuration(tmp_path):
    path = tmp_path / 'config.toml'
    assert load(path).data['general']['icons']
    path.write_text('[general]\nicons = false\ntheme="missing"\n[prompt]\nshow_git="bad"')
    result = load(path)
    assert not result.data['general']['icons']
    assert len(result.warnings) == 2
    path.write_text('not toml !')
    assert load(path).warnings
    assert load(path).data['general']['icons']


def test_filesystem(tmp_path):
    (tmp_path / 'folder').mkdir()
    (tmp_path / 'file').write_bytes(b'abc')
    (tmp_path / '.hidden').touch()
    assert [e.path.name for e in scan(tmp_path)] == ['folder', 'file']
    assert len(scan(tmp_path, True)) == 3
    assert human_size(1024) == '1.0 KB'
    with patch.object(Path, 'lstat', side_effect=PermissionError('denied')):
        assert all(e.error for e in scan(tmp_path))
    try:
        (tmp_path / 'link').symlink_to(tmp_path / 'folder', target_is_directory=True)
    except OSError:
        return
    assert next(e for e in scan(tmp_path) if e.path.name == 'link').symlink


def test_environment(monkeypatch):
    monkeypatch.setenv('VIRTUAL_ENV', '/tmp/my-env')
    assert virtual_environment() == 'my-env'
    monkeypatch.setenv('PATH', os.pathsep.join(['same', 'same']))
    assert duplicate_paths()
    assert tool_version('crux_nonexistent_tool') is None


@pytest.fixture
def repo(tmp_path):
    def git(*args):
        return subprocess.run(['git', '-C', str(tmp_path), *args], check=True, capture_output=True)
    git('init', '-b', 'main')
    git('config', 'user.name', 'Test')
    git('config', 'user.email', 'test@example.invalid')
    (tmp_path / 'tracked').write_text('initial')
    git('add', '.')
    git('commit', '-m', 'initial')
    return tmp_path, git


def test_git(repo):
    path, git = repo
    assert in_repository(path)
    result = status(path)
    assert result.branch == 'main' and not result.changes
    (path / 'tracked').write_text('changed')
    (path / 'untracked space').touch()
    assert (' .M'.strip(), 'tracked') in status(path).changes
    git('add', 'tracked')
    assert ('M.', 'tracked') in status(path).changes
    assert ('??', 'untracked space') in status(path).changes
    git('commit', '-m', 'changed')
    git('mv', 'tracked', 'renamed')
    assert any('tracked -> renamed' == name for _, name in status(path).changes)


def test_git_missing_and_nonrepo(tmp_path):
    assert not in_repository(tmp_path)
    with pytest.raises(ValueError): status(tmp_path)
    with patch('shutil.which', return_value=None), pytest.raises(ValueError, match='not installed'):
        status(tmp_path)


def test_prompt(tmp_path, monkeypatch, repo):
    monkeypatch.setenv('VIRTUAL_ENV', '/tmp/demo')
    (tmp_path / 'package.json').touch()
    start = time.perf_counter()
    value = build(2, tmp_path)
    assert time.perf_counter() - start < .05
    assert 'exit 2' in value and '(demo)' in value and 'node project' in value
    assert 'main' in build(path=repo[0])
    assert '\x1b' not in safe_text('bad\x1b[2J')
    config = load()
    config.data['prompt']['show_git'] = False
    with patch('crux.prompt.builder.status', side_effect=AssertionError):
        build(path=repo[0], configuration=config)


def test_git_ahead_behind_parser():
    output = b'# branch.head feature\0# branch.ab +2 -1\0? name with spaces\0'
    result = subprocess.CompletedProcess([], 0, output, b'')
    with patch('shutil.which', return_value='git'), patch('subprocess.run', return_value=result):
        data = status()
    assert (data.branch, data.ahead, data.behind) == ('feature', 2, 1)
    assert data.changes == [('??', 'name with spaces')]


def test_optional_prompt_failures(tmp_path):
    (tmp_path / '.git').mkdir()
    (tmp_path / '.git/HEAD').write_text('ref: refs/heads/main')
    with patch('crux.prompt.builder.status', side_effect=ValueError('timeout')):
        assert build(path=tmp_path).endswith('> ')
    config = load()
    config.data['prompt']['enabled'] = False
    assert build(configuration=config) == '> '


def test_prompt_themes_and_shell_width_markers(tmp_path, monkeypatch):
    monkeypatch.setenv('TERM', 'xterm-256color')
    monkeypatch.delenv('NO_COLOR', raising=False)
    config = load()
    default = build(path=tmp_path, configuration=config, shell='bash')
    config.data['general']['theme'] = 'light'
    light = build(path=tmp_path, configuration=config, shell='bash')
    assert '\x1b[1;96m' in default and '\x1b[1;34m' in light
    assert default != light
    assert '\x01\x1b[' in light and 'm\x02' in light
    path = tmp_path / 'percent%F{red}'
    path.mkdir()
    zsh = build(path=path, configuration=config, shell='zsh')
    assert '%{\x1b[' in zsh and 'percent%%F{red}' in zsh
    monkeypatch.setenv('NO_COLOR', '')
    assert '\x1b' not in build(path=tmp_path, configuration=config, shell='bash')
    monkeypatch.delenv('NO_COLOR')
    config.data['general']['theme'] = 'monochrome'
    assert '\x1b' not in build(path=tmp_path, configuration=config, shell='bash')


def test_output_theme_colors(monkeypatch):
    from crux.render.renderer import Renderer
    class Terminal(io.StringIO):
        encoding = 'utf-8'
        def isatty(self): return True
    monkeypatch.setenv('TERM', 'xterm')
    monkeypatch.delenv('NO_COLOR', raising=False)
    outputs = []
    for theme in ('default', 'light', 'monochrome'):
        terminal = Terminal()
        with patch('sys.stdout', terminal):
            renderer = Renderer(theme=theme)
            renderer.line('folder/', 'directory')
            renderer.line('file', 'file')
        outputs.append(terminal.getvalue())
    assert '\x1b[1;94m' in outputs[0]
    assert '\x1b[1;35m' in outputs[1]
    assert '\x1b[34m' in outputs[1]
    assert len(set(outputs)) == 3
