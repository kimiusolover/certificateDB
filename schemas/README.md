# Data contracts

These JSON Schemas define the portable record shapes used by certificateDB.
YAML files in the repository must represent one of these JSON-compatible
objects.

| Schema | Purpose |
| --- | --- |
| `device-variant.schema.json` | Exact device identity, without claiming RF capability. |
| `certification-record.schema.json` | Link from a device variant to a certification identity and its evidence bundle. |
| `evidence-bundle.schema.json` | Immutable-source provenance and source-faithful observations. |
| `derived-constraint-bundle.schema.json` | Reproducible constraints based on identified inputs; explicitly not permission or runtime configuration. |
| `review-gate.schema.json` | Hash-bound human attestation required only for the four trust boundaries. |

`additionalProperties: false` is intentional. It prevents silently adding
firmware settings or an authorization flag to a record type whose purpose is
evidence. Add a reviewed, documented schema version when a new evidence field
is genuinely needed.

`review-gate.schema.json` is deliberately separate from evidence records. This
keeps ordinary collection and extraction free of review ceremony while making a
trust-boundary approval explicit and invalid when its subject or cited evidence
bytes change.
