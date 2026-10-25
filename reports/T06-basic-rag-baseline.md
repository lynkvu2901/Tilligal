# T6 — Basic RAG baseline E2E

Ngày 25/10/2026. Phạm vi theo phê duyệt mới nhất: **Basic RAG, không Citation Verification**. Hoàn thành kỹ thuật bằng mock; **chưa chạy LLM thật**. Không triển khai T7/T8/L-MARS. T5 chưa human-approved gold. Trạng thái học chưa được người dùng xác nhận.

## A. Mục tiêu và kết quả

Pipeline Python CLI đã chạy: Question → BM25 → Evidence Builder T6.1 → Generation → Draft Answer + Candidate Citations + Trace.

- 138/138 test PASS: 21 mới + 117 hồi quy, không skip.
- Demo thực tế: [draft.json](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-basic-rag-mock-v1/draft.json>), [no-evidence.json](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-basic-rag-mock-v1/no-evidence.json>), [manifest.json](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-basic-rag-mock-v1/manifest.json>).
- Demo mock sinh DRAFT_UNVERIFIED và candidate citations có trace về nguồn. Query OOV trả NO_EVIDENCE, không generation.
- Giữ nguyên hash 52 file cũ, gồm T1–T5, raw/index/nhãn và T6.1. Không đổi parser/BM25/policy. Không gọi mạng, không phát sinh chi phí LLM hoặc cài thư viện.
- Có live adapter cấu hình được, nhưng chỉ kiểm HTTP contract bằng mocks; không tuyên bố live E2E hoặc chất lượng trả lời pháp lý.

## B. File và quyết định thiết kế

| File | Vai trò |
|---|---|
| [rag_generation.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/rag_generation.py>) | Provider protocol, prompt, mock, HTTP adapter, JSON/schema/ID-membership validation |
| [basic_rag.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/basic_rag.py>) | Điều phối tuần tự, skip generation khi rỗng, candidate citations, trace/error handling |
| [rag_cli.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/rag_cli.py>) | CLI JSON/text, cấu hình live có opt-in, ghi output exclusive |
| [test_basic_rag.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_basic_rag.py>) | Contract/provider/isolation/CLI/integration tests |
| [03-STATE-AND-CONTRACTS.md](<D:/DOWNLOAD/Ligalli Illigal/03-STATE-AND-CONTRACTS.md>) | Mục 2.7 công bố hợp đồng hiện hành, thay phạm vi verification T6 cũ |
| [CHECKPOINT.md](<D:/DOWNLOAD/Ligalli Illigal/CHECKPOINT.md>) | Trạng thái kỹ thuật và bước tiếp theo chưa triển khai |

Giữ nguyên Evidence Builder và toàn bộ provenance. Provider chỉ được trả text JSON với `draft_answer`, `candidate_evidence_ids`, `abstain`; metadata citation được lấy từ bundle trong code. Output của model không được tự tạo document/version/URL hoặc trạng thái nguồn ở các trường citation có cấu trúc.

Validator kiểm JSON/schema, ID thuộc bundle, không trùng, quy tắc abstain. Không phân tích tính đúng đắn của draft, citation viết trong prose, quote/hash/locator so nguồn, hoặc semantic support. Có test cố ý cho nội dung bịa nhưng đúng schema đi qua: đây là giới hạn được công khai, không phải verifier bị thiếu test.

Mock lấy quote của evidence đầu tiên với tiền tố MOCK; không có suy luận và không đánh giá relevance. Live adapter nhận endpoint HTTPS tương thích chat-completions: request gồm model/messages/max_tokens/stream=false; response cần một choice với message.content và finish_reason=stop. Chưa chọn hãng/model, chưa kiểm khả năng tương thích với dịch vụ thực tế. Không tools, redirect, stream hoặc retry.

Các giới hạn: context có thể thiếu ngoại lệ/dẫn chiếu; candidate citations gắn toàn draft, chưa mapping từng claim. Prompt chỉ yêu cầu tránh suy diễn, không bảo đảm LLM tuân thủ hoặc chống prompt injection thành công. Schema không chặn được câu chữ sai pháp lý trong prose. Trace chứa câu hỏi và nội dung nguồn, cần xem xét trước khi chia sẻ; raw_ref cục bộ không gửi vào prompt live. Bundle/index ở RAM, trace JSON khá lớn do giữ provenance. Chưa triển khai verifier, token/cost estimator, hard request deadline hoặc benchmark chất lượng.

## C. Luồng và chạy demo

Trong thư mục dự án `D:\DOWNLOAD\Ligalli Illigal`:

```powershell
python -B -m ai_core.rag_cli --question "đối thoại định kỳ" --top-k 3 --request-id demo-local --format text
python -B -m ai_core.rag_cli --question "đối thoại định kỳ" --top-k 3 --request-id demo-json --format json
python -B -m ai_core.rag_cli --question "zzzzqqqnotincorpus" --format json
```

Để lưu đầy đủ JSON, thêm `--output` trỏ tới **file mới** trong thư mục đã tồn tại. Không dùng đường dẫn artifact cũ. CLI không overwrite. Text mode hiển thị draft/candidate quote/version/chunk/warnings và trace ngắn; JSON giữ toàn bộ evidence/context/locators.

Mỗi request: validate input → search một lần → build evidence → nếu rỗng trả NO_EVIDENCE → tạo prompt → generate một lần → validate JSON/IDs → lấy citation payload từ bundle → trả DRAFT_UNVERIFIED hoặc ABSTAINED_UNVERIFIED. Lỗi trả FAILED với stage/code, không hiển thị raw invalid output như answer. Raw generation vẫn giữ trong trace có giới hạn để debug.

API Python:

```python
from ai_core.bm25_retrieval import load_index
from ai_core.basic_rag import BasicRAG
from ai_core.rag_generation import MockProvider

index = load_index('data/indexes/labor-pilot-3-t4-bm25/manifest.json')
response = BasicRAG(index, MockProvider()).answer(
    'đối thoại định kỳ', request_id='example-001', top_k=3)
```

Live chưa chạy. Khi người dùng đã chọn provider/model, cho phép chi phí và muốn thử, cấu hình môi trường `TILLEGAL_LLM_ENDPOINT` (URL endpoint đầy đủ), `TILLEGAL_LLM_MODEL`, `TILLEGAL_LLM_API_KEY`; sau đó chạy CLI với `--mode live --allow-live`. Không đặt key trong code, báo cáo hoặc command argument. Không có key/model mặc định và không tự lấy cấu hình rồi gọi live. Endpoint phải tuân theo wire contract ở mục B; dịch vụ khác cần adapter riêng.

Giới hạn mặc định: question 10.000 ký tự; evidence kế thừa 32 chunk/24.000 ký tự; messages tối đa 120.000 bytes UTF-8; output 1.024 tokens (cấu hình được); raw generation tối đa 65.536 ký tự; answer 12.000 ký tự; HTTP response 1MiB. Socket timeout 30s là timeout thao tác I/O, **không hard deadline toàn request**. Token cap và timeout không đủ để kết luận chi phí bằng một con số; phí live chưa đo.

## D. Hướng dẫn đọc code cho AI Engineer

1. `basic_rag.BasicRAG.answer`: theo luồng request đến response, chú ý nhánh NO_EVIDENCE, FAILED và counters. Hiểu input/output trước khi đọc provider.
2. `rag_generation.generation_messages`: vì sao system instructions tách khỏi dữ liệu question/evidence; vì sao gửi warnings/omissions nhưng giữ raw filesystem refs ở local.
3. `rag_generation.validate_draft`: schema và ID membership đảm bảo điều gì; tại sao nội dung sai vẫn có thể pass.
4. `MockProvider.generate` rồi `ChatCompletionsProvider.generate`: hai implementations cùng protocol; mock deterministic phục vụ kiểm plumbing, live có networking, timeout và lỗi response.
5. `rag_cli.main`: mặc định mock, opt-in live, output JSON và exit code; đọc `CLITests` để biết cách gọi từ process thật.
6. `PipelineTests`: request-local state, deepcopy và IDs thuộc bundle. Cùng nguồn có thể có cùng evidence ID giữa requests; điều bị cấm là tham chiếu evidence không có trong bundle hiện tại.

Cần hiểu ngay: dependency injection qua provider, structured output, request isolation, traceability, fail-closed khi schema sai, khác biệt giữa kiểm kỹ thuật và chất lượng. Có thể học sau: streaming, provider SDK riêng, token accounting, deployment và tối ưu RAM. Không cần framework agent để có baseline này.

## E. Bằng chứng kiểm thử và demo

Đã chạy `python -B -m unittest discover -s tests -p test_basic_rag.py -v`: lượt đầu 19 tests PASS, phát hiện ResourceWarning ở HTTPError mock. Đã đóng HTTPError trong adapter, thêm hai test prompt budget và reproducibility; sau đó chạy **`python -B -m unittest discover -s tests -v`: 138 tests PASS trong 27,815s**, không skip hoặc ResourceWarning.

21 tests mới bao gồm: valid/abstain output, sai schema/field/type/duplicate key/NaN/fence/ID/oversize, prompt byte limit, mock trace/provenance, no evidence skip, input invalid, provider timeout/error/no retry, invalid raw retention, partial context, concurrent isolation/cross-request IDs, prompt data boundary/caller mutation, deterministic repeat, live opt-in/config, HTTP wire contract/no redirect/error/truncation/tool output, subprocess JSON/text CLI và exclusive output.

Tất cả HTTP tests dùng mocked opener, không server ngoài. Test prompt injection chỉ chứng minh dữ liệu vẫn nằm ở data message và output không sửa state; chưa chứng minh model thật chống được injection. Test đúng schema không chứng minh đúng luật. T1–T5/T6.1 được chạy hồi quy; freeze/evaluate chỉ thuộc fixture synthetic đã có, không chạy benchmark trên nhãn T5 thật.

Demo xuất sau khi tests PASS, không dùng D01–D08 để tune:

| Demo | Kết quả | Evidence | Generation / live LLM |
|---|---|---:|---:|
| “đối thoại định kỳ”, top3 | DRAFT_UNVERIFIED | 29 | 1 mock / 0 |
| OOV “zzzzqqqnotincorpus” | NO_EVIDENCE | 0 | 0 / 0 |

Một lần đo local trong draft trace: retrieval 2,491ms, evidence 6,010ms, prompt 1,778ms, mock generation 0,380ms, structured output 0,054ms. Không gồm load index/process startup, không SLA hoặc phân bố latency. Draft JSON 396.093 bytes do trace/provenance đầy đủ. Hash/bytes/code/index/snapshot của demo nằm trong manifest. Raw LLM live output, latency, cost và chất lượng live đều **chưa có**. Không Recall/MRR hoặc quality score mới.

## F. Bàn giao học cùng ChatGPT

> Tôi làm AI Core Tillegal. T6 mới chỉ Basic RAG, không Citation Verification. T1–T4 và T6.1 dùng dữ liệu thử nghiệm, T5 chưa human-approved gold. Pipeline BM25 → Evidence Builder → generation → draft/candidate citations/trace chạy bằng mock; 138 tests PASS. Gửi kèm ai_core/basic_rag.py, rag_generation.py, rag_cli.py, evidence_builder.py, tests/test_basic_rag.py và báo cáo này. Hãy giải thích interface provider, structured output vs semantic correctness, request-local state, nguồn UNVERIFIED và citation ứng viên, cách debug trace và giới hạn của mock. Mock chỉ trích quote; live adapter chưa gọi LLM thật. Không diễn giải test PASS thành chất lượng pháp lý hoặc tự đề xuất triển khai agent ngay.

## G. Kiểm tra hiểu biết

1. Vì sao một draft đúng schema và chỉ dùng IDs hợp lệ vẫn có thể sai?
2. Trường hợp nào trả NO_EVIDENCE, ABSTAINED_UNVERIFIED hoặc FAILED?
3. Trace cho biết lỗi thuộc retrieval, generation hay structured output bằng cách nào?
4. Khi cùng EvidenceBuilder phục vụ hai requests, vì sao không giữ draft/evidence hiện tại trong instance mutable state?
5. Tại sao mock E2E PASS chưa chứng minh live adapter tương thích hoặc câu trả lời có ích?

Phỏng vấn: bạn thiết kế interface để đổi LLM provider mà không viết lại retrieval như thế nào? Bạn đo và debug baseline trước khi quyết định thêm multi-agent bằng bằng chứng gì?

## H. Đề xuất sau T6 — chưa triển khai

Task tiếp theo đề xuất là **T7 Evaluation & Error Analysis**: người dùng duyệt gold/relevant units trước khi freeze/evaluate; giữ policy T5 và pin corpus/index/prompt/model/config. Đo retrieval riêng với draft quality/candidate citation quality; thử live có kiểm soát sau khi chốt provider/budget. Phân loại lỗi retrieval/context/generation/schema để quyết định thay đổi nào thực sự cần.

Sau evaluation, đề xuất task Citation Verification riêng: deterministic integrity rồi semantic claim–evidence checks, test riêng và giữ nguồn/hiệu lực độc lập. Sau khi có dữ liệu lỗi và module contracts, mới đề xuất L-MARS với query/judge/re-search khi có lợi ích đo được. Chưa chốt số task cho hai phần này, chưa xây agents/API/backend hoặc triển khai T7/T8. **Dừng sau T6 Basic RAG.**
