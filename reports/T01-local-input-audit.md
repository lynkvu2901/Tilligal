# T01 — Khóa đầu vào local và chọn pilot

Ngày: 18/10/2026 (Asia/Saigon). T1 đã được phê duyệt. Trạng thái kỹ thuật: hoàn thành; trạng thái học: chưa có xác nhận người học đã hiểu. Không triển khai T2.

## A. Mục tiêu và kết quả

Đã tạo công cụ offline kiểm tra ba Parquet, nhận diện snapshot bằng hash và chọn đúng ba văn bản tiếng Việt làm đầu vào audit. “Khóa” nghĩa là lưu fingerprint để phát hiện thay đổi, không đổi quyền ghi của raw.

| Hiện vật | Vị trí |
|---|---|
| Manifest: hash, schema, số dòng, môi trường, trạng thái nguồn | [manifest.json](<D:/DOWNLOAD/Ligalli Illigal/data/inspection/local-legal-v1/manifest.json>) |
| Thống kê, lỗi, phương pháp lấy mẫu và giới hạn | [validation.json](<D:/DOWNLOAD/Ligalli Illigal/data/inspection/local-legal-v1/validation.json>) |
| Selection ba văn bản gắn snapshot | [labor-pilot-3.json](<D:/DOWNLOAD/Ligalli Illigal/data/selections/labor-pilot-3.json>) |

Snapshot ID: `e2551a80c69ef56a6d1906fff79890916540e63f0450258c5c4a1bac333dd279`.

Kết quả `PASS_WITH_WARNINGS` chỉ nói về kiểm tra kỹ thuật trong phạm vi đã chạy. Selection là `READY_FOR_AUDIT`, không phải đã được duyệt làm nguồn kiểm chứng pháp lý.

| Kiểm tra toàn bộ cột tương ứng | Kết quả |
|---|---:|
| Metadata / content / relationships | 171.556 / 170.824 / 1.033.255 dòng |
| ID thiếu hoặc trùng trong metadata/content | 0 |
| Metadata thiếu content / content mồ côi | 732 / 0 |
| Relationship nguồn ngoài metadata | 0 |
| Relationship đích ngoài metadata | 43.128 dòng, 17.706 ID đích |
| Bộ ba quan hệ trùng / quan hệ tự trỏ | 0 / 259 |
| Metadata thiếu ngày có hiệu lực / thông tin áp dụng | 4.929 / 171.556 |

HTML chỉ kiểm tra năm record có chủ đích: ba pilot, dòng content đầu và probe body rỗng `135139`. Probe này có 83 byte HTML nhưng không có body text. Không suy ra tỷ lệ body rỗng toàn corpus. Metadata lấy ba pilot và dòng đầu/giữa, tối đa năm record đầy đủ; ứng viên cùng số hiệu được liệt kê riêng bằng trường nhận diện tối thiểu. Relationships lấy năm dòng đầu làm mẫu.

Ba ID được chọn: `139264` — `45/2019/QH14`; `146696` — `10/2020/TT-BLĐTBXH`; `152668` — `145/2020/NĐ-CP`. Bản dịch `vbpqta_11135` xuất hiện trong danh sách ứng viên nhưng không được chọn.

Tất cả selection giữ `decision=QUARANTINE`, `approved_for_retrieval=false`, `reviewer=null`, provenance/quyền sử dụng chưa xác minh, temporal `UNKNOWN`. Chưa có parser cấu trúc, chunks, index, nhãn gold hoặc benchmark AI.

## B. Thay đổi và lý do

- Tạo [scripts/inspect_local_legal.py](<D:/DOWNLOAD/Ligalli Illigal/scripts/inspect_local_legal.py>): hai lệnh `inspect` và `verify`; không truy cập mạng, không thay nguồn.
- Tạo [tests/test_inspect_local_legal.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_inspect_local_legal.py>): 13 kiểm thử bằng Parquet giả có nội dung DEMO, không phải luật thật.
- Tạo ba JSON ở mục A và báo cáo này; cập nhật [CHECKPOINT.md](<D:/DOWNLOAD/Ligalli Illigal/CHECKPOINT.md>). Không tổ chức lại repo hoặc phục hồi pipeline remote.

Quyết định, đánh đổi và giới hạn:

1. Metadata và relationships đọc theo batch 4.096 dòng, content ID đọc riêng. Bộ đếm ID và tập bộ ba quan hệ nằm trong RAM, nên RAM vẫn tăng theo số khóa/cạnh; chưa phải giải pháp ngoài bộ nhớ cho kho lớn tùy ý.
2. HTML đọc theo batch một dòng trong row group có mẫu, dừng sau vị trí cần. Phải đi qua một số dòng trước mẫu, không phải đọc ngẫu nhiên từng hàng. Trang Parquet hoặc một record lớn vẫn có thể dùng nhiều RAM. Chỉ năm mẫu được kiểm tra bằng BeautifulSoup; không xuất toàn bộ HTML/base64.
3. Chọn ID chỉ định và kiểm tra số hiệu, loại văn bản, tính duy nhất metadata/content. Không chọn record đầu tiên có số hiệu trùng. Điều kiện này không thay thế kiểm tra nguồn hay nhận diện ngôn ngữ cho toàn corpus.
4. Hash toàn bộ bytes trước/sau khảo sát để phát hiện nguồn thay đổi. Snapshot ID tính từ tên bảng → hash, không phụ thuộc đường dẫn/thời gian.
5. Từ chối ghi đè output hoặc ghi output vào thư mục raw. Validation/selection được ghi trước, manifest cuối làm dấu hoàn tất. Lỗi I/O giữa chừng có thể để lại output chưa đủ; chưa có rollback/resume.
6. Manifest ghi hash validation/selection. `verify` kiểm tra ba raw và hai output; không xác thực chữ ký hay độ tin cậy của manifest, không tự kiểm tra code hiện tại giống phiên bản đã chạy. Hash code và phiên bản thư viện được lưu để đối chiếu.
7. Schema phải đúng danh sách cột/string hiện tại; schema khác thì dừng rõ ràng, không tự đoán ánh xạ.

Revision để `null/UNVERIFIED`; commit lịch sử chỉ là `revision_hint_from_history`. Quan sát web trước T1 không được biến thành kết quả của lần chạy offline: lần khảo sát đó có hash khớp trang file `main` nhưng pointer relationships không nhất quán và không truy cập được file tại commit cố định. T1 chưa giải quyết việc này, chưa xác nhận nguồn chính thức/quyền phân phối lại.

## C. Luồng hoạt động

`input-dir` → hash/schema/footer → quét metadata → quét content ID/vị trí mẫu → kiểm tra năm HTML → kiểm tra relationships → ghép tập ID → selection có điều kiện chặn → hash raw lần hai → xuất JSON.

Ví dụ: `45/2019/QH14` có ID tiếng Việt và bản dịch. Công cụ chỉ chọn `139264` nếu số hiệu/loại đúng, metadata/content đều duy nhất và body mẫu có chữ. Dù đạt vẫn chỉ là chọn để audit.

Nhánh lỗi: thiếu file/schema sai/nguồn thay đổi → exit 2, không xuất bộ kết quả hoàn chỉnh. ID trùng hoặc selection thất bại → report `FAIL`, exit 1. Cảnh báo như đích quan hệ ngoài kho → `PASS_WITH_WARNINGS`, exit 0. Đọc status trong output, không chỉ exit code.

`verify` đọc manifest → hash lại raw và output → `PASS` hoặc danh sách file thiếu/sai hash; không cập nhật file.

## D. Hướng dẫn đọc code

Đọc [script](<D:/DOWNLOAD/Ligalli Illigal/scripts/inspect_local_legal.py>) theo thứ tự này:

| Hàm | Input → output; nhánh cần hiểu |
|---|---|
| `main`, `output_targets` | Tham số CLI → đường dẫn, guard không ghi đè, exit code |
| `inspect_inputs`, `sha256_file` | Raw → ba object; schema sai/hash thay đổi chặn xuất |
| `inspect_metadata`, `inspect_content_ids` | Parquet → bộ đếm, ứng viên, vị trí mẫu; ID mới là khóa ghép |
| `sample_html` | Vị trí mẫu → byte/hash/body-empty/bảng/ảnh; chuỗi HTML có chữ không chứng minh body có nội dung |
| `inspect_relationships` | Cạnh + tập ID metadata → thống kê; không suy hiệu lực từ nhãn |
| `select_pilot` | Bộ đếm/mẫu → selection hoặc lỗi; đọc các guard trước trường trạng thái |
| `write_artifacts`, `verify_snapshot` | Object → JSON/hash; bytes đã lưu → kiểm tra tính toàn vẹn |

Tiếp theo đọc class `LocalInspectionTests` trong [tests](<D:/DOWNLOAD/Ligalli Illigal/tests/test_inspect_local_legal.py>), ưu tiên `test_join_by_id_and_explicit_vietnamese_selection`, `test_duplicate_ids_block_selection_and_cardinality`, `test_empty_body_is_detected_despite_nonempty_html`, `test_verify_detects_changed_raw_and_artifact`.

Cần hiểu ngay: ID khác số hiệu; join khác thứ tự dòng; hash khác revision; trạng thái kỹ thuật khác phê duyệt pháp lý; mẫu khác toàn bộ. Có thể học sau: nén/trang Parquet, parser pháp lý, vector search, tối ưu RAM.

## E. Bằng chứng kiểm thử

Đã chạy từ `D:/DOWNLOAD/Ligalli Illigal`, với Python 3.14.2, PyArrow 25.0.1, BeautifulSoup 4.14.3:

```powershell
python -B -m unittest discover -s tests -p test_inspect_local_legal.py -v
python -B scripts/inspect_local_legal.py inspect --input-dir data/downloads/hf-legal --output-dir data/inspection/local-legal-v1 --selection data/selections/labor-pilot-3.json
python -B scripts/inspect_local_legal.py verify --manifest data/inspection/local-legal-v1/manifest.json
```

Bản cuối: **13/13 tests OK**; inspect exit 0, `PASS_WITH_WARNINGS` / `READY_FOR_AUDIT`; verify exit 0, `PASS`, failures rỗng. Không chạy inspect lại vào cùng output: công cụ từ chối ghi đè; nếu muốn lưu lần mới, chỉ định đường dẫn mới.

Lần test đầu lỗi setup/cleanup `PermissionError [WinError 5]` ở thư mục tạm Windows sandbox, chưa kiểm tra được logic. Đã chuyển fixture sang thư mục ngẫu nhiên dưới `tests`, kiểm tra đường dẫn tuyệt đối trước khi dọn. Lần cuối trong sandbox thành công, không còn fixture tạm dưới `tests`; không cần cài thư viện hay chạy ngoài sandbox.

Đã chạy thêm Python trực tiếp **không ghi file**, gọi lại `inspect_inputs` trên ba Parquet và so JSON: `validation_exact=true`, `selection_exact=true`, `manifest_except_time_and_output_refs=true`. Chỉ loại `created_at_utc` và `artifacts` khi so manifest vì lần hai giữ object trong RAM, chưa có tham chiếu output.

Test kiểm tra: ghép ID khi khác thứ tự dòng; không chọn bản dịch; chặn ID trùng; báo thiếu/mồ côi/ID rỗng; ngày lỗi/thiếu không được điền; body rỗng; cạnh lỗi; schema/file thiếu; lặp lại; raw không đổi; phát hiện hash đổi giữa lần đọc hoặc sau snapshot; chặn ghi đè/ghi vào raw.

Số dòng, SHA-256 và lỗi chính khớp khảo sát trước T1. Hash ba raw trước/sau giống nhau, verifier xác nhận lại. Không phát hiện lỗi chức năng còn tồn tại trong các ca đã kiểm tra; cảnh báo dữ liệu vẫn giữ nguyên, không sửa “cho sạch”.

Chưa chứng minh: nội dung pháp lý đầy đủ/đúng, hiệu lực theo thời điểm, quyền sử dụng, chất lượng toàn bộ HTML, nghĩa pháp lý mọi cạnh, khả năng mở rộng RAM, parser hoặc benchmark AI. Không có kết quả P9 precision/F1.

## F. Bàn giao để học cùng ChatGPT

Sao chép khối dưới và gửi file kèm; không cần gửi cả corpus:

> Tôi làm Tillegal, AI Core cho Project 9 kiểm chứng citation tích hợp Project 1 Legal RAG; là sinh viên CS năm 3. T1 vừa tạo công cụ kiểm tra Parquet local và chọn ba ID lao động; chưa có parser cấu trúc/retrieval/verifier AI. Giải thích tiếng Việt theo luồng dữ liệu, không giảng từng import. Thiết kế: PyArrow theo batch, join bằng ID string, hash trước/sau, output không ghi đè, revision chưa xác minh. Selection: 139264, 146696, 152668; không chọn bản dịch vbpqta_11135. Tất cả QUARANTINE, reviewer null. Kết quả thật: 171556 metadata, 170824 content, 1033255 relationships; 732 metadata thiếu content; 43128 cạnh có đích ngoài metadata/17706 ID đích; 259 self-edge; body rỗng 135139 trong năm mẫu có chủ đích. 13 tests qua, verify hash qua; chạy lại validation/selection giống hệt. Hãy dạy ID/số hiệu, join cardinality, snapshot/hash/revision, sampling, trạng thái lỗi; kiểm tra vì sao code chạy không chứng minh luật đúng. Đọc inspect_inputs → inspect_metadata/inspect_content_ids → sample_html/inspect_relationships → select_pilot → write_artifacts/verify_snapshot, rồi tests. Chưa rõ revision cố định, xuất xứ chính thức, quyền sử dụng và thời điểm áp dụng. Không tự kết luận tôi đã hiểu.

Gửi kèm sáu file:

- `D:/DOWNLOAD/Ligalli Illigal/scripts/inspect_local_legal.py`
- `D:/DOWNLOAD/Ligalli Illigal/tests/test_inspect_local_legal.py`
- `D:/DOWNLOAD/Ligalli Illigal/data/inspection/local-legal-v1/manifest.json`
- `D:/DOWNLOAD/Ligalli Illigal/data/inspection/local-legal-v1/validation.json`
- `D:/DOWNLOAD/Ligalli Illigal/data/selections/labor-pilot-3.json`
- `D:/DOWNLOAD/Ligalli Illigal/reports/T01-local-input-audit.md`

Artifact chứa thống kê, định danh, đoạn ngắn từ dữ liệu pháp luật và đường dẫn môi trường; không có API key, secret hay hội thoại người dùng.

## G. Kiểm tra hiểu biết

1. Vì sao không ghép dòng 100 metadata với dòng 100 content? Test nào mô phỏng rủi ro này?
2. Cùng số hiệu có hai ID: công cụ chọn bằng điều kiện nào? Các điều kiện ấy chưa chứng minh điều gì?
3. Vì sao HTML 83 byte chưa chắc dùng làm bằng chứng được? Vì sao không báo tỷ lệ lỗi toàn corpus từ năm mẫu?
4. File content đổi sau T1 thì phát hiện bằng lệnh nào? Nếu cả file và manifest bị thay thì giới hạn là gì?
5. `PASS_WITH_WARNINGS`, `READY_FOR_AUDIT`, `QUARANTINE` cùng xuất hiện có mâu thuẫn không? Thiếu ngày hết hiệu lực có được coi còn hiệu lực không?

Phỏng vấn:

- Bạn nhận diện và kiểm tra lại đầu vào thí nghiệm thế nào? Hash chưa bảo đảm được điều gì?
- Vì sao dùng batch và bộ đếm trong RAM cho pilot; khi kho lớn hơn cần đo gì trước khi đổi kiến trúc?

## H. Bước tiếp theo

Đề xuất duy nhất: **T2 — Audit bằng chứng ba văn bản pilot**. Input là manifest/selection T1 và nguồn chính thức; output là bảng audit mức văn bản, phạm vi điều khoản/ngày đã đối chiếu, bằng chứng, trạng thái quyền sử dụng và người xác nhận. Chỉ chấp nhận phạm vi đủ bằng chứng; thiếu nguồn/lịch sử phải giữ chưa xác minh. T1 đã kiểm soát định danh bytes và selection nhưng chưa đủ căn cứ dùng kiểm chứng pháp lý. Chờ phê duyệt T2.
