"""Behavior tests use tiny synthetic Parquet files, never the legal corpus."""
from copy import deepcopy
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq

from scripts import inspect_local_legal as audit


class LocalInspectionTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(__file__).resolve().parent
        self.root = self.test_dir / (".tmp-tillegal-t1-" + uuid4().hex)
        self.root.mkdir()
        self.addCleanup(self.cleanup_fixture)
        self.raw = self.root / "raw"
        self.raw.mkdir()
        self.metadata = []
        for doc_id, number, kind in audit.PILOT:
            self.metadata.append(self.meta(doc_id, number, kind))
        self.metadata.append(self.meta("vbpqta_11135", "45/2019/QH14", "Bản dịch văn bản"))
        self.metadata.append(self.meta("135139", "DEMO-EMPTY", "Fixture"))
        # Deliberately not aligned with metadata row positions.
        self.content = [{"id": r["id"], "content_html": "<html><body><p>DEMO, không phải luật thật.</p></body></html>"}
                        for r in reversed(self.metadata)]
        self.content[0]["content_html"] = "<html><head><title>Not body text</title></head><body> </body></html>"
        self.relationships = [{"doc_id": "139264", "other_doc_id": "146696", "relationship": "DEMO"}]

    def cleanup_fixture(self):
        resolved = self.root.resolve()
        if resolved.parent != self.test_dir or not resolved.name.startswith(".tmp-tillegal-t1-"):
            raise ValueError("Refusing cleanup outside the generated test fixture directory")
        shutil.rmtree(resolved)

    @staticmethod
    def meta(doc_id, number, kind):
        row = dict.fromkeys(audit.METADATA_FIELDS)
        row.update(id=doc_id, title="Synthetic fixture", so_ky_hieu=number,
                   loai_van_ban=kind, ngay_ban_hanh="01/02/2021", tinh_trang_hieu_luc="UNKNOWN")
        return row

    def save(self):
        for name, data in (("metadata", self.metadata), ("content", self.content), ("relationships", self.relationships)):
            schema = pa.schema([(key, pa.string()) for key in audit.SCHEMAS[name]])
            pq.write_table(pa.Table.from_pylist(data, schema=schema), self.raw / f"{name}.parquet", row_group_size=2)

    def inspect(self):
        self.save()
        return audit.inspect_inputs(self.raw)

    def publish(self):
        manifest, validation, selection = self.inspect()
        targets = audit.output_targets(self.raw, self.root / "inspection", self.root / "selection.json")
        audit.write_artifacts(manifest, validation, selection, targets)
        return targets

    def test_join_by_id_and_explicit_vietnamese_selection(self):
        manifest, report, selection = self.inspect()
        self.assertEqual(report["join"]["matched_distinct_ids"], 5)
        self.assertEqual(selection["status"], "READY_FOR_AUDIT")
        self.assertEqual([r["id"] for r in selection["records"]], [r[0] for r in audit.PILOT])
        self.assertEqual(len([r for r in report["metadata"]["pilot_number_candidates"] if r["so_ky_hieu"] == "45/2019/QH14"]), 2)
        for row in selection["records"]:
            self.assertEqual(row["content_sample"]["id"], row["id"])
            self.assertEqual(row["decision"], "QUARANTINE")
            self.assertIsNone(row["reviewer"])
            self.assertFalse(row["approved_for_retrieval"])
        self.assertIsNone(manifest["dataset_revision"])
        self.assertEqual(manifest["revision_status"], "UNVERIFIED")

    def test_empty_body_is_detected_despite_nonempty_html(self):
        _, report, _ = self.inspect()
        empty = next(r for r in report["content"]["samples"] if r["id"] == "135139")
        self.assertTrue(empty["body_text_empty"])
        self.assertFalse(empty["html_blank"])
        self.assertEqual(report["content"]["html_quality_population"], "NOT_SCANNED")
        self.assertLessEqual(len(report["content"]["samples"]), 5)
        self.assertNotIn("content_html", empty)

    def test_missing_content_blocks_pilot_without_losing_metadata(self):
        self.content = [r for r in self.content if r["id"] != "139264"]
        _, report, selection = self.inspect()
        self.assertEqual(report["join"]["metadata_without_content"], 1)
        self.assertEqual(report["metadata"]["rows"], 5)
        self.assertEqual(selection["records"][0]["selection_status"], "REJECTED")
        self.assertEqual(selection["status"], "BLOCKED")

    def test_duplicate_ids_block_selection_and_cardinality(self):
        self.metadata.append(deepcopy(self.metadata[0]))
        self.content.append(next(deepcopy(r) for r in self.content if r["id"] == "139264"))
        _, report, selection = self.inspect()
        self.assertEqual(report["metadata"]["duplicate_excess_rows"], 1)
        self.assertEqual(report["content"]["duplicate_excess_rows"], 1)
        self.assertEqual(report["join"]["cardinality"], "NOT_ONE_TO_ONE")
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(selection["records"][0]["selection_status"], "REJECTED")

    def test_expected_id_with_wrong_type_is_not_accepted(self):
        self.metadata[0]["loai_van_ban"] = "Bản dịch văn bản"
        _, _, selection = self.inspect()
        self.assertIn("EXPECTED_NUMBER_OR_DOCUMENT_TYPE_MISMATCH", selection["records"][0]["errors"])

    def test_content_orphan_and_blank_ids_are_reported(self):
        self.content.extend([{"id": "orphan", "content_html": "x"}, {"id": " ", "content_html": None}])
        self.metadata.append(self.meta(None, "MISSING-ID", "Fixture"))
        _, report, _ = self.inspect()
        self.assertEqual(report["join"]["content_without_metadata"], 1)
        self.assertEqual(report["metadata"]["missing_id_rows"], 1)
        self.assertEqual(report["content"]["missing_id_rows"], 1)
        self.assertEqual(report["status"], "FAIL")

    def test_relationship_diagnostics_do_not_infer_legal_effect(self):
        self.relationships += [
            {"doc_id": "139264", "other_doc_id": "external", "relationship": "Văn bản được sửa đổi"},
            {"doc_id": "139264", "other_doc_id": "external", "relationship": "Văn bản được sửa đổi"},
            {"doc_id": "139264", "other_doc_id": "139264", "relationship": "DEMO"},
            {"doc_id": "absent", "other_doc_id": "139264", "relationship": None},
        ]
        _, report, _ = self.inspect()
        rel = report["relationships"]
        self.assertEqual(rel["target_missing_rows"], 2)
        self.assertEqual(rel["target_missing_distinct"], 1)
        self.assertEqual(rel["source_missing_rows"], 1)
        self.assertEqual(rel["duplicate_triples"], 1)
        self.assertEqual(rel["self_edges"], 1)
        self.assertEqual(rel["missing_or_blank_fields"], {"relationship": 1})
        self.assertIn("UNVERIFIED", rel["legal_semantics"])

    def test_invalid_date_and_null_fields_are_not_filled(self):
        self.metadata[0]["ngay_ban_hanh"] = "31/02/2021"
        self.metadata[1]["title"] = " "
        _, report, selection = self.inspect()
        self.assertEqual(report["metadata"]["date_validation"]["ngay_ban_hanh"]["invalid"], 1)
        self.assertEqual(report["metadata"]["missing_values"]["title"]["blank"], 1)
        self.assertEqual(report["metadata"]["missing_values"]["ngay_het_hieu_luc"]["null"], 5)
        self.assertEqual(selection["records"][0]["temporal_status"], "UNKNOWN")

    def test_wrong_schema_and_missing_file_fail_explicitly(self):
        self.save()
        pq.write_table(pa.table({"id": [1], "content_html": ["x"]}), self.raw / "content.parquet")
        with self.assertRaisesRegex(ValueError, "Unexpected schema"):
            audit.inspect_inputs(self.raw)
        (self.raw / "content.parquet").unlink()
        with self.assertRaises(FileNotFoundError):
            audit.inspect_inputs(self.raw)

    def test_repeatability_and_raw_preservation(self):
        self.save()
        before = {p.name: audit.sha256_file(p) for p in self.raw.glob("*.parquet")}
        first = audit.inspect_inputs(self.raw)
        second = audit.inspect_inputs(self.raw)
        self.assertEqual(first[1:], second[1:])
        a, b = deepcopy(first[0]), deepcopy(second[0])
        a.pop("created_at_utc"); b.pop("created_at_utc")
        self.assertEqual(a, b)
        self.assertEqual(before, {p.name: audit.sha256_file(p) for p in self.raw.glob("*.parquet")})

    def test_input_change_during_inspection_aborts(self):
        self.save()
        original = audit.sha256_file
        counts = {}
        def changing_hash(path):
            counts[path.name] = counts.get(path.name, 0) + 1
            if path.name == "metadata.parquet" and counts[path.name] == 2:
                return "0" * 64
            return original(path)
        with patch.object(audit, "sha256_file", side_effect=changing_hash):
            with self.assertRaisesRegex(ValueError, "Input changed"):
                audit.inspect_inputs(self.raw)

    def test_verify_detects_changed_raw_and_artifact(self):
        targets = self.publish()
        self.assertEqual(audit.verify_snapshot(targets[0])["status"], "PASS")
        with (self.raw / "content.parquet").open("ab") as stream:
            stream.write(b"changed fixture")
        targets[2].write_text("{}", encoding="utf-8")
        result = audit.verify_snapshot(targets[0])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(len(result["failures"]), 2)
        self.assertEqual({r["reason"] for r in result["failures"]}, {"HASH_MISMATCH"})

    def test_existing_outputs_and_raw_destination_are_rejected(self):
        targets = self.publish()
        before = targets[0].read_bytes()
        with self.assertRaises(FileExistsError):
            audit.output_targets(self.raw, targets[0].parent, targets[2])
        self.assertEqual(targets[0].read_bytes(), before)
        with self.assertRaisesRegex(ValueError, "outside"):
            audit.output_targets(self.raw, self.raw / "new", self.root / "new-selection.json")
        with self.assertRaisesRegex(ValueError, "distinct"):
            audit.output_targets(self.raw, self.root / "other", self.root / "other" / "validation.json")


if __name__ == "__main__":
    unittest.main()
