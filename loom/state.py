from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os
import tempfile
from typing import Any

try:
    import fcntl

    def _lock_shared(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)

    def _lock_exclusive(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

    def _unlock(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

except ImportError:
    # Windows: no fcntl — file operations are already atomic enough via os.replace
    _lock_shared = None  # type: ignore[assignment]
    _lock_exclusive = None  # type: ignore[assignment]
    _unlock = None  # type: ignore[assignment]


@dataclass
class PipelineState:
    current_node: str
    visit_counts: dict[str, int]
    shared_state: dict[str, Any]

    def save(self, path: Path) -> None:
        """Atomic save using unique temp file + os.replace to prevent corruption."""
        path.parent.mkdir(parents=True, exist_ok=True)
        # Unique tmp file per invocation prevents concurrent-write corruption.
        # Same directory ensures same filesystem for atomic os.replace.
        tmp_fd, tmp_path_str = tempfile.mkstemp(
            dir=str(path.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
            os.replace(tmp_path_str, path)
        except BaseException:
            try:
                os.unlink(tmp_path_str)
            except OSError:
                pass
            raise

    @classmethod
    def load(cls, path: Path) -> "PipelineState":
        with open(path, "r", encoding="utf-8") as f:
            if _lock_shared:
                _lock_shared(f)
            try:
                data = json.load(f)
            finally:
                if _unlock:
                    _unlock(f)
        return cls(**data)
