from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class ToolRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    required_action: str
    risk: ToolRisk
    handler: Callable[..., Any]

    async def execute(self, *args, **kwargs) -> Any:
        return await self.handler(*args, **kwargs)





