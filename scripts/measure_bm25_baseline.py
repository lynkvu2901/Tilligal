"""Offline T4 operational smoke/latency, not Recall@K/MRR or legal evaluation."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_core.bm25_retrieval import build_index, load_index
from ai_core.data_contracts import canonical_json, ContractError, file_hash

QUERIES = ["tiền lương làm thêm giờ", "hợp đồng lao động", "nghỉ hằng năm",
           "Hội đồng tiền lương quốc gia", "Các văn bản quy định tại điểm a điểm b khoản này",
           "Mẫu số 03/PLIII", "zzzxqvkhongcotrongcorpus", ""]


def measure(manifest_path, output_dir, repeats=30):
    if type(repeats) is not int or not 1 <= repeats <= 1000:
        raise ContractError("repeats must be an integer in [1,1000]")
    manifest_path, output_dir = Path(manifest_path).resolve(), Path(output_dir).resolve()
    if output_dir.exists() or output_dir.is_relative_to(manifest_path.parent):
        raise ContractError("measurement output must be new and outside index directory")
    started = perf_counter()
    index = load_index(manifest_path)
    load_ms = (perf_counter() - started) * 1000
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    started = perf_counter()
    rebuilt = build_index(manifest['input_manifest_path'], manifest['source']['processed_snapshot_id'])
    rebuild_ms = (perf_counter() - started) * 1000
    if canonical_json(rebuilt.to_dict()) != canonical_json(index.to_dict()):
        raise ContractError("rebuild did not reproduce index bytes")
    rows, timings = [], []
    for query in QUERIES:
        expected = index.search(query, 5)  # one warm-up per query
        stable = {k: v for k, v in expected.items() if k != 'latency_ms'}
        durations = []
        for _ in range(repeats):
            response = index.search(query, 5)
            if {k: v for k, v in response.items() if k != 'latency_ms'} != stable:
                raise ContractError("repeated retrieval changed ranks/scores/metadata")
            durations.append(response['latency_ms'])
        if query == QUERIES[-2] and expected['status'] != 'NO_MATCH':
            raise ContractError("technical OOV probe unexpectedly matched")
        if not query and expected['status'] != 'EMPTY_QUERY':
            raise ContractError("empty query probe failed")
        timings.extend(durations)
        rows.append({"query": query, "gold_status": "NOT_ANNOTATED", "response": expected,
                     "warm_search_ms": {"median": statistics.median(durations),
                                        "p95_nearest_rank": sorted(durations)[math.ceil(.95 * len(durations)) - 1],
                                        "min": min(durations), "max": max(durations)}})
    payload = index.to_dict()
    summary = {"measurement_kind": "technical_smoke_and_latency_only", "index_id": index.index_id,
               "source": payload['source'], "usage_policy": "EXPERIMENTAL_ONLY", "corpus_snapshot_id": None,
               "config": payload['config'], "tokenizer": payload['tokenizer'],
               "index_manifest_sha256": file_hash(manifest_path),
               "script_sha256": file_hash(Path(__file__)),
               "python_version": sys.version, "platform": platform.platform(), "processor": platform.processor(),
               "load_and_integrity_validation_ms": load_ms, "rebuild_and_source_validation_ms": rebuild_ms,
               "index_bytes_reproduced": True, "repeated_results_identical": True,
               "query_count": len(QUERIES), "repetitions_per_query": repeats, "top_k": 5,
               "warm_search_calls": len(timings), "warm_search_ms": {
                   "median": statistics.median(timings),
                   "p95_nearest_rank": sorted(timings)[math.ceil(.95 * len(timings)) - 1],
                   "min": min(timings), "max": max(timings)},
               "document_count": len(payload['documents']), "chunk_count": len(payload['chunks']),
               "vocabulary_size": len(payload['statistics']['postings']),
               "total_tokens": sum(payload['statistics']['lengths']),
               "zero_token_chunks": payload['statistics']['lengths'].count(0),
               "attachment_counts": dict(Counter(c['attachment_status'] for c in payload['chunks'])),
               "recall_at_k": None, "mrr": None, "gold_dataset": None,
               "limitations": ["No relevance labels; hits are not verified legal evidence.",
                               "Single local process, warm queries, OS cache uncontrolled; not a service SLA.",
                               "Search timing includes tokenization/scoring/sorting/result copies, excludes index load and JSON serialization.",
                               "Load timing includes artifact integrity checks and rebuilding statistics for validation."]}
    samples = b''.join(canonical_json(row) + b'\n' for row in rows)
    summary['samples_sha256'] = hashlib.sha256(samples).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=False)
    for name, data in [('samples.jsonl', samples), ('summary.json', canonical_json(summary) + b'\n')]:
        with (output_dir / name).open('xb') as stream:
            stream.write(data)
    return summary


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index-manifest', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--repeats', type=int, default=30)
    args = parser.parse_args()
    try:
        print(json.dumps(measure(args.index_manifest, args.output_dir, args.repeats), ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({'status': 'ERROR', 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
