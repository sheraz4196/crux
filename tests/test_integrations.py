import os
import shutil
import subprocess
from pathlib import Path
import pytest
from typer.testing import CliRunner
from crux.cli.main import app
from crux.integrations.manager import edit_profile, block, read_profile


@pytest.mark.parametrize('shell', ['bash', 'zsh', 'powershell'])
@pytest.mark.parametrize('suffix', ['', '\n', '\r\n'])
def test_roundtrip(tmp_path, shell, suffix):
    path = tmp_path / 'profile'
    original = ('# personal configuration' + suffix).encode()
    path.write_bytes(original)
    assert edit_profile(path, shell)
    assert not edit_profile(path, shell)
    assert path.read_text().count('# >>> crux >>>') == 1
    assert path.with_name('profile.crux-backup').read_bytes() == original
    assert edit_profile(path, shell, remove=True)
    assert path.read_bytes() == original
    assert not edit_profile(path, shell, remove=True)


def test_refuse_ambiguous(tmp_path):
    path = tmp_path / 'profile'
    path.write_text('# >>> crux >>>\nbroken')
    with pytest.raises(ValueError): edit_profile(path, 'bash')
    assert path.read_text().endswith('broken')
    with pytest.raises(ValueError): block('cmd')


def test_cli_profile(tmp_path):
    path = tmp_path / 'profile'
    runner = CliRunner()
    args = ['--shell', 'bash', '--profile', str(path)]
    assert runner.invoke(app, ['init', *args, '--dry-run']).exit_code == 0
    assert not path.exists()
    assert runner.invoke(app, ['init', *args], input='n\n').exit_code != 0
    assert not path.exists()
    assert runner.invoke(app, ['init', *args, '--yes']).exit_code == 0
    assert runner.invoke(app, ['uninstall', *args, '--yes']).exit_code == 0
    assert path.read_text() == ''


def test_bash_preserves_shell(tmp_path):
    bash = shutil.which('bash')
    if not bash: pytest.skip('Bash unavailable')
    path = tmp_path / 'profile'
    original = '''alias personal='echo alias-ok'
personal_function() { echo function-ok; }
export PERSONAL=value
PS1='original> '
PROMPT_COMMAND='true'
complete -W 'one two' personal_function
'''
    path.write_text(original)
    edit_profile(path, 'bash')
    env = dict(os.environ)
    env['PATH'] = str(Path('.venv/bin').resolve()) + os.pathsep + env['PATH']
    script = f'''source "{path}"
personal
personal_function
printf '%s\\n' "$PERSONAL"
printf 'pipe-ok\\n' | cat
printf 'redirect-ok\\n' > "{tmp_path}/output"
cat "{tmp_path}/output"
complete -p personal_function
printf '%s\\n' "$PROMPT_COMMAND"
false
printf '%s\\n' "${{PS1@P}}"
'''
    result = subprocess.run([bash, '--noprofile', '--norc', '-O', 'expand_aliases', '-c', script], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for value in ('alias-ok', 'function-ok', 'value', 'pipe-ok', 'redirect-ok', 'complete', 'true', 'exit 1'):
        assert value in result.stdout, result.stdout
    edit_profile(path, 'bash', remove=True)
    assert path.read_text() == original


@pytest.mark.parametrize('shell', ['zsh', 'powershell'])
def test_other_shells_when_available(tmp_path, shell):
    executable = shutil.which('zsh' if shell == 'zsh' else 'pwsh')
    if not executable:
        pytest.skip(f'{shell} unavailable on this host')
    path = tmp_path / 'profile'
    if shell == 'zsh':
        path.write_text("alias personal='echo alias-ok'\npersonal_function() { echo function-ok; }\nexport PERSONAL=value\n")
        command = f'source "{path}"\npersonal\npersonal_function\nprint -r -- "$PERSONAL"\nprint pipe-ok | cat\n'
        args = [executable, '-f', '-c', command]
    else:
        path.write_text("function personal { 'alias-ok' }\nfunction personal_function { 'function-ok' }\n$env:PERSONAL='value'\n")
        command = f". '{path}'; personal; personal_function; $env:PERSONAL; 'pipe-ok' | Write-Output; $global:LASTEXITCODE=17; prompt; if ($global:LASTEXITCODE -ne 17) {{ exit 1 }}"
        args = [executable, '-NoProfile', '-Command', command]
    edit_profile(path, shell)
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for value in ('alias-ok', 'function-ok', 'value', 'pipe-ok'):
        assert value in result.stdout


def test_preserve_later_changes(tmp_path):
    path = tmp_path / 'profile'
    path.write_text('before\n')
    edit_profile(path, 'bash')
    with path.open('a') as stream:
        stream.write('after\n')
    edit_profile(path, 'bash', remove=True)
    assert path.read_text() == 'before\nafter\n'


def test_atomic_failure(tmp_path, monkeypatch):
    path = tmp_path / 'profile'
    path.write_text('original\n')
    def failed_replace(*args):
        raise OSError('simulated write failure')
    monkeypatch.setattr(os, 'replace', failed_replace)
    with pytest.raises(OSError): edit_profile(path, 'bash')
    assert path.read_text() == 'original\n'


def test_bash_command_routing(tmp_path):
    """TTY output gets Crux; flags, other subcommands and pipes stay native."""
    bash = shutil.which('bash')
    if not bash:
        pytest.skip('Bash unavailable')
    bindir = tmp_path / 'bin'
    bindir.mkdir()
    for name in ('crux', 'git', 'ls', 'tree'):
        executable = bindir / name
        executable.write_text(f'#!/bin/sh\nprintf "{name}:%s\\n" "$*"\n')
        executable.chmod(0o755)
    profile = tmp_path / 'profile'
    edit_profile(profile, 'bash')
    # Override the terminal predicate to exercise routing without a real terminal.
    script = f'''export PATH="{bindir}:$PATH"
source "{profile}"
[() {{ if test "$1" = -t; then return 0; else builtin [ "$@"; fi; }}
git status
git status --porcelain
git diff
ls
tree
unset -f '['
git status | cat
'''
    result = subprocess.run([bash, '--noprofile', '--norc', '-c', script], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        'crux:_git status', 'git:status --porcelain', 'git:diff',
        'crux:_ls', 'crux:_tree', 'git:status',
    ]


def test_upgrade_old_integration(tmp_path):
    path = tmp_path / 'profile'
    path.write_text('before\n# >>> crux >>>\n# old prompt only\n# <<< crux <<<\nafter\n')
    assert edit_profile(path, 'bash')
    assert 'git()' in path.read_text()
    assert not edit_profile(path, 'bash')
    edit_profile(path, 'bash', remove=True)
    assert path.read_text() == 'before\nafter\n'
