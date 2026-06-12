from loom.nodes.base import BaseNode

def test_base_node_routing():
    node = BaseNode(name="test", config={"on_pass": "next", "on_fail": "retry"})
    assert node.route(True) == "next"
    assert node.route(False) == "retry"
