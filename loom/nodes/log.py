from pathlib import Path
from jinja2 import Template
from loom.nodes.base import BaseNode


class LogNode(BaseNode):
    """Write a log message to a file.

    Supports Jinja2 templating for message content.
    """

    async def run(self, state: dict) -> tuple[bool, str, dict]:
        message_template = self.config.get("message", "")
        file_path_str = self.config.get("file", "loom.log")

        # Render Jinja2 template with state variables
        template = Template(message_template)
        rendered_message = template.render(**state)

        # Write to file (append mode)
        file_path = Path(file_path_str)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(rendered_message + "\n")

        return True, f"Logged to {file_path}", state
