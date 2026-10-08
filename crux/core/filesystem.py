from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileEntry:
    path: Path
    directory: bool
    symlink: bool
    size: int | None
    error: str | None = None


def scan(path, hidden=False):
    entries = []
    for item in Path(path).iterdir():
        if not hidden and item.name.startswith("."):
            continue
        try:
            stat = item.lstat()
            entries.append(FileEntry(item, item.is_dir(), item.is_symlink(), stat.st_size))
        except OSError as exc:
            entries.append(FileEntry(item, False, item.is_symlink(), None, str(exc)))
    return sorted(entries, key=lambda e: (not e.directory, e.path.name.casefold(), e.path.name))


def human_size(size):
    if size is None:
        return "?"
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
