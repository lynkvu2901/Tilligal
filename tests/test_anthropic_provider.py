"""Offline only: fake keys and mocked HTTP. No Anthropic API requests."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from ai_core.anthropic_provider import AnthropicProvider, ENDPOINT, API_VERSION
from ai_core.basic_rag import BasicRAG
from ai_core.rag_generation import GenerationError, GenerationText, NoRedirect
from ai_core.rag_cli import main
from test_bm25_retrieval import synthetic_index

FAKE_KEY = 'unit-test-credential-only'
MESSAGES = [{'role': 'system', 'content': 'rules'}, {'role': 'user', 'content': 'data'}]


def response(text='{}', **updates):
    return {'type': 'message', 'role': 'assistant', 'model': 'claude-test-fixture',
            'content': [{'type': 'text', 'text': text}], 'stop_reason': 'end_turn',
            'usage': {'input_tokens': 123, 'output_tokens': 17}, **updates}


def opened(obj):
    stream = MagicMock()
    stream.__enter__.return_value = stream
    stream.status = 200
    stream.read.return_value = json.dumps(obj).encode('utf-8')
    return stream


class AnthropicTests(unittest.TestCase):
    def provider(self, **kwargs):
        return AnthropicProvider(**{'model': 'claude-test-fixture', 'api_key': FAKE_KEY,
                                    'allow_live': True, **kwargs})

    def test_configuration_no_default_model_opt_in_or_generic_key_fallback(self):
        for kwargs in ({'model': ''}, {'model': 'guessed'}, {'api_key': ''}, {'allow_live': False},
                       {'max_tokens': 2049}, {'timeout_seconds': float('nan')}, {'api_key': 'bad\nkey'}):
            with self.assertRaises(GenerationError):
                self.provider(**kwargs)
        with patch.dict(os.environ, {'TILLEGAL_LLM_API_KEY': FAKE_KEY}, clear=True):
            with self.assertRaises(GenerationError):
                AnthropicProvider.from_environment(allow_live=True)
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': FAKE_KEY, 'ANTHROPIC_MODEL': 'claude-test-fixture'}, clear=True):
            self.assertEqual(AnthropicProvider.from_environment(allow_live=True).model, 'claude-test-fixture')
        self.assertNotIn(FAKE_KEY, repr(self.provider()))

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_messages_wire_contract_headers_proxy_disabled_no_tools_one_call(self, opener):
        opener.return_value.open.return_value = opened(response())
        result = self.provider().generate(MESSAGES)
        self.assertIsInstance(result, str)
        self.assertIsInstance(result, GenerationText)
        req = opener.return_value.open.call_args.args[0]
        self.assertEqual(req.full_url, ENDPOINT)
        self.assertEqual(req.get_header('X-api-key'), FAKE_KEY)
        self.assertEqual(req.get_header('Anthropic-version'), API_VERSION)
        payload = json.loads(req.data)
        self.assertEqual(set(payload), {'model', 'max_tokens', 'stream', 'system', 'messages'})
        self.assertEqual(payload['system'], 'rules')
        self.assertEqual(payload['messages'], [MESSAGES[1]])
        self.assertFalse(payload['stream'])
        self.assertNotIn(FAKE_KEY, req.data.decode())
        self.assertEqual(opener.call_args.args[0].proxies, {})
        self.assertIsInstance(opener.call_args.args[1], NoRedirect)
        opener.return_value.open.assert_called_once()
        self.assertEqual(result.metadata['usage'], {'input_tokens': 123, 'output_tokens': 17})

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_runtime_model_budget_and_thinking_without_os_changes(self, opener):
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': FAKE_KEY}, clear=True):
            provider = AnthropicProvider.from_environment(model='claude-sonnet-5', allow_live=True,
                thinking_type='disabled', max_input_bytes=40000)
            self.assertNotIn('ANTHROPIC_MODEL', os.environ)
        opener.return_value.open.return_value = opened(response())
        provider.generate(MESSAGES)
        payload = json.loads(opener.return_value.open.call_args.args[0].data)
        self.assertEqual(payload['model'], 'claude-sonnet-5')
        self.assertEqual(payload['thinking'], {'type': 'disabled'})
        opener.reset_mock()
        with self.assertRaises(GenerationError) as caught:
            self.provider(max_input_bytes=1).generate(MESSAGES)
        self.assertEqual(caught.exception.code, 'GENERATION_INPUT_LIMIT')
        opener.assert_not_called()

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_multi_text_blocks_and_missing_usage(self, opener):
        obj = response(content=[{'type': 'text', 'text': '{'}, {'type': 'text', 'text': '}'}])
        obj.pop('usage')
        opener.return_value.open.return_value = opened(obj)
        result = self.provider().generate(MESSAGES)
        self.assertEqual(result, '{}')
        self.assertIsNone(result.metadata['usage'])

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_status_errors_distinct_sanitized_and_never_retried(self, opener):
        for status, code in [(401, 'ANTHROPIC_AUTHENTICATION_ERROR'), (403, 'ANTHROPIC_PERMISSION_ERROR'),
                             (429, 'ANTHROPIC_RATE_LIMIT'), (500, 'ANTHROPIC_PROVIDER_ERROR'),
                             (529, 'ANTHROPIC_PROVIDER_ERROR'), (302, 'ANTHROPIC_PROVIDER_ERROR'),
                             (404, 'ANTHROPIC_MODEL_OR_RESOURCE_NOT_FOUND'), (400, 'ANTHROPIC_BAD_REQUEST'),
                             (402, 'ANTHROPIC_BILLING_ERROR'), (504, 'PROVIDER_TIMEOUT')]:
            opener.return_value.open.reset_mock()
            opener.return_value.open.side_effect = HTTPError(ENDPOINT, status, FAKE_KEY, {}, io.BytesIO(FAKE_KEY.encode()))
            with self.assertRaises(GenerationError) as caught:
                self.provider().generate(MESSAGES)
            self.assertEqual(caught.exception.code, code)
            self.assertEqual(caught.exception.metadata['http_status'], status)
            self.assertNotIn(FAKE_KEY, str(caught.exception) + json.dumps(caught.exception.metadata))
            opener.return_value.open.assert_called_once()

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_timeouts_and_network_errors(self, opener):
        for exc, code in [(TimeoutError(FAKE_KEY), 'PROVIDER_TIMEOUT'),
                          (URLError(TimeoutError()), 'PROVIDER_TIMEOUT'),
                          (URLError(FAKE_KEY), 'ANTHROPIC_NETWORK_ERROR')]:
            opener.return_value.open.side_effect = exc
            with self.assertRaises(GenerationError) as caught:
                self.provider().generate(MESSAGES)
            self.assertEqual(caught.exception.code, code)

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_stop_reasons_keep_usage_and_reject_partial_or_refusal(self, opener):
        for reason in ('max_tokens', 'tool_use', 'refusal', 'pause_turn', None):
            opener.return_value.open.return_value = opened(response(stop_reason=reason))
            with self.assertRaises(GenerationError) as caught:
                self.provider().generate(MESSAGES)
            self.assertEqual(caught.exception.code, 'ANTHROPIC_INCOMPLETE_OR_REFUSED')
            self.assertEqual(caught.exception.metadata['usage']['output_tokens'], 17)
        opener.return_value.open.return_value = opened(response(stop_details={'type': 'refusal'}))
        with self.assertRaises(GenerationError):
            self.provider().generate(MESSAGES)

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_content_usage_status_and_malformed_response(self, opener):
        variants = [{}, response(content=[]), response(content=[{'type': 'tool_use'}]),
                    response(content=[{'type': 'thinking', 'thinking': 'private'}]), response(text=''),
                    response(usage={'input_tokens': -1, 'output_tokens': 1}),
                    response(usage={'input_tokens': True, 'output_tokens': 1}), response(role='user'),
                    response(stop_details='malformed')]
        for obj in variants:
            opener.return_value.open.return_value = opened(obj)
            with self.assertRaises(GenerationError):
                self.provider().generate(MESSAGES)
        for raw in (b'{', b'x' * 1048577, b'\xff'):
            stream = opened(response())
            stream.read.return_value = raw
            opener.return_value.open.return_value = stream
            with self.assertRaises(GenerationError):
                self.provider().generate(MESSAGES)
        stream = opened(response())
        stream.status = 201
        opener.return_value.open.return_value = stream
        with self.assertRaises(GenerationError):
            self.provider().generate(MESSAGES)

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_secret_not_allowed_in_payload_or_returned_text(self, opener):
        with self.assertRaises(GenerationError):
            self.provider().generate([MESSAGES[0], {'role': 'user', 'content': FAKE_KEY}])
        opener.assert_not_called()
        opener.return_value.open.return_value = opened(response(text=FAKE_KEY))
        with self.assertRaises(GenerationError) as caught:
            self.provider().generate(MESSAGES)
        self.assertNotIn(FAKE_KEY, str(caught.exception) + json.dumps(caught.exception.metadata))

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_pipeline_usage_is_request_local_even_schema_failure(self, opener):
        index = synthetic_index(['Điều 1. Mèo\n1. mèo nghỉ.', 'Điều 2. Chim\n1. chim học.'])
        def send(req, **kwargs):
            data = json.loads(json.loads(req.data)['messages'][0]['content'])
            e = data['evidence'][0]
            if data['question'] == 'mèo':
                text = json.dumps({'draft_answer': 'Fixture offline.', 'candidate_evidence_ids': [e['evidence_id']], 'abstain': False})
                count = 11
            else:
                text, count = 'not JSON', 22
            return opened(response(text=text, usage={'input_tokens': count, 'output_tokens': 5}))
        opener.return_value.open.side_effect = send
        rag = BasicRAG(index, self.provider())
        with ThreadPoolExecutor(max_workers=2) as pool:
            cat, bird = list(pool.map(lambda q: rag.answer(q, request_id=q, top_k=1), ['mèo', 'chim']))
        self.assertEqual(cat['status'], 'DRAFT_UNVERIFIED')
        self.assertEqual(bird['error']['code'], 'INVALID_OUTPUT')
        self.assertEqual(cat['trace']['provider_response']['usage']['input_tokens'], 11)
        self.assertEqual(bird['trace']['provider_response']['usage']['input_tokens'], 22)
        self.assertNotIn(FAKE_KEY, json.dumps([cat, bird]))

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_pipeline_provider_failure_keeps_usage_telemetry(self, opener):
        opener.return_value.open.return_value = opened(response(text='{"draft_answer":"unfinished', stop_reason='max_tokens'))
        result = BasicRAG(synthetic_index(['mèo']), self.provider()).answer('mèo', request_id='fail')
        self.assertEqual(result['trace']['provider_response']['usage']['output_tokens'], 17)
        self.assertEqual(result['trace']['generation_raw'], '{"draft_answer":"unfinished')
        self.assertIsNone(result['answer'])

    @patch('ai_core.anthropic_provider.request.build_opener')
    def test_cli_anthropic_mocked_http(self, opener):
        opener.return_value.open.return_value = opened(response(text=json.dumps({
            'draft_answer': 'Fixture offline: thiếu thông tin.', 'candidate_evidence_ids': [], 'abstain': True})))
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': FAKE_KEY, 'ANTHROPIC_MODEL': 'claude-test-fixture'}, clear=True), patch('sys.stdout', new_callable=io.StringIO) as output:
            code = main(['--question', 'đối thoại định kỳ', '--provider', 'anthropic', '--mode', 'live', '--allow-live'])
            result = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'ABSTAINED_UNVERIFIED')
        self.assertEqual(result['trace']['provider_response']['provider'], 'anthropic')


if __name__ == '__main__':
    unittest.main()
