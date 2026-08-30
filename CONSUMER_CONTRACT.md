# Consumer contract

Consumers may use `reviewed` or `verified` records as evidence inputs only.
They must not interpret either status, a certification identifier, or a
derived constraint bundle as authorization to transmit.

To produce a runtime RF configuration, a consumer must intersect at least:

1. certificateDB evidence-derived constraints for the exact device variant;
2. applicable current jurisdictional rules;
3. hardware and antenna capability from `router-platform`;
4. immutable calibration and board-data limits; and
5. limits reported by the kernel and driver.

The consumer selects the most restrictive compatible result. Missing,
ambiguous, stale, or contradictory safety-relevant inputs require a fail-closed
result. The generated runtime configuration belongs to the consumer project;
it is not committed to certificateDB.
