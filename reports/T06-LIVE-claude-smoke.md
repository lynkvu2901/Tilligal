# T6-LIVE — Claude Messages API và controlled smoke

Ngày 25/10/2026. Phê duyệt mới nhất cho phép tự chọn model/runtime và tối đa 3 generation requests. **Adapter đã tích hợp; đã nhận hai response Anthropic thật; chưa đạt live Basic RAG E2E.** Không T7, Citation Verification hoặc L-MARS. Trạng thái học chưa được người dùng xác nhận.

## A. Kết quả thực tế

| Attempt | Kết quả | Input/output tokens | Provider latency | Ước tính USD |
|---|---|---:|---:|---:|
| 001 | DNS sandbox thất bại trước HTTP; ANTHROPIC_NETWORK_ERROR | chưa có usage | 108,3ms đến lỗi | không có phí generation quan sát được |
| 002 | HTTP200/end_turn; JSON bị bọc Markdown → INVALID_OUTPUT | 5.774 / 371 | 5.241,2ms | 0,015258 |
| 003 | HTTP200; stop_reason=max_tokens → ANTHROPIC_INCOMPLETE_OR_REFUSED | 19.848 / 1.024 | 10.200,4ms | 0,049936 |

**Tổng: 3 attempts, 2 HTTP200, 0 live RAG E2E success.** Giữ nguyên lỗi và validator; không làm đẹp kết quả bằng cách sửa output. Không tự retry; không vượt 3 attempts. Câu hỏi 002 và 003 là hai request độc lập, không retry câu 001. Sau lỗi DNS, chỉ kiểm DNS/TCP/TLS không credential; ngoài sandbox kết nối đạt. Hai generation sau chạy ngoài sandbox tới endpoint Anthropic cố định.

150/150 tests cuối PASS (12 mới + 138 hồi quy), 21,482s, không skip. Mock tests chứng minh logic tích hợp và lỗi; không chứng minh live quality. T1–T5/T6.1 và nhãn evaluation không thay đổi.

## B. File và Messages API

| File | Thay đổi |
|---|---|
| [anthropic_provider.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/anthropic_provider.py>) | Provider Messages API mới, validation response/errors/usage, không proxy/redirect/retry |
| [rag_generation.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/rag_generation.py>) | Thêm GenerationText, subclass str với telemetry request-local; generation/schema contract không đổi |
| [basic_rag.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/basic_rag.py>) | Lưu metadata provider và raw text của stop-error vào trace, không dựng answer từ lỗi |
| [rag_cli.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/rag_cli.py>) | Chọn Anthropic, --model runtime, thinking mode và input-byte budget |
| [test_anthropic_provider.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_anthropic_provider.py>) | 12 tests offline về wire contract, secret handling, provider failures, trace và CLI |
| [03-STATE-AND-CONTRACTS.md](<D:/DOWNLOAD/Ligalli Illigal/03-STATE-AND-CONTRACTS.md>) | Hợp đồng 2.8 |
| [CHECKPOINT.md](<D:/DOWNLOAD/Ligalli Illigal/CHECKPOINT.md>) | Ghi live results và phần còn thiếu |

Anthropic dùng POST `https://api.anthropic.com/v1/messages`. Adapter gửi Content-Type application/json, x-api-key và anthropic-version; x-api-key vẫn được tài liệu hỗ trợ. System prompt ở trường system top-level, còn messages chứa user content. Response chứa content blocks và stop_reason/usage, không có choices[0].message.content như Chat Completions. Vì vậy không thể chỉ thay URL của adapter cũ. [API overview](https://platform.claude.com/docs/en/api/overview), [Messages API](https://platform.claude.com/docs/en/api/messages/create).

Pin API version 2026-10-21 theo tài liệu hiện hành. Không gửi tools/stream/web-search/cache-control. Chỉ ghép các text blocks; không lưu thinking/signatures. Response không end_turn không trở thành answer. HTTP401/402/403/429/504 được phân biệt với schema error ở downstream; không lấy error body có thể chứa dữ liệu nhạy cảm vào logs. [Versioning](https://platform.claude.com/docs/en/api/versioning), [Errors](https://platform.claude.com/docs/en/api/errors).

## C. Model, bảo mật và ngân sách

Đã xác minh `claude-sonnet-5` là ID Claude API, trạng thái active legacy; tài liệu nói vẫn khả dụng. Hai response thật cũng trả đúng ID này, nên không cần fallback. Đây là model smoke theo ưu tiên người dùng, chưa phải model tối ưu. Giá chuẩn đã đối chiếu: $2/triệu input tokens và $10/triệu output tokens. [Sonnet 5](https://platform.claude.com/docs/en/models/sonnet-5/overview), [Pricing](https://platform.claude.com/docs/en/about-claude/pricing).

Sonnet5 bật adaptive thinking mặc định; tài liệu cho phép `thinking={type:disabled}`. Smoke tắt thinking để dành output budget cho draft; không đặt temperature/top_p/top_k provider. `top_k=3` của CLI là số BM25 hits, không phải sampling parameter gửi Anthropic. [Thinking configuration](https://platform.claude.com/docs/en/build-with-claude/thinking).

- API key chỉ nạp từ ANTHROPIC_API_KEY; kiểm cấu hình chỉ xuất boolean có/không. Không hiện prefix/suffix/value, không yêu cầu người dùng gửi key. Không nạp .env, không tìm trong thư mục cá nhân.
- Endpoint cố định; bỏ proxy OS/environment và chặn redirect; key chỉ ở header request Anthropic, không nằm trong body/prompt, trace hoặc exception text. repr provider che key; tests dùng credential giả.
- Trước khi có quyền chọn model, preflight thấy key có nhưng ANTHROPIC_MODEL/TILLEGAL_LLM_MODEL trống. Phê duyệt mới cho phép `--model claude-sonnet-5`; không sửa environment OS.
- Caps mỗi attempt: request JSON <=40.000 bytes, output <=1.024 tokens, max24 evidence/8.000 quote chars, top3, socket timeout45s. Bytes thực tế001/002/003: 31.590 /10.886 /38.253. Không có thêm API đếm token, list-model, batch, search hoặc retry.
- Kế hoạch chi phí trước call dùng dự phòng 80.000 input tokens/request cho giới hạn40KB (ước lượng bảo thủ, không phải tokenizer chuẩn), cộng1.024 output: khoảng$0,17024/request, ba lượt khoảng$0,51072, dự phòng$0,55. Đây không phải hard billing cap; input bytes/output tokens là caps được code thực thi. Không mua credit hoặc thay billing.
- Usage thực tế hai HTTP200: 25.622 input +1.395 output, cache creation/read đều0. Theo đơn giá trên: `(25622×2 +1395×10)/1e6 = $0,065194`, chưa thuế/chiết khấu, không phải hóa đơn. Lượt DNS chưa tới HTTP và không có usage; không gán token giả.

## D. Demo thật, evidence và quan sát sơ bộ

Artifacts mới, tách khỏi mock: [manifest](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-live-claude-smoke-v1/manifest.json>), [001](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-live-claude-smoke-v1/request-001.json>), [002](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-live-claude-smoke-v1/request-002.json>), [003](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-live-claude-smoke-v1/request-003.json>). Mỗi file giữ question, retrieval hits, evidence bundle/source trace, generation input, warnings, model/usage/latency/error. 001 chỉ có context chuẩn bị, chưa gửi thành công qua HTTP. Manifest giữ hash/bytes và phân biệt code sau trace-fix với phiên bản chạy smoke.

**001:** “Đối thoại tại nơi làm việc được tổ chức định kỳ như thế nào?” Không có model response do DNS; không nhận định generation/citation quality.

**002:** “Đối thoại tại nơi làm việc là gì và nhằm mục đích gì?” Bundle có6 evidence, đều heading/đề mục như “Mục 1. ĐỐI THOẠI TẠI NƠI LÀM VIỆC”, “Chương V”; không có article ID. Model viết trong raw output: “Không đủ thông tin để trả lời câu hỏi này”, giải thích context chỉ có heading và đặt abstain=true, candidate_evidence_ids=[]. Nhận xét thủ công: lý do thiếu thông tin phù hợp với context thực gửi; chưa đủ để đánh giá model trả lời khái niệm pháp lý. Output bọc bằng ```json nên strict validator chặn. Raw đầy đủ ở trace.generation_raw; answer=null, candidate_citations=[] — không tự bóc fence rồi coi là E2E thành công.

**003:** “Người sử dụng lao động cần thực hiện những việc gì để tổ chức đối thoại định kỳ tại nơi làm việc?” Top3 hits:

1. Heading Điều39, Nghị định145/2020/NĐ-CP: “Tổ chức đối thoại định kỳ tại nơi làm việc”.
2. Khoản1 Điều48 cùng nghị định: trách nhiệm ban hành quy chế dân chủ ở cơ sở để thực hiện đối thoại và dân chủ tại nơi làm việc.
3. Khoản2 Điều63, Bộ luật45/2019/QH14: mở đầu các trường hợp người sử dụng lao động phải tổ chức đối thoại.

Bundle23 evidence, không omission trong cửa sổ được chọn, ASSEMBLED. Nhận xét thủ công: các địa chỉ/chủ đề có vẻ liên quan; chưa xác nhận completeness, relevance labels hay tính chính xác citation. Model chạm output cap, nên không có answer/candidate citations hợp lệ để đánh giá.

**Thiếu sót trace được phát hiện:** adapter lúc chạy003 kiểm stop_reason trước khi trả raw text, nên partial draft bị mất khỏi artifact; usage/stop_reason/context vẫn còn. Không thể khôi phục partial text mà không gọi lại; không gọi lượt thứ4. Đã sửa nhánh lỗi để giữ text-only partial output, test offline PASS. Không sửa artifact003 để giả lập output. Đây là giới hạn thực tế của lần smoke này.

Phân biệt kết luận:

- Technical integration: endpoint/auth/model có response thật; Basic RAG live chưa hoàn thành E2E.
- Retrieval: quan sát một trường hợp heading-only và một cửa sổ có chủ đề liên quan; không có Recall/MRR/gold mới.
- Generation: một abstention hợp lý theo context, một output bị cắt; chưa đánh giá chất lượng tổng quát.
- Citation: chưa có candidate citations hợp lệ trong hai live outputs; không thể chấm chất lượng.
- Legal correctness: chưa kiểm chứng, nguồn vẫn QUARANTINE/UNVERIFIED/UNKNOWN.

## E. Tests và hướng dẫn chạy

Targeted tests chạy trước live: `python -B -m unittest discover -s tests -p test_anthropic_provider.py -q` →12 PASS. Full regression cuối sau trace-fix: `python -B -m unittest discover -s tests -q` →**150 PASS, 21,482s**. Tests HTTP đều mocked, không tự gọi API thật. Không sửa expected/test cũ để pass.

Phủ: config/runtime model không sửa OS, wire headers/system/messages, disabled proxies/redirects, input/output caps, đa text blocks, usage missing/invalid, HTTP auth/billing/permission/rate limit/provider timeout, malformed response, secret không vào payload/metadata, stop reasons, request isolation và CLI. Trace-fix thêm assertion raw partial được giữ khi max_tokens, answer vẫn null. Mock/demo T6 cũ và T5 labels không bị thay đổi.

Lệnh mẫu cho một đợt live mới **sau khi được phê duyệt thêm**; lần này đã dùng hết3 attempts, không chạy lại:

```powershell
python -B -m ai_core.rag_cli --provider anthropic --mode live --allow-live --model claude-sonnet-5 --anthropic-thinking disabled --max-output-tokens 1024 --max-input-bytes 40000 --max-evidence-chunks 24 --max-quote-chars 8000 --top-k 3 --timeout 45 --question "Câu hỏi thử nghiệm" --format json
```

Không cần ANTHROPIC_MODEL. Key đã có thì không đổi; nếu một terminal mới thiếu key, cấu hình ANTHROPIC_API_KEY qua cơ chế environment/secret của máy rồi khởi động terminal nhận biến, không gửi key vào chat hoặc lưu vào repo. --output chỉ dùng file mới. Môi trường sandbox hiện chặn DNS; một môi trường có network trực tiếp tới Anthropic mới chạy được. Không tắt TLS hoặc thêm proxy để vượt lỗi.

## F. Hướng dẫn học và bàn giao

Đọc theo thứ tự: `AnthropicProvider.from_environment` → `generate` (map request, error paths, usage) → `GenerationText` → `BasicRAG.answer` (metadata/raw lỗi) → `rag_cli.main` → tests. API adapter chuyển giao thức, không làm verifier. Telemetry nằm trong object trả về của mỗi request, không dùng provider.last_response nên tránh trộn usage khi concurrent.

> Tôi làm Tillegal T6 Basic RAG, đã tích hợp Anthropic bằng stdlib. Gửi kèm anthropic_provider.py, rag_generation.py, basic_rag.py, rag_cli.py, test_anthropic_provider.py và báo cáo này. 150 tests PASS; smoke3 attempts có1 lỗi DNS,1 fenced JSON,1 max_tokens; chưa live E2E success. Hãy giải thích Messages API vs Chat Completions, schema vs semantic correctness, caps vs estimated cost, stop_reason, request-local telemetry và tại sao không nên sửa output để giấu lỗi baseline. Không coi draft hoặc test PASS là xác nhận luật.

## G. Kiểm tra hiểu biết

1. Vì sao HTTP200 chưa đồng nghĩa Basic RAG E2E thành công?
2. Vì sao model biết abstain vẫn có thể bị validator chặn?
3. Bytes, tokens và hóa đơn khác nhau thế nào?
4. Vì sao max_tokens phải giữ usage lẫn raw partial nhưng không dựng answer?
5. Vì sao context ASSEMBLED không chứng minh đã đủ ngoại lệ/điều kiện pháp lý?

Phỏng vấn: bạn dùng trace để phân biệt lỗi retrieval/provider/schema như thế nào? Bạn bảo vệ credential và giới hạn chi phí trong smoke test đầu tiên ra sao?

## H. Bước tiếp theo — chỉ đề xuất

Đề xuất một bước T6-LIVE-FIX riêng: dùng output format JSON/schema mà model hỗ trợ hoặc quy tắc format rõ hơn, giới hạn độ dài draft trong prompt, rồi duyệt một đợt smoke mới có ngân sách. Giữ strict validator và ghi nhận heading-only như vấn đề retrieval/context cần đánh giá sau, không tự sửa BM25/T6.1. Chưa thay prompt, không tăng token cap hoặc mở evaluation trong lượt này. Chưa triển khai T7, Citation Verification, L-MARS.
