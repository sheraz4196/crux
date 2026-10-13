"""Run the source installer with a disposable HOME, then check its owned edits."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--wheelhouse', type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    bash = shutil.which('bash')
    if bash is None:
        parser.error('Bash is required for installer verification')
    with tempfile.TemporaryDirectory(prefix='crux-installer-') as directory:
        root = Path(directory)
        home = root / 'home with spaces'
        home.mkdir()
        profile = home / '.bashrc'
        original = "alias ls='echo native-alias'\ngit() { echo native-function; }\nPS1='original> '\n"
        profile.write_text(original, encoding='utf-8')
        environment = {**os.environ, 'HOME': str(home), 'XDG_DATA_HOME': str(root / 'data'),
                       'XDG_CONFIG_HOME': str(root / 'config'), 'NO_COLOR': '1', 'PIP_DISABLE_PIP_VERSION_CHECK': '1', 'PIP_NO_CACHE_DIR': '1'}
        environment.pop('GNOME_TERMINAL_SERVICE', None)
        if args.wheelhouse:
            environment['PIP_NO_INDEX'] = '1'
            environment['PIP_FIND_LINKS'] = str(args.wheelhouse.resolve())
        command = ['sh', str(source / 'install.sh'), '--shell', 'bash']
        subprocess.run(command, cwd=root, env=environment, check=True, capture_output=True, text=True, timeout=120)
        backup = home / '.bashrc.crux-backup'
        assert backup.read_text() == original
        executable = home / '.local' / 'bin' / 'crux'
        assert executable.is_symlink()
        environment['PATH'] = str(executable.parent) + os.pathsep + environment['PATH']
        script = f'''previous_path=$PATH
source "{profile}"
ls
git status
[ "$PATH" = "$previous_path" ] || exit 2
crux_restore_prompt
[ "$PS1" = 'original> ' ] || exit 3
'''
        result = subprocess.run([bash, '--noprofile', '--norc', '-O', 'expand_aliases', '-c', script], env=environment, capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == ['native-alias', 'native-function']
        subprocess.run(command, cwd=root, env=environment, capture_output=True, check=True, timeout=120)
        assert profile.read_text().count('# >>> crux >>>') == 1
        assert backup.read_text() == original
        subprocess.run([str(executable), 'uninstall', '--shell', 'bash', '--yes'], env=environment, capture_output=True, check=True)
        assert profile.read_text() == original
        # An unrelated executable must not be replaced by the source installer.
        executable.unlink()
        executable.write_text('personal executable\n')
        result = subprocess.run(command, cwd=root, env=environment, capture_output=True, text=True, timeout=120)
        assert result.returncode != 0 and 'Refusing to replace' in result.stderr, result.stdout + result.stderr
        assert executable.read_text() == 'personal executable\n'
        assert profile.read_text() == original
        print('Installer passed: isolated install/link, aliases/functions/PATH/prompt, backup, repeated install, uninstall, unrelated executable refusal.')


if __name__ == '__main__':
    main()
