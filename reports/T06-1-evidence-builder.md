# T6.1 — Evidence Builder tối thiểu

Ngày 25/10/2026. Phê duyệt riêng T6.1 theo chiến lược baseline-first. Hoàn thành kỹ thuật bước này; chưa generation, verifier, final answer hoặc CLI E2E. Trạng thái học chưa được người dùng xác nhận. T5 chưa human-approved gold.

## A. Mục tiêu và kết quả

Chuyển kết quả BM25 T4 thành evidence có định danh, context giới hạn và provenance để các bước generation/verification sau dùng cùng nguồn. Không gọi LLM/search trong builder, không thay dữ liệu hay thuật toán cũ.

- Code: [evidence_builder.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/evidence_builder.py>).
- Tests: [test_evidence_builder.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_evidence_builder.py>).
- 17 test mới và 100 test cũ: **117/117 PASS**, không skip.
- Giữ nguyên SHA-256 của 49 file cũ trong ai_core/tests/scripts/data/reports, gồm raw, T1–T5, index và nhãn T5. Không xuất lại artifact cũ; evidence smoke chỉ ở RAM.
- Pin index `bm25:2a751dc020052aed315bd56ac49b92c734e632db94b1f4241d18e273640117ed`, processed schema 2, snapshot `8040db1bfeddb99b93e8937a1c35e634de198a703286318d459d80e90987bfb7`.

## B. Thay đổi và lý do

Tạo hai file trên; bổ sung hợp đồng mục 2.6 ở [03-STATE-AND-CONTRACTS.md](<D:/DOWNLOAD/Ligalli Illigal/03-STATE-AND-CONTRACTS.md>) và cập nhật [CHECKPOINT.md](<D:/DOWNLOAD/Ligalli Illigal/CHECKPOINT.md>). Không sửa module/test T1–T5; không thư viện mới.

Một evidence tương ứng một chunk nguyên vẹn: không ghép nhiều đoạn thành quote giả hoặc đổi source trace. Giữ toàn document metadata, chunk, ancestry; thêm quote/hash, article ID ứng viên, locator tường minh và warnings. Trùng context được dedupe theo chunk; từng hit vẫn có nhóm riêng giữ rank/score và vai trò context.

Builder dùng public `index.to_dict()`, tránh phụ thuộc private API của BM25. Code production phải nạp index bằng `load_index` để kiểm hash/manifest. Response khác index/snapshot, chunk bị sửa, score không hữu hạn hoặc status được nâng trái phép bị chặn bằng ContractError. Không tính lại BM25 score, không kiểm relevance.

Context chọn đơn giản, chưa tune: giữ seed trước, rồi fragment cùng block, ancestor heading cùng scope, body cùng Điều ứng viên theo thứ tự nguồn. Khóa là ID/version/scope/form, không phải nhãn Điều. HEURISTIC vẫn được context ứng viên; REVIEW_REQUIRED/quoted không tự mở article-body. Mỗi evidence giữ trạng thái riêng, không coi trạng thái seed là trạng thái cả nhóm.

Mặc định 32 chunk/24.000 ký tự quote duy nhất. Không cắt quote để vừa budget. Cửa sổ bị thiếu ghi `omitted_chunk_ids`, kể cả khi seed không vừa. `ASSEMBLED` chỉ nghĩa đóng gói xong cửa sổ đã chọn; `PARTIAL` có omission; `EMPTY` không chứa evidence. Mọi nhóm vẫn `context_sufficiency=NOT_EVALUATED`.

Các giới hạn còn tồn tại:

- Context cùng Điều chưa bảo đảm chứa ngoại lệ/dẫn chiếu ở Điều hoặc văn bản khác; parent heuristic có thể sai. Không tự bổ sung dữ liệu còn thiếu.
- Chọn context theo thứ tự nguồn có thể ưu tiên đoạn xa seed khi Điều dài; không có reranker hoặc phân bổ công bằng giữa nhóm. Omissions được công khai để downstream không giả định đầy đủ.
- Quote là normalized chunk text, raw locator bao toàn block; normalized offset không được áp trực tiếp lên raw HTML. Hash không chứng minh pháp luật đúng hoặc hiệu lực hiện tại.
- Bảng/ảnh/heading/quoted/nguồn nghi thiếu vẫn là dữ liệu cần review; chưa diễn giải topology/OCR hoặc nội dung luật.
- Budget ký tự chỉ tính quote, không tính metadata/JSON và không tương đương token của provider. Bước generation cần kiểm giới hạn prompt riêng.
- Index được copy vào RAM; chưa tối ưu memory/streaming. Không benchmark chất lượng, không verifier; bundle hash không phải chữ ký xác thực. Downstream phải giới hạn evidence IDs trong bundle request hiện tại.

## C. Luồng hoạt động

```python
from ai_core.bm25_retrieval import load_index
from ai_core.evidence_builder import EvidenceBuilder

index = load_index('data/indexes/labor-pilot-3-t4-bm25/manifest.json')
retrieval = index.search('đối thoại định kỳ', top_k=3)  # một retrieval bên ngoài builder
bundle = EvidenceBuilder(index).build(retrieval, request_id='t61-local-smoke')
```

Input response → kiểm origin/content → giữ seed → tìm context trong index có sẵn → áp budget/dedupe → evidence + groups + omissions + trace + bundle hash. Không có lượt search mới.

Ví dụ synthetic: seed “1. Người giữ mèo được nghỉ.” được bổ sung heading và “2. Trừ trường hợp khẩn cấp.” trong cùng Điều. Budget chỉ một chunk thì ngoại lệ nằm trong omission và status PARTIAL. Test này chứng minh giữ/ghi nhận thiếu context, **chưa chứng minh phát hiện claim bỏ sót ngoại lệ**; phần đó thuộc semantic verification sau.

`evidence_id` hash builder version/index/chunk/text hash; ổn định giữa request dùng cùng nguồn. `bundle_id` hash toàn bundle trừ chính ID, bao request/query/budget. Latency không nằm trong bundle để kết quả tái lập được. Trace builder ghi search_calls=0/llm_calls=0; không phải tổng số lượt search của toàn pipeline.

## D. Hướng dẫn đọc code

1. [bm25_retrieval.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/bm25_retrieval.py>): `load_index`, `BM25Index.search`, `to_dict` — đầu vào có provenance ở đâu.
2. [evidence_builder.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/evidence_builder.py>): `EvidenceBudget`, `_validate_retrieval`, `build` — kiểm input, giữ seed, giới hạn output và nhánh lỗi.
3. Cùng file: `_window_key`, `_candidates` — tránh ghép nhầm version/scope/mẫu; `_evidence` — quote/locator/status/hash.
4. [test_evidence_builder.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_evidence_builder.py>): test ngoại lệ/budget, tampering và request isolation; sau đó ba integration tests pinned.

Cần hiểu ngay: định danh khác nhãn Điều; quote khác raw span; technical integrity khác semantic support; bản sao tránh lẫn request. Có thể học sau: tối ưu RAM, tokenizer budget, context ranking.

## E. Bằng chứng kiểm thử

Đã chạy:

```text
python -B -m unittest discover -s tests -p test_evidence_builder.py -v
17 tests, 1.291s, OK
python -B -m unittest discover -s tests -v
117 tests, 18.530s, OK
```

14 tests synthetic: context ngoại lệ, heading→body, fragments/Unicode, budget, ưu tiên seed/dedupe, empty/OOV, HEURISTIC/REVIEW_REQUIRED, bảng/ảnh/cảnh báo nguồn, tách version, tamper origin/quote/hash/locator/approval/rank/score, chunk thiếu, tính tái lập/JSON, request concurrency/caller mutation, cấu hình sai. Ba integration tests: smoke riêng, kiểm cửa sổ của toàn bộ 3.085 seed không vượt version/scope/form/article, giữ annotation nguồn nghi thiếu.

Smoke kỹ thuật riêng “đối thoại định kỳ”, top3, request_id `t61-local-smoke`: 29 evidence, 4.665 ký tự quote, 28 STRUCTURAL + 1 HEURISTIC, ASSEMBLED, omission mỗi nhóm [0,0,0]. Bundle ID `bundle:66f0b95bcbdead51f833bec9e21385aa3c0b796d9ec4213626853ae3d39e6aa8`. Một phép đo local: khởi tạo builder 153,924ms, build 5,707ms; không tính load index/search vào build, không phải p95/SLA hoặc benchmark relevance. Không dùng D01–D08 để tune; không đo Recall/MRR.

Hash trước/sau của 49 file cũ khớp. Không LLM mock hoặc LLM thật; toàn bộ là kiểm kỹ thuật deterministic và index local. Tests claim unsupported/omitted exception/provider timeout/schema generation chưa thuộc T6.1, sẽ làm ở bước tương ứng. Không có lỗi test đang mở; các giới hạn context ở mục B chưa được giải quyết bằng kiểm thử này.

## F. Bàn giao để học cùng ChatGPT

> Tôi đang làm Tillegal, T6.1 Evidence Builder, sau T4 BM25 và T5 chưa có human-approved gold. Gửi kèm ai_core/evidence_builder.py, ai_core/bm25_retrieval.py, tests/test_evidence_builder.py và mục 2.6 của 03-STATE-AND-CONTRACTS.md. Builder nhận response BM25, giữ nguyên chunks/provenance, bổ sung context có budget và cảnh báo. 17 test mới + 100 cũ PASS; không LLM/semantic verification. Hãy giải thích evidence ID so với article label, normalized/raw offsets, seed/context/dedupe, ASSEMBLED so với đủ căn cứ pháp lý, và vì sao request-local output quan trọng. Context same-article còn có thể thiếu dẫn chiếu/ngoại lệ; chưa có kết quả chất lượng pháp lý. Không giả định các test đã chứng minh semantic support.

## G. Kiểm tra hiểu biết

1. Vì sao hai Điều cùng số trong hai mẫu không được gom chung context?
2. Vì sao `article_id` tồn tại nhưng `exact_citation_verified` vẫn false?
3. Nếu quote dài hơn budget, builder trả gì và downstream cần lưu ý gì?
4. Vì sao không dùng normalized offsets để cắt raw HTML?
5. Ngoại lệ có mặt trong bundle đã chứng minh claim xử lý đúng ngoại lệ chưa?

Phỏng vấn: thiết kế provenance có thể debug từ answer về nguồn như thế nào? Bạn chứng minh request isolation bằng test gì và phép kiểm đó chưa chứng minh điều gì về chất lượng pháp lý?

## H. Bước tiếp theo — chờ phê duyệt

Đề xuất **T6.2 — Generation adapter một lượt**: nhận question + evidence bundle → structured claims và evidence IDs; provider interface dễ thay, kiểm schema/ID/budget, xử lý timeout/provider error, deterministic mock tests. Không final answer chưa qua verification, không retry search. Cần chốt provider/model/budget trước thử LLM thật; mock và live phải báo riêng. Chưa triển khai T6.2. Dừng tại T6.1 theo yêu cầu người dùng.
