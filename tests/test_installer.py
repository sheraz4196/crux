import os
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.skipif(os.name == 'nt', reason='POSIX source installer')
def test_installer_reuses_environment_and_refuses_unrelated_file(tmp_path):
    shell = shutil.which('sh')
    if not shell:
        pytest.skip('sh unavailable')
    home = tmp_path / 'home with spaces'
    bindir = home / '.local' / 'bin'
    bindir.mkdir(parents=True)
    data = tmp_path / 'data'
    envbin = data / 'crux' / 'venv' / 'bin'
    envbin.mkdir(parents=True)
    fakebin = tmp_path / 'bin'
    fakebin.mkdir()
    log = tmp_path / 'calls'
    for path, message in [(fakebin / 'python3', 'unexpected-create'), (envbin / 'python', 'install'), (envbin / 'crux', 'integrate')]:
        path.write_text(f'#!/bin/sh\nprintf "%s\\n" "{message}" >> "$CRUX_TEST_LOG"\n')
        path.chmod(0o755)
    environment = {**os.environ, 'HOME': str(home), 'XDG_DATA_HOME': str(data), 'PATH': str(fakebin) + os.pathsep + os.environ['PATH'], 'CRUX_TEST_LOG': str(log)}
    command = [shell, str(Path('install.sh').resolve()), '--shell', 'bash']
    result = subprocess.run(command, env=environment, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == ['install', 'integrate']
    assert (bindir / 'crux').is_symlink()
    assert 'PATH unchanged' in result.stdout
    (bindir / 'crux').unlink()
    (bindir / 'crux').write_text('personal')
    log.write_text('')
    result = subprocess.run(command, env=environment, capture_output=True, text=True)
    assert result.returncode == 1 and 'Refusing to replace' in result.stderr
    assert (bindir / 'crux').read_text() == 'personal' and log.read_text() == ''


@pytest.mark.skipif(os.name == 'nt', reason='POSIX source installer')
def test_installer_refuses_incomplete_environment(tmp_path):
    shell = shutil.which('sh')
    if not shell:
        pytest.skip('sh unavailable')
    data = tmp_path / 'data'
    (data / 'crux' / 'venv').mkdir(parents=True)
    environment = {**os.environ, 'HOME': str(tmp_path), 'XDG_DATA_HOME': str(data)}
    result = subprocess.run([shell, str(Path('install.sh').resolve())], env=environment, capture_output=True, text=True)
    assert result.returncode == 1 and 'incomplete' in result.stderr
    assert not (tmp_path / '.local' / 'bin' / 'crux').exists()


@pytest.mark.skipif(os.name == 'nt', reason='POSIX source installer')
def test_installer_refuses_unrelated_symlinks(tmp_path):
    shell = shutil.which('sh')
    if not shell:
        pytest.skip('sh unavailable')
    data = tmp_path / 'data'
    bindir = tmp_path / '.local' / 'bin'
    bindir.mkdir(parents=True)
    target = tmp_path / 'personal'
    target.write_text('personal')
    (bindir / 'crux').symlink_to(target)
    environment = {**os.environ, 'HOME': str(tmp_path), 'XDG_DATA_HOME': str(data)}
    command = [shell, str(Path('install.sh').resolve())]
    result = subprocess.run(command, env=environment, capture_output=True, text=True)
    assert result.returncode == 1 and 'unrelated Crux link' in result.stderr
    assert (bindir / 'crux').resolve() == target and target.read_text() == 'personal'
    assert not data.exists()
    (bindir / 'crux').unlink()
    (data / 'crux').mkdir(parents=True)
    (data / 'crux' / 'venv').symlink_to(tmp_path, target_is_directory=True)
    result = subprocess.run(command, env=environment, capture_output=True, text=True)
    assert result.returncode == 1 and 'symlinked environment' in result.stderr
