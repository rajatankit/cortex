"""
cortex_health.py
Runtime health-check system for CORTEX.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List


class HealthStatus(Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    detail: str = ""


@dataclass
class CortexHealthReport:
    overall_status: HealthStatus
    components: List[ComponentHealth] = field(default_factory=list)

    def is_healthy(self) -> bool:
        return self.overall_status == HealthStatus.OK

    def summary(self) -> str:
        lines = [f"CORTEX Health: {self.overall_status.value}"]

        for component in self.components:
            lines.append(
                f"  - {component.name}: "
                f"{component.status.value} "
                f"{component.detail}".rstrip()
            )

        return "\n".join(lines)


class CortexHealth:

    def __init__(self) -> None:
        self._checks: Dict[str, Callable[[], bool]] = {}

    def register(
        self,
        name: str,
        check: Callable[[], bool],
    ) -> None:
        self._checks[name] = check

    def run(self) -> CortexHealthReport:

        components: List[ComponentHealth] = []
        overall = HealthStatus.OK

        for name, check in self._checks.items():

            try:

                if check():

                    components.append(
                        ComponentHealth(
                            name=name,
                            status=HealthStatus.OK,
                        )
                    )

                else:

                    components.append(
                        ComponentHealth(
                            name=name,
                            status=HealthStatus.FAILED,
                            detail="check returned False",
                        )
                    )

                    overall = HealthStatus.FAILED

            except Exception as exc:

                components.append(
                    ComponentHealth(
                        name=name,
                        status=HealthStatus.FAILED,
                        detail=f"exception: {exc}",
                    )
                )

                overall = HealthStatus.FAILED

        return CortexHealthReport(
            overall_status=overall,
            components=components,
        )




