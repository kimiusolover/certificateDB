#!/usr/bin/env python3
"""Classify changed evidence and require a hash-valid ReviewGate when needed."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from verify_review_gate import verify


RECORD = re.compile(r"^jurisdictions/[^/]+/[^/]+/record\.yaml$")
EVIDENCE = re.compile(r"^jurisdictions/[^/]+/[^/]+/evidence\.yaml$")
GATE_DIR = "review-gates/"
DEPLOYMENT = re.compile(r'''(?ix)
    ["']?(?:flashable|deployable|release[_-]?kind)["']?\s*[:=]\s*
    ["']?(?:true|yes|on|1|firmware[_-]?image|production)["']?
''')


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, text=True, stdout=subprocess.PIPE).stdout


def status_at(root, revision, path):
    try:
        text = git(root, "show", f"{revision}:{path}")
    except subprocess.CalledProcessError:
        return None
    match = re.search(r"^status\s*:\s*([^\s#]+)", text, re.MULTILINE)
    return match.group(1) if match else "__unknown__"


def changes(root, base, head):
    output = git(root, "diff", "--name-status", "--find-renames", base, head)
    result = []
    for line in output.splitlines():
        parts = line.split("\t")
        state = parts[0]
        if state.startswith("R"):
            result.append((state, parts[2], parts[1]))
        else:
            result.append((state, parts[1], None))
    return result


def required_scopes(root, base, head):
    required = {}
    for state, path, old_path in changes(root, base, head):
        if path.startswith(GATE_DIR):
            continue
        if state != "A" and EVIDENCE.fullmatch(path):
            required.setdefault(path, set()).add("regulatory_change")
        if RECORD.fullmatch(path):
            before = status_at(root, base, old_path or path)
            after = status_at(root, head, path)
            if after in {"reviewed", "verified"} and before != after:
                required.setdefault(path, set()).add("verified_promotion")
            elif after not in {"candidate", "extracted"} or (state != "A" and before not in {"candidate", "extracted"}):
                # Unknown YAML status and all non-automatic lifecycle changes
                # are safety-relevant until a schema-aware classifier exists.
                required.setdefault(path, set()).add("regulatory_change")
        try:
            text = git(root, "show", f"{head}:{path}")
        except subprocess.CalledProcessError:
            continue
        if DEPLOYMENT.search(text):
            required.setdefault(path, set()).add("deployment")
    return required


def load_gates(root, alternate_root=None):
    gates = []
    gate_root = root / "review-gates"
    if not gate_root.is_dir():
        return gates
    for path in sorted(gate_root.rglob("*.json")):
        try:
            gate = json.loads(path.read_text(encoding="utf-8"))
            verify(root, gate, alternate_root)
            gates.append(gate)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid ReviewGate {path.relative_to(root)}: {error}") from error
    return gates


def release_files(directory):
    return {path.relative_to(directory).as_posix(): path for path in directory.rglob("*") if path.is_file()}


def enforce(root, base, head, required_scope=None, released_content_dir=None):
    required = required_scopes(root, base, head)
    gates = load_gates(root, released_content_dir)
    approved = {(gate["scope"], gate["subject"]["path"]) for gate in gates}
    missing = [(scope, path) for path, scopes in required.items() for scope in scopes if (scope, path) not in approved]
    if missing:
        details = ", ".join(f"{scope}:{path}" for scope, path in missing)
        raise ValueError(f"required ReviewGate is missing or does not match the changed subject: {details}")
    if required_scope:
        release_gates = [gate for gate in gates if gate["scope"] == required_scope]
        if not release_gates:
            raise ValueError(f"required {required_scope} ReviewGate is missing")
        if released_content_dir:
            contents = release_files(released_content_dir)
            if not contents:
                raise ValueError("release contains no downloadable content")
            approved = {
                (entry["path"], entry["sha256"])
                for gate in release_gates
                for entry in [gate["subject"], *gate["evidence"]]
            }
            missing = [name for name, path in contents.items() if (name, hashlib.sha256(path.read_bytes()).hexdigest()) not in approved]
            if missing:
                raise ValueError("public_release ReviewGate does not bind every released file: " + ", ".join(sorted(missing)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Git revision before the change")
    parser.add_argument("--head", default="HEAD", help="Git revision under review")
    parser.add_argument("--require-scope", choices=sorted({"public_release"}), help="require at least one valid gate of this scope")
    parser.add_argument("--released-content-dir", type=Path, help="downloaded release assets that must all be hash-bound by public_release")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        release_dir = args.released_content_dir.resolve() if args.released_content_dir else None
        enforce(args.root.resolve(), args.base, args.head, args.require_scope, release_dir)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"review gate enforcement failed: {error}", file=sys.stderr)
        return 1
    print("review gate enforcement passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
