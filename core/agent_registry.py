from typing import Dict
from core.agent import BaseAgent


class AgentRegistry:
    """
    Central registry for CORTEX agents.
    """

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        if agent.agent_id in self._agents:
            raise ValueError(f"Agent already registered: {agent.agent_id}")

        self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> BaseAgent | None:
        return self._agents.get(agent_id)

    def list_agents(self) -> list[dict]:
        return [agent.info() for agent in self._agents.values()]

    def exists(self, agent_id: str) -> bool:
        return agent_id in self._agents