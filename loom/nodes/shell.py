import asyncio
from jinja2 import Template
from loom.nodes.base import BaseNode


class ShellNode(BaseNode):
    """Execute shell commands sequentially, stopping on first failure.

    Supports Jinja2 templating for command content using shared_state variables.
    """

    async def run(self, state):
        commands = self.config.get("commands", [])
        outputs = []
        for cmd_template in commands:
            # Render Jinja2 template with state variables
            template = Template(cmd_template)
            cmd = template.render(**state)

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            outputs.append(stdout.decode() + stderr.decode())
            if proc.returncode != 0:
                return False, "\n".join(outputs), state
        return True, "\n".join(outputs), state
