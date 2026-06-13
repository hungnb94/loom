import asyncio
import os
from loom.nodes.base import BaseNode


class HumanNode(BaseNode):
    """Pause pipeline for human approval.

    Modes (priority order):
    1. _user_input set → use directly (test mode)
    2. channel configured → send message, wait for reply
    3. TTY stdin → interactive prompt
    4. Non-TTY → auto-approve (CI mode)

    Config:
      channel: telegram:chat_id:thread_id  # messaging platform
      message: "custom prompt"             # optional override
      timeout: 300                        # seconds to wait (default 300)
      on_timeout: "abort"                 # route on timeout
    """

    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self._user_input: str | None = None

    async def run(self, state: dict) -> tuple[bool, str, dict]:
        if self._user_input is not None:
            return self._parse_input(self._user_input), self._user_input, state

        channel = self.config.get("channel")
        if channel:
            return await self._run_channel(state, channel)

        if os.isatty(0):
            try:
                self._user_input = input(f"[{self.name}] approve/decline? ")
            except (EOFError, KeyboardInterrupt):
                self._user_input = "decline"
            return self._parse_input(self._user_input), self._user_input, state

        # Non-TTY: auto-approve
        self._user_input = "approve"
        return True, self._user_input, state

    async def _run_channel(self, state: dict, channel: str) -> tuple[bool, str, dict]:
        """Send message via messaging channel, wait for reply."""
        try:
            from hermes_tools import send_message
        except ImportError:
            # Fallback: hermes_tools not available, skip channel
            self._user_input = "approve"
            return True, self._user_input, state

        # Build context message
        default_msg = f"🔔 Pipeline cần approve\n\nNode: `{self.name}`\nReply: **approve** hoặc **decline**"
        msg = self.config.get("message", default_msg)
        msg = self.render(msg, state)

        # Send
        try:
            send_message(message=msg, target=channel)
        except Exception:
            # Send failed, fallback to approve
            self._user_input = "approve"
            return True, self._user_input, state

        # Wait for reply (polling loop)
        timeout = self.config.get("timeout", 300)
        poll_interval = 5
        waited = 0

        while waited < timeout:
            await asyncio.sleep(poll_interval)
            waited += poll_interval
            # Check if user set _user_input externally (e.g., via webhook handler)
            if self._user_input is not None:
                return self._parse_input(self._user_input), self._user_input, state

        # Timeout
        self._user_input = "timeout"
        return False, self._user_input, state

    @staticmethod
    def _parse_input(val: str) -> bool:
        return val.lower() in ("approve", "yes", "y")

    def route(self, success: bool) -> str | None:
        if success:
            return self.config.get("on_approve") or self.config.get("next")
        
        # Check if timeout
        if self._user_input == "timeout":
            return self.config.get("on_timeout") or self.config.get("on_decline") or self.config.get("next")
        
        return self.config.get("on_decline") or self.config.get("on_skip") or self.config.get("next")
