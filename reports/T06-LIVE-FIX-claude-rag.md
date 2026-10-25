# T6-LIVE-FIX — Live Basic RAG với structured JSON

Ngày25/10/2026. **Đã đạt mục tiêu technical E2E với Claude thật: 2 draft trả lời +1 abstention hợp lệ.** Không Citation Verification, T7 Evaluation hoặc L-MARS. Nguồn vẫn QUARANTINE/UNVERIFIED/UNKNOWN; trạng thái học chưa được người dùng xác nhận.

## A. Kết quả nghiệm thu

| Request | Kết quả | Evidence / candidate citations | Input / output tokens | Latency¹ | Ước tính USD |
|---|---|---:|---:|---:|---:|
|001 — trách nhiệm tổ chức đối thoại định kỳ|DRAFT_UNVERIFIED|23 /6|7.327 /785|9,905s|0,022504|
|002 — đối thoại định kỳ tổ chức như thế nào|DRAFT_UNVERIFIED|19 /8|6.759 /892|9,731s|0,022438|
|003 — khái niệm và mục đích đối thoại|ABSTAINED_UNVERIFIED|6 /0|3.246 /148|3,027s|0,007972|

¹ Đo từ adapter, bao gồm count_tokens preflight và generation, không gồm retrieval/index load. Không phải SLA/p95.

3 generation requests, 3 token-count requests miễn phí; không retry/batch/tools/web search. Ba generation trả HTTP200/end_turn, không truncation. Tổng17.332 input +1.825 output tokens; cache0. **Ước tính$0,052914**, dưới$0,30. 3/3 technical successes không đồng nghĩa3 câu trả lời hữu ích: request003 abstain vì context thiếu. Không benchmark hoặc legal approval.

Artifacts riêng: [run-config](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-live-fix-claude-v1/run-config.json>), [manifest](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-live-fix-claude-v1/manifest.json>), [request001](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-live-fix-claude-v1/request-001.json>), [request002](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-live-fix-claude-v1/request-002.json>), [request003](<D:/DOWNLOAD/Ligalli Illigal/data/demos/t6-live-fix-claude-v1/request-003.json>). Giữ nguyên toàn bộ live/mock artifacts cũ.

## B. Sửa gì và vì sao

| File | Thay đổi |
|---|---|
|[rag_generation.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/rag_generation.py>)|DRAFT_OUTPUT_SCHEMA, promptv2, compact document/warnings/group metadata|
|[anthropic_provider.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/anthropic_provider.py>)|Provider schema option, max2.048 tokens, optional count_tokens gate và telemetry|
|[rag_cli.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/rag_cli.py>)|Flags --structured-output và --input-token-cap|
|[test_live_fix.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_live_fix.py>)|7 tests mới cho context/schema/fence/truncation/budget/abstain/isolation|
|[smoke_claude_live_fix.py](<D:/DOWNLOAD/Ligalli Illigal/scripts/smoke_claude_live_fix.py>)|3 câu tuần tự, budget gate, output riêng, dừng khi lỗi; không retry|

Cập nhật hợp đồng03 mục2.9 và CHECKPOINT; không sửa BM25, Evidence Builder, parser hoặc dữ liệu/nhãn cũ. Hash66/69 file có trước task không đổi;3 file thay đổi là các module T6 trong bảng. Không sửa test cũ hoặc expectation để pass.

Anthropic liệt kê Sonnet5 hỗ trợ `output_config.format` JSON Schema. Schema provider khai đúng ba trường draft_answer/candidate_evidence_ids/abstain, required và additionalProperties=false. Validator local vẫn kiểm nonblank/types/membership/duplicate IDs/duplicate JSON keys/abstain consistency. Provider schema không thay semantic verification. [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).

Không dùng fallback bóc fence vì model hiện tại hỗ trợ structured output. Test tiếp tục từ chối cả một fence JSON hợp lệ, JSON bị cắt và duplicate keys. Nếu provider từ chối/max_tokens, pipeline không nhận draft kể cả text tình cờ parse được. Không bù JSON, thêm citation hoặc thay đổi outcome sai thành verified.

Case003 cũ chỉ chứng minh stop_reason=max_tokens với1.024 output tokens; partial text bị mất ở phiên bản lúc đó, nên **không thể khẳng định nguyên nhân chi tiết model đã viết gì**. Hạn chế thiết kế quan sát được: không có target độ dài draft, prompt lặp nhiều document/warnings/context IDs, và không ràng buộc JSON phía provider. FIX xử lý cả ba, tăng cap2.048. Đây không phải thí nghiệm ablation chứng minh riêng thay đổi nào gây thành công.

Context compact giữ nguyên từng quote/evidence ID và thứ tự, gom metadata document một lần theo D1/D2, gom warnings chung một lần. Điều/Khoản/Điểm/scope/form/appendix chỉ là structure_candidate. Không rút ngắn text, bỏ điều kiện hoặc cắt ngoại lệ. Hash/locator/ancestry/rank/score/omitted IDs vẫn đầy đủ trong bundle/trace local, không lặp vào prompt khi không giúp generation.

Đối chiếu trên bundle cũ: messages case002 giảm10.802→5.997 bytes; case003 giảm38.169→16.178 bytes. Quote lists bằng nhau hoàn toàn. Group omission count và cảnh báo context vẫn gửi model. ASSEMBLED chỉ nghĩa đủ cửa sổ đã chọn, không bảo đảm đã mở hết dẫn chiếu pháp lý.

## C. Luồng, budget và bảo mật

BM25 một lượt → T6.1 nguyên trạng → compact prompt → count_tokens → gate input → Claude một lượt với provider schema → local schema/ID validator → draft/candidate citations +trace.

Giữ model `claude-sonnet-5`, thinking disabled; không tìm model mới hoặc thay global environment. Giá chuẩn$2/triệu input và$10/triệu output được đối chiếu. [Model và giá](https://platform.claude.com/docs/en/models/sonnet-5/overview).

Count API dùng cùng model/system/messages/thinking/output_config, bỏ các trường generation max_tokens/stream. Chặn nếu count>12.000; output cap2.048; JSON request body cap40.000 bytes; evidence24 chunks/8.000chars/top3 như smoke trước. Không giảm evidence budget hoặc cắt quote để vừa token cap: vượt thì dừng. Token counting miễn phí, nhưng là estimate; dùng reserve input gấp đôi và output đạt trần: `(24.000×2 +2.048×10)/1e6=$0,06848/lượt`; ba lượt$0,20544<$0,30. [Token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting).

Body JSON thực tế16.775/14.865/6.594 bytes. Count preflight bằng input usage trả về ở cả3 lượt. Actual estimate `(17.332×2 +1.825×10)/1e6=$0,052914`; không phải hóa đơn, chưa thuế/chiết khấu. Reserve không phải thay đổi billing limit phía Anthropic; là gate kỹ thuật cho đợt thử theo giá công bố. Dừng script nếu response/error/usage không cho phép tiếp tục kiểm soát chi phí.

Key chỉ từ environment, endpoint Anthropic cố định, proxy/redirect bị tắt. Không hiển thị/ghi key, không đọc config cá nhân, không đưa key vào prompt, không mua credit. Script chạy ngoài sandbox vì đã xác định DNS sandbox không hoạt động ở đợt trước; không lặp lại lỗi DNS hoặc bypass TLS. Không automation, không agent phụ.

## D. Demo và review thủ công

**Request001:** “Người sử dụng lao động cần thực hiện những việc gì để tổ chức đối thoại định kỳ tại nơi làm việc?”

Bản nháp Claude thật, chưa verified:

> Theo dữ liệu, để tổ chức đối thoại định kỳ tại nơi làm việc (ít nhất 1 năm/lần theo Điều 63.2.a BLLĐ), người sử dụng lao động cần: (1) Phối hợp với tổ chức đại diện người lao động tại cơ sở hoặc nhóm đại diện đối thoại của người lao động để tổ chức đối thoại; (2) Cùng bên kia thống nhất thời gian, địa điểm, cách thức tổ chức phù hợp điều kiện thực tế và quy chế dân chủ ở cơ sở; (3) Chậm nhất 5 ngày làm việc trước khi đối thoại, gửi nội dung đối thoại cho bên tham gia; (4) Đảm bảo khi tiến hành đối thoại có sự tham gia của người đại diện theo pháp luật (hoặc người được ủy quyền) và trên 70% tổng số thành viên đại diện người lao động; lập biên bản ghi diễn biến, có chữ ký các bên; (5) Chậm nhất 3 ngày làm việc sau khi kết thúc đối thoại, công bố công khai tại nơi làm việc các nội dung chính của đối thoại. Ngoài ra, cần ban hành và phổ biến quy chế dân chủ ở cơ sở quy định các nội dung đối thoại này.

6 candidate citations trỏ vào Khoản1–5 Điều39 Nghị định145/2020/NĐ-CP và Điểm a Khoản2 Điều63 Bộ luật45/2019/QH14. Mỗi citation trong JSON giữ canonical evidence/chunk/document version IDs, exact quote, hash, locators và warnings. Ví dụ claim thời hạn5 ngày tham chiếu candidate `evidence:8c8c2b7eee2cfee91e86e336466e13c88a5b9020a826520026e39f26cfafd85e`, quote “Chậm nhất 05 ngày làm việc trước ngày bắt đầu tổ chức đối thoại định kỳ…” trong bundle. Đây là quan sát liên quan nội dung, không kết quả citation verifier.

Review thủ công: câu trả lời đúng trọng tâm tổ chức đối thoại theo context gửi, có các mốc và điều kiện chính. Tuy nhiên câu cuối về ban hành/phổ biến quy chế có context Điều48 nhưng model không chọn candidate Điều48; citation coverage theo từng claim chưa đầy đủ. Cụm “chữ ký các bên” rút gọn yêu cầu cụ thể về chữ ký trong quote Khoản4. Không kết luận nguồn còn hiệu lực hoặc mọi chi tiết pháp lý đều đúng.

**Request002:** “Đối thoại tại nơi làm việc được tổ chức định kỳ như thế nào?” Trả draft với8 candidate citations, nhắc tần suất, chuẩn bị, điều kiện tiến hành và công bố. Review thủ công: nội dung có vẻ liên quan; cách viết “thành phần … theo quy chế dân chủ cơ sở” đơn giản hóa nguồn ghi rõ dẫn chiếu Khoản3 Điều38. Điều38 chưa được mở trong bundle này; không thể coi context đã đầy đủ thành phần. Các trường hợp đối thoại khác được nhắc khái quát nhưng chưa mapping từng claim với citation.

**Request003:** “Đối thoại tại nơi làm việc là gì và nhằm mục đích gì?” Context6 evidence chỉ heading, không body Điều. Model trả:

> Evidence chỉ cung cấp các tiêu đề chương/mục (như 'Đối thoại tại nơi làm việc', Chương V, Mục 1) mà không có nội dung điều khoản cụ thể, nên không đủ căn cứ để trả lời khái niệm và mục đích đối thoại tại nơi làm việc.

Abstain=true, candidate list rỗng, đúng schema. Đây là technical success và phản ứng phù hợp với context thiếu, **không chứng minh chatbot trả lời hữu ích câu này**. Không sửa retrieval hoặc ép model nhớ luật bên ngoài.

Giới hạn chung: soft target180 từ chưa đạt nếu đếm whitespace —001 có203,002 có224 đơn vị, lần lượt910/1.022 ký tự. Hard token cap đạt và không truncation. Source statuses vẫn chưa xác minh; semantic support, citation correctness, temporal/legal validity chưa được đánh giá chính thức. Chỉ3 câu cùng chủ đề, không bộ gold hoặc benchmark.

## E. Tests và chạy lại

Targeted: `python -B -m unittest discover -s tests -p test_live_fix.py -q` →7/7 PASS. Full suite cuối: `python -B -m unittest discover -s tests -q` →**157/157 PASS trong26,068s**, không skip. Includes150 tests cũ; không sửa chúng. Tests mới kiểm nguyên quotes/warnings/version, fence/duplicate-key/truncated JSON, provider schema/count cùng content, input gate không generation, max_tokens fail-closed dù JSON parse được, abstention/request usage isolation và reserve dưới budget.

Mock HTTP tests hoàn toàn offline. Live artifacts là response Claude thật, độc lập mock output. 3 requests mới đã dùng hết; không chạy lại lệnh live trong đợt này. Cho một đợt mới được duyệt, lệnh reproducible là:

```powershell
python -B -m scripts.smoke_claude_live_fix --allow-live --output data/demos/TEN-THU-MUC-MOI
```

Script chỉ tạo thư mục mới; tồn tại thì không chạy generation. Giá pin ngày25/10/2026 cần kiểm lại trước đợt tương lai. CLI một câu có các flags `--provider anthropic --mode live --allow-live --model claude-sonnet-5 --anthropic-thinking disabled --structured-output --input-token-cap 12000 --max-output-tokens 2048 --max-input-bytes 40000`; script thêm giới hạn số requests/tổng reserve cho cả đợt.

## F. Hướng dẫn đọc code và bàn giao

Đọc `generation_messages` trước để thấy projection LLM vs bundle local; tiếp theo `DRAFT_OUTPUT_SCHEMA` và `validate_draft` để phân biệt provider constraints với local validation. Sau đó đọc `AnthropicProvider.generate`: count gate → HTTP generation → stop_reason → text/usage. Cuối cùng đọc smoke script để thấy điều kiện dừng và cost reserve. Không cần đọc lại parser/BM25.

> Tillegal T6-LIVE-FIX dùng Sonnet5 JSON Schema phía provider và prompt compact. 157 tests PASS;3 live technical successes gồm2 drafts và1 abstention, cost estimate$0,052914. Gửi rag_generation.py, anthropic_provider.py, rag_cli.py, test_live_fix.py, smoke_claude_live_fix.py và báo cáo này. Hãy giải thích constrained output vs semantic correctness, giữ quote nhưng gộp metadata, preflight token gate và budget reserve, trace đầy đủ, abstention khi heading-only. Không giả định citations hoặc pháp luật đã được verified.

## G. Kiểm tra hiểu biết

1. Vì sao JSON Schema thành công vẫn cần ID-membership và duplicate-key checks local?
2. Gộp document metadata khác gì cắt context pháp lý?
3. Vì sao abstention có thể là technical success nhưng chưa là câu trả lời hữu ích?
4. Vì sao count_tokens và actual usage cần ghi riêng dù lần này bằng nhau?
5. Vì sao không bỏ validate stop_reason khi text trả về có vẻ là JSON hợp lệ?

Phỏng vấn: bạn làm thế nào để một lần smoke thất bại trở thành thay đổi có test và bằng chứng? Bạn sẽ dùng trace hiện tại để xây evaluation/citation verification sau này như thế nào mà không tuyên bố sớm về chất lượng?

## H. Đề xuất tiếp theo — chưa triển khai

Đề xuất T7 Evaluation & Error Analysis sau khi người dùng phê duyệt nhãn human-reviewed: tách retrieval, context sufficiency, draft usefulness và citation coverage. Giữ case heading-only/citation coverage thiếu làm ứng viên phân tích lỗi, không tự đưa vào gold. Citation Verification và L-MARS vẫn cần phê duyệt riêng. **Dừng sau T6-LIVE-FIX; không gọi live thêm.**
