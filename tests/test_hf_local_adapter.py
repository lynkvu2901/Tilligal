"""T2 behavior tests: synthetic records only, no network/model calls."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq

from ai_core import data_contracts as contract
from ai_core.adapters import hf_local as adapter
from scripts import inspect_local_legal as t1


def neutral_document(**changes):
    values = dict(
        source_id="team-crawl-fixture", source_record_id="doc-001",
        source_snapshot_id="delivery-001", source_version=None,
        document_number="DEMO-001", title="Synthetic, not law", document_type="DEMO",
        issuing_authority=None, language="vi", content_format="text",
        content="  Nội dung giả: không phải luật.\r\nĐiều 1. Không bỏ phủ định.  ",
        raw_ref={"uri": "file:///fixture/raw.txt", "file_sha256": "a" * 64,
                 "record_key": "stable_id", "record_value": "doc-001"},
        source_url="https://example.org/fixture", collected_at="2026-10-20T09:00:00+07:00",
        issued_on=None, effective_from=None, effective_to=None,
        effect_status_reported=None, status_observed_at=None,
        processing_steps=["FIXTURE_ONLY"], issues=["NOT_LEGAL_DATA"],
    )
    values.update(changes)
    return contract.build_document(**values)


class HFLocalAdapterTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(__file__).resolve().parent
        self.root = self.test_dir / (".tmp-tillegal-t2-" + uuid4().hex)
        self.root.mkdir()
        self.addCleanup(self.cleanup_fixture)
        self.raw = self.root / "raw"
        self.raw.mkdir()
        self.metadata = []
        for doc_id, (number, kind) in adapter.PILOT.items():
            row = dict.fromkeys(t1.METADATA_FIELDS)
            row.update(id=doc_id, so_ky_hieu=number, title="DEMO", loai_van_ban=kind,
                       ngay_ban_hanh="20/11/2019", ngay_co_hieu_luc="01/01/2021",
                       tinh_trang_hieu_luc="Còn hiệu lực")
            self.metadata.append(row)
        translated = deepcopy(self.metadata[0])
        translated.update(id="vbpqta_11135", loai_van_ban="Bản dịch văn bản")
        self.metadata.insert(0, translated)
        self.content = [{"id": r["id"], "content_html": f'<html><body>\r\n<p>DEMO {r["id"]}: Không xóa chữ.</p><table><tr><td>A</td><td>10</td></tr></table><img src="data:fixture"/>\r\n</body></html>'}
                        for r in reversed(self.metadata)]
        self.manifest_path = self.root / "t1" / "manifest.json"
        self.selection_path = self.root / "selection" / "pilot.json"

    def cleanup_fixture(self):
        resolved = self.root.resolve()
        if resolved.parent != self.test_dir or not resolved.name.startswith(".tmp-tillegal-t2-"):
            raise ValueError("Refusing cleanup outside this test's fixture directory")
        shutil.rmtree(resolved)

    def write_table(self, name, rows):
        schema = pa.schema([(key, pa.string()) for key in t1.SCHEMAS[name]])
        pq.write_table(pa.Table.from_pylist(rows, schema=schema), self.raw / f"{name}.parquet", row_group_size=2)

    def prepare_t1(self):
        self.write_table("metadata", self.metadata)
        self.write_table("content", self.content)
        self.write_table("relationships", [{"doc_id": "139264", "other_doc_id": "146696", "relationship": "DEMO"}])
        manifest, validation, selection = t1.inspect_inputs(self.raw)
        targets = t1.output_targets(self.raw, self.manifest_path.parent, self.selection_path)
        t1.write_artifacts(manifest, validation, selection, targets)
        return manifest, selection

    def test_export_preserves_html_and_t1_and_selects_by_id(self):
        self.prepare_t1()
        before = {p: contract.file_hash(p) for p in self.root.rglob("*") if p.is_file()}
        result = adapter.export_pilot(self.manifest_path, self.selection_path, self.root / "staging")
        documents = contract.load_documents(self.root / "staging" / "documents.jsonl")
        originals = {row["id"]: row["content_html"] for row in self.content}
        self.assertEqual({d.source_record_id for d in documents}, set(adapter.PILOT))
        for document in documents:
            self.assertEqual(document.content, originals[document.source_record_id])
            self.assertEqual(document.content_sha256, contract.content_hash(originals[document.source_record_id]))
            self.assertEqual(document.effective_from, "2021-01-01")
            self.assertEqual(document.effect_status_reported, "Còn hiệu lực")
            self.assertEqual(document.temporal_status, "UNKNOWN")
            self.assertEqual(document.legal_approval, "QUARANTINE")
            self.assertEqual(document.usage_policy, "EXPERIMENTAL_ONLY")
            self.assertIsNone(document.source_url)
            self.assertIsNone(document.collected_at)
            self.assertIsNone(document.source_version)
            self.assertIn("IMAGES_PRESERVED_NOT_INTERPRETED", document.issues)
        self.assertIsNone(result["corpus_snapshot_id"])
        self.assertFalse(result["approved_for_legal_verification"])
        for path, digest in before.items():
            self.assertEqual(contract.file_hash(path), digest)
        for artifact in result["artifacts"]:
            self.assertEqual(contract.file_hash(self.root / "staging" / artifact["path"]), artifact["sha256"])

    def test_duplicate_or_missing_ids_fail_in_readers(self):
        for table, source, reader in (("metadata", self.metadata, adapter.read_selected_metadata),
                                      ("content", self.content, adapter.read_selected_content)):
            pilot = next(row for row in source if row["id"] == "139264")
            self.write_table(table, source + [deepcopy(pilot)])
            with self.assertRaisesRegex(contract.ContractError, "Duplicate"):
                reader(self.raw / f"{table}.parquet")
            self.write_table(table, [row for row in source if row["id"] != "139264"])
            with self.assertRaisesRegex(contract.ContractError, "Missing"):
                reader(self.raw / f"{table}.parquet")

    def test_wrong_parquet_type_rejected(self):
        pq.write_table(pa.table({"id": [139264], "content_html": ["x"]}), self.raw / "content.parquet")
        with self.assertRaisesRegex(contract.ContractError, "schema"):
            adapter.read_selected_content(self.raw / "content.parquet")

    def test_source_hash_change_blocks_export(self):
        self.prepare_t1()
        with (self.raw / "content.parquet").open("ab") as stream:
            stream.write(b"changed fixture")
        with self.assertRaisesRegex(contract.ContractError, "hash mismatch"):
            adapter.export_pilot(self.manifest_path, self.selection_path, self.root / "staging")
        self.assertFalse((self.root / "staging").exists())

    def test_selection_change_and_snapshot_mismatch_rejected(self):
        self.prepare_t1()
        data = json.loads(self.selection_path.read_text(encoding="utf-8"))
        data["snapshot_id"] = "b" * 64
        self.selection_path.write_bytes(contract.canonical_json(data))
        with self.assertRaisesRegex(contract.ContractError, "snapshot identity"):
            adapter.verify_inputs(self.manifest_path, self.selection_path)

    def test_invalid_date_is_unknown_with_issue_not_legal_approval(self):
        manifest, _ = self.prepare_t1()
        row = deepcopy(next(r for r in self.metadata if r["id"] == "139264"))
        row["ngay_co_hieu_luc"] = "31/02/2021"
        document = adapter.map_document(row, "<body>DEMO</body>", manifest)
        self.assertIsNone(document.effective_from)
        self.assertIn("INVALID_DATE:effective_from:31/02/2021", document.issues)
        self.assertEqual(document.temporal_status, "UNKNOWN")

    def test_html_empty_or_only_script_is_rejected(self):
        manifest, _ = self.prepare_t1()
        row = next(r for r in self.metadata if r["id"] == "139264")
        for html in (None, " ", "<body></body>", "<body><script>not content</script><img src='x'/></body>"):
            with self.subTest(html=html):
                with self.assertRaises(contract.ContractError):
                    adapter.map_document(row, html, manifest)

    def test_partial_export_not_published_if_inputs_change(self):
        self.prepare_t1()
        original = adapter.convert_pilot
        def change_after_read(manifest, selection):
            docs = original(manifest, selection)
            self.selection_path.write_text("{}", encoding="utf-8")
            return docs
        with patch.object(adapter, "convert_pilot", side_effect=change_after_read):
            with self.assertRaisesRegex(contract.ContractError, "hash mismatch"):
                adapter.export_pilot(self.manifest_path, self.selection_path, self.root / "staging")
        self.assertFalse((self.root / "staging").exists())

    def test_no_overwrite_or_output_inside_raw(self):
        self.prepare_t1()
        output_dir = self.root / "staging"
        adapter.export_pilot(self.manifest_path, self.selection_path, output_dir)
        before = (output_dir / "manifest.json").read_bytes()
        with self.assertRaises(FileExistsError):
            adapter.export_pilot(self.manifest_path, self.selection_path, output_dir)
        self.assertEqual((output_dir / "manifest.json").read_bytes(), before)
        with self.assertRaisesRegex(contract.ContractError, "outside"):
            adapter.export_pilot(self.manifest_path, self.selection_path, self.raw / "staging")

    def test_repeat_conversion_identical_except_creation_timestamp(self):
        self.prepare_t1()
        first = adapter.export_pilot(self.manifest_path, self.selection_path, self.root / "a")
        second = adapter.export_pilot(self.manifest_path, self.selection_path, self.root / "b")
        self.assertEqual((self.root / "a/documents.jsonl").read_bytes(), (self.root / "b/documents.jsonl").read_bytes())
        first.pop("created_at_utc"); second.pop("created_at_utc")
        self.assertEqual(first, second)

    def test_contract_accepts_team_fixture_without_hf_dependencies(self):
        document = neutral_document()
        path = self.root / "team.jsonl"
        path.write_bytes(contract.canonical_json(document.to_dict()) + b"\n")
        code = '''
import builtins, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.startswith(('pyarrow', 'bs4', 'ai_core.adapters', 'scripts')):
        raise AssertionError('Unexpected source-specific dependency: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from pathlib import Path
from ai_core.data_contracts import load_documents
doc = load_documents(Path(sys.argv[1]))[0]
assert doc.source_id == 'team-crawl-fixture'
assert doc.content_format == 'text'
print('neutral-contract-only: PASS')
'''
        result = subprocess.run([sys.executable, "-B", "-c", code, str(path)], cwd=self.test_dir.parent,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_contract_missing_wrong_types_and_unknown_fields(self):
        original = neutral_document().to_dict()
        for key, value in (("content", 123), ("collected_at", "2026-10-20T09:00:00"),
                           ("effective_from", "2021-02-31"), ("source_url", "file:///x"),
                           ("issues", "not-an-array"), ("language", "")):
            data = deepcopy(original); data[key] = value
            with self.subTest(key=key), self.assertRaises(contract.ContractError):
                contract.DocumentVersion.from_dict(data)
        missing = deepcopy(original); missing.pop("source_record_id")
        with self.assertRaises(contract.ContractError):
            contract.DocumentVersion.from_dict(missing)
        extra = deepcopy(original); extra["so_ky_hieu"] = "HF field leaks into core"
        with self.assertRaises(contract.ContractError):
            contract.DocumentVersion.from_dict(extra)

    def test_hash_identity_and_approval_tampering_rejected(self):
        original = neutral_document().to_dict()
        for key, value in (("content", "changed"), ("document_id", "someone-else"),
                           ("title", "changed metadata"), ("legal_approval", "VERIFIED")):
            data = deepcopy(original); data[key] = value
            with self.subTest(key=key), self.assertRaises(contract.ContractError):
                contract.DocumentVersion.from_dict(data)

    def test_version_changes_with_metadata_content_not_file_location(self):
        first = neutral_document()
        metadata_changed = neutral_document(title="New metadata")
        content_changed = neutral_document(content="New text")
        relocated = neutral_document(raw_ref={**first.to_dict()["raw_ref"], "uri": "file:///relocated/raw.txt"})
        self.assertEqual(first.document_id, content_changed.document_id)
        self.assertNotEqual(first.document_version_id, content_changed.document_version_id)
        self.assertNotEqual(first.document_version_id, metadata_changed.document_version_id)
        self.assertEqual(first.document_version_id, relocated.document_version_id)

    def test_loader_rejects_duplicate_record_and_broken_line(self):
        line = contract.canonical_json(neutral_document().to_dict()) + b"\n"
        path = self.root / "neutral.jsonl"
        path.write_bytes(line + line)
        with self.assertRaisesRegex(contract.ContractError, "duplicate"):
            contract.load_documents(path)
        path.write_bytes(line + b"not-json\n")
        with self.assertRaisesRegex(contract.ContractError, ":2:"):
            contract.load_documents(path)


if __name__ == "__main__":
    unittest.main()
