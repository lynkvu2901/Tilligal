"""Structured-output/context/budget checks; all HTTP mocked."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from ai_core.basic_rag import BasicRAG
from ai_core.evidence_builder import EvidenceBuilder
from ai_core.rag_generation import generation_messages, validate_draft, GenerationError, DRAFT_OUTPUT_SCHEMA
import test_anthropic_provider as fixtures
from test_anthropic_provider import MESSAGES, opened, response
from test_bm25_retrieval import synthetic_index
from scripts import smoke_claude_live_fix as smoke


class LiveFixTests(unittest.TestCase):
    def test_smoke_reservations_cover_three_requests_below_budget(self):
        self.assertEqual(len(smoke.QUESTIONS), 3)
        self.assertLessEqual(smoke.OUTPUT_CAP, 2048)
        self.assertLessEqual(smoke.INPUT_CAP, 12000)
        self.assertLessEqual(smoke.RESERVE_PER_CALL*3, smoke.BUDGET)
        self.assertEqual(str(smoke.RESERVE_PER_CALL*3), '0.20544')

    def provider(self, **kwargs):
        return fixtures.AnthropicTests().provider(structured_output=True, input_token_cap=12000, max_tokens=2048, **kwargs)

    def test_compact_context_preserves_every_quote_warning_and_version(self):
        index = synthetic_index(['Điều 1. Demo\n1. mèo được nghỉ.\n2. Trừ trường hợp khẩn cấp.\nĐoạn cần review.'])
        bundle = EvidenceBuilder(index).build(index.search('mèo', 1), request_id='compact')
        original = deepcopy(bundle)
        payload = json.loads(generation_messages('mèo', bundle)[1]['content'])
        self.assertEqual(bundle, original)
        self.assertEqual([e['evidence_id'] for e in payload['evidence']], [e['evidence_id'] for e in bundle['evidence']])
        for compact, full in zip(payload['evidence'], bundle['evidence']):
            self.assertEqual(compact['quote'], full['quote'])
            self.assertEqual(set(compact['warnings']) | set(payload['common_warnings']), set(full['warnings']))
            self.assertEqual(payload['documents'][compact['document_ref']]['document_version_id'], full['document_version_id'])
        self.assertTrue(any('Trừ trường hợp' in e['quote'] for e in payload['evidence']))
        self.assertEqual(len(payload['documents']), 1)

    def test_fences_duplicate_keys_and_partial_json_still_fail_closed(self):
        good = '{"draft_answer":"Chưa đủ thông tin.","candidate_evidence_ids":[],"abstain":true}'
        self.assertTrue(validate_draft(good, set())['abstain'])
        for raw in ('```json\n'+good+'\n```', good[:-1], good.replace('"abstain":true', '"abstain":true,"abstain":false')):
            with self.assertRaises(GenerationError):
                validate_draft(raw, set())

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_schema_and_count_use_same_content_before_single_generation(self, opener):
        opener.return_value.open.side_effect = [opened({'input_tokens': 9000}), opened(response())]
        result = self.provider().generate(MESSAGES)
        calls = opener.return_value.open.call_args_list
        self.assertEqual(len(calls), 2)
        count = json.loads(calls[0].args[0].data)
        generate = json.loads(calls[1].args[0].data)
        self.assertTrue(calls[0].args[0].full_url.endswith('/count_tokens'))
        self.assertEqual(count, {k:v for k,v in generate.items() if k not in ('max_tokens','stream')})
        self.assertEqual(generate['output_config']['format']['schema'], DRAFT_OUTPUT_SCHEMA)
        self.assertFalse(generate['output_config']['format']['schema']['additionalProperties'])
        self.assertEqual(result.metadata['counted_input_tokens'], 9000)
        self.assertEqual(generate['max_tokens'], 2048)

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_count_failure_or_budget_exceeded_never_generates(self, opener):
        for counted in (12001, -1, True, None):
            opener.return_value.open.reset_mock()
            opener.return_value.open.return_value = opened({'input_tokens': counted})
            with self.assertRaises(GenerationError) as caught:
                self.provider().generate(MESSAGES)
            opener.return_value.open.assert_called_once()
            self.assertEqual(caught.exception.metadata['generation_http_attempts'], 0)

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_structured_max_tokens_does_not_accept_even_parseable_json(self, opener):
        raw = '{"draft_answer":"Thiếu thông tin.","candidate_evidence_ids":[],"abstain":true}'
        opener.return_value.open.side_effect = [opened({'input_tokens': 20}), opened(response(text=raw, stop_reason='max_tokens'))]
        r = BasicRAG(synthetic_index(['mèo']), self.provider()).answer('mèo',request_id='cut')
        self.assertEqual(r['status'], 'FAILED')
        self.assertEqual(r['trace']['generation_raw'], raw)
        self.assertIsNone(r['answer'])

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_structured_abstention_and_request_usage_isolation(self, opener):
        raw = '{"draft_answer":"Chỉ có tiêu đề, chưa đủ thông tin.","candidate_evidence_ids":[],"abstain":true}'
        rag = BasicRAG(synthetic_index(['mèo']), self.provider())
        results = []
        for n in (100, 200):
            opener.return_value.open.side_effect = [opened({'input_tokens': n}), opened(response(text=raw))]
            results.append(rag.answer('mèo',request_id=str(n)))
        self.assertEqual([r['status'] for r in results], ['ABSTAINED_UNVERIFIED']*2)
        self.assertEqual([r['trace']['provider_response']['counted_input_tokens'] for r in results], [100,200])


if __name__ == '__main__':
    unittest.main()
