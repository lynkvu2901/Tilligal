# T3-FIX — Sửa attachment và củng cố validator

Ngày: 25/10/2026 (Asia/Saigon). Đã được phê duyệt T3-FIX. Kỹ thuật: hoàn thành phạm vi sửa; học: chưa có xác nhận người dùng đã hiểu. Không triển khai T4.

## 1. Lỗi gốc và nguyên nhân

`build_structure` giữ node sâu nhất cho đoạn không đánh số: đoạn dùng chung cho khoản bị gắn vào điểm cuối; numbering thiếu khoảng trắng kế thừa khoản trước; chữ ký/ghi chú mẫu kế thừa điều cuối. Tiết a1)/b1)/c2) chưa có cảnh báo riêng. Nguồn Điều 49 của record 152668 có câu dừng ở “do”, chưa được ghi nhận là nghi vấn nguồn.

`validate_result` kiểm tra nhiều bất biến nội bộ nhưng chưa đối chiếu fingerprint, nhãn dư thừa theo ancestry và inventory block với nguồn. Vì vậy một số phép sửa metadata hoặc xóa đồng thời block/chunk vẫn vượt qua.

## 2. File và hàm đã sửa

| File | Phạm vi |
|---|---|
| [legal_parser.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/legal_parser.py>) | `build_structure`: A–D; `annotate_reviewed_source`: E; `make_chunks`: truyền attachment_status; `validate_source_completeness` và `validate_result`: bất biến; `parse_document`/`export_pilot`: schema, version và thống kê mới |
| [test_legal_parser_fix.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_legal_parser_fix.py>) | Thêm 21 test regression/negative/control/pilot; không sửa hoặc làm yếu test cũ |
| [03-STATE-AND-CONTRACTS.md](<D:/DOWNLOAD/Ligalli Illigal/03-STATE-AND-CONTRACTS.md>) | Mục 2.3 mô tả hợp đồng T3-FIX và giới hạn completeness |
| [CHECKPOINT.md](<D:/DOWNLOAD/Ligalli Illigal/CHECKPOINT.md>) | Ghi kết quả và dừng trước T4 |

Parser `legal-structure-v1.1`, processed schema `2`; staging DocumentVersion/schema T2 vẫn `1`. Hàm `split_text` được đối chiếu nguyên văn bằng AST: không đổi. Không đổi số ký tự tối đa hoặc cách gom/chia block.

## 3. Quy tắc mới và lý do

| Ca | Cách xử lý tối thiểu |
|---|---|
| A — đoạn chung khoản 4 Điều 24 | Chỉ đưa về khoản khi đoạn mở đầu theo mẫu “Các văn bản quy định tại điểm …, điểm … khoản này” và các điểm đó thực sự là anh em trong khoản hiện tại. Ghi `SHARED_CLAUSE_REFERENCE`. Không dùng rule này cho mọi câu nhắc đến điểm |
| Tiếp nối chưa chắc chắn | Giữ parent ứng viên sau điểm, thêm `attachment_status=REVIEW_REQUIRED` và `ATTACHMENT_REVIEW_REQUIRED`. Không tự nâng lên khoản; labels lúc này không phải địa chỉ citation đã xác nhận |
| B — mục `4...` | Cảnh báo `UNRESOLVED_NUMBERED_TEXT`, bỏ liên kết tới khoản/điểm trước, giữ điều trở lên. Không tự tuyên bố đây là khoản 4. Phần tiếp nối tiếp tục cần review đến cấu trúc rõ tiếp theo |
| C — đuôi mẫu | Tạo `form_tail` dưới form tại “Ghi chú:” sau điều hoặc bảng bắt đầu “Nơi nhận:” có “CHỦ TỊCH”. Scope vẫn form; article/clause/point null. Không nhận nhầm một câu nhắc “Nơi nhận” hoặc nội dung đang quoted |
| D — tiết | 26 tiết được giữ text/context, có `SUBPOINT_NOT_RESOLVED` và trạng thái review. Chưa thêm parser hay địa chỉ tiết đầy đủ |
| E — nguồn nghi vấn | Một annotation pin bằng content SHA-256, offset `[135063,135094)` và text chính xác. Thêm `SOURCE_TEXT_POSSIBLY_INCOMPLETE`; không sửa câu, không áp chẩn đoán này cho cùng cụm từ ở nguồn khác |

Ba attachment status: `STRUCTURAL` là rule cấu trúc có dấu hiệu rõ; `HEURISTIC` là suy từ ngữ cảnh; `REVIEW_REQUIRED` chưa đủ căn cứ tuyên bố địa chỉ chính xác. Chúng độc lập với legal approval/provenance/temporal validity.

Completeness trích lại từ DocumentVersion bất biến rồi so toàn bộ payload block (text, kind, spans, segments, thứ tự, số lượng) và danh sách loại trừ. Markup tag/attribute không phải prose; head/script/style/comment/whitespace được xử lý theo chính sách; entity, separator, ảnh có segment kind. Không so bytes HTML với số ký tự text. Phép kiểm tra phát hiện block/chunk bị xóa, nhưng không tự chứng minh extractor không có lỗi chung.

## 4. Kiểm thử và kết quả thực tế

Đã viết test mới trước khi sửa code và chạy trên logic T3 cũ: các ca lỗi tái hiện; bộ 21 test báo FAILED (33 failures, 4 errors khi tính cả subtests; một số ca đối chứng vẫn đạt). Sau sửa:

```powershell
python -B -m unittest discover -s tests -p 'test_legal_parser*.py' -v
python -B -m unittest discover -s tests -p 'test_*.py' -v
python -B -m ai_core.legal_parser --manifest data/staging/labor-pilot-3/manifest.json --output-dir data/processed/labor-pilot-3-t3-fix
```

- **41/41 test parser đạt**: 20 cũ + 21 mới.
- **69/69 test toàn bộ đạt**: thêm 28 test T1/T2; không skip.
- Test A–E gồm fixture cô lập và pilot pin content hash. Ca đối chứng: thiếu điểm anh em thì không nâng parent; đoạn tiếp nối giữ ứng viên; numbering `4.` bình thường vẫn hoạt động; form kế tiếp reset; bảng chỉ nhắc “Nơi nhận” và quote không mở form_tail.
- Negative tests chặn nhãn address sai, ID chunk/node/block không khớp, offset unit/end convention sai, result identity/parser/schema/config sai, xóa block và chunk, xóa/sửa lý do exclusion, bỏ attachment status hoặc issue từ chunk.
- Test completeness có HTML head/style/script/comment/entity và ký tự ngoài BMP; test đối chiếu text bằng BeautifulSoup cũ vẫn đạt. Không thay expected result cũ.
- Sau export: đọc output từ đĩa, validate, so với parse lại trong RAM, hash/bytes/manifest/code/input đều đạt. Tất cả raw, hiện vật T1/T2/T3 cũ và file test T3 cũ giữ nguyên hash. Không còn thư mục fixture tạm.

## 5. So sánh output trước/sau

Output mới: [manifest](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3-t3-fix/manifest.json>), [structures](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3-t3-fix/structures.jsonl>), [chunks](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3-t3-fix/chunks.jsonl>), [validation](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3-t3-fix/validation.json>).

Snapshot mới: `8040db1bfeddb99b93e8937a1c35e634de198a703286318d459d80e90987bfb7`.

Baseline T3 giữ nguyên tại `data/processed/labor-pilot-3/`, snapshot `d1a8d31fecf605a9d4e8c52b1a0d22561d38b0f44875c25048f0f32605252165`.

| Record | Block/chunk cũ → mới | Node cũ → mới | Địa chỉ đổi |
|---|---:|---:|---:|
| 139264 | 1.359 → 1.359 | 1.174 → 1.174 | 0 |
| 146696 | 133 → 133 | 108 → 108 | 0 |
| 152668 | 1.593 → 1.593 | 965 → 967 | 23 |

23 thay đổi đều có chủ đích, xác định bằng ordinal block **đếm từ 0 trong record 152668** của baseline và raw span (không dùng ID cũ làm ID mới):

- Block 219: point b → null, vẫn Điều 24/khoản 4.
- Block 1152: clause 3 → null, vẫn mẫu 03/PLIII/Điều 1, numbering cần review.
- Block 1155–1166: 12 block chữ ký/ghi chú của mẫu 03/PLIII bỏ article 3, chuyển vào form_tail.
- Block 1308–1316: 9 block chữ ký/ghi chú của mẫu 08/PLIII bỏ article 4, chuyển vào form_tail.

Giữ nguyên toàn bộ text/hash text, raw spans/segments, normalized offsets, danh sách exclusions, thứ tự và số chunk; vẫn 48 bảng/3 ảnh. Tất cả ID node/block/chunk đổi vì parser version tham gia fingerprint, không phải vì dữ liệu nguồn đổi. Validator v1.1 không âm thầm nhận schema v1; manifest cũ vẫn pin code hash cũ, không kỳ vọng khớp code hiện tại.

Trạng thái mới: **2.271 STRUCTURAL, 702 HEURISTIC, 112 REVIEW_REQUIRED**. Có 65 block `UNRESOLVED_NUMBERED_TEXT` (64 cũ + ca B); 26 tiết unresolved; một nguồn nghi vấn; hai form_tail. 707 cảnh báo unnumbered cũ vẫn giữ để truy nguyên. Cảnh báo tăng là chủ đích thể hiện bất định, không phải mất text.

## 6. Những vấn đề đã giải quyết

A không còn nhận địa chỉ điểm b; B không còn nhận địa chỉ khoản 3; C không còn lẫn ghi chú/chữ ký của hai mẫu vào điều cuối. D có trạng thái chưa resolve rõ ràng. E được cảnh báo với bằng chứng pin và không khôi phục nội dung.

Validator chặn các probe đã lọt: labels theo ancestry, fingerprint node/block/chunk, result identity, locator convention và việc xóa đồng thời block/chunk. Chunk giữ đúng attachment status/issues và các trạng thái nguồn. Không tự nâng QUARANTINE/UNVERIFIED/UNKNOWN.

## 7. Giới hạn còn lại

- Parent ứng viên của đoạn không đánh số vẫn có thể sai; review flag không phải giải quyết ngữ nghĩa. Ví dụ đoạn chung Điều 107/khoản 3 giữ parent ứng viên cũ nhưng nay cần review, không được coi là exact resolution.
- Rule shared-clause/form-tail hẹp, không phải bộ nhận diện tiếng Việt phổ quát. Chữ ký mẫu khác, ví dụ mẫu 01/PLV, chưa được chuẩn hóa toàn diện.
- Chưa resolve tiết, quote nội bộ, cấu trúc bảng đầy đủ hoặc OCR. Nguồn nghi vấn ngoài annotation đã pin vẫn có thể chưa được phát hiện.
- Completeness dùng cùng extractor để trích lại; lỗi chung của extractor cần test độc lập/mẫu đối chiếu. Nó không chứng minh nguồn luật đầy đủ hoặc đúng pháp lý. Chi phí trích lại tăng, chưa benchmark tài nguyên.
- Chunking vẫn theo block; chưa có bằng chứng BM25/retrieval tốt hơn. Không có benchmark AI, corpus/index được kích hoạt, crawler hoặc runtime mới.

## 8. Kiến thức cần hiểu và bàn giao học

Thứ tự đọc: `build_structure` → `annotate_reviewed_source` → metadata trong `make_chunks` → `validate_source_completeness` → `validate_result`, rồi ba class test mới: `AttachmentFixTests`, `ValidatorFixTests`, `PinnedFixTests`.

Cần giải thích được: candidate parent khác địa chỉ đã xác định; ID là fingerprint theo version chứ không phải số điều; metadata lặp phải kiểm tra với ancestry; coverage của danh sách tự khai khác completeness so với nguồn; giữ text không đồng nghĩa đúng cấu trúc/pháp lý. Học tokenizer/OCR/benchmark sau, không cần mở rộng chúng để hiểu fix này.

Câu hỏi tự kiểm tra/phỏng vấn:

1. Vì sao không nâng mọi đoạn không số lên khoản, và khi nào rule A được phép nâng?
2. Vì sao B tăng số unresolved nhưng là một sửa lỗi đúng?
3. Xóa cả block và chunk khác xóa riêng chunk như thế nào đối với validator cũ?
4. Vì sao IDs đổi hết dù toàn bộ text và cách chia chunk giữ nguyên?
5. Completeness mới còn có thể bỏ sót loại lỗi nào?

```text
Tôi làm Tillegal RAG/AI Core. T3-FIX giữ extractor/chunking, sửa attachment có bằng
chứng và củng cố validator. 69 tests đạt; 3.085 chunks giữ nguyên text/trace;
23 địa chỉ đổi có chủ đích, tất cả vẫn thử nghiệm/chưa xác minh pháp lý.
Hãy giúp tôi giải thích các quyết định và tự điều tra một probe validator.
Gửi kèm reports/T03-FIX-structural-and-validation.md, ai_core/legal_parser.py,
tests/test_legal_parser_fix.py, tests/test_legal_parser.py, ai_core/data_contracts.py,
mục 2.3 của 03-STATE-AND-CONTRACTS.md và manifest/validation T3-FIX.
Không cần toàn bộ Parquet. Chưa xác nhận tôi đã hiểu, chưa có T4 hoặc benchmark AI.
```

## 9. Các quyết định cần duyệt trước T4

Đề xuất duyệt T3-FIX với processed schema 2 và snapshot mới làm đầu vào thử nghiệm; giữ T3 v1 làm baseline lịch sử. Với T4 sau này, cần thống nhất rằng REVIEW_REQUIRED/tiết chưa resolve không được tuyên bố exact citation, có cách trả về thiếu chắc chắn; bảng/ảnh/nguồn nghi vấn cần giới hạn rõ khi làm evidence. HEURISTIC cũng không tự trở thành phê duyệt pháp lý.

Chỉ sau khi người dùng phê duyệt mới triển khai T4 theo phạm vi riêng. **Dừng ở T3-FIX; chưa triển khai retrieval/BM25/embedding/verifier.**
