from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os
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
        """Atomic save with advisory file locking to prevent corruption."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        # Advisory lock during atomic rename (no-op on Windows)
        with open(tmp_path, "r+") as f:
            if _lock_exclusive:
                _lock_exclusive(f)
            os.replace(tmp_path, path)
            if _unlock:
                _unlock(f)

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
