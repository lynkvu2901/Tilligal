# Yêu cầu, phạm vi và đối chiếu tài liệu

## Phạm vi chốt cho phần AI

Tên làm việc: Tillegal AI Core. Hai chế độ dùng chung thư viện kiểm chứng:

- `answer_question`: nền Project 1, trả lời có evidence và hậu kiểm.
- `verify_citations`: trọng tâm Project 9, nhận một câu trả lời/văn bản có citations, giữ nguyên bản gốc và trả báo cáo kiểm chứng từng claim–citation.

MVP nghiên cứu trong một phạm vi hẹp. Mặc định đề xuất: câu hỏi về hợp đồng lao động, giới hạn corpus và thời điểm đã kiểm tra. Đây là lựa chọn làm dự án, không phải khẳng định đã xác minh các luật hiện hành. Nếu nhóm đã có domain khác, thay scope bằng ADR trước khi gán nhãn. Không ôm mọi ngành luật; không xây chức năng tư vấn tình huống phức tạp riêng ở giai đoạn đầu.

## Ma trận truy vết bắt buộc

| ID nội bộ | Nguồn | Yêu cầu | Hiện vật/kiểm chứng dự kiến |
|---|---|---|---|
| P1-01 | S2 tr.4 | Query processing | QueryPlan + test bảo toàn câu hỏi và thiếu dữ kiện |
| P1-02 | S2 tr.4 | Hybrid BM25 + dense | Hai retriever + fusion; bảng BM25/dense/hybrid |
| P1-03 | S2 tr.4 | Reranking → context | Reranker có bật/tắt; so sánh hybrid có/không rerank |
| P1-04 | S2 tr.4 | LLM + citation | Draft có định danh evidence; không bịa URL |
| P1-05 | S2 tr.4 | Top-K recall ≥85%; đánh giá Recall@5, MRR | Chốt vận hành Recall@5 ≥0.85, đồng thời báo K khác; ghi rõ đây là cách cụ thể hóa K |
| P1-06 | S2 tr.4 | Citation correctness ≥90% | Gold audit các citation được xuất + coverage |
| P1-07 | S2 tr.4 | Answer quality ≥ baseline | Chấm ẩn tên cấu hình, cùng bộ câu hỏi; expert answer score, hallucination rate |
| P9-01 | S2 tr.12 | Claim extraction | Atomic claims + span; bộ nhãn để đo bỏ sót/tách sai |
| P9-02 | S2 tr.12 | Citation extraction | Citation nguyên văn + claim links + locator |
| P9-03 | S2 tr.12 | Source retrieval | Resolve đúng văn bản/điều/khoản/phiên bản, không thay bằng nguồn bất kỳ |
| P9-04 | S2 tr.12 | Entailment/support classifier | Nhãn + quote + lý do ngắn theo từng cặp |
| P9-05 | S2 tr.12 | Citation precision ≥90% | Đo cả precision của quyết định chấp nhận citation và độ đúng citations đầu ra, công thức ở file 05 |
| P9-06 | S2 tr.12 | Unsupported-claim detection F1 ≥0.80 | Nhãn gold, positive class cố định, confusion matrix |
| P9-07 | S2 tr.12 | Citation correctness, entailment F1, FPR/FNR | Báo cáo riêng semantic, resolution, hệ thống đầu cuối |
| G-01 | S2 tr.17 | Evaluation dataset riêng, provenance, ground truth, annotation, split | Dataset card + annotation guide + frozen manifest |
| G-02 | S2 tr.18 | Ít nhất một baseline | Có baseline cho retrieval, verifier và Q&A |
| G-03 | S2 tr.19 | Evaluation plan trước khi hoàn tất hệ thống | File 05 được khóa phiên bản trước final test |
| G-04 | S2 tr.20 | Demo có real input, evidence, failure và evaluation | Kịch bản thành công + citation sai + dependency lỗi |
| G-05 | S2 tr.14,21 | Project R&D: research question, giả thuyết, thực nghiệm, phân tích | Ablation và error analysis, kể cả kết quả không cải thiện |
| G-06 | S2 tr.16 | UI/API/application/retrieval/KB/LLM/logging-evaluation | AI core bàn giao API cho nhóm web; không tuyên bố hoàn thành toàn project khi mới có CLI |

Ngưỡng là mục tiêu phải đo, không phải số có thể viết sẵn vào kết quả. Nếu không đạt thì báo chưa đạt và phân tích. Ten Projects không quy định Project 9 phải có 500 câu; con số ≥500 thuộc Project 8. Quy mô đề xuất trong file 05 không phải yêu cầu của giảng viên.

## Những điểm cần sửa hoặc làm rõ trong tài liệu nhóm

| Quan sát | Căn cứ | Quyết định bàn giao |
|---|---|---|
| “Độ chính xác pháp lý tuyệt đối” không phải cam kết kiểm chứng được bằng dự án này | S3 tr.1 | Thay bằng metric, giới hạn phạm vi, uncertainty và failure cases |
| Bảng sprint vừa xoay quanh extraction→verification vừa xoay quanh Query→Judge; ranh giới Judge/Verify dễ lẫn | S3 tr.2,5–6 | Một verifier độc lập làm trung tâm; Evidence Judge chỉ kiểm tra đủ tài liệu trước draft |
| Recall@5 ≥80%, verification F1 ≥78% trong sprint thấp hơn ngưỡng môn cuối kỳ | S3 tr.5–6 so với S2 | Chỉ dùng làm checkpoint nội bộ, không thay chuẩn cuối kỳ |
| Hybrid/reranker còn được coi là lựa chọn mở | S10 tr.12–13,31 | Triển khai và đánh giá cả hybrid và reranker theo P1; kết quả kém vẫn phải báo trung thực |
| Một số đoạn viện dẫn bộ đánh giá “đã có” | S4 tr.24–25; tình trạng người dùng cung cấp | Yêu cầu hiện vật thật; nếu chưa có thì lập mới, không giả định tồn tại |
| Tên “Faith-Search / Citation Verifier” có lúc gộp, các phần sau tách | S9 tr.13 so với tr.26–27 | Verify quyết định nhãn; RepairSearch chỉ đề xuất evidence mới |
| 10 tuần và 8 tuần không đồng nhất | S3 tr.1, S10 tr.23 | Dùng milestones theo năng lực/đầu ra; nhóm tự ánh xạ vào deadline thật |
| Cập nhật dữ liệu ngày một lần | S8 tr.16 | Backlog có pipeline cập nhật theo phiên bản; không cho agent trả lời tự sửa corpus |

Điểm tốt cần giữ: S9 tr.25 đã phân biệt SUFFICIENT với VERIFIED; S9 tr.27 yêu cầu orchestrator sở hữu state; S10 tr.14–15 yêu cầu giữ verdict citation gốc và kiểm tra lại nguồn thay thế. Không cần viết lại toàn bộ tài liệu nhóm.

## Kế thừa L-MARS có chọn lọc

| Thành phần paper | Cách áp dụng |
|---|---|
| Query, Search, Judge, Summary; shared state; search–judge loop | Giữ phân vai, schema và loop hữu hạn; triển khai Python rõ ràng trước |
| Judge checklist: factual, jurisdiction, temporal, contradiction | Dùng checklist theo từng issue và evidence IDs; không dùng số lượng tài liệu để kết luận đủ |
| Post-draft atomic-claim audit | Module độc lập Verify, nhiệm vụ chính Project 9 |
| Verifier chỉ đọc nguồn đang được trích | Giữ nguyên; không đưa toàn bộ retrieval pool để “cứu” một citation sai |
| Sáu nhãn audit | Lưu nhãn gần paper bên cạnh source/identity/temporal statuses; không ép mọi lỗi thành unsupported |
| Faith-Search sửa URL không truy cập được | Chức năng mở rộng có ngân sách, sau verifier ổn định; sửa lỗi support rộng hơn phải gọi là biến thể của nhóm |
| Cross-provider evaluation | Thử khi ngân sách cho phép; gold phải có kiểm tra của người, không lấy đồng thuận LLM làm sự thật |
| Web search/CourtListener | Web là backend tùy chọn; không nhập CourtListener vào bài luật Việt Nam chỉ vì paper dùng |

S1 tr.6–8 báo cáo loop đa lượt cải thiện citation F1 trong thí nghiệm của họ, nhưng Faith-Search không cho cải thiện F1 có ý nghĩa thống kê so với loop trên mẫu đó. Human stress test cũng không đạt gate tác giả đặt. Vì vậy không dùng paper làm bằng chứng rằng một verifier LLM chắc chắn đúng.

Nhận xét về “black box”: framework không tự làm mất kiểm soát. Quyền sở hữu state, routing, schema, budgets và trace mới quyết định khả năng kiểm tra. Temperature=0 và seed cũng không bảo đảm mọi API model trả byte giống hệt; replay fixture giúp kiểm thử logic điều phối, live rerun dùng để đo biến động.

## Câu hỏi nghiên cứu

RQ1: Verifier tách source resolution, support và applicability có phát hiện claim chưa được hỗ trợ tốt hơn baseline đơn giản trên tập tiếng Việt của nhóm không?

RQ2: Gắn verifier vào Project 1 thay đổi citation correctness, tỷ lệ trả lời có ích, hallucination, latency và chi phí như thế nào?

RQ3 (mở rộng): Evidence Judge đa lượt hoặc repair có đem lại cải thiện đáng kể so với một lượt trong cùng ngân sách không?

Đóng góp dự kiến: tập claim–citation–evidence được gán nhãn có quy trình; verifier truy vết được; thí nghiệm và error analysis. Chưa tuyên bố là thuật toán mới hoặc tốt hơn paper.
