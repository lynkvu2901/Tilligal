"""T6.1 assembly tests, not claim support tests or a retrieval benchmark."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import unittest

from ai_core.bm25_retrieval import BM25Index, digest, load_index
from ai_core.data_contracts import ContractError, content_hash
from ai_core.evidence_builder import EvidenceBudget, EvidenceBuilder
from test_bm25_retrieval import synthetic_index

ROOT = Path(__file__).resolve().parents[1]
DEMO = 'Điều 1. Chế độ minh họa\n1. Người giữ mèo được nghỉ.\n2. Trừ trường hợp khẩn cấp.\nĐiều 2. Khác\n1. Người giữ chim đi học.'


class EvidenceBuilderTests(unittest.TestCase):
    def setUp(self):
        self.index = synthetic_index([DEMO])
        self.builder = EvidenceBuilder(self.index)

    def test_body_expansion_keeps_exception_and_excludes_other_article(self):
        bundle = self.builder.build(self.index.search('mèo', 1), request_id='one')
        quotes = [e['quote'] for e in bundle['evidence']]
        self.assertEqual(len(quotes), 3)
        self.assertIn('2. Trừ trường hợp khẩn cấp.', quotes)
        self.assertFalse(any('chim' in q for q in quotes))
        self.assertEqual(bundle['status'], 'ASSEMBLED')
        self.assertEqual(bundle['groups'][0]['context_sufficiency'], 'NOT_EVALUATED')

    def test_heading_hit_has_body_and_heading_warning(self):
        bundle = self.builder.build(self.index.search('minh họa', 1), request_id='heading')
        self.assertEqual(len(bundle['evidence']), 3)
        heading = next(e for e in bundle['evidence'] if e['is_heading'])
        self.assertIn('HEADING_BLOCK_MAY_REQUIRE_BODY', heading['warnings'])

    def test_fragment_context_preserves_exact_quotes_and_unicode_offsets(self):
        index = synthetic_index(['Điều 1. Demo\n1. ' + 'mèo 😀 & chó. ' * 35], max_chars=100)
        bundle = EvidenceBuilder(index).build(index.search('mèo', 1), request_id='fragment')
        self.assertGreater(len(bundle['evidence']), 3)
        originals = {c['chunk_id']: c for c in index.to_dict()['chunks']}
        for evidence in bundle['evidence']:
            chunk = originals[evidence['chunk_id']]
            self.assertEqual(evidence['quote'], chunk['text'])
            self.assertEqual(evidence['quote_sha256'], content_hash(evidence['quote']))
            self.assertEqual(evidence['normalized_locator']['end'] - evidence['normalized_locator']['start'], len(evidence['quote']))
            self.assertEqual(evidence['source_locator'], chunk['source_locator'])
            self.assertEqual(evidence['source_locator_extent'], 'WHOLE_BLOCK')
            self.assertEqual(evidence['chunk'], chunk)
        self.assertIn('SAME_BLOCK', [m['role'] for m in bundle['groups'][0]['members']])

    def test_budget_records_missing_exception_without_cutting_quotes(self):
        bundle = EvidenceBuilder(self.index, EvidenceBudget(max_chunks=1)).build(self.index.search('mèo', 1), request_id='limited')
        self.assertEqual(bundle['status'], 'PARTIAL')
        self.assertEqual(bundle['groups'][0]['omitted_chunk_ids'].__len__(), 2)
        self.assertEqual(bundle['evidence'][0]['quote'], '1. Người giữ mèo được nghỉ.')
        empty = EvidenceBuilder(self.index, EvidenceBudget(max_quote_chars=1)).build(self.index.search('mèo', 1), request_id='tiny')
        self.assertEqual(empty['status'], 'EMPTY')
        self.assertFalse(empty['groups'][0]['seed_included'])
        self.assertTrue(empty['groups'][0]['omitted_chunk_ids'])

    def test_seeds_before_context_and_duplicate_context_only_once(self):
        response = self.index.search('mèo chim', 2)
        bundle = EvidenceBuilder(self.index, EvidenceBudget(max_chunks=2)).build(response, request_id='seeds')
        self.assertTrue(all(g['seed_included'] for g in bundle['groups']))
        self.assertEqual({e['chunk_id'] for e in bundle['evidence']}, {h['chunk']['chunk_id'] for h in response['results']})
        full = self.builder.build(self.index.search('mèo khẩn cấp', 2), request_id='shared')
        self.assertEqual(len(full['evidence']), 3)
        self.assertEqual(len({e['evidence_id'] for e in full['evidence']}), 3)

    def test_empty_oov_not_legal_insufficiency_verdict(self):
        for query in ('', 'zzzznotfound'):
            result = self.builder.build(self.index.search(query), request_id='empty')
            self.assertEqual(result['status'], 'EMPTY')
            self.assertEqual(result['evidence'], [])
            self.assertEqual(result['trace']['llm_calls'], 0)
            self.assertIn('NO_LEGAL_OR_SEMANTIC_VERIFICATION', result['limitations'])

    def test_heuristic_and_review_required_never_promoted(self):
        index = synthetic_index(['Điều 1. Demo\n1. Nội dung.\nĐoạn tiếp nối mèo.\na1) chim chưa resolve.'])
        builder = EvidenceBuilder(index)
        heuristic = builder.build(index.search('mèo', 1), request_id='heuristic')
        seed = heuristic['evidence'][0]
        self.assertEqual(seed['attachment_status'], 'HEURISTIC')
        self.assertEqual(seed['address_status'], 'HEURISTIC_CANDIDATE')
        review = builder.build(index.search('resolve', 1), request_id='review')
        self.assertEqual(review['evidence'][0]['attachment_status'], 'REVIEW_REQUIRED')
        self.assertIn('SUBPOINT_NOT_RESOLVED', review['evidence'][0]['warnings'])
        self.assertFalse(review['groups'][0]['article_expansion_allowed'])
        self.assertNotIn('ARTICLE_CONTEXT_CANDIDATE', [m['role'] for m in review['groups'][0]['members']])
        for result in (heuristic, review):
            for e in result['evidence']:
                self.assertFalse(e['exact_citation_verified'])
                self.assertEqual(e['document']['provenance_status'], 'UNVERIFIED')
                self.assertEqual(e['legal_evidence_status'], 'NOT_EVALUATED')

    def test_table_image_and_document_warnings_survive(self):
        index = synthetic_index(['<p>Điều 1. Demo</p><p>1. mèo</p><table><tr><td>hàng</td></tr></table><p><img src="x"/></p>'], fmt='html')
        payload = index.to_dict()
        payload['documents'][0]['issues'].append('SYNTHETIC_SOURCE_WARNING')
        index = BM25Index(payload)
        result = EvidenceBuilder(index).build(index.search('mèo', 1), request_id='table')
        self.assertTrue(any('TABLE_REQUIRES_RAW_LAYOUT' in e['warnings'] for e in result['evidence']))
        self.assertTrue(any('IMAGE_NOT_INTERPRETED' in e['warnings'] for e in result['evidence']))
        self.assertTrue(all('SYNTHETIC_SOURCE_WARNING' in e['warnings'] for e in result['evidence']))

    def test_same_article_label_in_different_documents_never_merges(self):
        index = synthetic_index([DEMO, 'Điều 1. Văn bản khác\n1. hươu.'])
        bundle = EvidenceBuilder(index).build(index.search('mèo', 1), request_id='versions')
        self.assertEqual(len({e['document_version_id'] for e in bundle['evidence']}), 1)
        self.assertFalse(any('hươu' in e['quote'] for e in bundle['evidence']))

    def test_tampered_origin_quotes_hashes_locator_metadata_and_status_rejected(self):
        original = self.index.search('mèo', 1)
        changes = [lambda r: r.update(index_id='foreign'),
                   lambda r: r['source'].update(processed_snapshot_id='foreign'),
                   lambda r: r.update(status='NO_MATCH'),
                   lambda r: r['results'][0]['chunk'].update(text='invented'),
                   lambda r: r['results'][0]['chunk'].update(text_sha256='0' * 64),
                   lambda r: r['results'][0]['chunk']['source_locator'].update(offset_unit='byte'),
                   lambda r: r['results'][0]['document'].update(provenance_status='VERIFIED'),
                   lambda r: r['results'][0].update(exact_citation_verified=True),
                   lambda r: r['results'][0].update(bm25_score=float('nan')),
                   lambda r: r['results'][0].update(rank=2),
                   lambda r: r['results'].append(deepcopy(r['results'][0]))]
        for change in changes:
            response = deepcopy(original)
            change(response)
            with self.subTest(change=changes.index(change)), self.assertRaises(ContractError):
                self.builder.build(response, request_id='bad')

    def test_missing_or_foreign_chunk_rejected(self):
        response = self.index.search('mèo', 1)
        for chunk in ({}, {'chunk_id': 'missing'}):
            response['results'][0]['chunk'] = chunk
            with self.assertRaises(ContractError):
                self.builder.build(response, request_id='missing')

    def test_determinism_json_and_input_immutability(self):
        response = self.index.search('mèo', 1)
        before = deepcopy(response)
        first = self.builder.build(response, request_id='stable')
        response['latency_ms'] = 999
        second = self.builder.build(response, request_id='stable')
        self.assertEqual(first, second)
        self.assertEqual(json.loads(json.dumps(first, ensure_ascii=False)), first)
        response['latency_ms'] = before['latency_ms']
        self.assertEqual(response, before)
        unsigned = deepcopy(first)
        bid = unsigned.pop('bundle_id')
        self.assertEqual(bid, 'bundle:' + digest(unsigned))

    def test_requests_and_caller_mutations_are_isolated(self):
        def build(query):
            return self.builder.build(self.index.search(query, 1), request_id=query)
        with ThreadPoolExecutor(max_workers=2) as executor:
            cat, bird = list(executor.map(build, ['mèo', 'chim']))
        self.assertFalse(any('mèo' in e['quote'] for e in bird['evidence']))
        cat['evidence'][0]['document']['title'] = 'MUTATED'
        cat['evidence'][0]['chunk']['text'] = 'MUTATED'
        fresh = build('mèo')
        self.assertNotEqual(fresh['evidence'][0]['document']['title'], 'MUTATED')
        self.assertNotEqual(fresh['evidence'][0]['chunk']['text'], 'MUTATED')

    def test_bad_budgets_and_request_ids(self):
        for value in (0, -1, True, 1.5, '2'):
            with self.assertRaises(ContractError):
                EvidenceBudget(max_chunks=value)
            with self.assertRaises(ContractError):
                EvidenceBudget(max_quote_chars=value)
        for request in ('', ' ', None):
            with self.assertRaises(ContractError):
                self.builder.build(self.index.search('mèo'), request_id=request)


class PinnedEvidenceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = load_index(ROOT / 'data/indexes/labor-pilot-3-t4-bm25/manifest.json')
        cls.builder = EvidenceBuilder(cls.index)

    def test_pilot_smoke_independent_of_d01_d08(self):
        # Technical smoke only; not a relevance label, model tuning, or benchmark.
        response = self.index.search('đối thoại định kỳ', 3)
        bundle = self.builder.build(response, request_id='t61-local-smoke')
        self.assertTrue(bundle['evidence'])
        self.assertEqual(bundle['source']['processed_snapshot_id'], '8040db1bfeddb99b93e8937a1c35e634de198a703286318d459d80e90987bfb7')
        self.assertEqual(bundle['source']['processed_schema_version'], '2')
        self.assertEqual(bundle['trace']['search_calls'], 0)
        self.assertIsNone(bundle['corpus_snapshot_id'])
        self.assertFalse(bundle['approved_for_legal_verification'])
        ids = {e['evidence_id'] for e in bundle['evidence']}
        for group in bundle['groups']:
            self.assertTrue(all(m['evidence_id'] in ids for m in group['members']))
        for e in bundle['evidence']:
            self.assertEqual(e['source_locator']['content_sha256'], e['document']['content_sha256'])
            article = [n['node_id'] for n in e['ancestry'] if n['kind'] == 'article']
            self.assertEqual(e['article_id'], article[-1] if article else None)

    def test_all_pilot_windows_respect_scope_version_form_boundaries(self):
        # Source inventory inspection, not a search over benchmark questions.
        for seed in self.index.to_dict()['chunks']:
            for cid, role in self.builder._candidates(seed).items():
                chunk = self.builder._chunks[cid]
                self.assertEqual(chunk['document_version_id'], seed['document_version_id'])
                self.assertEqual(chunk['scope'], seed['scope'])
                if role == 'ARTICLE_CONTEXT_CANDIDATE':
                    self.assertEqual(self.builder._window_key(chunk), self.builder._window_key(seed))
                    self.assertNotEqual(seed['scope'], 'quoted')
                    self.assertNotEqual(seed['attachment_status'], 'REVIEW_REQUIRED')

    def test_pinned_source_anomaly_preserved_without_reconstruction(self):
        seed = next(c for c in self.index.to_dict()['chunks'] if 'SOURCE_TEXT_POSSIBLY_INCOMPLETE' in c['issues'])
        evidence = self.builder._evidence(seed)
        self.assertIn('SOURCE_TEXT_POSSIBLY_INCOMPLETE', evidence['warnings'])
        self.assertEqual(evidence['quote'], seed['text'])
        self.assertEqual(evidence['quote_sha256'], seed['text_sha256'])


if __name__ == '__main__':
    unittest.main()
