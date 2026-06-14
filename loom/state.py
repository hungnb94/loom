from dataclasses import dataclass, asdict
from pathlib import Path
import json
import fcntl
import os
from typing import Any

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
        # Advisory lock during atomic rename
        with open(tmp_path, "r+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            os.replace(tmp_path, path)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    @classmethod
    def load(cls, path: Path) -> "PipelineState":
        with open(path, "r", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return cls(**data)
