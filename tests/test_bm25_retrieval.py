"""T4 technical correctness tests; synthetic cases and pilot are not legal gold."""
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest

from ai_core import bm25_retrieval as bm25
from ai_core.data_contracts import canonical_json, ContractError, file_hash
from ai_core.legal_parser import parse_document
from test_legal_parser import document

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed/labor-pilot-3-t3-fix/manifest.json"
SNAPSHOT = "8040db1bfeddb99b93e8937a1c35e634de198a703286318d459d80e90987bfb7"


def synthetic_index(texts, config=None, fmt="text", max_chars=1800):
    documents = [document(text, fmt=fmt, record=str(i)) for i, text in enumerate(texts)]
    results = [parse_document(d, max_chars=max_chars) for d in documents]
    chunks = sorted([c for r in results for c in r['chunks']], key=lambda c: c['chunk_id'])
    payload = {"schema_version": "1", "algorithm_version": bm25.ALGORITHM_VERSION,
               "tokenizer": deepcopy(bm25.TOKENIZER), "config": config or deepcopy(bm25.DEFAULT_CONFIG),
               "source": {"processed_snapshot_id": "synthetic-not-law", "processed_manifest_sha256": "a" * 64},
               "usage_policy": "EXPERIMENTAL_ONLY", "corpus_snapshot_id": None,
               "approved_for_legal_verification": False,
               "documents": [{k: v for k, v in d.to_dict().items() if k != 'content'} for d in documents],
               "nodes": {r['document_version_id']: r['nodes'] for r in results},
               "chunks": chunks, "statistics": bm25.term_statistics(chunks)}
    return bm25.BM25Index(payload)


class TokenizerAndScoreTests(unittest.TestCase):
    def test_vietnamese_nfc_case_accents_negation_numbers_and_markers(self):
        text = 'KHÔNG được 45/2019/QH14; a1), lao_động [IMAGE] [EMPTY_TABLE] 😀'
        expected = ['không', 'được', '45', '2019', 'qh14', 'a1', 'lao', 'động']
        self.assertEqual(bm25.tokenize(text), expected)
        self.assertEqual(bm25.tokenize(unicodedata.normalize('NFD', text)), expected)
        self.assertNotEqual(bm25.tokenize('luật'), bm25.tokenize('luat'))

    def test_hand_calculated_score_and_no_zero_score_padding(self):
        index = synthetic_index(['mèo mèo chó', 'chó', 'chim'])
        hit = index.search('mèo', 5)['results']
        self.assertEqual(len(hit), 1)
        # N=3, df=1, tf=2, dl=3, avgdl=5/3; formula independent of index stats.
        expected = math.log(1 + 2.5 / 1.5) * 2 * 2.2 / (2 + 1.2 * (0.25 + 0.75 * 3 / (5 / 3)))
        self.assertAlmostEqual(hit[0]['bm25_score'], expected, places=12)
        self.assertEqual(hit[0]['rank'], 1)

    def test_length_normalization_and_tf_saturation(self):
        index = synthetic_index(['mèo', 'mèo chó chó chó', 'mèo mèo mèo mèo'])
        scores = {r['chunk']['text']: r['bm25_score'] for r in index.search('mèo')['results']}
        self.assertGreater(scores['mèo'], scores['mèo chó chó chó'])
        index = synthetic_index(['mèo', 'mèo mèo mèo mèo'], config={'k1': 1.2, 'b': 0})
        scores = {r['chunk']['text']: r['bm25_score'] for r in index.search('mèo')['results']}
        self.assertGreater(scores['mèo mèo mèo mèo'], scores['mèo'])
        self.assertLess(scores['mèo mèo mèo mèo'], 4 * scores['mèo'])

    def test_query_tf_binary_order_invariant_and_tie_by_id(self):
        index = synthetic_index(['mèo chó', 'mèo chó', 'chim'])
        a = index.search('mèo chó')['results']
        self.assertEqual(a, index.search('chó mèo mèo')['results'])
        self.assertEqual([r['chunk']['chunk_id'] for r in a], sorted(r['chunk']['chunk_id'] for r in a))
        self.assertEqual(a[0]['bm25_score'], a[1]['bm25_score'])

    def test_empty_oov_partial_and_k(self):
        index = synthetic_index(['mèo chó', 'chó'])
        for query in ['', '  ', '!!!😀', '[IMAGE]']:
            self.assertEqual(index.search(query)['status'], 'EMPTY_QUERY')
        self.assertEqual(index.search('vắng')['status'], 'NO_MATCH')
        result = index.search('chó vắng', 1)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['unmatched_terms'], ['vắng'])
        self.assertEqual(result['results'][0]['matched_terms'], ['chó'])

    def test_marker_only_chunk_retained_but_not_searchable_metadata_not_scored(self):
        index = synthetic_index(['<p>mèo</p><p><img src="x"/></p>'], fmt='html')
        self.assertEqual(len(index.to_dict()['chunks']), 2)
        self.assertIn(0, index.to_dict()['statistics']['lengths'])
        self.assertEqual(index.search('IMAGE')['status'], 'NO_MATCH')
        self.assertEqual(index.search('DEMO')['status'], 'NO_MATCH')  # document_number metadata
        self.assertEqual(len(index.search('mèo')['results']), 1)

    def test_bad_queries_config_and_empty_corpus_rejected(self):
        index = synthetic_index(['mèo'])
        for k in [0, -1, 101, True, 1.5, '3']:
            with self.subTest(k=k), self.assertRaises(ContractError):
                index.search('mèo', k)
        for query in [None, 5, 'a' * 10001]:
            with self.assertRaises(ContractError):
                index.search(query)
        for config in [{'k1': 0, 'b': .75}, {'k1': True, 'b': 0}, {'k1': 1.2, 'b': 2},
                       {'k1': float('nan'), 'b': .75}, {'k1': 1.2, 'b': float('inf')}, {}]:
            with self.assertRaises(ContractError):
                bm25.validate_config(config)
        with self.assertRaises(ContractError):
            bm25.term_statistics([])
        with self.assertRaises(ContractError):
            synthetic_index(['[IMAGE]'])


class MetadataAndIndexTests(unittest.TestCase):
    def test_all_attachment_states_are_candidates_never_verified(self):
        index = synthetic_index(['<p>Điều 1. Chung</p><p>Đoạn heuristic</p><p>1. Khoản</p><p>a) Điểm</p><p>Tiếp nối cần review</p>'], fmt='html')
        for query, attachment, address in [('Chung', 'STRUCTURAL', 'RULE_BASED_UNVERIFIED'),
                                          ('heuristic', 'HEURISTIC', 'HEURISTIC_CANDIDATE'),
                                          ('review', 'REVIEW_REQUIRED', 'REVIEW_REQUIRED')]:
            hit = index.search(query)['results'][0]
            self.assertEqual(hit['chunk']['attachment_status'], attachment)
            self.assertEqual(hit['address_status'], address)
            self.assertFalse(hit['exact_citation_verified'])
            self.assertEqual(hit['legal_evidence_status'], 'NOT_EVALUATED')
            self.assertEqual(hit['chunk']['legal_approval'], 'QUARANTINE')

    def test_table_image_quote_heading_fragment_cautions_and_refs(self):
        raw = '<p>Điều 1. Demo</p><p>1. Nội dung</p><table><tr><td>Bảng lương<img src="x"/></td></tr></table><p>“Điều 2. Trích dẫn.”</p>'
        index = synthetic_index([raw], fmt='html')
        hit = index.search('Bảng')['results'][0]
        self.assertIn('TABLE_REQUIRES_RAW_LAYOUT', hit['cautions'])
        self.assertIn('IMAGE_NOT_INTERPRETED', hit['cautions'])
        self.assertTrue(hit['context_refs']['ancestor_heading_chunk_ids'])
        quote = index.search('Trích')['results'][0]
        self.assertIn('QUOTED_ADDRESS_IS_OUTER_CONTEXT', quote['cautions'])
        heading = index.search('Demo')['results'][0]
        self.assertIn('HEADING_BLOCK_MAY_REQUIRE_BODY', heading['cautions'])
        long = synthetic_index(['<p>' + 'Ngữ cảnh có điều kiện. ' * 12 + '</p>'], fmt='html', max_chars=64)
        hit = long.search('điều')['results'][0]
        self.assertIn('SPLIT_BLOCK_REQUIRES_CONTEXT', hit['cautions'])
        self.assertGreater(len(hit['context_refs']['block_chunk_ids']), 1)
        chunks = {c['chunk_id']: c for c in long.to_dict()['chunks']}
        offsets = [chunks[cid]['text_start'] for cid in hit['context_refs']['block_chunk_ids']]
        self.assertEqual(offsets, sorted(offsets))
        self.assertFalse(hit['context_expanded'])

    def test_verbatim_chunk_metadata_and_defensive_copies(self):
        index = synthetic_index(['mèo chó'])
        before = index.to_dict()
        hit = index.search('mèo')['results'][0]
        self.assertEqual(hit['chunk'], before['chunks'][0])
        self.assertEqual(hit['document']['raw_ref'], before['documents'][0]['raw_ref'])
        self.assertIsNone(hit['document']['source_url'])
        hit['chunk']['text'] = 'corrupt'
        hit['document']['raw_ref']['uri'] = 'corrupt'
        before['statistics']['postings'].clear()
        self.assertEqual(index.search('mèo')['results'][0]['chunk']['text'], 'mèo chó')

    def test_statistics_status_and_locator_tamper_rejected(self):
        index = synthetic_index(['mèo chó'])
        mutations = [lambda p: p['statistics']['lengths'].__setitem__(0, 999),
                     lambda p: p['chunks'][0].__setitem__('attachment_status', 'VERIFIED'),
                     lambda p: p['chunks'][0].__setitem__('legal_approval', 'APPROVED'),
                     lambda p: p['chunks'][0]['source_locator'].__setitem__('end_exclusive', False),
                     lambda p: p.__setitem__('corpus_snapshot_id', 'official'),
                     lambda p: p.__setitem__('tokenizer', {})]
        for mutate in mutations:
            bad = index.to_dict()
            mutate(bad)
            with self.assertRaises(ContractError):
                bm25.BM25Index(bad)


@unittest.skipUnless(PROCESSED.exists(), 'local pinned pilot unavailable')
class PilotIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = bm25.build_index(PROCESSED, SNAPSHOT)

    def test_pinned_snapshot_full_inventory_and_exact_chunk_preservation(self):
        payload = self.index.to_dict()
        original = [json.loads(line) for line in (PROCESSED.parent / 'chunks.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(payload['chunks'], sorted(original, key=lambda c: c['chunk_id']))
        self.assertEqual(len(payload['chunks']), 3085)
        self.assertEqual(payload['source']['processed_snapshot_id'], SNAPSHOT)
        self.assertEqual(len(payload['documents']), 3)
        self.assertIsNone(payload['corpus_snapshot_id'])

    def test_pinned_unresolved_subpoints_and_suspect_source_flags_survive(self):
        chunks = self.index.to_dict()['chunks']
        suspect = next(c for c in chunks if 'SOURCE_TEXT_POSSIBLY_INCOMPLETE' in c['issues'])
        self.assertIn('SOURCE_TEXT_POSSIBLY_INCOMPLETE', self.index._context_and_cautions(suspect)['cautions'])
        subpoints = [c for c in chunks if 'SUBPOINT_NOT_RESOLVED' in c['issues']]
        self.assertEqual(len(subpoints), 26)
        self.assertTrue(all(self.index._context_and_cautions(c)['address_status'] == 'REVIEW_REQUIRED' for c in subpoints))
        self.assertEqual(sum(c['attachment_status'] == 'REVIEW_REQUIRED' for c in chunks), 112)

    def test_repeat_build_byte_identical_and_results_stable(self):
        rebuilt = bm25.build_index(PROCESSED, SNAPSHOT)
        self.assertEqual(canonical_json(self.index.to_dict()), canonical_json(rebuilt.to_dict()))
        self.assertEqual(self.index.index_id, rebuilt.index_id)
        for query in ['tiền lương làm thêm giờ', 'hợp đồng lao động', 'nghỉ hằng năm']:
            self.assertEqual(self.index.search(query)['results'], rebuilt.search(query)['results'])

    def test_export_load_cli_utf8_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='.tmp-tillegal-t4-', dir=ROOT) as tmp:
            out = Path(tmp) / 'index'
            manifest = bm25.export_index(self.index, out, PROCESSED)
            second = Path(tmp) / 'second'
            bm25.export_index(self.index, second, PROCESSED)
            for name in ['index.json', 'manifest.json']:
                self.assertEqual((out / name).read_bytes(), (second / name).read_bytes())
            loaded = bm25.load_index(out / 'manifest.json')
            self.assertEqual(loaded.index_id, self.index.index_id)
            self.assertEqual(loaded.search('tiền lương')['results'], self.index.search('tiền lương')['results'])
            before = file_hash(out / 'index.json')
            with self.assertRaises(ContractError):
                bm25.export_index(self.index, out, PROCESSED)
            self.assertEqual(file_hash(out / 'index.json'), before)
            env = {**os.environ, 'PYTHONIOENCODING': 'cp1252'}
            run = subprocess.run([sys.executable, '-B', '-m', 'ai_core.bm25_retrieval', 'query', '--manifest',
                                  str(out / 'manifest.json'), '--query', 'tiền lương', '--top-k', '2'],
                                 cwd=ROOT, capture_output=True, env=env)
            self.assertEqual(run.returncode, 0, run.stderr.decode('utf-8'))
            response = json.loads(run.stdout.decode('utf-8'))
            self.assertEqual(response['query'], 'tiền lương')
            self.assertEqual(len(response['results']), 2)
            self.assertEqual(response['index_id'], manifest['index_id'])
            bad = subprocess.run([sys.executable, '-B', '-m', 'ai_core.bm25_retrieval', 'query', '--manifest',
                                  str(out / 'manifest.json'), '--query', 'x', '--top-k', '0'], cwd=ROOT, capture_output=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(json.loads(bad.stderr)['status'], 'ERROR')

    def test_corrupt_saved_index_and_manifest_rejected(self):
        with tempfile.TemporaryDirectory(prefix='.tmp-tillegal-t4-', dir=ROOT) as tmp:
            out = Path(tmp) / 'index'
            manifest = bm25.export_index(self.index, out, PROCESSED)
            bad = deepcopy(manifest)
            bad['index_id'] = 'wrong'
            (out / 'manifest.json').write_bytes(canonical_json(bad))
            with self.assertRaises(ContractError):
                bm25.load_index(out / 'manifest.json')
            bad = deepcopy(manifest)
            bad['code_hashes']['ai_core/bm25_retrieval.py'] = 'a' * 64
            (out / 'manifest.json').write_bytes(canonical_json(bad))
            with self.assertRaises(ContractError):
                bm25.load_index(out / 'manifest.json')
            (out / 'manifest.json').write_bytes(canonical_json(manifest))
            with (out / 'index.json').open('ab') as stream:
                stream.write(b' ')
            with self.assertRaises(ContractError):
                bm25.load_index(out / 'manifest.json')

    def test_wrong_snapshot_old_schema_tampered_source_fail_before_export(self):
        with self.assertRaises(ContractError):
            bm25.build_index(PROCESSED, 'wrong-snapshot')
        with self.assertRaises(ContractError):
            bm25.build_index(ROOT / 'data/processed/labor-pilot-3/manifest.json', SNAPSHOT)
        with tempfile.TemporaryDirectory(prefix='.tmp-tillegal-t4-', dir=ROOT) as tmp:
            copied = Path(tmp) / 'processed'
            shutil.copytree(PROCESSED.parent, copied)
            with (copied / 'chunks.jsonl').open('ab') as stream:
                stream.write(b' ')
            with self.assertRaises(ContractError):
                bm25.build_index(copied / 'manifest.json', SNAPSHOT)

    def test_consistently_rehashed_wrong_ancestry_still_rejected_by_parser_validator(self):
        with tempfile.TemporaryDirectory(prefix='.tmp-tillegal-t4-', dir=ROOT) as tmp:
            copied = Path(tmp) / 'processed'
            shutil.copytree(PROCESSED.parent, copied)
            chunks_path = copied / 'chunks.jsonl'
            chunks = [json.loads(line) for line in chunks_path.read_text(encoding='utf-8').splitlines()]
            chunks[0]['article'] = '999'
            chunks_path.write_bytes(b''.join(canonical_json(c) + b'\n' for c in chunks))
            manifest_path = copied / 'manifest.json'
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            artifact = next(a for a in manifest['artifacts'] if a['path'] == 'chunks.jsonl')
            artifact.update(sha256=file_hash(chunks_path), bytes=chunks_path.stat().st_size)
            manifest['processed_snapshot_id'] = bm25.digest({a['path']: a['sha256'] for a in manifest['artifacts']})
            manifest_path.write_bytes(canonical_json(manifest))
            with self.assertRaisesRegex(ContractError, 'ancestry'):
                bm25.build_index(manifest_path, manifest['processed_snapshot_id'])


if __name__ == '__main__':
    unittest.main()
