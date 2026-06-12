import json
import tempfile
from pathlib import Path
from loom.state import PipelineState

def test_state_serialize_deserialize():
    state = PipelineState(
        current_node="verify",
        visit_counts={"verify": 2, "fix_code": 1},
        shared_state={"requirement": "fix bug", "verify_output": "FAILED"}
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pipeline.state"
        state.save(path)
        loaded = PipelineState.load(path)
        assert loaded.current_node == "verify"
        assert loaded.visit_counts == {"verify": 2, "fix_code": 1}
        assert loaded.shared_state["requirement"] == "fix bug"
