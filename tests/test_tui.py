from rich.console import Console
from loom.tui import LoomTUI


def test_tui_render():
    console = Console(force_terminal=True, width=80)
    tui = LoomTUI(console=console)
    tui.update_node_status("clarify", "running")
    tui.update_streaming("clarify", "Processing...")
    # Just verify no exception
    assert tui is not None


def test_tui_render_panel():
    console = Console(force_terminal=True, width=80)
    tui = LoomTUI(console=console)
    tui.update_node_status("clarify", "running")
    tui.update_node_status("research", "completed")
    tui.update_node_status("write", "pending")
    panel = tui.render()
    assert panel is not None


def test_tui_streaming_appends():
    console = Console(force_terminal=True, width=80)
    tui = LoomTUI(console=console)
    tui.update_streaming("clarify", "Hello ")
    tui.update_streaming("clarify", "World")
    assert tui.streams["clarify"] == "Hello World"


def test_tui_state_update():
    console = Console(force_terminal=True, width=80)
    tui = LoomTUI(console=console)
    tui.update_state({"current_step": 3, "total_steps": 5})
    assert tui.state == {"current_step": 3, "total_steps": 5}
