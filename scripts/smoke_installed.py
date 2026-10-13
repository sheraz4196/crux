"""Smoke-test a wheel installation from outside the checkout, without networking."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', required=True, type=Path)
    parser.add_argument('--crux', required=True, type=Path)
    args = parser.parse_args()
    python = os.path.abspath(args.python)
    executable = str(args.crux.resolve())
    results = []
    with tempfile.TemporaryDirectory(prefix='crux-smoke-') as directory:
        root = Path(directory)
        hook = root / 'offline'
        hook.mkdir()
        (hook / 'sitecustomize.py').write_text(
            'import socket\ndef blocked(*a, **k):\n    raise RuntimeError("Network forbidden in CRUX smoke test")\n'
            'socket.socket.connect = blocked\nsocket.socket.connect_ex = blocked\nsocket.create_connection = blocked\nsocket.getaddrinfo = blocked\n', encoding='utf-8')
        environment = {**os.environ, 'HOME': str(root), 'USERPROFILE': str(root),
                       'XDG_CONFIG_HOME': str(root / 'config'), 'APPDATA': str(root / 'config'),
                       'PYTHONPATH': str(hook), 'NO_COLOR': '1', 'PIP_NO_INDEX': '1'}
        environment.pop('GNOME_TERMINAL_SERVICE', None)
        source = root / 'source with spaces.py'
        source.write_text('print("offline")\n', encoding='utf-8')
        profile = root / 'profile with spaces'
        commands = [
            ['--version'], ['--help'], ['doctor', '--json', '--shell', 'bash', '--profile', str(profile)],
            ['config'], ['config', '--json'], ['config', 'get', 'general.theme'],
            ['config', 'set', 'prompt.show_git', 'false'], ['config', 'reset', 'prompt.show_git'],
            ['config', 'reset', '--yes'], ['theme'], ['ls'], ['ls', '--json'],
            ['tree'], ['tree', '--json'], ['view', str(source)], ['_ls'], ['_tree'],
            ['prompt', '--status', '7', '--shell', 'bash'],
            ['init', '--shell', 'bash', '--profile', str(profile), '--dry-run'],
            ['install', '--shell', 'bash', '--profile', str(profile), '--yes'],
            ['uninstall', '--shell', 'bash', '--profile', str(profile), '--yes'],
            ['theme', '--reset-terminal'],
        ] + [['theme', name] for name in ('default', 'dark', 'light', 'cobalt', 'monochrome')]
        git = shutil.which('git')
        if git:
            for command in ([git, 'init', '-b', 'main'], [git, 'config', 'user.name', 'Smoke'], [git, 'config', 'user.email', 'smoke@example.invalid'], [git, 'add', source.name], [git, '-c', 'commit.gpgsign=false', 'commit', '-m', 'smoke']):
                subprocess.run(command, cwd=root, env=environment, capture_output=True, check=True, timeout=30)
            commands += [['git', 'status'], ['_git', 'status']]
        for prefix in ([executable], [python, '-m', 'crux']):
            for command in commands:
                result = subprocess.run([*prefix, *command], cwd=root, env=environment, capture_output=True, text=True, timeout=15)
                if result.returncode:
                    raise RuntimeError(f'{command}: {result.stderr}\n{result.stdout}')
                if '\x1b' in result.stdout:
                    raise RuntimeError(f'Unexpected terminal control in redirected {command}')
                if '--json' in command:
                    json.loads(result.stdout)
                results.append({'entry': 'module' if '-m' in prefix else 'executable', 'command': command, 'exit_code': result.returncode})
        location = subprocess.run([python, '-c', 'import crux,sys; from pathlib import Path; assert Path(crux.__file__).is_relative_to(Path(sys.prefix)); print(crux.__file__)'], cwd=root, env=environment, capture_output=True, text=True, check=True)
        print(json.dumps({'checks_passed': len(results), 'network': 'Python socket connections and DNS blocked', 'installed_module': location.stdout.strip(), 'git_tested': bool(git)}, indent=2))


if __name__ == '__main__':
    main()
