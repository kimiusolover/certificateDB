# certificateDB policy

## 1. Purpose and boundary

This repository is a versioned, traceable regulatory evidence ledger for
radio-equipment certification information. Its purpose is to make each
normalized observation traceable to an official source and to an exact device
variant.

It does **not**:

- issue, recreate, or validate a regulator's certification;
- decide whether a product is legal to operate in a jurisdiction;
- authorize a user to change an RF configuration; or
- contain final hostapd, driver, EEPROM, or factory-calibration settings.

Any downstream system must treat these records as one input to a conservative
constraint calculation, never as a unilateral permission to enable a channel
or transmit power.

## 2. Source of truth and provenance

Every accepted record must identify an official primary source: a regulator,
registered certification body, manufacturer declaration required by the
applicable scheme, or an official test report/certificate published by one of
those parties.

Each evidence item records:

- authority and jurisdiction;
- `sourceUrl`: the canonical official page or direct official document URL;
- `sourceUrlRetrievedAt`: the timestamp at which bytes were obtained, when
  bytes were obtained;
- retrieval timestamp and retriever identity or service account;
- original filename, MIME type, and SHA-256 of the original bytes;
- page, table, section, or other precise locator for each extracted fact; and
- any known source-access or redistribution restriction.

`sourceUrl` is a reference, not a liveness assertion. For a manually checked
registry search, preserve the exact URL string as entered or returned by the
authority, together with `retrieval: manual`, `checkedAt`, `checkedBy`, and
`matchStatus`. Do not normalize its query string or replace it with a generated
URL. Repository validation must never fetch it, preview it, issue a HEAD
request, monitor it, proxy it, or re-run the search.

The search form is for a new human investigation. A complete search-result URL
is immutable evidence of one completed investigation. A direct document URL is
preferred for extracted technical observations, but the registry search-result
or detail URL must also be recorded when it establishes the
certification-number-to-device association.

Search-result snippets, label photographs, OCR, reseller pages, forum posts,
and unofficial mirrors are discovery aids only. They may suggest a candidate
identifier but cannot establish a `verified` certification fact.

## 3. Device identity

Records are keyed by the exact combination of vendor, model, hardware revision,
radio/board revision when known, antenna configuration, jurisdiction, and
certification authority. A model name alone is never sufficient to inherit a
record from another revision or SKU.

Physical label evidence may establish that a mark and identifier appeared on a
specific device. It must be stored separately from official certification
evidence and must be marked `physical_label_observation`; it is not proof of
certification validity.

## 4. Data model and meaning

Values retain their original unit, wording, and meaning. At minimum, power
observations distinguish `measured`, `configured`, `certified_max`,
`regulatory_limit`, `eirp`, and `conducted_power`. Frequency, bandwidth,
antenna gain, DFS behaviour, and measurement setup have the same requirement:
they are observations with evidence, not inferred device capabilities.

Normalized records must preserve the original value and source locator. Unit
conversion is allowed only when the original representation remains available.
Unknown values remain unknown; contributors must not substitute a typical
value, a value from another revision, or a national maximum.

## 5. Status and review

Records use one of these evidence-review states:

- `candidate` — discovered but not yet source-checked;
- `extracted` — transcribed or parsed from an attached source;
- `reviewed` — a reviewer checked the value against the cited source;
- `verified` — device identity, source integrity, and every safety-relevant
  observation were independently reviewed;
- `superseded` or `retracted` — retained for audit, never selected by default.

These states describe the quality of the evidence record only. In particular,
`verified` is not an authorization to transmit and does not assert legal
operability, a permitted channel, bandwidth, or transmit power.

Automation may create `candidate` or `extracted` records only. Parsing,
normalization, and structural validation are automatic processing steps; they
do not promote an evidence-review state. Automation cannot set `reviewed` or
`verified`.

Review is required only at the trust boundaries defined in
[`REVIEW_GATES.md`](REVIEW_GATES.md): promotion to `reviewed` or `verified`, a
semantic regulatory-observation change, deployment-capable output, and an
external publication. A review binds the reviewed subject and cited evidence
to their SHA-256 values, so it expires when either changes. Self-review is
allowed when recorded; omitting the record is not. `matchStatus: unconfirmed`
or `mismatch` cannot be promoted to `reviewed` or `verified`, and cannot be
used to derive device, RF, or firmware constraints.

## 6. Derived data and consumers

`certificateDB` may store a reproducible derivation description, including its
input record hashes and rule version. A derivation is a constraint bundle, not
an authoritative firmware setting or permission decision. A consumer such as
`routerctl` must calculate the effective
configuration from the intersection of:

1. approved certification observations;
2. current jurisdiction rules;
3. exact hardware and antenna capability;
4. EEPROM/board-data calibration constraints; and
5. driver/kernel-reported limits.

The consumer must choose the most restrictive applicable limit and must fail
closed when it lacks a required, safety-relevant input. Neither an administrator
password nor a country-selection action may override a hardware, driver, or
approved-profile limit.

## 7. Privacy, security, and sensitive material

Never commit raw EEPROM, factory/NVRAM dumps, MAC addresses, serial numbers,
Wi-Fi credentials, private keys, QR codes containing secrets, or full device
label photos. Store only a digest and a sanitized, non-secret capability
summary when hardware evidence is required.

Do not commit authentication cookies, API keys, captured sessions, or documents
whose terms prohibit retention. Scan additions for secrets and personal data
before an external-publication review. Where an official source contains unavoidable personal data,
prefer a canonical link plus digest over copying the document.

## 8. Collection and automation

Collection must respect the source's access controls, terms, rate limits, and
robots or API requirements. Do not bypass CAPTCHA, login, paywall, or technical
access restrictions. A human may perform a permitted search and submit the
resulting official document for import.

Search URLs are never collected automatically. In particular, link-preview
fetches, health checks, scheduled recrawls, server-side proxying, and URL
canonicalization are prohibited. A user may explicitly open a saved link to
re-check it; a new check creates a new evidence record rather than mutating the
old URL or check metadata.

Importers are jurisdiction-specific adapters. They must emit evidence-bearing
observations, report ambiguity, and reject unsupported layouts rather than
guess. OCR is candidate generation only and requires a human source check.

## 9. Repository integrity and corrections

All substantive changes use reviewable commits. Evidence bytes are immutable:
fixes create a new record revision linked to the prior record rather than
silently rewriting history. Hash changes, corrected device identity, and
supersession reasons must be recorded explicitly.

Fixtures and demonstrations must be plainly labelled `synthetic` and use
non-production identifiers. They must never be placed in the production
jurisdiction or device index.

## 10. Jurisdiction extensions

Each jurisdiction adapter documents its authority, identifier syntax, source
types, status mapping, and restrictions. Shared schema fields have the same
meaning worldwide; a country-specific field must be namespaced and documented.
Adding a jurisdiction must not weaken the review or provenance requirements
above.

The jurisdiction policy must also list its governing legal and regulatory
sources with explicit `sourceUrl` fields. A law establishes the framework, but
does not justify inventing a device-specific numeric constraint: every such
constraint still requires its own applicable rule and official device evidence.
