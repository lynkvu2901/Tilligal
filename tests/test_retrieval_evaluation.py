"""T5 evaluation machinery. Reviewed identities below are SYNTHETIC fixtures."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai_core import retrieval_evaluation as ev
from ai_core.data_contracts import canonical_json, ContractError, file_hash
from test_bm25_retrieval import synthetic_index, ROOT, PROCESSED
from scripts.prepare_retrieval_review import prepare

INDEX_MANIFEST = ROOT / 'data/indexes/labor-pilot-3-t4-bm25/manifest.json'


def fixture():
    index = synthetic_index(['<p>Điều 1. Mèo</p><p>1. Mèo ngủ.</p><p>Đoạn tiếp mèo.</p><p>Điều 2. Chó</p><p>1. Chó thức.</p>'], fmt='html')
    corpus = ev.EvaluationCorpus(index)
    cases = []
    for qid, split, text in [('D1', 'dev', '1. Mèo ngủ.'), ('T1', 'test', '1. Chó thức.')]:
        chunk = next(c for c in corpus.chunks.values() if c['text'] == text)
        uid = corpus.article_for(chunk)
        cases.append({'question_id': qid, 'question': 'mèo' if split == 'dev' else 'chó', 'split': split,
                      'family_id': qid, 'as_of_date': None, 'answerability': 'UNKNOWN', 'proposed_units': [uid],
                      'relevant_units': [], 'evidence': [{'unit_id': uid, 'chunk_id': chunk['chunk_id'],
                          'start': 0, 'end': len(text), 'quote': text, 'text_sha256': chunk['text_sha256'],
                          'source_locator': chunk['source_locator']}],
                      'review': {'status': 'PENDING_HUMAN_REVIEW', 'reviewer_type': None, 'reviewer_id': None,
                                 'reviewed_at': None, 'source_read': False, 'unit_mapping_checked': False,
                                 'alternatives_checked': False, 'relevance_complete': False,
                                 'predictions_hidden': False, 'notes': ''}})
    dataset = {'schema_version': '1', 'artifact_kind': 'retrieval_annotation_dataset', 'dataset_id': 'SYNTHETIC_NOT_GOLD',
               'usage_policy': 'EXPERIMENTAL_ONLY', 'judgment_scope': 'LOCAL_SNAPSHOT_RELEVANCE_ONLY',
               'test_status': 'SYNTHETIC_NOT_HELD_OUT', 'policy': deepcopy(ev.POLICY), 'index_id': index.index_id,
               'processed_snapshot_id': corpus.payload['source']['processed_snapshot_id'], 'cases': cases}
    return index, corpus, dataset


def synthetic_accept(case):
    case['answerability'] = 'ANSWERABLE'
    case['relevant_units'] = list(case['proposed_units'])
    case['review'].update(status='ACCEPTED_HUMAN', reviewer_type='human', reviewer_id='SYNTHETIC_TEST_ID_NOT_REAL_REVIEW',
                          reviewed_at='2026-10-25T12:00:00+07:00', source_read=True, unit_mapping_checked=True,
                          alternatives_checked=True, relevance_complete=True, predictions_hidden=True,
                          notes='Synthetic control flow only; not a human label on real legal data.')


class MetricTests(unittest.TestCase):
    def test_hand_computed_recall_rr_and_cutoff(self):
        score = ev.score_units(['x', 'a', 'b'], ['a', 'b'], 2)
        self.assertEqual(score['recall'], .5)
        self.assertEqual(score['reciprocal_rank'], .5)
        self.assertEqual(ev.score_units(['x', 'a'], ['a'], 1)['reciprocal_rank'], 0)
        self.assertEqual(ev.score_units([], ['a'], 5)['recall'], 0)
        with self.assertRaises(ContractError):
            ev.score_units(['a', 'a'], ['a'], 5)
        with self.assertRaises(ContractError):
            ev.score_units(['a'], [], 5)

    def test_article_dedupe_preserves_uncertain_slot_and_heading_is_discovery(self):
        _, corpus, _ = fixture()
        texts = ['Đoạn tiếp mèo.', 'Điều 1. Mèo', '1. Mèo ngủ.', 'Điều 2. Chó']
        hits = [{'rank': i, 'chunk': next(c for c in corpus.chunks.values() if c['text'] == text)}
                for i, text in enumerate(texts, 1)]
        units = corpus.ranked_units(hits)
        self.assertEqual(len(units), 3)
        self.assertFalse(units[0]['eligible_article'])
        self.assertTrue(units[1]['eligible_article'])
        self.assertEqual(units[1]['first_chunk_rank'], 2)
        self.assertEqual(ev.score_units([u['unit_id'] for u in units], [units[1]['unit_id']], 5)['reciprocal_rank'], .5)

    def test_main_form_versions_and_quoted_are_distinct(self):
        raw = '<p>Điều 1. Chính</p><p>1. Chính</p><p>“Điều 1. Trích.”</p><p>Phụ lục I</p><p>Mẫu số 01/PLI</p><p>Điều 1. Mẫu</p>'
        index = synthetic_index([raw, '<p>Điều 1. Văn bản khác</p>'], fmt='html')
        corpus = ev.EvaluationCorpus(index)
        texts = ['Điều 1. Chính', '“Điều 1. Trích.”', 'Điều 1. Mẫu', 'Điều 1. Văn bản khác']
        hits = [{'rank': i, 'chunk': next(c for c in corpus.chunks.values() if c['text'] == text)}
                for i, text in enumerate(texts, 1)]
        units = corpus.ranked_units(hits)
        self.assertEqual(len({u['unit_id'] for u in units}), 4)
        self.assertFalse(units[1]['eligible_article'])
        self.assertEqual([u['scope'] for u in units], ['main', 'quoted', 'form', 'main'])

    def test_review_required_and_missing_source_never_promoted_by_metric(self):
        index = synthetic_index(['<p>Điều 1. Demo</p><p>1. Khoản</p><p>a) Điểm</p><p>a1) Tiết</p>'], fmt='html')
        corpus = ev.EvaluationCorpus(index)
        c = next(c for c in corpus.chunks.values() if c['text'].startswith('a1)'))
        self.assertFalse(corpus.ranked_units([{'rank': 1, 'chunk': c}])[0]['eligible_article'])
        bad = deepcopy(c)
        bad['attachment_status'] = 'STRUCTURAL'
        with self.assertRaises(ContractError):
            corpus.ranked_units([{'rank': 1, 'chunk': bad}])


class AnnotationGateTests(unittest.TestCase):
    def test_pending_labels_never_call_search(self):
        index, corpus, dataset = fixture()
        with patch.object(index, 'search', side_effect=AssertionError('must not retrieve')):
            state = ev.readiness(dataset, corpus, 'dev')
        self.assertEqual(state['status'], 'NEEDS_HUMAN_REVIEW')
        self.assertIsNone(state['metrics'])

    def test_all_required_human_attestations_and_quotes(self):
        _, corpus, dataset = fixture()
        synthetic_accept(dataset['cases'][0])
        self.assertEqual(ev.readiness(dataset, corpus, 'dev')['status'], 'READY')
        for flag in ['source_read', 'unit_mapping_checked', 'alternatives_checked', 'relevance_complete', 'predictions_hidden']:
            bad = deepcopy(dataset)
            bad['cases'][0]['review'][flag] = False
            with self.assertRaises(ContractError):
                ev.validate_dataset(bad, corpus)
        for field, value in [('reviewer_id', None), ('reviewer_type', 'assistant'), ('reviewed_at', '2026-10-25'), ('notes', '')]:
            bad = deepcopy(dataset)
            bad['cases'][0]['review'][field] = value
            with self.assertRaises(ContractError):
                ev.validate_dataset(bad, corpus)

    def test_wrong_snapshot_policy_quote_offset_trace_rejected(self):
        _, corpus, dataset = fixture()
        mutations = [lambda d: d.__setitem__('index_id', 'other'),
                     lambda d: d.__setitem__('processed_snapshot_id', 'other'),
                     lambda d: d['policy'].__setitem__('candidate_pool_k', 5),
                     lambda d: d['cases'][0]['evidence'][0].__setitem__('quote', 'wrong'),
                     lambda d: d['cases'][0]['evidence'][0].__setitem__('start', True),
                     lambda d: d['cases'][0]['evidence'][0]['source_locator'].__setitem__('offset_unit', 'utf16'),
                     lambda d: d['cases'][0].__setitem__('as_of_date', '2026-10-25')]
        for mutate in mutations:
            bad = deepcopy(dataset)
            mutate(bad)
            with self.assertRaises(ContractError):
                ev.validate_dataset(bad, corpus)

    def test_family_unit_and_question_leakage_rejected(self):
        _, corpus, dataset = fixture()
        for field, value in [('family_id', dataset['cases'][0]['family_id']),
                             ('proposed_units', dataset['cases'][0]['proposed_units']),
                             ('question', '  MÈO  '), ('question_id', 'D1')]:
            bad = deepcopy(dataset)
            bad['cases'][1][field] = value
            with self.assertRaises(ContractError):
                ev.validate_dataset(bad, corpus)

    def test_excluded_is_visible_and_not_scored_as_miss(self):
        _, corpus, dataset = fixture()
        case = dataset['cases'][0]
        synthetic_accept(case)
        case['review']['status'] = 'EXCLUDED_HUMAN'
        case['answerability'] = 'AMBIGUOUS'
        case['relevant_units'] = []
        state = ev.readiness(dataset, corpus, 'dev')
        self.assertEqual(state['status'], 'NO_SCORABLE_CASES')
        self.assertEqual(state['counts'], {'EXCLUDED_HUMAN': 1})


class FrozenEvaluationTests(unittest.TestCase):
    def test_synthetic_freeze_evaluate_no_test_execution_and_immutable_inputs(self):
        index, _, dataset = fixture()
        synthetic_accept(dataset['cases'][0])
        with tempfile.TemporaryDirectory(prefix='.tmp-tillegal-t5-', dir=ROOT) as tmp:
            root = Path(tmp)
            (root/'inputs').mkdir()
            labels = root/'inputs'/'labels.json'
            source = root/'inputs'/'index-manifest.json'
            labels.write_bytes(canonical_json(dataset))
            source.write_text('{}', encoding='utf-8')
            before = file_hash(labels)
            with patch.object(ev, 'load_index', return_value=index):
                frozen = ev.freeze_dataset(labels, source, 'dev', root/'frozen')
                with patch.object(index, 'search', wraps=index.search) as search:
                    report = ev.evaluate(root/'frozen'/'manifest.json', source, root/'output')
                self.assertEqual(search.call_count, 1)
                self.assertEqual(search.call_args.args[0], 'mèo')
                self.assertEqual(report['scored_cases'], 1)
                self.assertEqual(report['metrics']['5']['recall_at_k'], 1)
                self.assertEqual(file_hash(labels), before)
                self.assertEqual(file_hash(root/'frozen'/'dataset.json'), frozen['dataset_sha256'])
                with patch.object(index, 'search', side_effect=AssertionError('must check output before retrieval')):
                    with self.assertRaises(ContractError):
                        ev.evaluate(root/'frozen'/'manifest.json', source, root/'output')
                with self.assertRaises(ContractError):
                    ev.freeze_dataset(labels, source, 'dev', root/'frozen')
                bad = json.loads((root/'frozen'/'dataset.json').read_text(encoding='utf-8'))
                bad['cases'][0]['question'] += ' changed'
                (root/'frozen'/'dataset.json').write_bytes(canonical_json(bad))
                with self.assertRaises(ContractError):
                    ev.evaluate(root/'frozen'/'manifest.json', source, root/'bad-output')
                self.assertFalse((root/'bad-output').exists())
                # Even a consistently rehashed draft cannot bypass the review gate.
                bad['cases'][0]['review'].update(status='PENDING_HUMAN_REVIEW', reviewer_id=None, reviewed_at=None)
                data = canonical_json(bad)
                (root/'frozen'/'dataset.json').write_bytes(data)
                frozen['dataset_sha256'] = hashlib.sha256(data).hexdigest()
                (root/'frozen'/'manifest.json').write_bytes(canonical_json(frozen))
                with patch.object(index, 'search', side_effect=AssertionError('must block before retrieval')):
                    with self.assertRaisesRegex(ContractError, 'NEEDS_HUMAN_REVIEW'):
                        ev.evaluate(root/'frozen'/'manifest.json', source, root/'blocked-output')

    def test_pending_freeze_has_no_output_and_no_retrieval(self):
        index, _, dataset = fixture()
        with tempfile.TemporaryDirectory(prefix='.tmp-tillegal-t5-', dir=ROOT) as tmp:
            root = Path(tmp)
            (root/'inputs').mkdir()
            labels = root/'inputs'/'labels.json'
            source = root/'inputs'/'manifest.json'
            labels.write_bytes(canonical_json(dataset))
            source.write_text('{}', encoding='utf-8')
            with patch.object(ev, 'load_index', return_value=index), patch.object(index, 'search', side_effect=AssertionError('blocked')):
                with self.assertRaisesRegex(ContractError, 'NEEDS_HUMAN_REVIEW'):
                    ev.freeze_dataset(labels, source, 'dev', root/'frozen')
            self.assertFalse((root/'frozen').exists())

    def test_macro_average_denominator_exclusions_and_miss_on_synthetic_only(self):
        index, _, dataset = fixture()
        second = deepcopy(dataset['cases'][0])
        second.update(question_id='D2', question='zzznomatchingtoken')
        dataset['cases'].append(second)
        for case in dataset['cases']:
            case['split'] = 'dev'
            synthetic_accept(case)
        excluded = dataset['cases'][1]
        excluded['review']['status'] = 'EXCLUDED_HUMAN'
        excluded['answerability'] = 'AMBIGUOUS'
        excluded['relevant_units'] = []
        with tempfile.TemporaryDirectory(prefix='.tmp-tillegal-t5-', dir=ROOT) as tmp:
            root = Path(tmp)
            (root/'inputs').mkdir()
            labels, source = root/'inputs'/'labels.json', root/'inputs'/'manifest.json'
            labels.write_bytes(canonical_json(dataset))
            source.write_text('{}', encoding='utf-8')
            with patch.object(ev, 'load_index', return_value=index):
                ev.freeze_dataset(labels, source, 'dev', root/'frozen')
                # Isolate averaging from BM25 ranking: one known rank-1 hit,
                # one empty prediction. Real BM25 can rank a heuristic first.
                chunk = next(c for c in index.to_dict()['chunks'] if c['text'] == '1. Mèo ngủ.')
                def controlled_search(query, top_k):
                    return {'results': [] if query == 'zzznomatchingtoken' else [{'rank': 1, 'chunk': chunk}]}
                with patch.object(index, 'search', side_effect=controlled_search) as search:
                    report = ev.evaluate(root/'frozen'/'manifest.json', source, root/'output')
                self.assertEqual(search.call_count, 2)
            self.assertEqual(report['scored_cases'], 2)
            self.assertEqual(len(report['excluded_cases']), 1)
            self.assertEqual(report['metrics']['5']['recall_at_k'], .5)
            self.assertEqual(report['metrics']['10']['mrr_at_k'], .5)


@unittest.skipUnless(INDEX_MANIFEST.exists() and PROCESSED.exists(), 'local T4 index unavailable')
class PilotReviewPreparationTests(unittest.TestCase):
    def test_twelve_drafts_source_trace_and_no_gold_or_predictions(self):
        from ai_core.bm25_retrieval import BM25Index, load_index
        with tempfile.TemporaryDirectory(prefix='.tmp-tillegal-t5-', dir=ROOT) as tmp:
            out = Path(tmp)/'draft'
            with patch.object(BM25Index, 'search', side_effect=AssertionError('review must be blind')):
                manifest = prepare(INDEX_MANIFEST, out)
            self.assertEqual(manifest['case_count'], 12)
            self.assertEqual(manifest['split_counts'], {'dev': 8, 'test': 4})
            dataset = json.loads((out/'dataset.draft.json').read_text(encoding='utf-8'))
            corpus = ev.EvaluationCorpus(load_index(INDEX_MANIFEST))
            self.assertEqual(len(ev.readiness(dataset, corpus, 'dev')['pending_question_ids']), 8)
            self.assertEqual(len(ev.readiness(dataset, corpus, 'test')['pending_question_ids']), 4)
            self.assertTrue(all(not c['relevant_units'] and c['review']['reviewer_id'] is None for c in dataset['cases']))
            for artifact in manifest['artifacts']:
                self.assertEqual(file_hash(out/artifact['path']), artifact['sha256'])
            for qid, flag in [('D07', 'SOURCE_TEXT_POSSIBLY_INCOMPLETE'), ('D08', 'SUBPOINT_NOT_RESOLVED')]:
                case = next(c for c in dataset['cases'] if c['question_id'] == qid)
                self.assertIn(flag, corpus.chunks[case['evidence'][0]['chunk_id']]['issues'])
            contexts = [json.loads(line) for line in (out/'source_context.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual(len(contexts), 11)
            self.assertTrue(all(c['document']['legal_approval'] == 'QUARANTINE' for c in contexts))
            # Preparation produces no retrieval or metric artifact.
            self.assertEqual({p.name for p in out.iterdir()}, {'dataset.draft.json', 'source_context.jsonl', 'REVIEW.md', 'manifest.json'})


if __name__ == '__main__':
    unittest.main()
