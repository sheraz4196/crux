import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from scripts.benchmark_prompt import benchmark, summarize


def test_real_fast_prompt_outside_and_missing_tools(tmp_path):
    from crux import cli
    source_root = str(Path(cli.__file__).resolve().parents[2])
    environment = {**os.environ, 'PYTHONPATH': source_root, 'PATH': '', 'NO_COLOR': '1'}
    command = [sys.executable, '-m', 'crux', 'prompt', '--status', '7', '--shell', 'bash']
    result = subprocess.run(command, env=environment, cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0 and 'exit 7' in result.stdout and '\x1b' not in result.stdout
    assert benchmark(command, tmp_path, environment, 3)['samples'] == 3
    # Startup must keep the existing dependency-free prompt dispatch.
    code = "import sys; from crux.cli.entry import main; sys.argv=['crux','prompt']; main(); assert 'rich' not in sys.modules; assert 'typer' not in sys.modules"
    result = subprocess.run([sys.executable, '-c', code], env=environment, cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_percentiles_and_process_failure(tmp_path):
    import pytest
    assert summarize([1, 2, 3, 4, 100]) == {'samples': 5, 'median_ms': 3, 'p95_ms': 100, 'min_ms': 1, 'max_ms': 100}
    with patch('scripts.benchmark_prompt.subprocess.run', return_value=subprocess.CompletedProcess([], 1, stderr=b'failed')):
        with pytest.raises(RuntimeError, match='failed'):
            benchmark(['bad'], tmp_path, {}, 2)
