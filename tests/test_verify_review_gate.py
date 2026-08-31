import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).parents[1] / "tools" / "verify_review_gate.py"
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("verify_review_gate", MODULE_PATH)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)
ENFORCER_SPEC = importlib.util.spec_from_file_location("enforce_review_gates", Path(__file__).parents[1] / "tools" / "enforce_review_gates.py")
ENFORCER = importlib.util.module_from_spec(ENFORCER_SPEC)
ENFORCER_SPEC.loader.exec_module(ENFORCER)
SCANNER_SPEC = importlib.util.spec_from_file_location("scan_public_content", Path(__file__).parents[1] / "tools" / "scan_public_content.py")
SCANNER = importlib.util.module_from_spec(SCANNER_SPEC)
SCANNER_SPEC.loader.exec_module(SCANNER)


class VerifyReviewGateTest(unittest.TestCase):
    def make_gate(self, root):
        subject = root / "record.yaml"
        evidence = root / "evidence.pdf"
        subject.write_text("status: extracted\n", encoding="utf-8")
        evidence.write_bytes(b"source bytes")
        return {
            "apiVersion": "certificateDB/v1",
            "kind": "ReviewGate",
            "scope": "verified_promotion",
            "subject": {"path": "record.yaml", "sha256": hashlib.sha256(subject.read_bytes()).hexdigest()},
            "evidence": [{"path": "evidence.pdf", "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()}],
            "review": {"required": True, "reviewer": "self", "reviewedAt": "2026-08-30T00:00:00Z", "decision": "accepted"},
        }

    def test_accepts_exact_reviewed_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            GATE.verify(root, self.make_gate(root))

    def test_rejects_changed_subject(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gate = self.make_gate(root)
            (root / "record.yaml").write_text("status: verified\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash does not match"):
                GATE.verify(root, gate)

    def test_rejects_missing_required_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gate = self.make_gate(root)
            gate["review"]["required"] = False
            with self.assertRaisesRegex(ValueError, "accepted required review"):
                GATE.verify(root, gate)


class EnforceReviewGatesTest(unittest.TestCase):
    def git(self, root, *args):
        return subprocess.run(["git", *args], cwd=root, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()

    def commit(self, root, message):
        self.git(root, "add", ".")
        self.git(root, "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-qm", message)

    def test_verified_promotion_requires_matching_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.git(root, "init", "-q")
            record = root / "jurisdictions" / "JP" / "example" / "record.yaml"
            evidence = root / "jurisdictions" / "JP" / "example" / "evidence.yaml"
            record.parent.mkdir(parents=True)
            record.write_text("status: extracted\n", encoding="utf-8")
            evidence.write_text("observations: []\n", encoding="utf-8")
            self.commit(root, "base")
            base = self.git(root, "rev-parse", "HEAD")
            record.write_text("status: verified\n", encoding="utf-8")
            self.commit(root, "promote")
            with self.assertRaisesRegex(ValueError, "verified_promotion"):
                ENFORCER.enforce(root, base, "HEAD")
            gate_path = root / "review-gates" / "verified.json"
            gate_path.parent.mkdir()
            gate_path.write_text(json.dumps({
                "apiVersion": "certificateDB/v1", "kind": "ReviewGate", "scope": "verified_promotion",
                "subject": {"path": "jurisdictions/JP/example/record.yaml", "sha256": hashlib.sha256(record.read_bytes()).hexdigest()},
                "evidence": [{"path": "jurisdictions/JP/example/evidence.yaml", "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()}],
                "review": {"required": True, "reviewer": "self", "reviewedAt": "2026-08-30T00:00:00Z", "decision": "accepted"},
            }), encoding="utf-8")
            ENFORCER.enforce(root, base, "HEAD")

    def test_json_deployable_value_requires_deployment_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.git(root, "init", "-q")
            manifest = root / "artifact.json"
            manifest.write_text('{"deployable": false}', encoding="utf-8")
            self.commit(root, "base")
            base = self.git(root, "rev-parse", "HEAD")
            manifest.write_text('{"deployable": true}', encoding="utf-8")
            self.commit(root, "deployable")
            with self.assertRaisesRegex(ValueError, "deployment:artifact.json"):
                ENFORCER.enforce(root, base, "HEAD")

    def test_binary_evidence_does_not_require_utf8_decoding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.git(root, "init", "-q")
            evidence = root / "documents" / "JP" / "example.pdf"
            evidence.parent.mkdir(parents=True)
            evidence.write_bytes(b"%PDF-1.7\nbase")
            self.commit(root, "base")
            base = self.git(root, "rev-parse", "HEAD")
            # Deliberately invalid UTF-8, as is normal for PDF content.
            evidence.write_bytes(b"%PDF-1.7\n\xe2\x28\xa1")
            self.commit(root, "add binary evidence")
            ENFORCER.enforce(root, base, "HEAD")

    def test_public_release_gate_must_cover_every_downloaded_asset(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.git(root, "init", "-q")
            (root / "record.yaml").write_text("record\n", encoding="utf-8")
            self.commit(root, "base")
            base = self.git(root, "rev-parse", "HEAD")
            assets = root / "downloaded"
            assets.mkdir()
            (assets / "one.bin").write_bytes(b"one")
            (assets / "two.bin").write_bytes(b"two")
            gate_dir = root / "review-gates"
            gate_dir.mkdir()
            gate = {
                "apiVersion": "certificateDB/v1", "kind": "ReviewGate", "scope": "public_release",
                "subject": {"path": "record.yaml", "sha256": hashlib.sha256((root / "record.yaml").read_bytes()).hexdigest()},
                "evidence": [{"path": "one.bin", "sha256": hashlib.sha256((assets / "one.bin").read_bytes()).hexdigest()}],
                "review": {"required": True, "reviewer": "self", "reviewedAt": "2026-08-30T00:00:00Z", "decision": "accepted"},
            }
            (gate_dir / "release.json").write_text(json.dumps(gate), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "every released file: two.bin"):
                ENFORCER.enforce(root, base, "HEAD", "public_release", assets)
            gate["evidence"].append({"path": "two.bin", "sha256": hashlib.sha256((assets / "two.bin").read_bytes()).hexdigest()})
            (gate_dir / "release.json").write_text(json.dumps(gate), encoding="utf-8")
            ENFORCER.enforce(root, base, "HEAD", "public_release", assets)


class PublicContentScanTest(unittest.TestCase):
    def test_scans_binary_image_metadata_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "label.jpg").write_bytes(b"\xff\xd8Exif\x00MAC=00:11:22:33:44:55\xff\xd9")
            self.assertEqual(SCANNER.scan(directory, directory), ["mac-address: label.jpg"])


class ReleaseWorkflowTest(unittest.TestCase):
    def test_publication_happens_after_tag_preflight(self):
        workflow = (Path(__file__).parents[1] / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("tags: ['v*']", workflow)
        self.assertNotIn("\n  release:\n", workflow)
        self.assertLess(workflow.index("Require publication review"), workflow.index("Publish reviewed assets"))
        self.assertIn("gh release create", workflow)

    def test_push_falls_back_to_a_full_tree_review_when_base_is_unavailable(self):
        workflow = (Path(__file__).parents[1] / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn('git cat-file -e "$BASE^{commit}"', workflow)
        self.assertIn('git hash-object -t tree /dev/null', workflow)
