# Review gates

Routine collection is automatic. A collector may create or update `candidate`
and `extracted` records after parsing, normalization, and structural
validation. `normalized` and `validated` are processing results, not
additional evidence-review statuses: an automatically generated record remains
`extracted`.

Human review is required only when a change crosses one of these boundaries:

| Boundary | Required `scope` | Gate condition |
| --- | --- | --- |
| `reviewed` or `verified` evidence | `verified_promotion` | The record, cited evidence bytes, device identity, and safety-relevant observations have been checked. |
| Any semantic change to a regulatory observation | `regulatory_change` | The old and new normalized values, units, meanings, and locators have been compared. |
| A consumer artifact becomes deployable to hardware | `deployment` | The exact artifact and its evidence inputs have been checked; consumer-side hardware, calibration, driver, and transport gates must also pass. |
| Material is released outside the repository | `public_release` | The exact release content passed sensitive-data scanning and is approved for publication. |

Every approval is a `ReviewGate` document conforming to
`schemas/review-gate.schema.json`. Its `subject`, optional `base`, and every
`evidence` entry bind a repository-relative path to the SHA-256 of the exact
bytes reviewed. A changed hash invalidates the approval; it must not be copied
forward. `--force`, an environment variable, or an absent gate must never
bypass this rule.

Use `python tools/verify_review_gate.py path/to/gate.json` in CI to reject a
missing file, unsafe path, hash mismatch, unknown scope, or incomplete
acceptance record. The command intentionally accepts JSON only, so its own
input has a deterministic byte representation; evidence and subject files may
remain YAML, PDF, or another repository format.

`python tools/enforce_review_gates.py --base <revision>` classifies the Git
diff and requires matching gates; `make check-review-gates BASE=<revision>` is
its CI-friendly form. A `v*` tag starts a pre-publication workflow: it checks
out that immutable tag, requires a non-empty `release-assets/` directory, and
requires a valid `public_release` gate to bind the SHA-256 of every asset
before scanning those exact bytes. Only after all checks pass does the workflow
create the GitHub Release and upload those assets.

This is a trust boundary for the repository's GitHub Actions publication path,
not a GitHub-wide release prohibition. A user or external token with
`contents: write` can create a GitHub Release directly without invoking this
workflow or its `ReviewGate` check. Repository roles, token issuance, and any
separate release-protection controls must restrict that manual path.

Self-review is permitted for a one-person project, but it must be recorded
with `review.required: true`, reviewer identity, timestamp, accepted decision,
and concise notes. A workflow may require a different reviewer later without
changing the evidence model.

## CI contract

CI must classify a change before merge or release. Classification is
fail-closed: unknown fields or a difference that cannot be classified are
treated as `regulatory_change`.

1. Validate all changed YAML/JSON documents against their schema.
2. Permit ordinary generated changes that remain `candidate` or `extracted`
   without a review gate.
3. Require a matching, hash-valid gate for a status promotion to `reviewed` or
   `verified`.
4. Require `regulatory_change` when an observation's original value, unit,
   meaning, field, or locator changes; a formatting-only change does not.
5. Require `deployment` for `flashable: true`, `deployable: true`, or an
   equivalent consumer hand-off.
6. Require `public_release` for release artifacts, published documents, or
   externally visible image assets, and run secret/privacy checks for
   credentials, MAC addresses, serial numbers, QR payloads, and image
   metadata.

The gate is evidence review only. It neither grants RF transmission permission
nor overrides the downstream restrictive-intersection and fail-closed rules.
