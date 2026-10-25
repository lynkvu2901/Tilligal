# Lộ trình: học qua việc xây một lát cắt chạy được

Các mốc dưới đây là thứ tự phụ thuộc, không hứa số ngày. Nếu lịch học chỉ có ít thời gian, thu hẹp domain/corpus/optional experiments; không cắt bỏ evaluation để giữ nhiều agent.

## M0 — Đọc bản đồ và mô phỏng state

Đầu vào: bộ bàn giao, PDF nguồn, máy/repo hiện có. Đầu ra: scope.md, requirement matrix, ADR ban đầu, JSON examples, fake-provider state walkthrough. Chưa tải corpus lớn hay gọi paid API.

Codex phải dạy: request khác state thế nào; corpus khác evaluation dataset thế nào; claim/citation/evidence là gì; Query khác Verify; lỗi model khác claim sai.

Bài tự làm: chỉ từng trường thay đổi qua 5 bước của fixture DEMO-A; giải thích vì sao original_input không mất. Gate: bạn tự vẽ hai luồng và nói đúng điều kiện dừng.

## M1 — Hợp đồng và bài kiểm chứng giả lập

Đầu ra: typed schemas, validators, CLI verify fixture, source resolver giả lập, baseline rules, trace và tests. Fake provider phải ghi rõ `execution_mode=mock`; không tạo benchmark score giả. Có thể dùng 10 fixture tự viết, tất cả mang nhãn “không phải luật thật”.

Bài tự làm: đổi citation sang điều sai, làm source timeout, trả JSON lỗi, xem trace và giải thích trạng thái. Gate: input→extraction→resolution→report chạy được; errors không bị chuyển thành VERIFIED.

## M2 — Corpus thật nhỏ và annotation đầu tiên

Đầu ra: source register, dataset revision, 30-sample audit, corpus khoảng 10 văn bản đã duyệt, parser/chunks/index, 10–30 mẫu dev được người đọc nguồn gán nhãn.

Bài tự làm: lấy một raw HTML, chỉ vị trí điều/khoản trong text sau parse, đối chiếu hash và locator. Gate: trace được mỗi chunk về raw/version; record rỗng/thiếu source bị quarantine; nhãn có quote.

## M3 — Verifier thật, trọng tâm Project 9

Đầu ra: source-scoped prompt, provider adapter, semantic classifier, temporal/identity rules, eval runner V0/V1/V2. Kiểm tra extraction/linking riêng và toàn pipeline. Offline unit tests + một số live smoke khi cấu hình model sẵn sàng.

Bài tự làm: tính confusion matrix của 10 mẫu; phân tích một false acceptance và một false rejection. Gate: không có source substitution; biết precision/F1 đang dùng positive class/mẫu số gì; kết quả lưu predictions và config thật.

## M4 — Baseline hỏi đáp Project 1

Đầu ra: Query → BM25 → draft; dùng verifier M3 để tạo bản QA có hậu kiểm. Lưu cả draft lẫn final để đo tác dụng của Verify. Không cần loop ở mốc đầu.

Bài tự làm: so câu đúng kết luận nhưng citation sai với câu có căn cứ đầy đủ. Gate: toàn claim pháp lý xuất ra được trace; không thêm câu chưa verify trong final formatting.

## M5 — Hybrid và reranking

Đầu ra: dense adapter, BM25+dense fusion, reranker, retrieval evaluation. RRF là default fusion đề xuất; lựa chọn/params được đo trên dev. Ghi corpus version và model revisions.

Bài tự làm: tìm một query BM25 tốt hơn dense và một query ngược lại; đọc top5 trước/sau rerank. Gate: so sánh cùng labels, dedupe điều/khoản; không khẳng định hybrid tốt hơn nếu bảng không chứng minh.

## M6 — Evidence Judge và vòng lặp có giới hạn

Đầu ra: issue coverage checklist, gap-directed queries, max budgets, timeout/retry/no-progress handling. Adapter LangGraph chỉ xem xét sau khi Python workflow đã có tests và bạn hiểu state transition.

Bài tự làm: khiến Judge luôn INSUFFICIENT; chứng minh chương trình vẫn dừng và báo đúng stop_reason. Gate: budget tests qua; một vòng nghĩa gì được ghi rõ; draft sau sửa được verify lại.

## M7 — Sửa citation và online tùy chọn

Đầu ra: RepairProposal bất biến với verdict gốc; strict same-source re-verification; một vòng repair nằm trong ngân sách tổng. Online search chỉ khi có nhu cầu và điều kiện truy cập thực tế; corpus update staging là pipeline khác.

Bài tự làm: A sai nhưng B đúng, giải thích vì sao A vẫn sai. Gate: repair có thử nghiệm so với tắt repair; không dùng “Faith-Search” để hứa semantic correctness.

## M8 — Tích hợp, đóng gói và final evaluation

Đầu ra: API mỏng cho nhóm, OpenAPI/schema examples, môi trường tái lập, container nếu cần triển khai, error/health/logging, versioned data update và rollback, frozen test run, baseline/ablation report và failure demo.

Bài tự làm: chạy một request từ CLI/curl với nhóm backend; truy request_id ra trace; xử lý provider không hoạt động. Gate: code tests qua, report thật, target đạt/chưa đạt ghi rõ, hạn chế chuyên môn gán nhãn được công bố. Full project còn cần UI/API do nhóm ghép theo kiến trúc môn.

## Một buổi làm việc mẫu

1. Codex nêu mục tiêu nhỏ và ví dụ input/output.
2. Bạn dự đoán kết quả một ca bình thường và một ca lỗi.
3. Codex giải thích quyết định rồi code một module có thể review.
4. Cùng chạy lệnh, mở output và so assertion.
5. Bạn sửa input hoặc một logic nhỏ để gây lỗi có chủ đích.
6. Codex giải thích nguồn lỗi và ghi lại bài học; cập nhật `learning-log.md`.

Không yêu cầu bạn trả lời mọi câu hỏi mới cho chạy một lệnh nhỏ. Codex được tự xử lý chi tiết implementation thường lệ trong mốc đã giao; dừng ở ranh giới bài học để bạn theo kịp. Nếu bạn nói tiếp tục, nó tiếp tục mốc tiếp theo; không hỏi lại quyền cho việc đã cho phép.

## Tư duy kỹ sư phải thể hiện bằng hiện vật

| Năng lực | Bằng chứng bạn làm được |
|---|---|
| Chốt bài toán | Nói được input/output, scope, điều không thể xác minh |
| Thiết kế dữ liệu | Tự lần từ claim tới citation, chunk, document version, raw bytes |
| Thiết kế control flow | Tự giải thích mọi nhánh loop/timeout/budget |
| Chọn phương pháp | Có baseline và lý do từ dev results, biết khi nào bỏ phần phức tạp |
| Đánh giá | Tự gán nhãn, tính một metric, đọc FP/FN và nhận diện leakage |
| Debug | Xác định lỗi thuộc parser/retrieval/extraction/verification/routing |
| Vận hành | Reproduce run, rollback corpus, biết token/cost/latency |
| Trình bày nghiên cứu | Không phóng đại, tách hypothesis/result, báo null result và giới hạn |

## Định dạng báo cáo cuối mỗi mốc

Codex trả: mục tiêu đã hoàn thành; file thay đổi; lệnh chạy và output thật; điều đã học; lỗi/giới hạn còn lại; một bài tập nhỏ để bạn tự kiểm tra; bước tiếp theo. Nếu chưa chạy được vì thiếu key/dependency/network, ghi BLOCKED hoặc NOT_RUN, tuyệt đối không ghi PASSED.
