import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GitStatus:
    branch: str
    ahead: int = 0
    behind: int = 0
    changes: list[tuple[str, str]] = field(default_factory=list)


def in_repository(path):
    path = Path(path).resolve()
    return any((parent / ".git" / "HEAD").is_file() or (parent / ".git").is_file() for parent in (path, *path.parents))


def status(path=".", timeout=2):
    if not shutil.which("git"):
        raise ValueError("Git is not installed or not available in PATH.")
    try:
        result = subprocess.run(["git", "-C", str(path), "status", "--porcelain=v2", "--branch", "-z"], capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"Git status unavailable: {exc}") from exc
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip())
    data = GitStatus("unknown")
    records = iter(result.stdout.decode(errors="replace").split("\0"))
    for record in records:
        if record.startswith("# branch.head "):
            data.branch = record[14:]
        elif record.startswith("# branch.ab "):
            ahead, behind = record[12:].split()
            data.ahead, data.behind = int(ahead), -int(behind)
        elif record.startswith("1 "):
            parts = record.split(" ", 8)
            data.changes.append((parts[1], parts[8]))
        elif record.startswith("2 "):
            parts = record.split(" ", 9)
            original = next(records, "")
            data.changes.append((parts[1], f"{original} -> {parts[9]}"))
        elif record.startswith("u "):
            parts = record.split(" ", 10)
            data.changes.append((parts[1], parts[10]))
        elif record.startswith("? "):
            data.changes.append(("??", record[2:]))
    return data
