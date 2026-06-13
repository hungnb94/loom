import pytest
from loom.graph import render_graph, build_edges


class TestBuildEdges:
    def test_simple_linear(self):
        config = {
            "entry": "a",
            "steps": {
                "a": {"type": "shell", "commands": ["echo"], "on_pass": "b"},
                "b": {"type": "shell", "commands": ["echo"]},
            },
        }
        edges = build_edges(config)
        assert ("a", "b", "✓") in edges

    def test_conditional_edges(self):
        config = {
            "entry": "a",
            "steps": {
                "a": {"type": "condition", "expression": "True", "on_true": "b", "on_false": "c"},
                "b": {"type": "shell", "commands": ["echo"]},
                "c": {"type": "shell", "commands": ["echo"]},
            },
        }
        edges = build_edges(config)
        assert ("a", "b", "T") in edges
        assert ("a", "c", "F") in edges

    def test_multiple_edge_types(self):
        config = {
            "entry": "a",
            "steps": {
                "a": {"type": "shell", "commands": ["echo"], "on_pass": "b", "on_fail": "c"},
                "b": {"type": "shell", "commands": ["echo"]},
                "c": {"type": "shell", "commands": ["echo"]},
            },
        }
        edges = build_edges(config)
        assert len(edges) == 2

    def test_human_edges(self):
        config = {
            "entry": "a",
            "steps": {
                "a": {"type": "human", "on_approve": "b", "on_decline": "c"},
                "b": {"type": "shell", "commands": ["echo"]},
                "c": {"type": "shell", "commands": ["echo"]},
            },
        }
        edges = build_edges(config)
        assert ("a", "b", "✓") in edges
        assert ("a", "c", "✗") in edges

    def test_next_edge(self):
        config = {
            "entry": "a",
            "steps": {
                "a": {"type": "log", "message": "hi", "next": "b"},
                "b": {"type": "shell", "commands": ["echo"]},
            },
        }
        edges = build_edges(config)
        assert ("a", "b", "→") in edges


class TestRenderGraph:
    def test_returns_string(self):
        config = {
            "entry": "a",
            "steps": {
                "a": {"type": "shell", "commands": ["echo"], "on_pass": "b"},
                "b": {"type": "shell", "commands": ["echo"]},
            },
        }
        result = render_graph(config)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_node_names(self):
        config = {
            "entry": "a",
            "steps": {
                "a": {"type": "shell", "commands": ["echo"], "on_pass": "b"},
                "b": {"type": "agent", "agent": "hermes", "prompt": "hi"},
            },
        }
        result = render_graph(config)
        assert "a" in result
        assert "b" in result

    def test_contains_edge_labels(self):
        config = {
            "entry": "a",
            "steps": {
                "a": {"type": "condition", "expression": "True", "on_true": "b", "on_fail": "c"},
                "b": {"type": "shell", "commands": ["echo"]},
                "c": {"type": "shell", "commands": ["echo"]},
            },
        }
        result = render_graph(config)
        assert "T" in result or "F" in result

    def test_contains_node_types(self):
        config = {
            "entry": "a",
            "steps": {
                "a": {"type": "agent", "agent": "hermes", "prompt": "hi", "on_pass": "b"},
                "b": {"type": "parallel", "branches": [{"name": "x", "type": "shell", "commands": ["echo"]}]},
            },
        }
        result = render_graph(config)
        assert "agent" in result
        assert "parallel" in result

    def test_entry_marked(self):
        config = {
            "entry": "start",
            "steps": {
                "start": {"type": "shell", "commands": ["echo"], "on_pass": "end"},
                "end": {"type": "shell", "commands": ["echo"]},
            },
        }
        result = render_graph(config)
        assert "start" in result
        assert "ENTRY" in result or "▶" in result or ">" in result

    def test_full_pipeline(self):
        """Test with real test_full_pipeline.yaml."""
        from loom.config import load_pipeline
        from pathlib import Path
        config = load_pipeline(Path("test_full_pipeline.yaml"))
        result = render_graph(config)
        assert "setup" in result
        assert "done" in result
        assert len(result.split("\n")) >= 5  # Multi-line output
