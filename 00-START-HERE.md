# Legal AI: bộ thiết kế và bàn giao Codex

Ngày lập: 14/10/2026. Phạm vi: một người học và triển khai phần AI/data/retrieval/evaluation; nhóm khác làm web. Đây là thiết kế đề xuất để triển khai, **chưa phải hệ thống đã chạy và chưa có kết quả benchmark**.

## Điều cần hiểu trước tiên

Project 1 là hệ thống hỏi đáp: câu hỏi → tìm luật → viết câu trả lời có nguồn. Project 9 là bộ kiểm tra: câu trả lời → tách từng khẳng định → tìm đúng nguồn được trích → kiểm tra nguồn có hỗ trợ khẳng định không. Xây Project 9 thành module độc lập, rồi dùng chính module đó để hậu kiểm câu trả lời Project 1.

RAG không tự huấn luyện lại model. Nó tìm tài liệu và đưa tài liệu đó vào đầu vào của model lúc trả lời. Agent trong thiết kế này là một module có nhiệm vụ, dữ liệu vào/ra và giới hạn rõ ràng; không nhất thiết là một model riêng, một máy chủ riêng hay một cuộc trò chuyện giữa các AI.

Bạn chưa cần hiểu mọi thư viện để bắt đầu. Mục tiêu mỗi buổi là tự trả lời được: bước này làm gì, nhận gì, trả gì, dữ liệu nằm đâu, vì sao chọn cách này, làm sao biết nó sai và sửa ở đâu. Một dự án không bảo đảm thành thạo mọi kỹ năng ngay lập tức; bộ này biến mong muốn đó thành các năng lực kiểm tra được.

## Đọc theo thứ tự

1. `01-REQUIREMENTS-AND-AUDIT.md`: việc bắt buộc, xung đột tài liệu, điều kế thừa từ paper.
2. `02-SYSTEM-BLUEPRINT.md`: sơ đồ, hai luồng chạy, trách nhiệm từng module.
3. `03-STATE-AND-CONTRACTS.md`: dữ liệu và state, ai được sửa trường nào, điều kiện dừng.
4. `04-DATA-PLAN.md`: quyết định dataset và pipeline dữ liệu.
5. `05-EVALUATION-AND-TESTING.md`: tạo nhãn đúng, công thức, bài thực hành và kiểm thử lỗi.
6. `06-LEARNING-AND-IMPLEMENTATION.md`: thứ tự triển khai, đầu ra và điều kiện hoàn thành từng mốc.
7. `07-CODEX-PROMPT.md`: prompt dán vào phiên Codex mới.

Các sơ đồ dùng Mermaid, xem được trong trình đọc Markdown hỗ trợ Mermaid. Không có sơ đồ nào hàm ý chức năng đã triển khai.

## Giao gì cho Codex?

Giải nén toàn bộ thư mục này vào `docs/ai-handoff/` của repository làm việc. Đặt 11 PDF đã gửi vào `project_sources/`, giữ tên tương ứng trong `SOURCE-MAP.md`. Dán nguyên nội dung `07-CODEX-PROMPT.md` vào chat Codex.

Hai file nguồn bắt buộc phải có: `02-Legal_AI_P3_Ten_Projects.pdf` và `01-Paper-L-MARS.pdf`. Nên đưa cả 11 PDF vì hợp đồng tích hợp còn nằm trong tài liệu nhóm. Nếu giới hạn upload, ưu tiên thêm Document 7, Document 8, Document 6, Document 1; tải các file còn lại sau. Không upload API key, `.env`, tài khoản thật hoặc hội thoại có thông tin riêng tư. Nếu đã có code, cho Codex quyền đọc đúng repository hiện tại để tránh tạo dự án trùng.

Không cần tải toàn bộ Hugging Face về trước. Không cần bắt đầu bằng Docker, LangGraph hoặc fine-tuning. Không cần giao FE/BE cho Codex ở nhiệm vụ này. API mỏng của AI Service là ranh giới tích hợp thuộc phần AI; backend nghiệp vụ .NET vẫn ngoài phạm vi.

## Lần đầu Codex phải làm gì?

Đọc nguồn → lập bảng yêu cầu và mâu thuẫn → dạy bản đồ hệ thống qua một ví dụ giả lập → kiểm kê môi trường và repository → hoàn thiện hợp đồng → chạy bài tập state với fake provider. Dừng tại mốc học đầu tiên; chưa viết toàn bộ hệ thống, chưa gọi API tính tiền hay tải kho dữ liệu lớn.

Bạn tự kiểm tra mình đã hiểu bằng ba câu:

- Tại sao tìm thấy luật liên quan chưa đủ để nói citation đúng?
- Nếu người dùng trích Điều 3 sai nhưng Điều 8 đúng, kết quả đối với citation gốc là gì?
- Nếu model lỗi hoặc tìm kiếm hết lượt, chương trình dừng ở đâu và trả trạng thái gì?

Không trả lời được thì yêu cầu Codex diễn giải lại bằng dữ liệu mẫu, không yêu cầu nó viết thêm agent.

## Việc đã làm và chưa làm

Đã đối chiếu yêu cầu Project 1/9 và yêu cầu chung của Ten Projects; đọc phương pháp, audit và giới hạn trong paper; rà soát những phần liên quan đến AI/data/evaluation của bộ tài liệu nhóm; kiểm tra dataset card/viewer hiện có; thiết kế hợp đồng, luồng, điều kiện dừng, đánh giá và prompt.

Chưa tải/audit toàn bộ corpus, chưa kiểm chứng hiệu lực từng văn bản, chưa cài hệ thống, chưa chọn model bằng benchmark, chưa tạo gold labels thực, chưa chạy test/benchmark của sản phẩm. Không được biến mục tiêu thành kết quả trong README hoặc CV.
