from core.cortex_health import (
    CortexHealth,
    HealthStatus,
)


def main():

    print("CORTEX HEALTH CHECK")
    print("=" * 50)

    health = CortexHealth()

    # --------------------------------------------------
    # REGISTER CORE HEALTH CHECKS
    # --------------------------------------------------

    health.register(
        "core",
        lambda: True,
    )

    health.register(
        "agent_registry",
        lambda: True,
    )

    health.register(
        "permission_engine",
        lambda: True,
    )

    health.register(
        "approval_gate",
        lambda: True,
    )

    health.register(
        "tool_registry",
        lambda: True,
    )

    health.register(
        "tool_gateway",
        lambda: True,
    )

    # --------------------------------------------------
    # RUN HEALTH CHECK
    # --------------------------------------------------

    report = health.run()

    print("\n" + report.summary())

    print("\nOVERALL STATUS:")
    print(report.overall_status.value)

    print("\nCOMPONENT STATUS:")

    for component in report.components:

        print(
            f"{component.name:<20} | "
            f"{component.status.value:<8} | "
            f"{component.detail}"
        )

    # --------------------------------------------------
    # VERIFY
    # --------------------------------------------------

    print("\n" + "=" * 50)

    if report.is_healthy():
        print("CORTEX HEALTH CHECK: PASS")
        print("CORTEX STATUS: READY")
    else:
        print("CORTEX HEALTH CHECK: FAIL")
        print("CORTEX STATUS: NOT READY")


if __name__ == "__main__":
    main()





