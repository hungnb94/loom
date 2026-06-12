from dataclasses import dataclass, asdict
from pathlib import Path
import json
from typing import Any

@dataclass
class PipelineState:
    current_node: str
    visit_counts: dict[str, int]
    shared_state: dict[str, Any]

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "PipelineState":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)
