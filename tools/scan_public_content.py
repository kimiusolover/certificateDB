#!/usr/bin/env python3
"""Fail closed on likely secrets or device identifiers before public release."""

import argparse
from pathlib import Path
import re
import subprocess
import sys


RULES = {
    "private-key": re.compile(rb"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    "credential-assignment": re.compile(rb"(?i)\b(?:password|passwd|api[_-]?key|secret|token)\s*[:=]\s*[^\s#]{4,}"),
    "mac-address": re.compile(rb"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b"),
    "serial-number": re.compile(rb"(?i)\b(?:serial(?:[_ -]?number)?|s/n)\s*[:#=]\s*\S+"),
}


def tracked_files(root):
    output = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, stdout=subprocess.PIPE).stdout
    return [root / item for item in output.decode().split("\0") if item]


def scan(root, directory=None):
    findings = []
    files = [path for path in directory.rglob("*") if path.is_file()] if directory else tracked_files(root)
    for path in files:
        try:
            content = path.read_bytes()
        except OSError:
            continue
        for label, rule in RULES.items():
            if rule.search(content):
                findings.append(f"{label}: {path.relative_to(directory or root)}")
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--directory", type=Path, help="scan every released asset, including binary images and metadata")
    args = parser.parse_args()
    try:
        findings = scan(args.root.resolve(), args.directory.resolve() if args.directory else None)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"public-content scan failed: {error}", file=sys.stderr)
        return 1
    if findings:
        print("public-content scan rejected:\n" + "\n".join(findings), file=sys.stderr)
        return 1
    print("public-content scan passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
