# T02 — Hợp đồng dữ liệu nội bộ và adapter HF local

Ngày: 22/10/2026 (Asia/Saigon). T2 được duyệt bằng “tiếp t2 đi”, theo phân công mới: nhóm cung cấp dữ liệu; người dùng phụ trách RAG và AI Core. Trạng thái kỹ thuật: hoàn thành T2. Trạng thái học: chưa xác nhận đã hiểu. T1 giữ nguyên; chưa triển khai T3.

## A. Mục tiêu và kết quả

Tách schema nguồn Hugging Face khỏi định dạng AI Core bằng adapter (bộ chuyển đổi theo nguồn) và `DocumentVersion` dùng chung. Đã chuyển đúng ba văn bản pilot thành staging (dữ liệu trung gian), giữ nguyên HTML và các trạng thái chưa xác minh.

| Output | Vị trí |
|---|---|
| Ba record, mỗi dòng một JSON | [documents.jsonl](<D:/DOWNLOAD/Ligalli Illigal/data/staging/labor-pilot-3/documents.jsonl>) |
| Schema trao đổi cấu trúc | [document.schema.json](<D:/DOWNLOAD/Ligalli Illigal/data/staging/labor-pilot-3/document.schema.json>) |
| Hash đầu vào/output/code, môi trường và giới hạn | [manifest.json](<D:/DOWNLOAD/Ligalli Illigal/data/staging/labor-pilot-3/manifest.json>) |
| Hợp đồng/phân công bàn giao | [03-STATE-AND-CONTRACTS.md, mục 2.1](<D:/DOWNLOAD/Ligalli Illigal/03-STATE-AND-CONTRACTS.md>) |

Snapshot raw T1: `e2551a80c69ef56a6d1906fff79890916540e63f0450258c5c4a1bac333dd279`.

Snapshot staging T2: `57b706177f7d1ad72efd20f90bb36715dce6be1c0268b041319ca465afdb1faa`.

| Source record ID | Số hiệu | HTML UTF-8 giữ nguyên |
|---|---|---:|
| 139264 | 45/2019/QH14 | 413.666 byte |
| 146696 | 10/2020/TT-BLĐTBXH | 58.762 byte |
| 152668 | 145/2020/NĐ-CP | 759.084 byte |

Đạt `READY_FOR_EXPERIMENTAL_PARSING`, `usage_policy=EXPERIMENTAL_ONLY`; tất cả `legal_approval=QUARANTINE`. `corpus_snapshot_id` và `index_version` vẫn null. Chưa có parser cấu trúc, chunks, retrieval, verifier hoặc benchmark AI.

## B. Thay đổi và lý do

- Tạo [ai_core/data_contracts.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/data_contracts.py>): kiểu dữ liệu, kiểm tra hợp đồng, hash/ID, bộ đọc JSONL; chỉ dùng thư viện chuẩn Python.
- Tạo [ai_core/adapters/hf_local.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/adapters/hf_local.py>): kiểm tra đầu vào T1, đọc Parquet, ánh xạ HF và xuất staging. Hai file `__init__.py` chỉ khai báo package.
- Tạo [tests/test_hf_local_adapter.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_hf_local_adapter.py>): 15 kiểm thử bằng dữ liệu giả, gồm fixture trung lập nguồn.
- Cập nhật mục hợp đồng trong tài liệu 03, báo cáo này và [CHECKPOINT.md](<D:/DOWNLOAD/Ligalli Illigal/CHECKPOINT.md>). Không sửa raw, selection hoặc output kiểm tra T1.

Các quyết định và giới hạn:

1. `document_id = source_id::source_record_id`; số hiệu không phải khóa duy nhất. `document_version_id` là fingerprint kỹ thuật của nội dung, metadata, trạng thái và snapshot, không chứng nhận phiên bản luật. Chỉ đổi URI nơi lưu raw không đổi version ID.
2. Giữ HTML nguyên văn. BeautifulSoup chỉ xem bản sao để phát hiện body rỗng và cảnh báo bảng/ảnh; chưa làm sạch hoặc suy cấu trúc. Record chỉ có ảnh/script bị chặn; bảng/ảnh trong văn bản có chữ vẫn được bảo toàn.
3. Trường chưa biết dùng `null`, không dùng ngày giả hoặc ngày chạy adapter thay ngày crawl. Ngày sai chuyển null kèm giá trị gốc trong `issues`. Nhãn hiệu lực HF là thông tin nguồn khai báo, không cấp trạng thái VALID.
4. JSON Schema mô tả cấu trúc; Python bổ sung kiểm tra ngày, hash và liên kết ID. V1 cố định các trạng thái chưa xác minh; chưa có quy trình nâng thành nguồn đã duyệt.
5. Adapter giới hạn đúng ba ID pilot. Relationships được kiểm tra hash thuộc snapshot nhưng không chuyển thành quan hệ pháp lý. Không tải thêm, crawl hoặc đồng bộ HF.
6. Batch giảm số dòng giữ trong RAM, không bảo đảm trần bộ nhớ theo byte. Ba HTML và output được giữ trong RAM; bộ đọc JSONL phục vụ pilot. Raw reference dùng URI tuyệt đối theo máy hiện tại.
7. Từ chối ghi đè output và ghi vào thư mục input T1. Manifest ghi cuối làm dấu hoàn tất; lỗi I/O vẫn có thể để lại bộ output thiếu, chưa có rollback/resume.

Hợp đồng bàn giao: ID ổn định, số hiệu/nội dung/định dạng, raw/hash, URL, thời điểm thu thập, phiên bản/hiệu lực nếu có, các biến đổi đã làm; thiếu ghi null và lý do. Phân công ở tài liệu 03 là đề xuất cần thống nhất: người crawl thu thập và khai báo nguồn/biến đổi/cập nhật; AI kiểm tra đầu vào, chuẩn hóa, parsing/chunking và ảnh hưởng tới retrieval/gold. Chưa mặc định người crawl đã làm sạch hoặc xác minh nguồn. Chưa viết/kiểm thử adapter dữ liệu thật của nhóm.

Thay corpus phải kiểm tra lại parsing/retrieval và các mẫu đánh giá bị ảnh hưởng. Benchmark phải gắn corpus, parser/index, bộ nhãn và cấu hình model thực tế; không kế thừa điểm corpus tạm cho corpus mới. Các hợp đồng Evidence/request version là định hướng; chưa xây scheduler, PostgreSQL queue hoặc runtime nhiều agent.

## C. Luồng hoạt động

Manifest + selection T1 → kiểm tra snapshot/hash → đọc metadata/content bằng ID → kiểm tra số hiệu/loại và hash HTML mẫu T1 → ánh xạ DocumentVersion → kiểm tra hợp đồng → hash lại input → xuất JSONL/schema → manifest cuối.

Ví dụ, record `139264` có `so_ky_hieu=45/2019/QH14` thành `document_number`; ID nội bộ là `hf/th1nhng0/vietnamese-legal-documents::139264`. Ngày đổi từ DD/MM/YYYY sang YYYY-MM-DD; ví dụ giả `01/02/2020` thành `2020-02-01`. HTML không được viết lại. URL/thời điểm crawl thiếu giữ null; thời điểm tạo manifest là trường riêng.

Schema sai, ID thiếu/trùng, hash khác T1, body rỗng hoặc output đã tồn tại → CLI exit 2. Thành công → exit 0 và trạng thái staging thử nghiệm, không phải kết luận pháp lý.

## D. Hướng dẫn đọc code

| Thứ tự | File → hàm/class | Cần theo dõi |
|---|---|---|
| 1 | `ai_core/data_contracts.py` → `RawReference`, `DocumentVersion`, `from_dict` | Record chung; chặn trường thiếu/dư, ngày/hash/ID sai và tự nâng trạng thái |
| 2 | Cùng file → `make_document_id`, `make_version_id`, `build_document` | Document khác phiên bản kỹ thuật; metadata cũng ảnh hưởng version |
| 3 | `ai_core/adapters/hf_local.py` → `verify_inputs`, `read_selected_metadata`, `read_selected_content` | Toàn vẹn input; join bằng ID, không theo thứ tự dòng |
| 4 | Cùng file → `map_date`, `map_document`, `convert_pilot` | Ánh xạ riêng HF; bảo toàn raw và unknown |
| 5 | Cùng file → `export_pilot`, `main`; core → `load_documents` | Guard, manifest cuối, exit code; downstream đọc hợp đồng chung |
| 6 | `tests/test_hf_local_adapter.py` → `HFLocalAdapterTests` | Ưu tiên bảo toàn HTML, hash đổi, ngày sai và `test_contract_accepts_team_fixture_without_hf_dependencies` |

Đường dẫn đầy đủ ở mục B. Hiểu ngay: adapter là ranh giới phụ thuộc; null khác phủ định; hash khác xác minh nguồn; staging khác retrieval corpus và gold. Học sau: tối ưu Parquet, full/delta delivery, adapter crawl thật và quản lý phiên bản hiệu lực có bằng chứng.

## E. Bằng chứng kiểm thử

Đã chạy từ workspace, Python 3.14.2 và PyArrow 25.0.1:

```powershell
python -B -m unittest discover -s tests -p test_hf_local_adapter.py -v
python -B -m ai_core.adapters.hf_local --manifest data/inspection/local-legal-v1/manifest.json --selection data/selections/labor-pilot-3.json --output-dir data/staging/labor-pilot-3
python -B -m unittest discover -s tests -p 'test_*.py' -v
```

**15/15 test T2 đạt**; adapter thật exit 0, xuất 3 record; **28/28 test tổng đạt**, gồm 13 test T1 hồi quy trên fixture. Không khảo sát lại toàn corpus của T1. JSONL 1.262.599 byte, schema 2.481 byte, manifest 4.281 byte. Lệnh xuất vào cùng thư mục bị từ chối; muốn lưu lần khác phải chỉ định thư mục mới.

Kiểm tra Python trực tiếp, không ghi file: `load_documents` đọc output thật, `verify_inputs` kiểm tra T1, `convert_pilot` chuyển lại trong RAM rồi so record. Chín kiểm tra đều true: đủ ba record; hash artifacts đúng; hash HTML khớp T1; kích thước HTML khớp T1; chuyển lại giống hệt; giữ QUARANTINE; chưa index; hash code khớp manifest; input không đổi.

Test bao phủ ID thiếu/trùng, sai kiểu Parquet, snapshot/hash đổi, ngày sai, body rỗng, input đổi trong lúc xử lý, ghi đè, tính lặp lại, trường hợp đồng thiếu/dư/sai kiểu, sửa nội dung/metadata/approval trái hợp đồng, JSONL lỗi/trùng record. Fixture trung lập được đọc trong subprocess chặn import HF adapter, PyArrow và BeautifulSoup, vẫn thành công.

Chưa đo RAM/latency, chưa kiểm tra dữ liệu crawl thật hay tính đúng của luật. Không có lỗi kiểm thử còn mở; thiếu hụt nguồn/hiệu lực/quyền sử dụng và bảng/ảnh chưa xử lý vẫn được ghi rõ. Mỗi record có 11 issue; `152668` có thêm ảnh nên 12. Đây là thông tin giới hạn, không phải 11–12 kết luận văn bản sai. Các test chứng minh hợp đồng/bảo toàn trong phạm vi đã chạy, chưa chứng minh retrieval/verifier tương thích vì chúng chưa được triển khai.

## F. Bàn giao để học cùng ChatGPT

```text
Tôi xây Tillegal, phụ trách RAG và AI Core; Citation Verification là trọng tâm.
T2 tách schema HF khỏi DocumentVersion, chuyển 3 pilot, giữ HTML và
QUARANTINE/UNKNOWN. 15 test T2 và 28 test tổng đạt. T1/raw không đổi.
Chưa có parser, retrieval, verifier hoặc benchmark AI.

Hướng dẫn tôi theo luồng dữ liệu và yêu cầu tôi giải thích lại:
1. data_contracts.py: DocumentVersion, make_version_id, build_document, load_documents.
2. adapters/hf_local.py: verify_inputs, map_document, convert_pilot, export_pilot.
3. test_hf_local_adapter.py: preservation, tampering, fixture trung lập nguồn.
Giải thích ID vs số hiệu, hash vs provenance, null vs false, staging vs corpus/gold.
Chưa biết nguồn chính thức, revision HF, ngày crawl, hiệu lực theo ngữ cảnh;
chưa thử dữ liệu thật của người crawl. Không suy tôi đã hiểu từ việc test đạt.

Gửi kèm báo cáo này; ai_core/data_contracts.py; ai_core/adapters/hf_local.py;
tests/test_hf_local_adapter.py; mục 2 của 03-STATE-AND-CONTRACTS.md;
data/staging/labor-pilot-3/manifest.json và document.schema.json.
Chỉ gửi documents.jsonl khi cần điều tra nội dung thật: có HTML/ảnh nhúng.
Không cần gửi cả ba Parquet để học hợp đồng và adapter.
```

## G. Câu hỏi tự kiểm tra và phỏng vấn

1. Vì sao cùng số hiệu vẫn có thể có document_id khác nhau?
2. Chỉ đổi nơi lưu raw và sửa ngày hiệu lực tác động khác nhau đến version ID thế nào?
3. Vì sao có effective_from vẫn giữ temporal UNKNOWN? URL null có nghĩa nguồn giả không?
4. Người crawl đổi tên cột thì phần nào cần sửa? Test hiện tại chưa chứng minh gì về retrieval?
5. Corpus mới đến thì cần kiểm tra lại gì trước khi báo điểm benchmark?

Câu hỏi phỏng vấn: “Bạn chứng minh adapter không mất nội dung và phát hiện input bị đổi thế nào?”; “Hãy phân biệt citation tồn tại, nguồn đáng tin, áp dụng đúng thời điểm/phạm vi và nội dung hỗ trợ claim bằng một ví dụ.”

## H. Bước tiếp theo duy nhất được đề xuất

**T3 — parser cấu trúc và chunking thử nghiệm trên đúng ba DocumentVersion.** Input staging T2 → cây cấu trúc, chunks truy vết về document/version/locator và báo cáo phần chưa nhận diện. Parser đọc hợp đồng chung, không đọc schema HF.

Phương án: tách nội dung chính, mở đầu, phụ lục/biểu mẫu; nhận diện Chương/Điều/Khoản/Điểm theo ngữ cảnh; giữ bảng và phần chưa nhận diện kèm cảnh báo. Kiểm tra “Điều 7” xuất hiện ở nội dung chính và phụ lục của `152668`, tránh khóa chỉ bằng số điều. Chưa cần vector database.

File dự kiến: `ai_core/legal_parser.py`, `tests/test_legal_parser.py`, output `data/processed/labor-pilot-3/`, báo cáo T03 và checkpoint; mở rộng hợp đồng chunk khi triển khai T3. Hoàn thành khi ba văn bản tạo output có trace, không âm thầm bỏ phần chưa nhận diện, test cấu trúc trùng/bảng/phụ lục và mẫu đối chiếu thủ công đạt; không suy parser đúng toàn corpus. Rủi ro chính: bảng/biểu mẫu và ảnh khó biểu diễn đủ bằng text. Cần hiểu locator là vị trí trong nguồn, không chỉ nhãn “Điều 7”.

Giữ trạng thái thử nghiệm; đối chiếu bằng chứng và gold vẫn cần cho đánh giá baseline. **Dừng sau T2; T3 chờ phê duyệt.**
