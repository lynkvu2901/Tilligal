# T03 — Parser cấu trúc và chunking pilot

Ngày: 25/10/2026 (Asia/Saigon). Phê duyệt: “tiếp t3”. Trạng thái kỹ thuật: hoàn thành phạm vi T3, output có mục cần rà soát. Trạng thái học: chưa được người dùng xác nhận hiểu. Giữ nguyên raw và hiện vật T1/T2; dừng trước T4.

## A. Mục tiêu và kết quả

Đã biến ba `DocumentVersion` T2 thành cây cấu trúc và các đoạn nhỏ có truy vết nguồn, phục vụ bước retrieval/Citation Verification tiếp theo. Parser nhận hợp đồng nội bộ, không đọc cột Hugging Face.

| Output | Vị trí |
|---|---|
| Cây node, block, span nguồn và các phần loại trừ | [structures.jsonl](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3/structures.jsonl>) |
| 3.085 chunk, mỗi dòng một record | [chunks.jsonl](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3/chunks.jsonl>) |
| Thống kê/cảnh báo/phạm vi kiểm tra | [validation.json](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3/validation.json>) |
| Hash, cấu hình, phiên bản code và đầu vào | [manifest.json](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3/manifest.json>) |

| Record | Điều nội dung chính | Điều trong mẫu | Block / chunk | Bảng | Ảnh |
|---|---:|---:|---:|---:|---:|
| 139264 — 45/2019/QH14 | 220 | 0 | 1.359 / 1.359 | 3 | 0 |
| 146696 — 10/2020/TT-BLĐTBXH | 12 | 0 | 133 / 133 | 2 | 0 |
| 152668 — 145/2020/NĐ-CP | 115 | 18 | 1.593 / 1.593 | 43 | 3 |

Record `152668` có 6 phụ lục và 19 mẫu được nhận diện. Record `139264` có 4 phạm vi trích dẫn sửa đổi được giữ riêng. Các con số mô tả output của corpus tạm; không phải độ chính xác parser trên toàn corpus hoặc benchmark AI.

Staging đầu vào: `57b706177f7d1ad72efd20f90bb36715dce6be1c0268b041319ca465afdb1faa`.

Processed snapshot: `d1a8d31fecf605a9d4e8c52b1a0d22561d38b0f44875c25048f0f32605252165`.

Trạng thái `PASS_WITH_REVIEW_ITEMS`; chunk kế thừa `EXPERIMENTAL_ONLY`, `QUARANTINE`, provenance/rights `UNVERIFIED`, temporal `UNKNOWN`. `corpus_snapshot_id/index_version` vẫn null. Không có chỉ mục, generation, verifier hoặc điểm benchmark.

## B. Thay đổi và lý do

- Tạo [ai_core/legal_parser.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/legal_parser.py>): trích block có raw span, nhận diện cấu trúc, tạo chunk, kiểm tra truy vết và CLI xuất pilot. Chỉ dùng thư viện chuẩn Python.
- Tạo [tests/test_legal_parser.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_legal_parser.py>): 17 test giả lập và 3 test dữ liệu pilot đã pin hash.
- Cập nhật mục 2 của [03-STATE-AND-CONTRACTS.md](<D:/DOWNLOAD/Ligalli Illigal/03-STATE-AND-CONTRACTS.md>) để mô tả node/block/chunk thực tế, báo cáo này và [CHECKPOINT.md](<D:/DOWNLOAD/Ligalli Illigal/CHECKPOINT.md>).

Quyết định và đánh đổi:

1. Dùng `HTMLParser` để giữ vị trí trong chuỗi gốc, tránh serialize DOM rồi nhầm đó là raw. Chỉ giải mã entity và gộp khoảng trắng; không sửa số hiệu, chữ, phủ định hay dấu câu. Head/script/style/comment không vào text và có dấu vết loại trừ; không diễn giải CSS.
2. Tách preamble/main/closing/appendix/form/quoted. Các heading Chương/Mục/Điều/Khoản/Điểm được nhận diện theo mẫu và ngữ cảnh. ID không lấy số điều đơn lẻ; nhãn lặp vẫn có node khác. Không tin class/ID HTML upstream làm ground truth.
3. Bảng là block riêng, text tuyến tính giữ thứ tự ký tự nhưng chưa biểu diễn đủ quan hệ ô/cột. Raw span giữ nguyên HTML để đọc topology; không dùng text bảng đơn lẻ xác minh phép tính. Ảnh có marker và span, chưa OCR. Bảng rỗng có marker; text không rõ cấu trúc vẫn giữ cùng cảnh báo.
4. Đoạn sửa đổi đặt trong dấu ngoặc kép được giữ dưới node `quoted_text`, không phát sinh điều/khoản của văn bản đang đọc. Đây là heuristic, chưa resolve văn bản được sửa đổi. Thiếu dấu đóng thì báo review, không tự đoán.
5. Một block sinh một hoặc nhiều chunk, không gộp qua phạm vi. Ngưỡng 1.800 ký tự ưu tiên cắt ở cuối câu, rồi khoảng trắng; block phải chia có `SPLIT_BLOCK_REQUIRES_CONTEXT`. Không coi fragment độc lập là đủ điều kiện/ngữ cảnh. Pilot hiện có block dài nhất 1.130 ký tự nên chưa cần chia; nhánh chia đã thử bằng fixture dài.
6. Offset là Unicode code point của Python, khoảng `[start,end)`. Raw locator của chunk bao toàn block; `text_start/end` nằm trong text chuẩn hóa của block. Backend dùng UTF-16 phải chuyển đổi, không áp offset này trực tiếp lên JavaScript string. Chunk cha là node cấu trúc; downstream cần dùng ancestor_ids để mở rộng đủ điều/khoản.
7. Pilot giữ toàn bộ ba văn bản/cấu trúc trong RAM; JSON có metadata lặp nên output lớn hơn input. Chưa tối ưu tốc độ, bộ nhớ hoặc chất lượng chunk cho retrieval. CLI từ chối ghi đè, kiểm tra input trước/sau và ghi manifest cuối; lỗi I/O có thể để lại bộ thiếu, chưa rollback/resume.

Các vấn đề nguồn được giữ và báo: nhãn Chương XI lặp ở `152668`; nhãn `Mẫu số 07/PLII` nằm trong Phụ lục III. Không tự sửa thành nhãn khác. Có 64 block đánh số chưa gán được cấp pháp lý và 707 block dùng ngữ cảnh không đánh số mang tính heuristic. Số cảnh báo không phải số lỗi pháp lý. Trường `QUOTED_STRUCTURE_NOT_RESOLVED=38` trong validation cộng 34 block và 4 node, không phải 38 đoạn trích độc lập.

## C. Luồng hoạt động và ví dụ

Manifest staging → kiểm tra hash/declarations → đọc DocumentVersion → tách block + segment nguồn → xây cây phạm vi/cấp cấu trúc → cắt chunk → phát lại text từ raw và kiểm tra coverage → kiểm tra input không đổi → xuất structures/chunks/validation → manifest cuối.

Trong `152668`, “Điều 7” nội dung chính có `scope=main`, còn “Điều 7” mẫu hợp đồng có `scope=form`, `appendix=V`, `form=01/PLV`. Cả hai cùng article label 7 nhưng node/chunk ID và đường cha khác nhau. Tên mẫu trong bảng danh mục không mở thêm form node.

Trong `139264`, đoạn “Điều 54” được trích tại Điều 219 có `scope=quoted`, ngữ cảnh ngoài là article 219/clause 1/point a. Không nhận nhầm thành Điều 54 mới. Sau dấu đóng, điểm b trở lại đúng phạm vi ngoài.

Schema/hash sai, input thay đổi, đầu ra đã tồn tại, không có block hoặc coverage lỗi → exit 2. Thành công → exit 0 và `PASS_WITH_REVIEW_ITEMS`; không phải phê duyệt nguồn hoặc hiệu lực.

## D. Hướng dẫn đọc code

Đọc [legal_parser.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/legal_parser.py>) theo thứ tự:

| Hàm/class | Input → output; điểm cần hiểu |
|---|---|
| `parse_document` | DocumentVersion → một result; điều phối các bước, kiểm tra max_chars |
| `SourceBlocks`, `extract_blocks`, `segment_text` | HTML/text → block + segments; offset nguồn, bảng, ảnh, entity, nội dung bị loại |
| `build_structure` | Block → node cha/con và scope; reset phạm vi, quote, nhãn lặp, numbering chưa rõ |
| `split_text`, `make_chunks` | Block + node → fragment có parent/locator; không trộn phạm vi, không bỏ text |
| `validate_result` | Raw + result → pass hoặc ContractError; phát lại nguồn, kiểm tra cha/trạng thái và phủ kín text |
| `export_pilot`, `main` | Manifest → output mới; hash, kiểm tra thay đổi, manifest cuối, exit code |

Sau đó đọc ba class trong [test_legal_parser.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_legal_parser.py>): `LegalParserTests` cho tình huống khó, `ParserExportTests` cho hiện vật/hash, `LocalPilotParserTests` cho mẫu thật đã pin. Cần hiểu ngay: scope khác label; raw offset khác normalized offset; coverage không chứng minh gán cấu trúc đúng; retrieval phải lấy đủ ngữ cảnh. Có thể học sau: tokenizer/model budgets, OCR, cấu trúc bảng đầy đủ và parser nhiều định dạng.

## E. Bằng chứng kiểm thử

Các lệnh đã chạy từ workspace:

```powershell
python -B -m unittest discover -s tests -p test_legal_parser.py -v
python -B -m unittest discover -s tests -p 'test_*.py' -v
python -B -m ai_core.legal_parser --manifest data/staging/labor-pilot-3/manifest.json --output-dir data/processed/labor-pilot-3
```

- Bộ tổng **48/48 test đạt**: 28 hồi quy T1/T2 + 20 T3. Sau bổ sung ưu tiên ranh giới câu và cờ yêu cầu context cho block dài, chạy lại toàn bộ **20/20 test T3 đạt**. Không có test pilot bị skip.
- CLI xuất thật exit 0, 3 record. Output cuối được tái xuất bằng `export_pilot` với code cuối, snapshot nội dung không đổi; code hash trong manifest đã khớp.
- Đọc lại structures/chunks từ đĩa, gọi `validate_result`, kiểm tra hash/bytes, code/input và so với `parse_document` chạy lại trong RAM: đạt, kết quả record giống hệt. Structures 3.209.087 byte; chunks 5.322.842 byte; validation 2.173 byte.
- Đối chiếu bằng BeautifulSoup cho ba HTML: chuỗi ký tự khi bỏ khoảng trắng khớp toàn bộ, lần lượt 147.783 / 16.122 / 193.904 ký tự. Đủ 48 bảng và 3 ảnh có span/marker. Đây là kiểm tra nội dung bằng cách đọc khác, cùng nền HTML parser chuẩn; không phải đối chiếu hình ảnh trình duyệt hay xác thực nguồn luật.
- Mẫu cấu trúc đã đọc/đối chiếu local: 9 ca ở `test_reviewed_local_boundary_samples` gồm Điều 7 chính/mẫu, trích Điều 54 và điểm b sau trích, kết thúc/chữ ký, Điều 3 Thông tư, bảng công thức Điều 55; thêm kiểm tra nhãn lặp/lệch phụ lục và 3 ảnh ở Điều 56–57. Chuỗi điều nội dung chính liên tục 1–220, 1–12, 1–115. Đây là mẫu regression kỹ thuật do lượt triển khai đối chiếu, chưa có người dùng xác nhận và không phải gold pháp lý.

Test giả lập bao phủ bảng lồng/rỗng, inline text/entity/tiếng Việt, scope phụ lục, quote, dữ liệu lỗi, chia block dài, trace/coverage bị sửa, trạng thái bị nâng trái phép, tính lặp lại, ghi đè và input thay đổi. Khi pilot không có ở máy khác, ba test local báo skip rõ; khi hash đổi thì yêu cầu rà baseline thay vì tự đổi kỳ vọng.

Lần probe đầu gặp encoding console Windows; đã dùng stdout UTF-8. Lần chạy parser đầu phát hiện tên method trùng thuộc tính `HTMLParser.offset`; đã đổi thành `source_offset`. Không còn lỗi test mở. Các hạn chế cấu trúc/cảnh báo ở mục B vẫn tồn tại, chưa đo retrieval hoặc kết luận đúng luật.

## F. Bàn giao để học cùng ChatGPT

```text
Tôi xây Tillegal, phụ trách RAG/AI Core, trọng tâm Citation Verification.
T3 nhận DocumentVersion trung lập nguồn, tạo node/block/chunk cho 3 văn bản tạm.
Có 3.085 chunks, 48 bảng, 3 ảnh được giữ trace; 20 test T3 và bộ tổng 48 test đạt.
Tất cả vẫn EXPERIMENTAL_ONLY/QUARANTINE/UNKNOWN. Chưa có retrieval/verifier.

Hãy hướng dẫn theo parse_document → SourceBlocks/extract_blocks → build_structure
→ make_chunks → validate_result → export_pilot. Yêu cầu tôi giải thích lại:
- Vì sao Điều 7 chính khác Điều 7 trong mẫu, và Điều 54 trích không thành điều mới?
- Raw offset khác normalized text offset và UTF-16 như thế nào?
- Vì sao bảo toàn text vẫn chưa chứng minh cấu trúc/hiệu lực đúng?
- Vì sao bảng tuyến tính/ảnh/fragment cần context và cảnh báo?

Gửi kèm: reports/T03-legal-structure-and-chunks.md; ai_core/legal_parser.py;
tests/test_legal_parser.py; ai_core/data_contracts.py;
mục 2.2 của 03-STATE-AND-CONTRACTS.md;
data/processed/labor-pilot-3/manifest.json và validation.json.
Khi debug riêng một trường hợp mới gửi record structures/chunks tương ứng;
không cần gửi cả Parquet hoặc toàn JSONL nhiều MB để học luồng.
Chưa có gold pháp lý hoặc xác nhận người dùng đã hiểu.
```

## G. Câu hỏi tự kiểm tra và phỏng vấn

1. Cùng article=7 nhưng scope/ancestor khác thì resolver phải làm gì?
2. Có thể dùng text_start để cắt chuỗi HTML raw không? Vì sao ký tự tiếng Việt khiến byte offset khác code point?
3. Vì sao test giữ toàn bộ ký tự vẫn không chứng minh tất cả khoản/điểm được gán đúng?
4. Nếu chunk chỉ chứa `[IMAGE]` hoặc một phần câu dài, cần thông tin gì trước khi xác minh claim?
5. Khi nhóm thay corpus, vì sao phải rà mẫu parser và benchmark, kể cả khi schema không đổi?

Phỏng vấn: “Bạn tránh làm mất điều kiện/phủ định khi chunk thế nào, giới hạn hiện tại là gì?”; “Bạn chứng minh một đoạn retrieval đến từ phiên bản và vị trí nguồn nào?”

## H. Bước tiếp theo duy nhất được đề xuất

**T4 — resolver địa chỉ citation và retrieval BM25 thử nghiệm trên pilot.** Input: DocumentVersion + structures/chunks + manifest T3. Output dự kiến: tìm văn bản/điều/khoản/điểm đúng scope, trả evidence có version/hash/locator và mở rộng parent khi cần; truy vấn từ khóa có xếp hạng để chuẩn bị baseline P9. Không generation hoặc semantic verdict ở task này.

Phương án: lookup cấu trúc trước cho citation rõ, BM25 đơn giản cho tìm kiếm từ khóa; không cần vector DB. Điều kiện hoàn thành: test thiếu/trùng citation, nhầm main/form, quoted, đọc đủ điều/khoản và trace; tập ca dev nhỏ đối chiếu local có expected evidence IDs, ghi rõ chưa phải gold pháp lý do người dùng duyệt. Bất định nguồn/hiệu lực giữ nguyên; bảng/ảnh/phần chưa nhận diện không được tự nâng thành bằng chứng đủ.

File dự kiến: `ai_core/retrieval.py`, `tests/test_retrieval.py`, fixture dev dưới `tests/fixtures/`, hiện vật thử nghiệm `data/retrieval/labor-pilot-3/`, báo cáo T04 và checkpoint. Cần hiểu BM25 là xếp hạng từ khóa, không phải xác suất đúng luật. Rủi ro: tiếng Việt/tokenization, chunk nhỏ thiếu context, scope mơ hồ và nguồn chưa xác minh. Chỉ đo trên corpus tạm đã pin, không thay cờ phê duyệt nguồn. Đây là đề xuất bước sau theo phân công mới, chưa thực thi.

**Dừng sau T3, chờ phê duyệt T4.**
