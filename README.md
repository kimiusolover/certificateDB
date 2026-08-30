# certificateDB

`certificateDB` is a traceable regulatory evidence ledger for radio equipment.
It stores reviewable links between an exact device variant, an official
certification record, and carefully extracted regulatory observations.

It is not a replacement for a regulator's database, a legal opinion, a
firmware configuration generator, or an RF-transmission permission service.
Firmware projects may consume reviewed evidence and derived constraints from
this repository, but must independently combine them with device hardware,
calibration, driver, and current jurisdictional limits.

`verified` means that the device identity, evidence integrity, and
safety-relevant observations were independently reviewed against their cited
sources. It never means that a device, user, channel, bandwidth, or transmit
power is authorized for operation.

The repository policy is in [POLICY.md](POLICY.md). No certification record is
accepted merely because a label, OCR result, or search-result snippet appears
to match.

Routine extraction needs no approval. The four situations that do require one
are defined in [REVIEW_GATES.md](REVIEW_GATES.md); the gate is hash-bound to
the reviewed content and evidence, so it cannot silently approve later bytes.

## Intended layout

```
jurisdictions/
  JP/
    MIC/
      201-230283/
        record.yaml
        evidence.yaml
        documents/
          <sha256>.pdf
devices/
  tp-link/
    archer-ax23v/
      v1.yaml
derived/
  JP/
    tp-link.archer-ax23v.v1/
      <input-hash>.yaml
schemas/
  certification-record.schema.json
  evidence-bundle.schema.json
  device-variant.schema.json
  derived-constraint-bundle.schema.json
```

Jurisdiction-specific collection and verification rules belong below
`jurisdictions/`. For Japan, [jurisdictions/JP/policy.yaml](jurisdictions/JP/policy.yaml)
links the governing Radio Act and the applicable certification-rule source,
while preserving the distinction between legal sources, official certification
evidence, and downstream configuration constraints.

Binary source documents may instead be held in approved object storage. In
that case, `evidence.yaml` records the immutable source URL, retrieval date,
content hash, and access instructions. Do not add documents unless their terms
permit retention and redistribution.

## Repository boundary

`certificateDB` owns facts and their provenance:

- exact device and radio-variant identity;
- official certification identifiers and source links;
- immutable evidence hashes and precise source locators;
- source-faithful regulatory observations; and
- reproducible, evidence-derived constraint bundles.

It does not own hardware capability, board calibration, kernel/driver limits,
or a final runtime configuration. Consumers must calculate an effective RF
configuration from the most restrictive applicable inputs and fail closed when
a safety-relevant input is absent or conflicts.

The machine-readable contracts are in `schemas/`. They deliberately have no
fields for hostapd configuration, driver commands, EEPROM/NVRAM contents, or
an RF "allow" decision.

## Evidence URL example

Every reviewed source has an explicit official URL. Record both the registry
page that identifies the certification and the direct document URL when the
latter contains the extracted technical value.

```yaml
authority: MIC
jurisdiction: JP
certificationId: "201-230283"
sources:
  - role: registry_record
    sourceUrl: "https://official-authority.example/record/201-230283"
    sourceUrlRetrievedAt: "2026-08-30T00:00:00Z"
    sha256: "..."
  - role: test_report
    sourceUrl: "https://official-authority.example/documents/201-230283.pdf"
    sourceUrlRetrievedAt: "2026-08-30T00:00:00Z"
    sha256: "..."
    observations:
      - page: 23
        field: maxConductedPower
        value: 17.84
        unit: dBm
        meaning: certified_max
```
