import os
import shutil
import subprocess
from pathlib import Path


def virtual_environment():
    value = os.environ.get("VIRTUAL_ENV") or os.environ.get("CONDA_DEFAULT_ENV")
    return Path(value).name if value else None


def tool_version(tool, timeout=1):
    executable = shutil.which(tool)
    if not executable:
        return None
    try:
        result = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip().splitlines()[0] if result.returncode == 0 and result.stdout.strip() else "available"
    except (OSError, subprocess.TimeoutExpired):
        return "available (version unavailable)"


def duplicate_paths():
    paths = [os.path.normcase(os.path.normpath(p)) for p in os.environ.get("PATH", "").split(os.pathsep) if p]
    return len(paths) != len(set(paths))
