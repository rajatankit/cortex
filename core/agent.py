from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    success: bool
    agent: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Common contract for every CORTEX AI employee."""

    agent_id: str = ""
    name: str = ""
    role: str = ""

    def __init__(self):
        self.enabled = True

    @abstractmethod
    async def handle(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        raise NotImplementedError

    def info(self) -> dict[str, Any]:
        return {
            "id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "enabled": self.enabled,
        }