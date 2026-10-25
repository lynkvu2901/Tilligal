# T4 — BM25 retrieval baseline

Ngày 25/10/2026 (Asia/Saigon). T4 được phê duyệt và hoàn thành về kỹ thuật. Người dùng chưa xác nhận đã hiểu phần học. Dừng sau T4.

## A. Mục tiêu và kết quả

Đã có build/save/load/query BM25 local trên **3 văn bản, 3.085 chunk T3-FIX**, processed schema 2. Không thay T1/T2/T3/T3-FIX, không kích hoạt corpus pháp lý, không gọi API hoặc cài dependency.

- Input: [manifest T3-FIX](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3-t3-fix/manifest.json>), snapshot `8040db1bfeddb99b93e8937a1c35e634de198a703286318d459d80e90987bfb7`.
- Output: [manifest index](<D:/DOWNLOAD/Ligalli Illigal/data/indexes/labor-pilot-3-t4-bm25/manifest.json>), [index.json](<D:/DOWNLOAD/Ligalli Illigal/data/indexes/labor-pilot-3-t4-bm25/index.json>).
- Index ID: `bm25:2a751dc020052aed315bd56ac49b92c734e632db94b1f4241d18e273640117ed`.
- Payload 6.796.161 byte, SHA-256 `0e2fbd8cc6457a42e34f0a5b3129010af57b6a55bbe59f223a6c6586ed7e16c1`.
- **87/87 test đạt**, gồm 18 test T4 mới + 69 test trước; không skip. Rebuild payload giống hệt, kết quả truy vấn lặp giống hệt ngoài latency.
- [Summary đo kỹ thuật](<D:/DOWNLOAD/Ligalli Illigal/data/evaluation/t4-bm25-technical-smoke/summary.json>) và [8 mẫu kết quả đầy đủ](<D:/DOWNLOAD/Ligalli Illigal/data/evaluation/t4-bm25-technical-smoke/samples.jsonl>). Chưa có golden dataset: **Recall@K/MRR = null**, chưa tuyên bố chất lượng retrieval.

## B. Thay đổi, quyết định và giới hạn

| File | Vai trò |
|---|---|
| [ai_core/bm25_retrieval.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/bm25_retrieval.py>) | Gate input, tokenizer, inverted index (từ → danh sách chunk/tần suất), BM25, metadata/cautions, CLI |
| [tests/test_bm25_retrieval.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_bm25_retrieval.py>) | Unit, negative, integration và reproducibility tests |
| [scripts/measure_bm25_baseline.py](<D:/DOWNLOAD/Ligalli Illigal/scripts/measure_bm25_baseline.py>) | Smoke/latency offline có pin snapshot/config; không gán nhãn relevance |
| [03-STATE-AND-CONTRACTS.md](<D:/DOWNLOAD/Ligalli Illigal/03-STATE-AND-CONTRACTS.md>) | Hợp đồng T4, mục 2.4 |
| [CHECKPOINT.md](<D:/DOWNLOAD/Ligalli Illigal/CHECKPOINT.md>) | Trạng thái và điểm dừng |

**Tokenization:** NFC + casefold; giữ dấu, số, từ phủ định; tách theo dấu câu/whitespace/underscore. “hợp đồng lao động” → `hợp, đồng, lao, động`. Đây là token âm tiết, không phải bộ tách từ tiếng Việt. Dùng stdlib để không thêm model/dependency. Không bỏ stopword, stemming hoặc bỏ dấu; query không dấu có thể không tìm được từ có dấu. Số hiệu `45/2019/QH14` thành ba token, chưa phải citation resolver. Chỉ tìm trên chunk.text; metadata không được nối vào text hoặc boost.

**BM25:** với N là số chunk, df(t) số chunk chứa token, tf là tần suất trong chunk, dl là số token và avgdl là độ dài trung bình:

```text
idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
score(q,d) = Σ idf(t) × tf(t,d) × (k1+1)
                      / (tf(t,d) + k1 × (1-b + b × dl/avgdl))
```

Tổng chạy trên các token query phân biệt có trong index. k1=1.2, b=0.75 là lựa chọn ban đầu, chưa tune. IDF dương, không trả chunk có score 0 để bù K. Score bằng nhau sắp chunk_id; thứ tự cộng token cố định. Payload canonical JSON không có timestamp ngẫu nhiên. Tính lặp lại được kiểm tra trong cùng runtime; tokenizer pin Unicode 16.0.0, manifest pin Python/code. Không hứa bit-identical score giữa mọi nền tảng toán học.

**Inventory:** 1.557 token phân biệt, 96.422 token tổng. Giữ cả 42 chunk không có token để không mất inventory: 39 dòng chấm/gạch trống và 3 marker ảnh. Chúng không có postings nên không thể thắng lexical search; vẫn nằm trong N và avgdl. Đây là quy tắc baseline công khai, chưa tối ưu theo benchmark. Mọi scope/form/table được giữ; không dedupe text khác nguồn hay tự ưu tiên văn bản.

**Địa chỉ/evidence:** 2.271 STRUCTURAL → RULE_BASED_UNVERIFIED; 702 HEURISTIC → HEURISTIC_CANDIDATE; 112 REVIEW_REQUIRED giữ tên trạng thái. Tất cả hit có `exact_citation_verified=false`, `legal_evidence_status=NOT_EVALUATED`; không chuyển thành VERIFIED. Chunk và document metadata giữ nguyên, gồm raw_ref, null URL/thời điểm, hashes, scope, offsets và mọi issue. Bảng cần layout nguồn, ảnh chưa OCR, quoted là context bên ngoài; fragment/tiết chưa resolve/nguồn nghi thiếu nội dung đều có cautions. Context refs chưa tự mở rộng body điều/khoản.

**Giới hạn:** bag-of-words không hiểu nghĩa/phủ định dù giữ token; chưa có word segmentation, synonym, fuzzy/không dấu, phrase search, field weighting, metadata filter hoặc resolver. Chunk ngắn/heading/form có thể đứng cao. Index nạp toàn bộ RAM và load tính lại thống kê để kiểm tra; phù hợp pilot, chưa đo RAM hoặc throughput/concurrency trên kho lớn. Export không ghi đè; lỗi I/O giữa chừng có thể để thư mục thiếu manifest, không có resume. Hash phát hiện thay đổi, không chứng minh tính đúng pháp lý hay xác thực nhà cung cấp.

## C. Luồng hoạt động và ví dụ thực tế

Manifest T3-FIX + expected snapshot → kiểm hash/bytes/schema/code và T2 → validate_result từng document → giữ chunks/nodes/metadata → tokenize text → postings/lengths → lưu index và manifest riêng. Query → cùng tokenizer → cộng BM25 trên postings → Top-K → trả chunk/source cùng rank/score/cautions. Load từ chối runtime khác code đã pin; rebuild cần output mới và lựa chọn snapshot tường minh.

| Query smoke chưa có gold | Quan sát trên snapshot này |
|---|---|
| tiền lương làm thêm giờ | Top1 record 152668, heading Điều 55, score 18,92977; có cảnh báo heading cần body. Top2 là bảng công thức khoản 1, cần raw layout |
| nghỉ hằng năm | Top1 dòng “Ngày nghỉ hằng năm...” trong form; Top2 heading Điều 113 record 139264. Đây là hạn chế ranking quan sát được, không tự sửa scope/boost để khớp mẫu |
| Hội đồng tiền lương quốc gia | Top2 là “Hội đồng tiền lương quốc gia do”, mang SOURCE_TEXT_POSSIBLY_INCOMPLETE. Điểm cao không xóa nghi vấn nguồn |
| Các văn bản quy định tại điểm a điểm b khoản này | Top1 đoạn đã sửa ở Điều 24/khoản 4 record 152668; point vẫn null. Đây là smoke trace, không phải gold recall |

Hai query kiểm tra lỗi vận hành: chuỗi OOV `zzzxqvkhongcotrongcorpus` trả NO_MATCH; query rỗng trả EMPTY_QUERY. NO_MATCH không phải kết luận không có quy định pháp luật. K sai, schema/snapshot/hash/ancestry sai trả lỗi; CLI exit 2, không tạo kết quả giả thành công.

## D. Hướng dẫn đọc và chạy code

Đọc module BM25 theo thứ tự: `tokenize` → `term_statistics` → `BM25Index.search` (công thức/rank) → `_context_and_cautions` (ranh giới evidence) → `load_processed` (gate T3/T2) → `export_index`/`load_index`. Đọc test tính điểm tay trước, rồi fixture metadata và pilot integration. Cần hiểu ngay TF/DF/IDF, normalization độ dài, tie-break, fingerprint và candidate khác citation đã resolve. Tối ưu index lớn và tách từ nâng cao để sau khi có benchmark.

Lệnh thực tế, chạy tại workspace:

```powershell
python -B -m unittest discover -s tests -p 'test_*.py' -v
python -B -m ai_core.bm25_retrieval build --manifest data/processed/labor-pilot-3-t3-fix/manifest.json --expected-snapshot 8040db1bfeddb99b93e8937a1c35e634de198a703286318d459d80e90987bfb7 --output-dir data/indexes/labor-pilot-3-t4-bm25
python -B scripts/measure_bm25_baseline.py --index-manifest data/indexes/labor-pilot-3-t4-bm25/manifest.json --output-dir data/evaluation/t4-bm25-technical-smoke --repeats 30
```

Hai thư mục output trên đã tồn tại; chạy lại build/measure phải chọn **tên thư mục mới**. Truy vấn index đã có, không ghi file:

```powershell
python -B -m ai_core.bm25_retrieval query --manifest data/indexes/labor-pilot-3-t4-bm25/manifest.json --query "tiền lương làm thêm giờ" --top-k 5
```

## E. Bằng chứng kiểm thử và latency

87 tests đạt trong 17,016 giây trên lần chạy toàn bộ. 18 tests T4 bao phủ điểm tính tay độc lập; length normalization/TF saturation; Unicode NFC/NFD, dấu/phủ định/số; duplicate query tokens; tie-break; empty/OOV/K; marker-only; metadata/defensive copy; attachment, bảng/ảnh/quote/heading/fragment; negative index/hash/code; build/export/load/CLI UTF-8; rebuild byte-identical; snapshot cũ/sai và ancestry sai dù hash được tính lại. Không sửa test hoặc code các bước trước. Đối chiếu SHA-256 **31 file cũ** trong data/code/tests/reports/scripts: không file nào đổi.

Lỗi thực tế trong lúc phát triển: stdout Windows cp1252 gây UnicodeEncodeError khi in text tiếng Việt ở probe. CLI nay xuất UTF-8 và có subprocess test ép môi trường cp1252. Không có failure còn lại trong bộ test đã chạy; điều này không chứng minh relevance hay đủ evidence.

Đo trên Windows 11, Python 3.14.2, một process; 8 query × 30 lần = 240 warm calls, mỗi query có một warm-up. **Tổng gồm 6 query nội dung và 2 query rỗng/OOV rất nhanh**; không coi aggregate là workload sản phẩm đại diện.

| Phép đo | Kết quả |
|---|---:|
| CLI build + export thực tế | 1.447,99 ms |
| Load + integrity/statistics validation | 551,30 ms |
| Rebuild + source validation trong script đo | 1.270,52 ms |
| Warm search median / p95 (240 calls) | 1,603 / 5,457 ms |
| Warm search min / max | 0,018 / 7,557 ms |
| “hợp đồng lao động” median / p95 (30 calls) | 4,782 / 7,316 ms |

Search latency bao gồm tokenize/scoring/sort/copy kết quả, không gồm load hoặc JSON serialization. OS cache không được kiểm soát; không gọi đây là cold-start hoặc SLA. Summary pin index/source/config/môi trường/script hash; samples lưu đầy đủ kết quả và latency theo query. Xếp hạng/điểm/metadata không đổi qua 240 lần; rebuild khớp toàn bộ payload. Chưa có gold nên không tính Recall@K/MRR, không suy độ chính xác từ query tự chọn hoặc test công thức.

## F. Bàn giao học cùng ChatGPT

```text
Tôi phụ trách RAG và AI Core của Tillegal. T4 đã có BM25 local trên 3 văn bản,
3.085 chunk T3-FIX schema 2, chỉ dùng dữ liệu tạm EXPERIMENTAL_ONLY.
Thiết kế: token âm tiết NFC/casefold giữ dấu, positive-IDF BM25 k1=1.2/b=.75,
không boost metadata, không vector/LLM. Hit giữ source và cảnh báo địa chỉ/evidence.
87 tests đạt (18 mới); index rebuild giống hệt; chưa có gold, Recall/MRR null.
Giúp tôi giải thích công thức bằng fixture mèo/chó, luồng provenance và vì sao
heading/form/nguồn thiếu vẫn có thể đứng đầu mà không được coi là evidence đủ.
Gửi kèm reports/T04-bm25-retrieval-baseline.md, ai_core/bm25_retrieval.py,
tests/test_bm25_retrieval.py, scripts/measure_bm25_baseline.py,
mục 2.4 của 03-STATE-AND-CONTRACTS.md, manifest index và summary/samples đo.
Đọc thêm ai_core/legal_parser.py và data_contracts.py khi cần hiểu gate/trace.
Không cần gửi Parquet. Tôi chưa xác nhận đã hiểu; chưa có Citation Verification.
```

## G. Kiểm tra hiểu biết

1. Vì sao token “không” được giữ nhưng BM25 vẫn không hiểu phủ định?
2. TF saturation và length normalization giải quyết hai vấn đề gì? Tính lại fixture ba chunk trong test điểm tay.
3. Vì sao cùng query lặp token không làm đổi điểm, còn đổi corpus có thể làm đổi điểm mọi chunk?
4. Khi heading hoặc REVIEW_REQUIRED đứng đầu, trường nào ngăn bạn tuyên bố exact citation? Context refs đã lấy đủ body chưa?
5. 87 test pass và 240 kết quả ổn định khác Recall@5 cao như thế nào?

Phỏng vấn: giải thích cách tái lập index từ snapshot và phát hiện artifact/code khác phiên bản; trình bày một lỗi ranking đã quan sát, cách kiểm chứng bằng gold trước khi tối ưu.

## H. Bước tiếp theo — chỉ đề xuất

Đề xuất một task tiếp theo: **thiết lập bộ gold nhỏ có người đọc nguồn xác nhận và đánh giá retrieval trên đúng snapshot T3-FIX**. Chốt đơn vị relevant (chunk/điều/evidence span), quy tắc heading/form/nguồn thiếu và tập dev/test trước khi điều chỉnh BM25; việc này tạo cơ sở cho bước Citation Verification. Chưa tự tạo nhãn pháp lý, chưa triển khai task đó hoặc verifier. Chờ phê duyệt riêng.
