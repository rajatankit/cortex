from .tool import Tool


class ToolRegistry:
    """
    Registry for all CORTEX tools.
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(
                f"Tool already registered: {tool.name}"
            )

        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> Tool | None:
        return self._tools.get(tool_name)

    def exists(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def count(self) -> int:
        return len(self._tools)

    def find_by_action(self, action: str) -> Tool | None:
        for tool in self._tools.values():
            if tool.required_action == action:
                return tool

        return None