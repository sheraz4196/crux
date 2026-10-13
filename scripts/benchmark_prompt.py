"""End-to-end prompt timing in disposable directories (no latency assertion).

Run with the same Python as CRUX, or pass --executable /path/to/installed/crux.
Results include process startup and Git work. No profiles or desktops are edited.
"""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time


def summarize(values):
    ordered = sorted(values)
    return {'samples': len(values), 'median_ms': round(statistics.median(values), 3),
            'p95_ms': round(ordered[math.ceil(len(ordered) * .95) - 1], 3),
            'min_ms': round(ordered[0], 3), 'max_ms': round(ordered[-1], 3)}


def benchmark(command, directory, environment, samples):
    values = []
    for _ in range(samples):
        start = time.perf_counter()
        result = subprocess.run(command, cwd=directory, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=10)
        values.append((time.perf_counter() - start) * 1000)
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors='replace'))
    return summarize(values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=30)
    parser.add_argument('--executable', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.samples < 2:
        parser.error('--samples must be at least 2')
    command = [str(args.executable.resolve())] if args.executable else [sys.executable, '-m', 'crux']
    command += ['prompt', '--status', '0', '--shell', 'bash']
    report = {'command': command, 'python': sys.version.split()[0], 'platform': sys.platform, 'target_ms': 50, 'results': {}}
    with tempfile.TemporaryDirectory(prefix='crux-benchmark-') as temp:
        root = Path(temp)
        outside = root / 'outside'
        outside.mkdir()
        environment = {**os.environ, 'XDG_CONFIG_HOME': str(root / 'config'), 'APPDATA': str(root / 'config'), 'NO_COLOR': '1'}
        environment.pop('GNOME_TERMINAL_SERVICE', None)
        report['results']['outside_missing_config'] = benchmark(command, outside, environment, args.samples)
        git = shutil.which('git')
        if git:
            repo = root / 'repo'
            repo.mkdir()
            def run_git(*arguments):
                subprocess.run([git, '-C', str(repo), *arguments], capture_output=True, check=True, env=environment, timeout=30)
            run_git('init', '-b', 'main')
            run_git('config', 'user.name', 'CRUX Benchmark')
            run_git('config', 'user.email', 'benchmark@example.invalid')
            (repo / 'tracked').write_text('initial\n')
            run_git('add', '.')
            run_git('-c', 'commit.gpgsign=false', 'commit', '-m', 'benchmark baseline')
            report['results']['clean_repository'] = benchmark(command, repo, environment, args.samples)
            (repo / 'tracked').write_text('dirty\n')
            (repo / 'untracked with spaces').touch()
            report['results']['dirty_repository'] = benchmark(command, repo, environment, args.samples)
            for index in range(1000):
                (repo / f'file-{index}').write_text('benchmark\n')
            run_git('add', '.')
            run_git('-c', 'commit.gpgsign=false', 'commit', '-m', 'larger benchmark')
            report['results']['larger_clean_1000_files'] = benchmark(command, repo, environment, args.samples)
            (repo / 'file-0').write_text('dirty\n')
            report['results']['larger_dirty_1000_files'] = benchmark(command, repo, environment, args.samples)
            report['results']['repository_missing_tools'] = benchmark(command, repo, {**environment, 'PATH': ''}, args.samples)
        else:
            report['git_scenarios_skipped'] = 'Git unavailable'
        config = root / 'config' / ('CRUX' if os.name == 'nt' else 'crux') / 'config.toml'
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text('invalid TOML !', encoding='utf-8')
        report['results']['invalid_config'] = benchmark(command, outside, environment, args.samples)
        report['results']['missing_optional_tools'] = benchmark(command, outside, {**environment, 'PATH': ''}, args.samples)
    text = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(text + '\n', encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
