# T5 — Chuẩn bị nhãn retrieval và công cụ đánh giá

Ngày 25/10/2026 (Asia/Saigon). Phê duyệt: “tiếp tục T5”, theo bước tiếp theo tại báo cáo T4. **Phần kỹ thuật đã triển khai; phần gold và benchmark chưa hoàn tất, chờ người review nguồn.** Không chuyển sang T6 hoặc Citation Verification. Trạng thái học chưa được người dùng xác nhận.

## A. Mục tiêu và kết quả

Đã tạo gói 12 câu ứng viên từ nguồn local, công cụ kiểm nhãn/freeze/evaluate và test công thức. Không dùng nhãn AI làm gold. Không chạy BM25 trên 12 câu T5 trước khi người review chốt nhãn; không tune hoặc sửa T4.

- [Gói review dễ đọc](<D:/DOWNLOAD/Ligalli Illigal/data/annotations/t5-retrieval-review-v1/REVIEW.md>): 8 dev, 4 test dự kiến; quote và context 11 Điều của 3 văn bản.
- [Dataset draft](<D:/DOWNLOAD/Ligalli Illigal/data/annotations/t5-retrieval-review-v1/dataset.draft.json>): toàn bộ PENDING_HUMAN_REVIEW, relevant_units=[], reviewer_id=null, answerability=UNKNOWN.
- [Source context](<D:/DOWNLOAD/Ligalli Illigal/data/annotations/t5-retrieval-review-v1/source_context.jsonl>): metadata, chunks cùng Điều ứng viên và raw excerpts; [manifest](<D:/DOWNLOAD/Ligalli Illigal/data/annotations/t5-retrieval-review-v1/manifest.json>) pin hash/bytes.
- [Readiness dev](<D:/DOWNLOAD/Ligalli Illigal/data/evaluation/t5-readiness-dev/readiness.json>) / [test](<D:/DOWNLOAD/Ligalli Illigal/data/evaluation/t5-readiness-test/readiness.json>): NEEDS_HUMAN_REVIEW, metrics=null, predictions_generated=false.
- **100/100 test đạt**: 13 T5 mới + 87 cũ, không skip. Hash 39 file trước T5 không đổi; không dependency/API mới.

Snapshot vẫn `8040db1bfeddb99b93e8937a1c35e634de198a703286318d459d80e90987bfb7`; index vẫn `bm25:2a751dc020052aed315bd56ac49b92c734e632db94b1f4241d18e273640117ed`. SHA-256 draft: `8d5f0d048e5779dc6df9646502e6e5e3725747711bf0699cb3809ab829557e49`. Chưa có frozen gold hoặc Recall/MRR trên corpus thật.

## B. Thay đổi và quyết định

| File | Vai trò |
|---|---|
| [ai_core/retrieval_evaluation.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/retrieval_evaluation.py>) | Lookup đơn vị chấm, validator nhãn, readiness, freeze và evaluator |
| [scripts/prepare_retrieval_review.py](<D:/DOWNLOAD/Ligalli Illigal/scripts/prepare_retrieval_review.py>) | Chọn source trước, tạo draft/context; không search và không cấp review |
| [tests/test_retrieval_evaluation.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_retrieval_evaluation.py>) | Test công thức, gates, split, provenance, lưu/nạp, pilot draft |
| [03-STATE-AND-CONTRACTS.md](<D:/DOWNLOAD/Ligalli Illigal/03-STATE-AND-CONTRACTS.md>) | Hợp đồng T5 tại mục 2.5 |
| [CHECKPOINT.md](<D:/DOWNLOAD/Ligalli Illigal/CHECKPOINT.md>) | Ghi trạng thái kỹ thuật và phần cần người review |

Theo tài liệu 05, primary retrieval unit cần là Điều/Khoản có version, không đếm nhiều chunk như nhiều luật liên quan. T5 chọn **Điều** để có baseline nhỏ và dễ review. Policy `article-discovery-strict-v1` không giải quyết đầy đủ evidence và không thay thiết kế BM25.

- Lấy tối đa 100 chunk bằng API T4 hiện có. Map hit STRUCTURAL ngoài quoted, không nghi thiếu nguồn, có ancestor Điều → `(document_version_id, article_node_id)`.
- HEURISTIC, REVIEW_REQUIRED, quoted, thiếu Điều hoặc nguồn nghi thiếu → unit unresolved-block. Unit này vẫn chiếm rank nhưng không được credit đúng Điều. Dedupe giữ lần xuất hiện đầu, không loại các slot khó để nâng điểm.
- Main/form cùng số Điều hoặc văn bản khác có ID riêng. Heading được tính là tìm được vị trí Điều, **không phải đã lấy đủ nội dung**. Bảng/ảnh vẫn giữ hạn chế evidence của T4.
- Báo Recall@5/@10 và **MRR@5/@10** giới hạn trong 100 chunk đầu. Macro mean trên các case answerable được người review chấp nhận; denominator Recall là số Điều relevant đã kiểm tra đầy đủ. Không gọi đây là MRR toàn ranking hoặc chunk Recall@5.
- Quy tắc bảo thủ có thể bỏ credit của đoạn heuristic thực ra đúng. Đây là giới hạn được công bố trước khi có điểm, không tune theo kết quả. Người review cần hiểu endpoint này khi chốt bộ nhãn.

Chọn 8 dev/4 test dự kiến theo family và Điều nguồn; câu D05/D08 cùng Điều 3 nằm chung dev, hai câu thử việc cùng family nằm chung dev. Không có family/Điều giao splits theo validator. Test là **PROVISIONAL_NOT_INDEPENDENT_HELD_OUT**: cùng corpus đã biết, câu hỏi do AI soạn gần nguồn, chưa đại diện người dùng thật và chưa được reviewer độc lập xác nhận. Không tuyên bố khả năng tổng quát.

## C. Luồng và việc cần người review

Index/source đã pin → chọn đoạn nguồn → viết câu hỏi dự thảo → xuất quote/context không có prediction → người đọc kiểm tra/sửa nhãn → freeze split → chạy BM25/evaluate → predictions và report tách khỏi nhãn.

Các nhóm dev: lương/thời gian thử việc, giờ làm, nghỉ tuần, địa điểm hợp đồng, bí mật kinh doanh, nguồn thiếu và tiết chưa resolve. Test dự kiến: nhiều hợp đồng, trả lương bình đẳng, báo trước chấm dứt, nội quy văn bản. Đây là ứng viên; chưa tự kết luận tập relevant đầy đủ.

Hai ca chẩn đoán cần đặc biệt thận trọng:

- **D07**, record 152668/Điều 49: source text “Hội đồng tiền lương quốc gia do” có SOURCE_TEXT_POSSIBLY_INCOMPLETE. Không tự khôi phục; người review có thể đánh dấu AMBIGUOUS/EXCLUDED_HUMAN kèm lý do.
- **D08**, record 146696/Điều 3: tiết b1) có SUBPOINT_NOT_RESOLVED. Unit ứng viên chỉ là Điều; chưa xác nhận địa chỉ tiết. Cần raw và các đoạn xung quanh.

Để hoàn tất nhãn dev, bạn/người review thực hiện:

1. Đọc [REVIEW.md](<D:/DOWNLOAD/Ligalli Illigal/data/annotations/t5-retrieval-review-v1/REVIEW.md>) từ D01 đến D08 cùng phần context; raw_blocks nằm trong source_context.jsonl. Chưa xem BM25 predictions.
2. Tạo bản sao dataset draft ở thư mục review riêng. Kiểm tra câu hỏi, ngoại lệ, mapping Điều và mọi nguồn thay thế trong snapshot; sửa proposed/relevant units, quote và câu hỏi nếu cần. Đề xuất hiện có không chứng minh đầy đủ.
3. Với mẫu đủ căn cứ, điền relevant_units, ANSWERABLE, ACCEPTED_HUMAN, reviewer_type=human, reviewer_id thật, reviewed_at ISO có múi giờ, notes và năm cờ review sau khi thực sự kiểm tra. Mỗi relevant unit phải có evidence exact quote/trace.
4. Với mẫu chưa thể chấm, dùng EXCLUDED_HUMAN và lý do, relevant_units=[]; không ép nguồn thiếu thành đáp án đúng/sai. Các ca loại được báo riêng, không âm thầm bỏ khỏi denominator.

Một mẫu pending trong dev chặn toàn bộ dev; test pending không chặn freeze dev. Cờ review là **khai báo do người dùng cung cấp**, không phải hệ thống xác thực reviewer. Không có chức năng AI tự duyệt hoặc lệnh batch approve. Approval relevance cũng không đổi QUARANTINE/UNVERIFIED/UNKNOWN của corpus.

## D. Hướng dẫn đọc và lệnh

Đọc `EvaluationCorpus.article_for/ranked_units` → `score_units` → `validate_dataset/readiness` → `freeze_dataset/evaluate`. Sau đó đọc `SPECS` và `prepare` trong script chuẩn bị. Hiểu ngay unit, dedupe, cutoff, denominator, gold completeness và leakage; học confidence interval hoặc benchmark lớn sau khi có nhãn thật.

Đã chạy:

```powershell
python -B -m unittest discover -s tests -p 'test_*.py' -q
python -B scripts/prepare_retrieval_review.py --index-manifest data/indexes/labor-pilot-3-t4-bm25/manifest.json --output-dir data/annotations/t5-retrieval-review-v1
python -B -m ai_core.retrieval_evaluation inspect --dataset data/annotations/t5-retrieval-review-v1/dataset.draft.json --index-manifest data/indexes/labor-pilot-3-t4-bm25/manifest.json --split dev --output-dir data/evaluation/t5-readiness-dev
python -B -m ai_core.retrieval_evaluation inspect --dataset data/annotations/t5-retrieval-review-v1/dataset.draft.json --index-manifest data/indexes/labor-pilot-3-t4-bm25/manifest.json --split test --output-dir data/evaluation/t5-readiness-test
```

Các output này đã tồn tại, không ghi đè. Sau khi **người review hoàn tất bản nhãn riêng**, các lệnh sau mới áp dụng; **chưa chạy trên gold thật**:

```powershell
python -B -m ai_core.retrieval_evaluation freeze --dataset data/annotations/t5-human-review/dataset.reviewed.json --index-manifest data/indexes/labor-pilot-3-t4-bm25/manifest.json --split dev --output-dir data/evaluation/t5-dev-frozen-v1
python -B -m ai_core.retrieval_evaluation evaluate --frozen-manifest data/evaluation/t5-dev-frozen-v1/manifest.json --index-manifest data/indexes/labor-pilot-3-t4-bm25/manifest.json --output-dir data/evaluation/t5-dev-run-v1
```

Path reviewed ở ví dụ chưa tồn tại. Freeze pin toàn bộ nội dung dataset, policy, index và code trước retrieval; evaluate chỉ chạy split đã freeze. Thay nhãn/index/code yêu cầu freeze hoặc review lại, không vá hash artifact cũ. Mỗi lần đo ra thư mục mới; output path sai/đã có bị chặn trước search. Chưa có UI hoặc hệ thống quản lý annotation.

## E. Kiểm thử và điều chưa được chứng minh

Lần hồi quy cuối: **100 tests trong 14,393 giây, PASS, không skip**. 13 test T5 kiểm:

- Recall/RR tính tay, cutoff, empty ranking, không double count; macro mean đúng denominator, case loại không biến thành miss.
- Dedupe heading/body cùng Điều; scope main/form và version khác không nhập; quote/attachment chưa chắc chắn giữ slot bất định.
- Query trùng, family/Điều giao split; quote/hash/Unicode offsets/locator/index/snapshot/policy sai đều bị chặn.
- Nhãn thiếu người review, thiếu completeness/kiểm tra nguồn thay thế hoặc predictions_hidden=false không freeze được; kể cả sửa lại hash draft vẫn không vượt review gate.
- Synthetic freeze/evaluate không chạy câu test khi chọn dev; không ghi đè/đổi nhãn gốc. Mọi “reviewer” trong fixtures đều ghi rõ SYNTHETIC_TEST_ID_NOT_REAL_REVIEW, không phải phê duyệt dữ liệu luật.
- Pilot preparation tạo đúng 12 draft/11 Điều, giữ flag D07/D08 và source trace; patch search thành lỗi vẫn prepare được, chứng minh không lấy BM25 prediction để soạn pack.

Một test mới lúc phát triển giả định sai rằng query `mèo` luôn cho article unit ở rank 1. BM25 thực tế có thể trả heuristic trước, nên MRR macro là 0,25 thay vì kỳ vọng 0,5. Đã sửa **fixture kiểm tra phép trung bình** để dùng ranking giả lập xác định (một rank-1 hit và một miss), giữ nguyên expected 0,5 và policy/code ranking. Test riêng vẫn kiểm slot heuristic trước relevant. Không sửa baseline hoặc test cũ để né failure.

CLI thử freeze bản draft thật đã bị chặn với `cannot freeze: NEEDS_HUMAN_REVIEW`; output probe không được tạo. Gói đã đọc lại kiểm hash/bytes, raw excerpts phát lại đúng source content T2; 39 file cũ giữ nguyên hash, không còn fixture tạm. Không có predictions/metrics T5 thật. Các phép tính trên synthetic chỉ chứng minh evaluator, không chứng minh BM25 tốt.

Giới hạn còn lại: chưa có người xác nhận relevance/coverage; parser context có thể sai; code chỉ kiểm tính nhất quán quote/ID, không hiểu đủ nghĩa/ngoại lệ. Chưa đo abstention cho unanswerable, chưa equivalence groups/đánh giá đủ evidence, chưa adjudication nhiều người, chưa confidence interval. Test split chưa độc lập; benchmark sau này vẫn chỉ áp dụng corpus tạm đã pin.

## F. Bàn giao học cùng ChatGPT

```text
Tôi phụ trách RAG/AI Core Tillegal. T5 chuẩn bị 12 câu retrieval draft (8 dev/4 test
dự kiến) từ 11 Điều trên index BM25 T4/T3-FIX. Chưa có gold người review, không
chạy predictions T5; metrics null. 100 tests đạt, 13 mới.
Policy đo tìm đúng Điều có document version/node ID: top100 chunks, dedupe,
hit STRUCTURAL ngoài quoted mới map; bất định giữ slot unresolved. Heading tìm
đúng vị trí không đồng nghĩa đủ evidence. Recall@5/@10 và MRR@5/@10 chỉ sau review.
Giúp tôi hiểu denominator, cutoff, leakage, blind annotation, freeze hash và
vì sao test công thức không phải benchmark AI. Không tự xác nhận reviewer cho tôi.
Gửi reports/T05-retrieval-annotation-and-evaluation.md, ai_core/retrieval_evaluation.py,
scripts/prepare_retrieval_review.py, tests/test_retrieval_evaluation.py,
dataset.draft.json, REVIEW.md và mục 2.5 tài liệu hợp đồng. Raw context có trong
source_context.jsonl; không cần toàn bộ Parquet. T4 vẫn nguyên, chưa verifier.
```

## G. Kiểm tra hiểu biết

1. Top5 chunk và top5 Điều sau dedupe khác nhau thế nào? Vì sao cần ghi pool=100?
2. Vì sao một heading đúng Điều vẫn không đủ làm bằng chứng trả lời?
3. Nếu chỉ tìm thấy một trong hai Điều relevant, Recall và RR phụ thuộc những gì?
4. Vì sao nhãn AI có quote đúng vẫn chưa được dùng làm gold? Ai kiểm phần nguồn thay thế còn thiếu?
5. Vì sao không xóa kết quả REVIEW_REQUIRED rồi đánh lại rank để làm metric đẹp hơn?

Phỏng vấn: mô tả một pipeline evaluation có freeze/trace và chống leakage; giải thích vì sao 100 test pass nhưng chưa được báo Recall@5 của hệ thống.

## H. Bước tiếp theo

**Hoàn tất phần human review 8 mẫu dev của T5, rồi freeze và chạy evaluation dev.** Đây là việc còn thiếu của T5, không phải chuyển sang task khác. Người review có thể sửa/loại mẫu với lý do; không yêu cầu duyệt tất cả. Chưa chạy test split hoặc tune BM25. Không tự triển khai T6; chờ bản nhãn có xác nhận người đọc nguồn.
