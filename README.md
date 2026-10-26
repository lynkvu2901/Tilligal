# Tillegal AI Core

RAG tuần tự: BM25 / dense / hybrid (RRF), reranker tùy chọn, evidence builder và generation provider. Entry point Python là `ai_core.basic_rag.BasicRAG.answer()`. Chưa có API server; kết quả là bản nháp và candidate citations chưa xác minh pháp lý.

**Clone source chưa đủ để chạy với corpus thật.** Corpus/index/model weights được bàn giao riêng. Tests, reports, dữ liệu và tài liệu nội bộ không nằm trong cây source bàn giao; các bản từng commit vẫn có thể tồn tại trong lịch sử Git cũ.

## 1. Setup

Chạy từ root repository. Môi trường local: Windows CPython 3.14.2. Lock ghi phiên bản môi trường đó; chưa xác nhận Linux/Python khác.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
```

Dependency trực tiếp: torch, transformers, numpy cho dense/rerank; pyarrow, beautifulsoup4 cho chuẩn bị dữ liệu. Provider HTTP dùng thư viện chuẩn Python, không cần Anthropic SDK. BM25 + mock không tải ML models. Không cài package toàn hệ thống.

## 2. Artifacts cần nhận riêng

Để chạy BM25, nhận cặp `manifest.json` và `index.json` tại `data/indexes/labor-pilot-3-t4-bm25/`. Index chứa corpus dùng cho runtime; `load_index()` không đọc lại raw/processed files. Bản local có 3.085 chunks; SHA256 `index.json`: `0e2fbd8cc6457a42e34f0a5b3129010af57b6a55bbe59f223a6c6586ed7e16c1`.

Manifest kiểm tra hash index và bytes của `bm25_retrieval.py`, `legal_parser.py`, `data_contracts.py`. `.gitattributes` giữ newline Python source khi checkout. Nếu hash lệch, tái tạo index với source hiện tại; không sửa hash để bỏ qua kiểm tra.

Dense/hybrid cần thêm `.model-cache/embedding.json` cùng đúng snapshot model, và `data/indexes/labor-pilot-3-t7-dense/` chứa `manifest.json`, `rows.json`, `vectors.npy`. Rerank cần `.model-cache/reranker.json` cùng snapshot weights. Lock local chứa đường dẫn Windows; khi đổi OS nên setup cache mới và build dense trên máy đích. Runtime không tự download và kiểm tra revision/hash.

### Tái tạo từ raw corpus

Nhận riêng `metadata.parquet`, `content.parquet`, `relationships.parquet` tại `data/downloads/hf-legal/`. Adapter hiện chỉ chọn ba văn bản pilot định nghĩa trong source, chưa phải pipeline cho corpus bất kỳ. Quyền sử dụng và tính đúng đắn của corpus cần xác nhận riêng.

Các lệnh dưới đây dành cho output chưa tồn tại. Giữ nguyên artifacts cũ nếu đã có; dùng output mới và điều chỉnh đường dẫn cho toàn chuỗi. Chạy chuỗi trên máy đích vì provenance manifests chứa đường dẫn tuyệt đối và hash liên kết:

```powershell
$py = '.\.venv\Scripts\python.exe'
& $py -B -m scripts.inspect_local_legal inspect --input-dir data/downloads/hf-legal --output-dir data/inspection/local-legal-v1 --selection data/selections/labor-pilot-3.json
& $py -B -m ai_core.adapters.hf_local --manifest data/inspection/local-legal-v1/manifest.json --selection data/selections/labor-pilot-3.json --output-dir data/staging/labor-pilot-3
& $py -B -m ai_core.legal_parser --manifest data/staging/labor-pilot-3/manifest.json --output-dir data/processed/labor-pilot-3-t3-fix
$snapshot = (Get-Content data/processed/labor-pilot-3-t3-fix/manifest.json -Raw | ConvertFrom-Json).processed_snapshot_id
& $py -B -m ai_core.bm25_retrieval build --manifest data/processed/labor-pilot-3-t3-fix/manifest.json --expected-snapshot $snapshot --output-dir data/indexes/labor-pilot-3-t4-bm25
```

### Models và dense index

Setup tải model công khai, cần mạng/dung lượng; không gọi Claude:

```powershell
$py = '.\.venv\Scripts\python.exe'
& $py -B -m scripts.setup_t7_models --kind embedding --revision 614241f622f53c4eeff9890bdc4f31cfecc418b3
& $py -B -m scripts.build_dense_index
# Chỉ cần cho hybrid + rerank:
& $py -B -m scripts.setup_t7_models --kind reranker --revision 953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e
```

Model IDs: `intfloat/multilingual-e5-small`, `BAAI/bge-reranker-v2-m3`. Setup từ chối ghi đè lock; build dense từ chối output đã tồn tại và mặc định đọc BM25 ở đường dẫn trên. Đổi output bằng `build_dense_index --output PATH`; truyền `dense_manifest=Path(...)` vào factory Python khi load.

## 3. Tích hợp Python

Khởi tạo index/provider/retriever khi worker khởi động. Ví dụ offline, không tốn phí:

```python
from pathlib import Path
from uuid import uuid4
from ai_core.basic_rag import BasicRAG
from ai_core.bm25_retrieval import load_index
from ai_core.evidence_builder import EvidenceBudget
from ai_core.rag_generation import MockProvider
from ai_core.retrieval_runtime import make_retriever

index = load_index(Path('data/indexes/labor-pilot-3-t4-bm25/manifest.json'))
retriever = make_retriever(index, mode='bm25')
# Khi có artifacts: mode='dense', hoặc mode='hybrid', rerank=True.
rag = BasicRAG(index, MockProvider(), EvidenceBudget(24, 8000), retriever=retriever)
result = rag.answer('Đối thoại tại nơi làm việc là gì?', request_id=str(uuid4()), top_k=3)
print(result['status'], result['answer'])
```

`answer()` trả dict JSON-serializable. Input: `question` không rỗng, tối đa 10.000 ký tự; `request_id` không rỗng; `top_k` integer 1–100. Mock chỉ trích evidence đầu tiên để kiểm tra luồng, không suy luận trả lời câu hỏi.

| Field | Ý nghĩa |
| --- | --- |
| `schema_version`, `request_id`, `question` | Version `"1"` và request |
| `status` | `DRAFT_UNVERIFIED`, `ABSTAINED_UNVERIFIED`, `NO_EVIDENCE`, `FAILED` |
| `answer` | Bản nháp/thông báo hoặc `null` khi lỗi |
| `candidate_citations` | Evidence với `citation_status=CANDIDATE_UNVERIFIED`, ID văn bản/chunk, quote, metadata, warnings |
| `verification_status`, `usage_policy` | `NOT_PERFORMED`, `EXPERIMENTAL_ONLY` |
| `corpus_snapshot_id` | Hiện `null`, chưa có corpus được phê duyệt |
| `evidence_bundle` | Evidence/context; có thể `null` nếu lỗi sớm |
| `trace` | Retrieval, prompt, raw generation, timings, provider metadata |
| `warnings` | Giới hạn xác minh/context |
| `error` | `null` hoặc `{ "code": "...", "stage": "..." }` |

Backend tự quyết định response DTO và mapping HTTP status. Lỗi trong `answer()` được trả dưới dạng `FAILED`; lỗi khởi tạo index/model/provider có thể raise. `rag_cli` có envelope lỗi cấu hình rút gọn, không đồng nhất hoàn toàn với `answer()`. Không trả nguyên trace/prompt/raw output cho client mặc định vì chứa câu hỏi và trích đoạn corpus.

## 4. Environment và generation thật

Mock không cần secrets. `.env.example` chỉ liệt kê tên biến rỗng; code không tự load `.env`. Backend đưa secrets vào process environment hoặc secret manager.

- Anthropic: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`. Thay mock bằng `AnthropicProvider.from_environment(allow_live=True, ...)` khi đã chủ động cho phép chi phí.
- Chat-completions: `TILLEGAL_LLM_ENDPOINT` (HTTPS), `TILLEGAL_LLM_MODEL`, `TILLEGAL_LLM_API_KEY`. `rag_cli` đọc các biến này; Python integration khởi tạo `ChatCompletionsProvider` bằng tham số tương ứng.
- `demo_cli --live` hiện hard-code `claude-sonnet-5` và preset riêng, không đọc `ANTHROPIC_MODEL`. Backend nên cấu hình provider trực tiếp.

Tương thích API version/model chưa được kiểm tra live trong đợt bàn giao này. Không có retry, streaming hoặc async provider.

## 5. Smoke sau khi nhận index

```powershell
.\.venv\Scripts\python.exe -B -m ai_core.rag_cli --question 'Đối thoại tại nơi làm việc là gì?' --mode mock --format text
.\.venv\Scripts\python.exe -B -m ai_core.demo_cli
# Khi đủ model/index:
.\.venv\Scripts\python.exe -B -m ai_core.demo_cli --retrieval hybrid --rerank
```

Không gọi Claude nếu không bật live. Demo tối đa ba câu hỏi; nhập `exit` để thoát. `--allow-retrieval-fallback` chỉ cho hybrid dùng nhánh còn khả dụng và đánh dấu `DEGRADED`; lỗi integrity không fallback. Reranker không tự thay bằng model khác.

## 6. Phạm vi và giới hạn

Bàn giao runtime trong `ai_core/`, adapter/parser, ba script `inspect_local_legal.py`, `setup_t7_models.py`, `build_dense_index.py`, dependency manifests và cấu hình mẫu. Script inspect được giữ vì tạo manifest/selection bắt buộc cho adapter dù có sinh validation report local. Modules so sánh/đánh giá retrieval và scripts benchmark/live-smoke chỉ giữ local; runtime không import chúng.

Chưa có HTTP routing, authentication, rate limiting, queue, cancellation, deployment config, kiểm thử tải/thread-safety. Inference đồng bộ; Backend cần chọn worker/concurrency và giới hạn tài nguyên. Chưa triển khai multi-agent, legal verification, claim-support verification, xác minh hiệu lực văn bản hoặc tự chọn phiên bản luật. Candidate citations chưa phải căn cứ đã xác minh.

Tests/reports không xuất bản theo phạm vi bàn giao. Tests local dùng mock HTTP/synthetic vectors để kiểm tra contract; không chứng minh chất lượng truy hồi hoặc đúng đắn pháp lý. Nhận tests riêng nếu cần tái chạy đầy đủ.
