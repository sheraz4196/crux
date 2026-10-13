"""Atomic UTF-8 writes shared by configuration and recovery state."""
import os
import tempfile
from pathlib import Path


def atomic_write(path, text):
    path = Path(path)
    if path.is_symlink():
        raise ValueError(f'Refusing to replace symlink: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.crux-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            os.chmod(temporary, path.stat().st_mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
