import os
import shutil
import shlex
import subprocess
import sys
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
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env['PATH']
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
eval 'printf "%s\\n" "'"$PS1"'"'
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
    path = tmp_path / ('profile.ps1' if shell == 'powershell' else 'profile')
    if shell == 'zsh':
        path.write_text("alias personal='echo alias-ok'\nalias git='echo native-git'\nls() { echo native-ls; }\npersonal_function() { echo function-ok; }\nexport PERSONAL=value\nPS1='original> '\n")
        command = f'source "{path}"\npersonal\npersonal_function\nprint -r -- "$PERSONAL"\nprint pipe-ok | cat\ngit status\nls\ncrux_restore_prompt\n[[ $PS1 == "original> " ]] || exit 4\n'
        source_line, commands = command.split('\n', 1)
        args = [executable, '-f', '-c', source_line + '\neval ' + shlex.quote(commands)]
    else:
        path.write_text("function personal { 'alias-ok' }\nfunction personal_function { 'function-ok' }\nfunction git { 'native-git' }\n$env:PERSONAL='value'\nfunction prompt { 'original> ' }\n")
        command = f"$ErrorActionPreference='Stop'; . '{path}'; personal; personal_function; $env:PERSONAL; 'pipe-ok' | Write-Output; $global:LASTEXITCODE=17; prompt; if ($global:LASTEXITCODE -ne 17) {{ exit 1 }}; git status; crux_restore_prompt; if ((prompt) -ne 'original> ') {{ exit 4 }}"
        args = [executable, '-NoProfile', '-Command', command]
    edit_profile(path, shell)
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for value in ('alias-ok', 'function-ok', 'value', 'pipe-ok', 'native-git'):
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


@pytest.mark.skipif(os.name == 'nt', reason='POSIX executable stubs')
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
    edit_profile(profile, 'bash', enhance_commands=True)
    # Override the terminal predicate to exercise routing without a real terminal.
    script = f'''export HOME="{tmp_path}"
export PATH="{bindir}:$PATH"
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
    assert 'function git {' not in path.read_text()
    assert 'unalias' not in path.read_text()
    assert not edit_profile(path, 'bash')
    edit_profile(path, 'bash', remove=True)
    assert path.read_text() == 'before\nafter\n'


@pytest.mark.skipif(os.name == 'nt', reason='POSIX pseudo-terminal')
@pytest.mark.parametrize('enhance_commands', [False, True])
def test_bash_aliases_and_real_terminal(tmp_path, enhance_commands):
    import pty
    bash = shutil.which('bash')
    if not bash:
        pytest.skip('Bash unavailable')
    bindir = tmp_path / 'bin'
    bindir.mkdir()
    for name in ('crux', 'git', 'ls', 'tree', 'cat'):
        executable = bindir / name
        executable.write_text(f'#!/bin/sh\nprintf "{name}:%s\\n" "$*"\n')
        executable.chmod(0o755)
    profile = tmp_path / 'profile'
    profile.write_text("alias ls='ls --color=auto'\nalias git='git --no-pager'\nalias tree='tree -C'\nalias cat='cat -n'\nalias personal='echo personal-ok'\n")
    source = tmp_path / 'code with spaces.py'
    source.write_text('print("hello")\n')
    edit_profile(profile, 'bash', enhance_commands=enhance_commands)
    script = f'''source "{profile}"
source "{profile}"
ls
git status
tree
git status --porcelain
git diff
ls | cat
cat "{source}"
cat -n "{source}"
cat "{source}" | {shlex.quote(shutil.which("cat"))}
cat "{source}" > "{tmp_path}/redirected"
cat -
personal
'''
    master, slave = pty.openpty()
    try:
        env = {**os.environ, 'HOME': str(tmp_path), 'PATH': str(bindir) + os.pathsep + os.environ['PATH']}
        result = subprocess.run([bash, '--noprofile', '--norc', '-O', 'expand_aliases', '-c', script], env=env, stdout=slave, stderr=subprocess.PIPE, timeout=10)
        # macOS may discard unread output when the last slave closes.
        # Drain the completed process's output while the slave remains open.
        import select
        output = b''
        while select.select([master], [], [], 1)[0]:
            chunk = os.read(master, 4096)
            if not chunk:
                break
            output += chunk
    finally:
        os.close(master)
        if slave is not None:
            os.close(slave)
    assert result.returncode == 0, result.stderr
    assert result.stderr == b''
    assert output.decode().splitlines() == [
        'ls:--color=auto', 'git:--no-pager status', 'tree:-C',
        'git:--no-pager status --porcelain', 'git:--no-pager diff', 'cat:-n',
        f'cat:-n {source}', f'cat:-n -n {source}', f'cat:-n {source}',
        'cat:-n -', 'personal-ok',
    ]
    assert (tmp_path / 'redirected').read_text() == f'cat:-n {source}\n'


@pytest.mark.parametrize('enhance_commands', [False, True])
def test_preserve_functions_path_and_restore_prompt(tmp_path, enhance_commands):
    bash = shutil.which('bash')
    if not bash:
        pytest.skip('Bash unavailable')
    profile = tmp_path / 'profile with spaces'
    original = "PS1='original> '\ngit() { echo git-function; }\nls() { echo ls-function; }\ntree() { echo tree-function; }\ncat() { echo cat-function; }\n"
    profile.write_text(original)
    edit_profile(profile, 'bash', enhance_commands=enhance_commands)
    env = {**os.environ, 'PATH': str(Path(sys.executable).parent) + os.pathsep + os.environ['PATH']}
    command = f'''original_path=$PATH
source "{profile}"
source "{profile}"
git status
ls
tree
cat
[ "$original_path" = "$PATH" ] || exit 4
crux_restore_prompt
[ "$PS1" = 'original> ' ] || exit 5
'''
    result = subprocess.run([bash, '--noprofile', '--norc', '-c', command], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ['git-function', 'ls-function', 'tree-function', 'cat-function']
    edit_profile(profile, 'bash', remove=True)
    assert profile.read_text() == original
    after = subprocess.run([bash, '--noprofile', '--norc', '-c', f'source "{profile}"\ngit; ls; tree; cat'], capture_output=True, text=True)
    assert after.stdout == result.stdout


def test_keep_prompt_and_no_crux_dependency(tmp_path):
    bash = shutil.which('bash')
    if not bash:
        pytest.skip('Bash unavailable')
    path = tmp_path / 'profile'
    path.write_text("PS1='custom> '\n")
    edit_profile(path, 'bash', keep_prompt=True)
    result = subprocess.run([bash, '--noprofile', '--norc', '-c', f'source "{path}"\nprintf "%s" "$PS1"'], capture_output=True, text=True)
    assert result.returncode == 0 and result.stdout == 'custom> '
    edit_profile(path, 'bash')
    result = subprocess.run([bash, '--noprofile', '--norc', '-c', f'PATH="{tmp_path}"\nsource "{path}"\nprintf "%s" "$PS1"'], capture_output=True, text=True)
    assert result.returncode == 0 and result.stdout == 'custom> '


def test_profile_symlink_backup_and_modes(tmp_path):
    path = tmp_path / 'profile'
    path.write_text('personal\n')
    if os.name != 'nt':
        path.chmod(0o640)
    edit_profile(path, 'bash')
    if os.name != 'nt':
        assert path.stat().st_mode & 0o777 == 0o640
    edit_profile(path, 'bash', remove=True)
    link = tmp_path / 'profile-link'
    try:
        link.symlink_to(path)
        path.with_name(path.name + '.crux-backup').unlink()
        path.with_name(path.name + '.crux-backup').symlink_to(tmp_path / 'missing')
    except OSError:
        pytest.skip('symlink creation unavailable')
    with pytest.raises(ValueError, match='symlink'):
        edit_profile(link, 'bash')
    with pytest.raises(ValueError, match='symlink'):
        edit_profile(path, 'bash')
    assert path.read_text() == 'personal\n'
    assert not (tmp_path / 'missing').exists()


@pytest.mark.skipif(os.name == 'nt', reason='POSIX pseudo-terminal')
def test_opt_in_tty_routes_and_native_streams(tmp_path):
    import pty
    bash = shutil.which('bash')
    if not bash:
        pytest.skip('Bash unavailable')
    bindir = tmp_path / 'bin'
    bindir.mkdir()
    for name in ('crux', 'git', 'ls', 'tree'):
        executable = bindir / name
        executable.write_text(f'#!/bin/sh\nprintf "{name}:%s\\n" "$*"\n')
        executable.chmod(0o755)
    source = tmp_path / 'source with spaces'
    source.write_text('raw\n')
    profile = tmp_path / 'profile'
    edit_profile(profile, 'bash', enhance_commands=True)
    script = f'''source "{profile}"
git status
ls
tree
cat "{source}"
git status --porcelain
ls -a
tree --help
printf 'stdin-ok\\n' | cat
printf 'dash-ok\\n' | cat -
printf 'input-pipe\\n' | cat "{source}"
cat "{source}" | command cat
cat "{source}" > "{tmp_path}/copy"
git status | command cat
'''
    master, slave = pty.openpty()
    try:
        env = {**os.environ, 'PATH': str(bindir) + os.pathsep + os.environ['PATH']}
        result = subprocess.run([bash, '--noprofile', '--norc', '-c', script], env=env, stdin=slave, stdout=slave, stderr=subprocess.PIPE, timeout=10)
        # macOS may discard unread output when the last slave closes.
        # Drain the completed process's output while the slave remains open.
        import select
        output = b''
        while select.select([master], [], [], 1)[0]:
            chunk = os.read(master, 4096)
            if not chunk:
                break
            output += chunk
    finally:
        os.close(master)
        if slave is not None:
            os.close(slave)
    assert result.returncode == 0, result.stderr
    assert output.decode().splitlines() == [
        'crux:_git status', 'crux:_ls', 'crux:_tree', f'crux:_cat -- {source}',
        'git:status --porcelain', 'ls:-a', 'tree:--help', 'stdin-ok', 'dash-ok', 'raw', 'raw', 'git:status',
    ]
    assert (tmp_path / 'copy').read_bytes() == source.read_bytes()


def test_prompt_helper_collision_is_preserved(tmp_path):
    bash = shutil.which('bash')
    if not bash:
        pytest.skip('Bash unavailable')
    profile = tmp_path / 'profile'
    profile.write_text('crux_restore_prompt() { echo personal-helper; }\n')
    edit_profile(profile, 'bash')
    result = subprocess.run([bash, '--noprofile', '--norc', '-c', f'source "{profile}"\ncrux_restore_prompt'], capture_output=True, text=True)
    assert result.returncode == 0 and result.stdout == 'personal-helper\n'


def test_reject_powershell_wrappers_and_unsupported_shell(tmp_path):
    runner = CliRunner()
    for shell, flags in [('powershell', ['--enhance-commands']), ('fish', []), ('cmd', [])]:
        path = tmp_path / shell
        result = runner.invoke(app, ['install', '--shell', shell, '--profile', str(path), '--yes', *flags])
        assert result.exit_code == 1 and 'Error:' in result.output
        assert not path.exists()
