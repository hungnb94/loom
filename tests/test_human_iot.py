import asyncio
import json
import sys
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest
from loom.nodes.human import HumanNode

# Mock hermes_tools for channel tests
_mock_hermes = MagicMock()
_mock_hermes.send_message = MagicMock()
if 'hermes_tools' not in sys.modules:
    sys.modules['hermes_tools'] = _mock_hermes


@pytest.mark.asyncio
async def test_human_approve_with_input():
    """HumanNode accepts explicit _user_input."""
    node = HumanNode(name="gate", config={"on_approve": "next", "on_decline": "abort"})
    node._user_input = "approve"
    success, output, state = await node.run({})
    assert success is True
    assert output == "approve"


@pytest.mark.asyncio
async def test_human_decline_with_input():
    """HumanNode declines when input is 'decline'."""
    node = HumanNode(name="gate", config={"on_approve": "next", "on_decline": "abort"})
    node._user_input = "decline"
    success, output, state = await node.run({})
    assert success is False
    assert output == "decline"


@pytest.mark.asyncio
async def test_human_yes_variants():
    """HumanNode accepts 'yes' and 'y'."""
    for val in ("yes", "y", "YES", "Yes"):
        node = HumanNode(name="gate", config={})
        node._user_input = val
        success, _, _ = await node.run({})
        assert success is True, f"Expected approve for '{val}'"


@pytest.mark.asyncio
async def test_human_no_variants():
    """HumanNode rejects 'no', 'n', 'abort'."""
    for val in ("no", "n", "abort", "NO"):
        node = HumanNode(name="gate", config={})
        node._user_input = val
        success, _, _ = await node.run({})
        assert success is False, f"Expected decline for '{val}'"


@pytest.mark.asyncio
async def test_human_non_tty_defaults_approve():
    """Non-TTY stdin (CI/pipe) defaults to approve."""
    node = HumanNode(name="gate", config={})
    # _user_input is None, and stdin is not a TTY in test
    # Since pytest doesn't have a real TTY, os.isatty(0) returns False
    success, output, state = await node.run({})
    assert success is True
    assert output == "approve"


def test_human_route_approve():
    """Route to on_approve when success."""
    node = HumanNode(name="gate", config={"on_approve": "next", "on_decline": "abort"})
    assert node.route(True) == "next"


def test_human_route_decline():
    """Route to on_decline when failure."""
    node = HumanNode(name="gate", config={"on_approve": "next", "on_decline": "abort"})
    assert node.route(False) == "abort"


def test_human_route_fallback():
    """Route falls back to on_skip then next."""
    node = HumanNode(name="gate", config={"on_skip": "skip", "next": "fallback"})
    assert node.route(False) == "skip"
    node2 = HumanNode(name="gate", config={"next": "fallback"})
    assert node2.route(False) == "fallback"


@pytest.mark.asyncio
async def test_human_input_none_stays_none_after_run():
    """_user_input is set during run, persists for inspection."""
    node = HumanNode(name="gate", config={})
    assert node._user_input is None
    await node.run({})
    assert node._user_input == "approve"  # auto-approved in non-TTY


@pytest.mark.asyncio
async def test_human_channel_fallback_no_hermes():
    """Channel mode falls back to approve when send_message fails."""
    # Make send_message raise to trigger fallback
    _mock_hermes.send_message.side_effect = Exception("no network")
    node = HumanNode(name="gate", config={
        "channel": "telegram:123:456",
        "on_approve": "next",
        "on_decline": "abort",
    })
    success, output, state = await node.run({})
    assert success is True
    assert output == "approve"
    _mock_hermes.send_message.side_effect = None  # reset


@pytest.mark.asyncio
async def test_human_channel_timeout():
    """Channel mode with timeout=0 immediately times out."""
    node = HumanNode(name="gate", config={
        "channel": "telegram:123:456",
        "timeout": 0,
        "on_timeout": "abort",
        "on_decline": "abort",
    })
    success, output, state = await node.run({})
    assert success is False
    assert output == "timeout"


def test_human_route_timeout():
    """Route to on_timeout when timeout occurred."""
    node = HumanNode(name="gate", config={
        "on_approve": "next",
        "on_decline": "abort",
        "on_timeout": "timeout_handler",
    })
    node._user_input = "timeout"
    assert node.route(False) == "timeout_handler"


def test_human_route_timeout_fallback():
    """Timeout falls back to on_decline if on_timeout not set."""
    node = HumanNode(name="gate", config={
        "on_approve": "next",
        "on_decline": "abort",
    })
    node._user_input = "timeout"
    assert node.route(False) == "abort"


@pytest.mark.asyncio
async def test_human_channel_message_jinja2():
    """Channel message supports Jinja2 rendering."""
    node = HumanNode(name="gate", config={
        "channel": "telegram:123:456",
        "message": "Node: {{current_node}} Score: {{score}}",
        "timeout": 0,
    })
    success, output, state = await node.run({"current_node": "gate", "score": 90})
    assert output == "timeout"
