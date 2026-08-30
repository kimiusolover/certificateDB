#!/usr/bin/env python3
"""Fail closed when a ReviewGate does not cover the exact reviewed bytes."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


SCOPES = {"verified_promotion", "regulatory_change", "deployment", "public_release"}


def fail(message):
    raise ValueError(message)


def repository_file(root, relative, alternate_root=None):
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts:
        fail(f"unsafe repository-relative path: {relative!r}")
    candidate = (root / path).resolve()
    if root not in candidate.parents and candidate != root:
        fail(f"path escapes repository: {relative!r}")
    if candidate.is_file():
        return candidate
    if alternate_root:
        alternate = (alternate_root / path).resolve()
        if alternate_root not in alternate.parents and alternate != alternate_root:
            fail(f"path escapes release content: {relative!r}")
        if alternate.is_file():
            return alternate
    fail(f"reviewed file is missing: {relative}")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_bound_file(root, entry, label, alternate_root=None):
    if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
        fail(f"{label} must contain exactly path and sha256")
    expected = entry["sha256"]
    if not isinstance(expected, str) or len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        fail(f"{label}.sha256 is not a lowercase SHA-256")
    actual = digest(repository_file(root, entry["path"], alternate_root))
    if actual != expected:
        fail(f"{label} hash does not match current bytes: {entry['path']}")


def verify(root, gate, alternate_root=None):
    required = {"apiVersion", "kind", "scope", "subject", "evidence", "review"}
    if set(gate) - {"apiVersion", "kind", "scope", "subject", "base", "evidence", "review"} or not required <= set(gate):
        fail("gate has missing or unknown top-level fields")
    if gate["apiVersion"] != "certificateDB/v1" or gate["kind"] != "ReviewGate":
        fail("not a certificateDB/v1 ReviewGate")
    if gate["scope"] not in SCOPES:
        fail("unknown review scope")
    verify_bound_file(root, gate["subject"], "subject", alternate_root)
    if "base" in gate:
        verify_bound_file(root, gate["base"], "base", alternate_root)
    if not isinstance(gate["evidence"], list) or not gate["evidence"]:
        fail("evidence must be a non-empty array")
    for index, entry in enumerate(gate["evidence"]):
        verify_bound_file(root, entry, f"evidence[{index}]", alternate_root)
    review = gate["review"]
    if not isinstance(review, dict) or set(review) - {"required", "reviewer", "reviewedAt", "decision", "notes"}:
        fail("review has unknown fields")
    if review.get("required") is not True or review.get("decision") != "accepted":
        fail("gate does not contain an accepted required review")
    if not isinstance(review.get("reviewer"), str) or not review["reviewer"].strip():
        fail("gate reviewer is required")
    if not isinstance(review.get("reviewedAt"), str) or not review["reviewedAt"].strip():
        fail("gate reviewedAt is required")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gate", type=Path, help="JSON ReviewGate document")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        gate = json.loads(args.gate.read_text(encoding="utf-8"))
        verify(root, gate)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"review gate rejected: {error}", file=sys.stderr)
        return 1
    print(f"review gate accepted: {args.gate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
