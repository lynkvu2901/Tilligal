# Học đánh giá và kiểm thử từ số 0

## 1. Hai câu hỏi khác nhau

**Software testing:** code có tuân thủ hợp đồng không? Ví dụ LLM timeout thì phải dừng; citation không tồn tại thì không được VERIFIED. Mock/fake providers giúp lặp lại chính xác tình huống này.

**AI evaluation:** với dữ liệu và nhãn đúng do người kiểm tra, hệ thống làm tốt đến đâu? Code hết lỗi vẫn có thể phân loại support sai. Evaluation dùng corpus thật và model thật khi có ngân sách; không gắn nhãn “benchmark đạt” cho test dùng fake.

## 2. Ba bộ dữ liệu cần xây

| Bộ | Một mẫu chứa gì? | Dùng đo gì? |
|---|---|---|
| Retrieval | question_id, question, as_of_date, relevant_document_versions, relevant_article_ids, evidence spans, review info | Recall@5, MRR, thiếu gold |
| Verification | input text, atomic claims, raw citations, links, exact cited source snapshot, gold source/identity/support/temporal labels, quotes, annotator | Extraction, resolution, support F1, detection, accepted-citation precision |
| End-to-end Q&A | question, facts, expected key points, acceptable evidence sets, unanswerable reason nếu có, rubric | Answer quality, citation correctness, hallucination, coverage |

Một bộ câu hỏi có thể có cả nhãn retrieval và rubric Q&A, nhưng development/test tách rõ. Bộ verification gồm cả đầu ra thật của baseline và lỗi tạo có kiểm soát; báo riêng điểm trên hai nhóm. Không đánh giá chỉ bằng lỗi dễ như đổi “2” thành “200”.

## 3. Làm 10 mẫu đầu tiên như thế nào?

1. Chọn 2–3 đoạn của văn bản đã audit; lưu nguồn, version và locator trước khi viết câu hỏi.
2. Với mỗi đoạn, viết claim bám sát nguồn, giữ đủ chủ thể, điều kiện, số lượng và thời điểm.
3. Viết một biến thể đổi điều kiện, số liệu hoặc dẫn nhầm điều; gán nhãn sau khi đọc nguồn, không vì “mình cố tình tạo lỗi” mà mặc định nhãn đúng.
4. Thêm một citation không resolve được và một lỗi fetch giả lập; phân biệt thiếu source với source đã đọc nhưng không hỗ trợ.
5. Ghi quote nguyên văn và lý do 1–3 câu. Không quyết định dựa vào hiểu biết bên ngoài khi đang chấm support của cited source.
6. Chạy baseline, lưu prediction ở file khác, không ghi đè gold.
7. Mở từng dòng gold/prediction và phân loại lỗi: extract, link, resolve, support, temporal, routing.
8. Tính metric bằng tay trên 10 mẫu rồi so với script. Đây là bài học kiểm tra script chấm, chưa phải kết quả cuối kỳ.

## 4. Annotation guide

- **Atomic claim:** một khẳng định có thể kiểm tra riêng. “A được X và B được Y” thường tách hai claim; điều kiện quyết định X phải đi cùng claim A.
- **SUPPORTED:** toàn bộ nội dung quan trọng được source hỗ trợ; không bỏ đối tượng, ngoại lệ, phạm vi, số lượng, điều kiện.
- **PARTIALLY_SUPPORTED:** có phần được hỗ trợ nhưng còn mệnh đề/điều kiện không đủ. Với strict detection, partial được tính là chưa hỗ trợ đầy đủ.
- **UNSUPPORTED:** source đã đọc không hỗ trợ claim, kể cả nói ngược hoặc chỉ cùng chủ đề. Lưu reason như CONTRADICTED/IRRELEVANT/NUMERIC_MISMATCH.
- **NO_CITATION:** claim cần căn cứ nhưng không có citation liên kết; chưa phải chứng minh claim sai.
- **UNRESOLVED/UNREACHABLE/VERIFIER_ERROR:** không ép thành nhãn semantic. Đo riêng operational failure.
- **Temporal/jurisdiction:** trục riêng; một nguồn có thể entail nội dung nhưng không áp dụng thời điểm/tình huống hiện tại.

Mỗi citation nguyên văn cần span, mỗi claim cần span. Citation cuối đoạn có thể nối nhiều claim; ghi quy tắc linking trước khi chấm. Multi-source claim có báo cáo tập nguồn bên cạnh từng cặp; không bỏ qua citation thừa/sai.

LLM có thể gợi ý mẫu và nhãn, nhưng người phải xác minh với nguồn. Nếu chỉ bạn gán nhãn: giấu prediction khi chấm; ghi quy trình kiểm tra lại sau một khoảng cách thời gian; công bố single-annotator limitation. Bất đồng không giải được đưa vào ambiguous, ghi tỷ lệ và không dùng làm gold semantic chắc chắn.

Mời người thứ hai gán nhãn độc lập một phần rồi adjudicate, ưu tiên người có kiến thức pháp lý cho applicability/answer score. Không gọi điểm tự chấm của sinh viên CS hay điểm LLM là “expert answer score”. Nếu chưa có expert thì báo riêng student/LLM scores và ghi hạng mục expert chưa hoàn thành.

## 5. Quy mô và split đề xuất

- Học quy trình: 10 rồi 30 cases; chỉ dùng development.
- Mốc báo cáo đề xuất: 120 câu hỏi (40 dev, 80 test) và khoảng 300 claim–citation units (100 dev, 200 test), đủ các nhóm lỗi. Con số này là kế hoạch thực tế ban đầu, không bảo đảm độ tin cậy và không phải ngưỡng giảng viên.
- Chia theo nhóm câu hỏi/nguồn mẫu/paraphrase family trước khi sinh biến thể. Các biến thể của cùng claim/câu hỏi không rơi vào hai split. Tốt hơn có thêm một held-out document family để đo khả năng tổng quát, báo riêng với in-domain test.
- Retrieval corpus có thể chứa luật cần trả lời câu hỏi test: đó là mục đích của RAG. Điều phải giữ kín là câu hỏi/nhãn test đối với tuning, prompt examples và lựa chọn cấu hình.
- Không fine-tune thì không cần giả vờ có train split. Nếu fine-tune sau này, tạo train/dev/test thật.
- Freeze test manifest và hash trước final run. Không chọn cấu hình dựa vào test rồi tiếp tục gọi kết quả đó là held-out. Nếu đã xem test để sửa, đánh dấu test đã dùng và cần tập cuối mới hoặc công bố hạn chế.

## 6. Công thức và mẫu số

**Retrieval:** đơn vị relevant chính là điều/khoản chuẩn hóa có version, không phải mỗi chunk cắt chồng lấn. Dedupe kết quả lên đơn vị này trước tính metric.

`Recall@5(q) = |top5(q) ∩ gold_relevant(q)| / |gold_relevant(q)|`.

Lấy trung bình trên các câu answerable có gold đầy đủ. Câu unanswerable đánh giá abstention riêng. `MRR = mean(1/rank_first_relevant)`, không tìm thấy thì 0. Ví dụ gold có 2 điều, top5 tìm được 1: Recall@5=0.5. Tìm relevant đầu tiên ở vị trí 2: reciprocal rank=0.5. Có nhiều nguồn thay thế hợp lệ thì annotation phải ghi equivalence groups hoặc bổ sung relevance; không phạt một đáp án đúng chỉ vì người gán nhãn bỏ sót nguồn.

P1 đặt mục tiêu vận hành Recall@5 ≥0.85 (Ten Projects ghi Top-K ≥85% và liệt kê Recall@5). Báo thêm Recall@10 nếu muốn, không dùng Recall@50 để thay Recall@5.

**Unsupported-claim detection:** positive là claim không được hỗ trợ đầy đủ bởi cited source, tức PARTIAL hoặc UNSUPPORTED trong tập semantic đã resolve và có gold; negative là SUPPORTED. Với multi-source, dùng gold claim-level đã định nghĩa. NO_CITATION có bài end-to-end detection riêng; source/error không được lẫn vào semantic F1.

`precision_bad = TP/(TP+FP)`; `recall_bad = TP/(TP+FN)`; `F1_bad = 2TP/(2TP+FP+FN)`.

Ví dụ 20 claims: 8 bad thật, model phát hiện 6; có 2 good bị báo bad. TP=6, FN=2, FP=2, TN=10 → precision=0.75, recall=0.75, F1=0.75. Chưa đạt mục tiêu 0.80.

`FPR_bad = FP/(FP+TN)` = good bị báo bad; `FNR_bad = FN/(TP+FN)` = bad bị bỏ lọt. Nếu dùng positive là supported thì tên FPR/FNR đổi ý nghĩa, vì vậy mọi bảng phải ghi positive class. Báo confusion matrix thay vì chỉ một số F1.

**Citation precision có thể bị hiểu hai cách; báo cả hai:**

1. `accepted_citation_precision = #predicted accepted citations đúng theo gold / #predicted accepted citations`. Đây là độ chính xác quyết định chấp nhận của Project 9. Mục tiêu ≥0.90, kèm acceptance coverage và false acceptance rate.
2. `output_citation_correctness = #citations đúng theo gold trong final answers / #citations được xuất trong final answers`. Đây là chất lượng citations Project 1 xuất ra; mục tiêu ≥0.90. Đúng gồm source identity + support + applicability theo scope đã định nghĩa.

Không có citation được chấp nhận/xuất thì precision là N/A, không phải 100%. Không được đạt mục tiêu bằng cách từ chối tất cả. Báo thêm `answer_coverage`, `accepted_claim_coverage`, `no_citation_rate`, và tỷ lệ core question được trả lời.

**Entailment F1:** báo per-class và macro F1 cho SUPPORTED/PARTIAL/UNSUPPORTED trên tập resolve được có gold. Đồng thời báo source-resolution accuracy và unresolved/error rate trên toàn test để không che lỗi bằng loại mẫu.

**Đo toàn pipeline P9:** chạy raw answer text qua extractor→resolver→verifier; gold claim nào bị extractor bỏ sót vẫn là một lỗi ở metric end-to-end. Nếu là bad claim bỏ sót, tính FN detection. Claim thừa hoặc link sai cũng phải ghi lỗi. Báo song song oracle-claims (để cô lập classifier) và predicted-claims (thực tế).

**Hallucination:** định nghĩa riêng `unsupported_generated_claim_rate` trên gold audit mọi factual/legal claims của bản nháp và bản cuối. Không coi một claim thiếu citation tự động là sai sự thật; báo `no_citation_rate` riêng. Đo factual wrongness nếu có gold đủ để kết luận. Không đổi tên support score thành factual accuracy.

**Answer quality:** chấm 1–5 cho đúng nội dung, đầy đủ, phù hợp tình huống, rõ ràng; cùng rubric và blind configuration. Mean paired difference phải ≥0 theo mục tiêu ≥baseline, báo phân bố/CI để thấy bất định. Thêm omission penalty/coverage để việc xóa hết claim không được xem là cải thiện chất lượng.

**Reliability/cost:** p50/p95 latency, tokens, provider calls, estimated cost với bảng giá/ngày, timeout/error rate, retries, stop reason. Báo warm/cold cache và hardware; không biến mục tiêu <10s trong tài liệu nhóm thành kết quả đã đạt.

Zero denominators: trả N/A + denominator + warning trong report; không bỏ mẫu âm thầm. Metric file cần numerator/denominator bên cạnh tỷ lệ.

## 7. Baselines và thí nghiệm

| Nhóm | Cấu hình | Mục đích |
|---|---|---|
| Retrieval | BM25; dense; hybrid; hybrid+reranker | Tách lợi ích từng bước, đáp ứng P1 |
| Verifier V0 | Resolve + rule lexical baseline | Baseline rẻ, cố ý có giới hạn entailment |
| Verifier V1 | Một prompt trực tiếp claim + cited text | So sánh với kiểm tra có cấu trúc |
| Verifier V2 | Source-scoped structured verifier + deterministic guards | Đóng góp P9 |
| QA B0 | BM25 RAG, single-pass, không hậu kiểm | Baseline tối thiểu |
| QA B1 | Hybrid+rerank, single-pass | Tách cải thiện retrieval |
| QA B2 | B1 + verifier/finalization | Tác động module P9 |
| QA B3 | B2 + Evidence Judge loop | Tác động multi-turn |
| QA B4 mở rộng | B3 + repair | Tác động repair và chi phí |

Đầu tiên so verifier V0/V1/V2 trên cùng các câu trả lời/citations cố định, để khác biệt generator không làm lệch đánh giá classifier. Sau đó so QA đầu cuối.

Giữ nguyên corpus, questions, model generator, prompt không thuộc biến thử nghiệm, context cap và schema; ghi đầy đủ yếu tố thay đổi. Với loop/repair, thêm thí nghiệm matched-budget: cùng tổng retrieval/model cap, phân biệt search rounds với backend calls. Chạy online ở audit window riêng.

Nếu có đủ mẫu, paired bootstrap theo question/document cluster, không giả định mọi claim trong cùng câu trả lời độc lập. CI rộng hoặc chồng 0 thì không kết luận chắc hệ thống tốt hơn. Tên seed, bootstrap resamples và procedure ghi trong evaluation plan. LLM-as-judge chỉ metric hỗ trợ, không sole gold cho claim đúng/sai.

## 8. Bộ kiểm thử code bắt buộc

| Ca lỗi/hành vi | Assertion cần kiểm tra |
|---|---|
| Hai evidence không liên quan | Judge không tự SUFFICIENT do count |
| Một evidence đủ | Không ép tìm thêm chỉ để đủ số lượng |
| Citation A sai, B đúng | Gốc A giữ verdict; B nằm proposal riêng |
| Source thiếu trong corpus | UNRESOLVED, không khẳng định văn bản không tồn tại |
| HTTP timeout/403 | UNREACHABLE/ERROR; không UNSUPPORTED semantic |
| LLM JSON hỏng | Schema retry trong cap; sau đó FAILED/UNVERIFIED |
| LLM trả evidence_id giả | Không nhận ID ngoài tập được cấp |
| Đổi draft sau Verify | Không tái dùng report cũ; reverify version mới |
| Thiếu ngày hiệu lực | Temporal UNKNOWN, không VERIFIED toàn phần |
| Citation có nhiều claim | Không bỏ claim thứ hai |
| Raw text có claim ngoài structured list | Extractor phát hiện hoặc coverage test báo lỗi |
| Cùng query lặp và evidence không đổi | no_progress hoặc budget stop |
| Retry và repair cùng xảy ra | Tổng calls/tokens vẫn không vượt cap |
| Đầu vào quá nhiều claims | Reject/chia batch minh bạch, không truncate silently |
| Prompt injection trong evidence | Không đổi policy/tools/budget |
| URL trỏ private IP/redirect | Fetcher chặn, không truy cập mạng nội bộ |
| Hai requests đồng thời | Không lẫn evidence, reports hoặc counters |
| Index update lỗi | Corpus active cũ vẫn dùng được |
| Citation precision mẫu số 0 | N/A, không 1.0 |
| Leak đáp án test vào index | Validation phát hiện artifact type/manifest không hợp lệ |

Lớp unit dùng fixtures; integration kiểm tra nối parser→resolver→verify; regression giữ lỗi đã sửa; live smoke chỉ ít cases cần API thật. Không gọi API trả phí trong unit tests.

## 9. Báo cáo và demo

Mỗi run cần config/revisions, dataset split/hash, environment, predictions nguyên bản, metrics với denominators, error slices, latency/cost, limitations. Không ghi kết quả giả. Demo ít nhất: câu hỏi có nguồn và report, một citation có thật nhưng không hỗ trợ claim, và một ca không đủ evidence/timeout. Chứng minh hệ thống biết giới hạn của mình.

Khi gửi kết quả cho mentor: cung cấp test command + output thật, 5–10 prediction rows có gold và source quotes, một trace fail, manifest cấu hình. Có các hiện vật này mới phân biệt lỗi dữ liệu, extraction, retrieval, prompt hay orchestration; screenshot “bot trả lời hay” không đủ.
