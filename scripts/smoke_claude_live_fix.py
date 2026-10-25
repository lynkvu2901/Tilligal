"""Explicit controlled live smoke: at most 3 generations, never retry/resume.

Run from repository root with python -B -m scripts.smoke_claude_live_fix.
Requires --allow-live and ANTHROPIC_API_KEY. Output directory must be new.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path

from ai_core.anthropic_provider import AnthropicProvider
from ai_core.basic_rag import BasicRAG
from ai_core.bm25_retrieval import load_index
from ai_core.data_contracts import file_hash
from ai_core.evidence_builder import EvidenceBudget

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = (
    'Người sử dụng lao động cần thực hiện những việc gì để tổ chức đối thoại định kỳ tại nơi làm việc?',
    'Đối thoại tại nơi làm việc được tổ chức định kỳ như thế nào?',
    'Đối thoại tại nơi làm việc là gì và nhằm mục đích gì?',
)
INPUT_CAP = 12000
OUTPUT_CAP = 2048
BUDGET = Decimal('0.30')
# Verified Sonnet5 standard USD/MTok rates, 2026-10-25. Recheck before future use.
INPUT_RATE, OUTPUT_RATE = Decimal('2'), Decimal('10')
RESERVE_PER_CALL = (2 * INPUT_CAP * INPUT_RATE + OUTPUT_CAP * OUTPUT_RATE) / 1000000


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-live', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.allow_live or RESERVE_PER_CALL * len(QUESTIONS) > BUDGET:
        print('LIVE_NOT_RUN: opt-in or budget gate')
        return 1
    provider = AnthropicProvider.from_environment(model='claude-sonnet-5', allow_live=True,
        max_tokens=OUTPUT_CAP, max_input_bytes=40000, timeout_seconds=60,
        thinking_type='disabled', structured_output=True, input_token_cap=INPUT_CAP)
    index = load_index(ROOT / 'data/indexes/labor-pilot-3-t4-bm25/manifest.json')
    rag = BasicRAG(index, provider, EvidenceBudget(max_chunks=24, max_quote_chars=8000))
    args.output.mkdir(parents=True, exist_ok=False)
    config = {'model': provider.model, 'generation_limit': 3, 'input_token_cap': INPUT_CAP,
              'max_output_tokens': OUTPUT_CAP, 'budget_usd': str(BUDGET),
              'reserve_per_call_usd': str(RESERVE_PER_CALL), 'total_reserve_usd': str(RESERVE_PER_CALL*3),
              'input_count_margin_multiplier': 2, 'pricing_verified_on': '2026-10-25',
              'pricing_source': 'https://platform.claude.com/docs/en/models/sonnet-5/overview',
              'input_usd_per_million': str(INPUT_RATE), 'output_usd_per_million': str(OUTPUT_RATE),
              'index_id': index.index_id, 'mode': 'live', 'verification_performed': False,
              'code_hashes': {name: file_hash(ROOT/name) for name in (
                  'ai_core/rag_generation.py','ai_core/anthropic_provider.py','ai_core/basic_rag.py',
                  'ai_core/rag_cli.py','ai_core/evidence_builder.py','scripts/smoke_claude_live_fix.py')}}
    with (args.output/'run-config.json').open('x',encoding='utf-8') as f:
        json.dump(config,f,ensure_ascii=False,indent=2)
    records, total = [], Decimal('0')
    for number, question in enumerate(QUESTIONS,1):
        if total + RESERVE_PER_CALL > BUDGET:
            break
        result = rag.answer(question,request_id=f't6-live-fix-{number:03d}',top_k=3)
        path = args.output/f'request-{number:03d}.json'
        with path.open('x',encoding='utf-8') as f:
            json.dump(result,f,ensure_ascii=False,indent=2)
        meta = result['trace'].get('provider_response',{})
        usage = meta.get('usage')
        cost = None
        if usage:
            # No caching requested; use highest cache-write rate if unexpectedly returned.
            cost = (Decimal(usage['input_tokens'])*INPUT_RATE + Decimal(usage['output_tokens'])*OUTPUT_RATE
                    + Decimal(usage.get('cache_creation_input_tokens',0))*4
                    + Decimal(usage.get('cache_read_input_tokens',0))*Decimal('0.2'))/1000000
            total += cost
        record = {'path':path.name,'sha256':file_hash(path),'bytes':path.stat().st_size,
                  'status':result['status'],'error':result['error'],'provider':meta,
                  'estimated_cost_usd':None if cost is None else str(cost)}
        records.append(record)
        print(json.dumps({'request':number,'status':result['status'],'error':result['error'],
                          'usage':usage,'cost_usd':record['estimated_cost_usd']},ensure_ascii=True),flush=True)
        # No automatic recovery: stop on any failure, missing usage, or anomalous budget.
        if result['status']=='FAILED' or usage is None or cost > RESERVE_PER_CALL:
            break
    manifest = {'config':config,'requests':records,'estimated_total_usd':str(total),
                'generation_http_attempts':sum(r['provider'].get('generation_http_attempts',0) for r in records),
                'token_count_http_attempts':sum(r['provider'].get('token_count_http_attempts',0) for r in records),
                'technical_successes':sum(r['status'] in ('DRAFT_UNVERIFIED','ABSTAINED_UNVERIFIED') for r in records)}
    with (args.output/'manifest.json').open('x',encoding='utf-8') as f:
        json.dump(manifest,f,ensure_ascii=False,indent=2)
    return 0 if records and manifest['technical_successes']==len(records) else 1


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception:
        # Never print exception arguments/headers/environment on setup failures.
        print('SMOKE_SETUP_OR_IO_ERROR')
        raise SystemExit(1)
