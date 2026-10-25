# State, hợp đồng dữ liệu và kiểm soát thực thi

## 1. State là gì? Dữ liệu nằm đâu?

State là hồ sơ của **một lần xử lý**, ví dụ một dict có kiểu trong RAM. Nó không phải vector database, không phải trí nhớ tự học và không dùng chung giữa các người dùng. Agent nhận một phần state do orchestrator cấp, trả kết quả có schema; orchestrator validate rồi mới cập nhật state.

| Dữ liệu | Trong lúc chạy | Lưu để kiểm tra lại |
|---|---|---|
| Câu hỏi/văn bản gốc | `request.original_input`, bất biến | Input đã giảm thông tin riêng tư trong run record |
| Query đã phân tích | `query_plan` | Step event; không ghi đè câu hỏi gốc |
| Raw luật tải về | Không nhét cả kho vào state | `data/raw/<snapshot>/` + source manifest |
| Đoạn luật chuẩn hóa | Đọc theo ID | `data/processed/<corpus_version>/` |
| Search candidates | `evidence_by_id` | IDs, snapshot refs, scores trong trace |
| Context đưa vào model | Danh sách evidence IDs + text có giới hạn | Exact prompt/input artifact theo retention policy |
| Claim/citation của người dùng | `original_claims`, `original_citations` | Giữ raw text, spans và bản gốc |
| Draft do hệ thống tạo | `drafts[version]` | Bất biến từng version; report gắn đúng version |
| Nhãn Verify | `verification_reports` | Gold/prediction không ghi cùng trường |
| Budget và counters | `control` | Orchestrator ghi trước/sau mỗi step |
| Lịch sử hội thoại sản phẩm | Chỉ context được backend truyền | Backend nhóm quản lý; AI không tự giữ mọi hội thoại |

Prototype lưu `runs/<request_id>/input.json`, `events.jsonl`, `result.json`, `manifest.json`. Snapshot đầy đủ chỉ cho dữ liệu demo/được phép; log vận hành chỉ giữ metadata cần thiết, có retention cấu hình. Không log API keys. Không dùng input người dùng để tự cập nhật corpus.

## 2. Hợp đồng miền tối thiểu

T2 đã hiện thực `DocumentVersion` cho staging và xuất JSON Schema. T3 bổ sung cây cấu trúc, block và chunk thử nghiệm ở mục 2.2. Các object runtime khác vẫn là đặc tả, chưa phải hệ thống điều phối đã chạy. Các hợp đồng này không cấp quyền phê duyệt pháp lý.

| Object | Trường bắt buộc/chính |
|---|---|
| Request | request_id, mode, original_input, as_of_date (nullable), jurisdiction, conversation_context có giới hạn |
| QueryPlan | intent, issues[], search_queries[], filters, missing_facts[], clarification_questions[], assumptions[] |
| DocumentVersion (staging v1 đã có) | document_id, document_version_id, source_id, source_record_id, source_snapshot_id, source_version nullable, content/content_format/content_sha256, raw_ref, source_url/collected_at nullable, title/document_number, effective_from/to, effect_status_reported, status_observed_at, usage_policy và các trạng thái chưa xác minh |
| Chunk (T3-FIX thử nghiệm) | chunk_id, document_id, document_version_id, node_id/parent_id, ancestor_ids, scope, appendix/form/chapter/section/article/clause/point nullable, block_id/block_kind, attachment_status, text/text_sha256, text_start/end, source_locator, issues và trạng thái kế thừa |
| Evidence (đề xuất) | evidence_id, chunk_id, document_id, document_version_id, source_locator, text hoặc content_ref bất biến, content_hash, corpus_snapshot_id, retrieval_method, rank_scores, collected_at nullable, provenance_status |
| Claim | claim_id, draft_version hoặc original_input_id, text, original_span, claim_type, needs_citation, citation_ids[] |
| Citation | citation_id, raw_text, original_span, document_ref, article/clause/point, url nullable, requested_version nullable, linked_claim_ids[] |
| Resolution | citation_id, source_status, identity_status, resolved_document_version nullable, cited_evidence_ids[], errors[] |
| Verification | claim_id, citation_id nullable, draft_version, cited_evidence_ids[], support_label, source_status, identity_status, temporal_status, jurisdiction_status, quoted_spans[], reason_codes[], explanation, verdict |
| RepairProposal | proposal_id, original_claim_id, original_citation_id, candidate_citation, candidate_evidence_ids[], candidate_report, adopted_in_draft_version nullable |
| FinalResponse | request_id, status, answer nullable, verification_report, proposals[], limitations[], stop_reason, corpus_version, trace_ref |

`score` của BM25/dense/reranker không phải xác suất pháp lý đúng. `confidence` do LLM tự báo không được dùng thay evidence hoặc hiệu chỉnh thống kê.

Khóa nội bộ document ID do hệ thống quản lý phải namespaced theo nguồn; không coi số “Điều 3” là duy nhất. `chunk_id` ổn định theo document/version/locator/hash. Hai đoạn giống chữ từ hai nguồn khác nhau không được mất provenance khi dedupe.

### 2.1. Hợp đồng dữ liệu T2 và ranh giới bàn giao

Luồng: dữ liệu nguồn → adapter theo nguồn → `DocumentVersion` nội bộ → parser/chunking → retrieval/verifier. T2 có adapter HF local và ba record pilot; chưa có adapter dữ liệu crawl thật của nhóm. Fixture trung lập được kiểm thử qua cùng bộ đọc, không import HF/PyArrow/BeautifulSoup. T3 đã thêm parser đọc DocumentVersion HTML/text, không phụ thuộc schema HF; chưa kiểm thử bộ crawl thật. T4 thêm BM25 thử nghiệm ở mục 2.4; verifier chưa được triển khai.

Code: [data_contracts.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/data_contracts.py>) và [hf_local.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/adapters/hf_local.py>). Schema trao đổi: [document.schema.json](<D:/DOWNLOAD/Ligalli Illigal/data/staging/labor-pilot-3/document.schema.json>). Schema mô tả cấu trúc; bộ kiểm tra Python bổ sung tính hợp lệ ngày, hash và quan hệ giữa các ID. JSON thiếu trường hoặc dư trường bị từ chối; trường nullable phải có mặt và nhận `null` khi chưa biết.

| Nhóm bàn giao | Quy tắc tối thiểu |
|---|---|
| ID | Người cung cấp giữ `source_record_id` ổn định. AI gán namespace `source_id`; `document_id = source_id::source_record_id`, hai thành phần không chứa `::`. Không dùng số hiệu/vị trí dòng làm khóa. Thay nhà cung cấp có thể tạo document_id khác; không tự nhập hai nguồn thành một văn bản |
| Nhận diện | `document_number`, `title`, `document_type`, `issuing_authority`, `language`; thiếu dùng null. Phân biệt bản dịch/hợp nhất với bản gốc bằng bằng chứng, không chỉ số hiệu |
| Nội dung | `content` không rỗng, `content_format` là `html` hoặc `text` trong v1. Giữ raw; `raw_ref` gồm URI file/nguồn, hash file, tên khóa và giá trị record. PDF/binary chưa được nhận trực tiếp qua schema này |
| Xuất xứ | `source_url` là URL HTTP(S) thực sự có bằng chứng; `collected_at` là thời điểm thu thập có múi giờ. Chưa biết dùng null; thời điểm chạy adapter chỉ nằm ở manifest và không thay thời điểm crawl |
| Phiên bản | `source_snapshot_id` nhận diện đợt nguồn; `source_version` chỉ điền khi có thông tin đã xác minh. Với HF đây là revision dataset, không phải phiên bản hiệu lực pháp lý. AI tính `content_sha256` từ chuỗi nội dung UTF-8 và `document_version_id` từ nội dung/hash, metadata, trạng thái và snapshot nguồn |
| Hiệu lực | `issued_on`, `effective_from/to` dạng YYYY-MM-DD hoặc null; `effect_status_reported` giữ nguyên trạng thái nguồn khai báo, `status_observed_at` nullable. Không suy temporal VALID từ các trường này |
| Biến đổi/lỗi | `processing_steps` ghi việc adapter thực sự đã làm; `issues` ghi dữ kiện thiếu, ngày không hợp lệ và cấu trúc chưa xử lý. Không mặc định đã biết lịch sử làm sạch của upstream |

`document_version_id` là fingerprint kỹ thuật của record materialized, không chứng nhận phiên bản luật. Đổi nội dung, metadata, trạng thái hoặc snapshot nguồn làm đổi ID này; chỉ đổi URI vị trí lưu raw không làm đổi nó. Chuỗi HTML giữ nguyên, kể cả bảng, ảnh nhúng, khoảng trắng và xuống dòng. Hash này khác hash bytes của cả file Parquet. Các record dùng namespace khác nhau vẫn được giữ xuất xứ riêng.

Output T2: [documents.jsonl](<D:/DOWNLOAD/Ligalli Illigal/data/staging/labor-pilot-3/documents.jsonl>) và [manifest staging](<D:/DOWNLOAD/Ligalli Illigal/data/staging/labor-pilot-3/manifest.json>). Ba mức nhận diện khác nhau: snapshot raw T1, snapshot staging T2, rồi corpus/index snapshot tương lai; T2 chưa có corpus/index (`null`). Chỉ `usage_policy=EXPERIMENTAL_ONLY`; tất cả `legal_approval=QUARANTINE`, `provenance_status=UNVERIFIED`, `temporal_status=UNKNOWN`, `rights_status=UNVERIFIED`. Schema v1 không hỗ trợ tự chuyển các trường này thành VERIFIED; quy trình promotion có bằng chứng sẽ được thiết kế riêng khi cần. Hiện vật T1 và cờ `approved_for_retrieval=false` giữ nguyên.

Metadata HF không cung cấp URL, thời điểm crawl, thời điểm quan sát trạng thái hoặc ngôn ngữ: adapter giữ null và ghi issue; không suy từ tên dataset hay ngày import. Ngày sai chuyển null kèm giá trị gốc trong issue; metadata gốc vẫn truy lại qua manifest T1. Bảng/ảnh được giữ nguyên nhưng chưa diễn giải. Record chỉ có ảnh/không có body text bị từ chối để xem xét riêng. Parser thử nghiệm phải đọc đúng các giới hạn này, không coi chúng là chứng cứ pháp lý đã duyệt.

Phân công cần thống nhất với nhóm, không giả định người crawl đã thực hiện:

| Việc | Người crawl/cung cấp | AI Core |
|---|---|---|
| Thu thập/nguồn | Bàn giao raw, ID ổn định, URL/thời điểm, lỗi thu thập, thông tin quyền và bằng chứng nguồn nếu có | Kiểm tra schema/hash/định danh/xuất xứ; phản hồi thiếu hoặc sai, không xây crawler |
| Làm sạch/cấu trúc | Khai báo biến đổi đã làm, giữ bản trước biến đổi; cung cấp cấu trúc nếu có | Chuẩn hóa và kiểm tra bảo toàn nội dung; chịu trách nhiệm cấu trúc dùng trong chunk/resolver, không tin cấu trúc upstream mặc định |
| Hiệu lực | Bàn giao thông tin/quan hệ và nguồn chứng minh, không chỉ nhãn suy đoán | Biểu diễn UNKNOWN khi thiếu bằng chứng; kiểm tra applicability theo yêu cầu; nhờ người phù hợp đối chiếu các nhãn pháp lý khó |
| Cập nhật | Manifest đợt bàn giao có schema_version, delivery_id, file/hash, loại full/delta; phân biệt thiếu trong đợt và rút/xóa rõ ràng | Tạo staging/corpus mới, kiểm tra parsing/retrieval và rà các mẫu gold bị ảnh hưởng trước khi kích hoạt |

Manifest giao nhận của nhóm và adapter cho full/delta mới là yêu cầu bàn giao, chưa được hiện thực. Không tự đồng bộ HF. Tiếp tục baseline trên corpus tạm có định danh rõ; mỗi benchmark phải ghi corpus/snapshot, parser/index, bộ nhãn và cấu hình model. Không chuyển điểm benchmark cũ thành điểm corpus mới.

Để tương thích phương án điều phối: EvidenceBundle sau này dùng cùng document_version_id, hash, locator và corpus snapshot; phân biệt lỗi tìm nguồn với kết luận support. Runtime giữ request/input/draft version riêng, model không được sửa định danh/quyền/ngân sách. T2 chưa tạo task envelope, scheduler, PostgreSQL queue hay multi-agent runtime; giữ thứ tự baseline trước hạ tầng điều phối bền vững.

### 2.2. Cấu trúc và chunk T3 — hợp đồng thử nghiệm

Mục này lưu mô tả baseline T3 v1. T3-FIX ở mục 2.3 là phiên bản code/output mới; artifacts T3 v1 được giữ nguyên để so sánh.

Code: [legal_parser.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/legal_parser.py>); kiểm thử: [test_legal_parser.py](<D:/DOWNLOAD/Ligalli Illigal/tests/test_legal_parser.py>). `DocumentVersion` T2 và raw không đổi. Parser chỉ dùng thư viện chuẩn Python; BeautifulSoup dùng trong kiểm thử đối chiếu văn bản, không phải phụ thuộc của parser.

| Hiện vật | Nội dung/hợp đồng |
|---|---|
| [structures.jsonl](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3/structures.jsonl>) | Mỗi document/version một record: parser_version/max_chars, nodes, blocks, excluded_segments và issues |
| Node | node_id, kind, label nullable, parent_id, scope, heading_block_id nullable, issues; cha xuất hiện trước con; root là document |
| Block | block_id, node_id, kind text/table, text/text_sha256, source_start/end, segments và issues; segments giữ span nguồn cho text/entity/image/separator/empty_table |
| [chunks.jsonl](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3/chunks.jsonl>) | Mỗi chunk thuộc đúng một block và node; có ancestor_ids để downstream lấy phần cha; giữ các trạng thái EXPERIMENTAL_ONLY/QUARANTINE/UNKNOWN từ DocumentVersion |
| [validation.json](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3/validation.json>) | Thống kê từng văn bản, cảnh báo, kiểm tra trace/coverage; PASS_WITH_REVIEW_ITEMS không phải độ chính xác pháp lý |
| [manifest.json](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3/manifest.json>) | Pin staging, code, Python, cấu hình và hash output; processed_snapshot_id riêng, corpus_snapshot_id/index_version vẫn null |

`scope` phân biệt preamble/main/closing/appendix/form/quoted. Không dùng số điều làm ID; ID gồm document_version, parser version, vị trí và hash; chunk ID còn phụ thuộc max_chars. `parent_id` của chunk trỏ tới node cấu trúc, không phải chunk khác. `article/clause/point` trong scope quoted chỉ là ngữ cảnh bên ngoài đoạn trích; không resolve “Điều 54” trong đoạn sửa đổi thành Điều 54 của văn bản hiện tại. Parser giữ đoạn trích nguyên khối logic, chưa phân tích cấu trúc pháp lý bên trong.

Hai hệ offset đều đếm **Unicode code point của Python**, khoảng `[start, end)`, không phải byte UTF-8 hoặc đơn vị UTF-16 của JavaScript. `source_start/end` của block và `source_locator.block_source_start/end` của chunk trỏ vào chuỗi content gốc T2. `text_start/end` trỏ vào text đã chuẩn hóa của block. Raw locator của chunk bao toàn block, không khẳng định là raw span chính xác của riêng fragment; dùng segments để phát lại nguồn. Backend cần thống nhất chuyển đổi offset nếu dùng JavaScript.

Chuẩn hóa chỉ giải mã HTML entity và gộp khoảng trắng; không sửa từ, dấu câu, số tiền hay phủ định. Head/script/style/comment được loại khỏi text có dấu vết loại trừ. Không diễn giải CSS. Một paragraph/khối ngoài bảng là một block; bảng lồng nằm trong block bảng ngoài cùng. Text bảng tuyến tính chỉ để dò; hình dạng ô/cột/rowspan/colspan phải đọc từ raw span, chưa đủ làm bằng chứng cho phép tính. Ảnh giữ span và marker `[IMAGE]`, không OCR; bảng rỗng có `[EMPTY_TABLE]`.

Chunk mặc định tối đa 1.800 ký tự, không phải token. Không gộp qua block/phạm vi. Block dài ưu tiên ranh giới câu/dấu chấm phẩy, rồi khoảng trắng; trường hợp buộc cắt được gắn `SPLIT_BLOCK_REQUIRES_CONTEXT`. Downstream phải lấy đủ parent/block trước khi dùng fragment kiểm chứng để không mất phủ định/điều kiện. Ba mẫu hiện tại không có block vượt mức này; chưa đo chất lượng retrieval của kích thước chunk.

Đoạn không nhận diện vẫn giữ text và cảnh báo; ngữ cảnh của đoạn không đánh số là heuristic. Nhãn nguồn lặp hoặc lệch phụ lục được báo, không tự sửa. `validate_result` kiểm tra phát lại block từ nguồn, cha/định danh/trạng thái và các chunk phủ kín text không chồng lặp; không chứng minh mọi quan hệ cấu trúc đúng. Khi đổi corpus phải chạy lại các ca parser đã pin và rà mẫu bị ảnh hưởng trước retrieval/evaluation.

### 2.3. T3-FIX — attachment và validator

Phiên bản parser hiện tại: `legal-structure-v1.1`; schema của **processed result/manifest** là `2`. DocumentVersion và schema staging T2 vẫn là `1`, không thay đổi. Output mới ở [manifest T3-FIX](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3-t3-fix/manifest.json>), [structures](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3-t3-fix/structures.jsonl>), [chunks](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3-t3-fix/chunks.jsonl>) và [validation](<D:/DOWNLOAD/Ligalli Illigal/data/processed/labor-pilot-3-t3-fix/validation.json>). Không ghi đè output T3 v1.

Block và chunk có thêm `attachment_status`:

| Giá trị | Ý nghĩa |
|---|---|
| STRUCTURAL | Có dấu hiệu cấu trúc theo rule đang dùng, hoặc ranh giới/quan hệ cục bộ rõ; không chứng nhận đúng luật |
| HEURISTIC | Gán theo ngữ cảnh gần nhất; chưa có bằng chứng độc lập rằng mọi parent đều đúng |
| REVIEW_REQUIRED | Chưa đủ căn cứ để tuyên bố địa chỉ chính xác; node/labels có thể chỉ là ứng viên hoặc ngữ cảnh cấp cao |

Đoạn không đánh số sau điểm vẫn giữ parent ứng viên, nhưng có `REVIEW_REQUIRED` và `ATTACHMENT_REVIEW_REQUIRED`; không nâng mọi đoạn lên khoản. Ngoại lệ có bằng chứng cục bộ: đoạn mở đầu “Các văn bản quy định tại điểm a, điểm b khoản này…” được gắn về khoản khi các điểm được nhắc thực sự là con của khoản đang xét; ghi `SHARED_CLAUSE_REFERENCE`. Numbering dạng `4...` chưa resolve bỏ liên kết tới khoản/điểm trước, giữ context từ điều trở lên và cảnh báo; phần tiếp nối giữ trạng thái review cho đến cấu trúc rõ tiếp theo.

`form_tail` là node con của form, scope vẫn `form`, không phải điều. Nó bắt đầu ở “Ghi chú:” sau điều trong mẫu, hoặc bảng bắt đầu “Nơi nhận:” có chữ ký “CHỦ TỊCH”. Nội dung đuôi mẫu không kế thừa article/clause/point; `FORM_LEVEL_TAIL` đi xuống chunks. Quy tắc này có phạm vi hẹp, không phải detector chữ ký phổ quát.

Các tiết dạng a1)/b1)/c2) có `SUBPOINT_NOT_RESOLVED` và `REVIEW_REQUIRED`; không có địa chỉ tiết đã resolve trong schema. `SOURCE_TEXT_POSSIBLY_INCOMPLETE` hiện chỉ ghi anomaly đã review ở content hash/offset/text chính xác của record 152668, không tự bổ sung nội dung hoặc suy lỗi cho mọi câu kết thúc bằng “do”.

`validate_result` kiểm tra identity/hash cấp result, schema/parser version, fingerprint node/block/chunk, nhãn theo ancestry, attachment/issue propagation, offset unit và end-exclusive. Completeness lấy DocumentVersion gốc để trích lại danh sách block và phần loại trừ, rồi so text/span/segments/thứ tự/số lượng. Tags/attributes HTML không được coi là prose; head/script/style/comment/whitespace có quy tắc loại trừ, entity và marker có segment kind riêng. Không dùng tỷ lệ bytes raw so với text. Xóa cả block lẫn chunk vẫn bị phát hiện.

Kiểm tra completeness chứng minh output phù hợp **chính sách extractor hiện tại**; không chứng minh extractor không có lỗi chung hoặc nội dung pháp lý đầy đủ. Test đối chiếu bằng bộ đọc khác vẫn cần. Validator mới từ chối processed schema/parser cũ thay vì âm thầm diễn giải; so baseline bằng content/version + raw locator và text. Parser version tham gia fingerprint nên toàn bộ ID node/block/chunk đổi có chủ đích; cách chia chunk, text và raw offsets giữ nguyên.

T3-FIX được giữ nguyên khi triển khai T4. Cách trả kết quả retrieval và cảnh báo được hiện thực ở mục 2.4; không coi ancestry tự nhất quán là nguồn đã xác minh.

### 2.4. T4 — BM25 retrieval thử nghiệm

Code: [bm25_retrieval.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/bm25_retrieval.py>). Input là processed schema 2/T3-FIX có snapshot được chọn tường minh; build kiểm tra hash/manifest, staging DocumentVersion và `validate_result` trước khi tạo index. T4 không sửa chunk, raw hay schema T2/T3-FIX. Output riêng: [manifest BM25](<D:/DOWNLOAD/Ligalli Illigal/data/indexes/labor-pilot-3-t4-bm25/manifest.json>).

Index schema 1 là schema **chỉ mục mới**, không phải downgrade processed schema. `index_id=bm25:<SHA-256 canonical payload>` bao gồm source snapshot/hash, tokenizer, config, metadata, chunks, nodes và term statistics. Manifest pin code hash; load từ chối runtime khác để yêu cầu rebuild tường minh. Không tự activate corpus; `usage_policy=EXPERIMENTAL_ONLY`, `corpus_snapshot_id=null`, `approved_for_legal_verification=false`. Cờ approval trong T1/T2/T3-FIX không đổi.

Tokenization áp dụng giống nhau cho query và chunk.text: NFC + casefold, giữ dấu tiếng Việt và chữ/số, dấu câu/underscore là ranh giới; bỏ marker `[IMAGE]`/`[EMPTY_TABLE]` khỏi tokens, giữ text gốc. Không bỏ stopword/phủ định, không stemming, không tách từ đa âm tiết. Chỉ chấm text của chunk; title/document_number/ancestry giữ làm metadata, không boost hoặc nối thêm vào text. BM25 Okapi với positive IDF, k1=1.2/b=0.75; các giá trị này chưa được tune trên gold. Query term trùng tính một lần; score bằng nhau phân thứ tự theo chunk_id. Tất cả scope/attachment được giữ, không lọc form/table/review mặc định.

`BM25Index.search(query, top_k=5)` trả `schema_version`, `retrieval_method`, `index_id`, source snapshot refs, query/tokens/unmatched_terms, status, `latency_ms` và `results`. K là integer 1–100, query tối đa 10.000 ký tự. Query không có token trả `EMPTY_QUERY`; không có từ khớp trả `NO_MATCH`; có kết quả trả `OK`. Không bù đủ K bằng chunk có score 0. Không tìm thấy không chứng minh quy định không tồn tại.

Mỗi hit có `rank` (từ 1), `bm25_score`, `matched_terms`, `chunk` nguyên vẹn, `document` metadata T2 không chứa content, `address_status`, `exact_citation_verified=false`, `legal_evidence_status=NOT_EVALUATED`, `context_review_required=true`, `context_expanded=false`, `cautions` và `context_refs`.

| Attachment của chunk | address_status của hit |
|---|---|
| STRUCTURAL | RULE_BASED_UNVERIFIED — địa chỉ theo rule, chưa xác minh |
| HEURISTIC | HEURISTIC_CANDIDATE — parent/địa chỉ ứng viên |
| REVIEW_REQUIRED | REVIEW_REQUIRED — không được khẳng định exact citation |

Mọi issue gốc truyền vào cautions; thêm cảnh báo bảng cần raw layout, quoted chỉ mang địa chỉ context bên ngoài, heading có thể cần body. Các cờ ảnh chưa OCR, fragment, tiết unresolved và nguồn nghi thiếu nội dung được giữ. Score không phải xác suất đúng luật, support hay temporal validity.

`context_refs` chứa snapshot, ancestor IDs, heading chunk IDs và toàn bộ chunk IDs cùng block theo normalized text_start. Đây là tham chiếu để downstream lấy thêm ngữ cảnh, **chưa tự mở rộng điều/khoản hoặc đánh giá đủ evidence**. Locators giữ Unicode code point `[start,end)` theo T3; token positions không được dùng thay source offsets.

Build/export/load chạy local, không cần thư viện mới/API. Index JSON chứa chunks/nodes/metadata/postings, nạp toàn bộ vào RAM; load kiểm tra hash và tính lại term statistics. Integrity là kiểm tra nhất quán kỹ thuật, không phải chữ ký xác thực hoặc chứng minh nguồn luật. Bộ đo [summary](<D:/DOWNLOAD/Ligalli Illigal/data/evaluation/t4-bm25-technical-smoke/summary.json>) ghi rõ snapshot, môi trường và latency; Recall@K/MRR null vì chưa có gold.

### 2.5. T5 — nhãn retrieval và cổng đánh giá

T5 theo bước tiếp theo của T4: chuẩn bị bộ nhãn và công cụ evaluation, chưa triển khai citation resolver/verifier. Code: [retrieval_evaluation.py](<D:/DOWNLOAD/Ligalli Illigal/ai_core/retrieval_evaluation.py>), [prepare_retrieval_review.py](<D:/DOWNLOAD/Ligalli Illigal/scripts/prepare_retrieval_review.py>). Bộ [draft](<D:/DOWNLOAD/Ligalli Illigal/data/annotations/t5-retrieval-review-v1/dataset.draft.json>) và [hướng dẫn review](<D:/DOWNLOAD/Ligalli Illigal/data/annotations/t5-retrieval-review-v1/REVIEW.md>) gồm 8 dev/4 test dự kiến. **Chưa phải gold**; toàn bộ relevant_units rỗng, reviewer null, PENDING_HUMAN_REVIEW. Không dùng các câu/nhãn này làm nội dung index hoặc tune T4.

Annotation schema 1 pin index_id và processed_snapshot_id. Mỗi case có question_id, question, family_id, split, as_of_date=null, answerability, proposed_units, relevant_units, evidence và review. Evidence pin chunk_id, quote, text hash, Unicode offsets vào chunk.text và source_locator T3-FIX. Không đồng nhất offsets quote với raw HTML. Bản source_context giữ metadata, các chunk cùng Điều ứng viên và raw block excerpts để đọc lại; parent vẫn là kết quả parser cần người review kiểm tra.

Nhãn chỉ đánh giá relevance trong snapshot local (`LOCAL_SNAPSHOT_RELEVANCE_ONLY`), không xác nhận hiệu lực pháp lý. Người review phải đọc nguồn, kiểm tra mapping Điều, rà nguồn thay thế và mức đầy đủ tập relevant; giấu prediction khi gán nhãn. `ACCEPTED_HUMAN` yêu cầu reviewer_type=human, reviewer_id, timestamp có múi giờ, notes, ANSWERABLE, relevant_units không rỗng, evidence cho mỗi unit và đủ các cờ review. Đây là khai báo do người dùng cung cấp, không phải xác thực danh tính bằng hệ thống. AI không tự điền các xác nhận này.

`EXCLUDED_HUMAN` cần người đọc nguồn và lý do, relevant_units rỗng; thống kê riêng, không đổi thành miss hoặc answerable. UNKNOWN/UNANSWERABLE/AMBIGUOUS không được tính vào Recall/MRR. Một case còn PENDING trong split đang chọn chặn toàn bộ phép đo split đó. Test còn pending không chặn freeze dev, nhưng không được chạy test cùng dev. Chặn query trùng sau NFC/casefold, family hoặc Điều nguồn giao nhau giữa splits; phát hiện paraphrase leakage vẫn cần người kiểm tra.

Policy `article-discovery-strict-v1`: unit là document_version_id + node Điều, tách main/form và văn bản khác dù cùng số Điều. Lấy tối đa **100 chunk** từ BM25 T4, duyệt theo rank và giữ lần xuất hiện đầu mỗi unit. Chỉ STRUCTURAL, ngoài quoted, không có SOURCE_TEXT_POSSIBLY_INCOMPLETE và có ancestor Điều mới được map vào article unit; các hit khác thành unresolved-block và **vẫn chiếm rank**, không xóa để làm đẹp metric. Dedupe fragment cùng block bất định. HEURISTIC/REVIEW_REQUIRED không tự nhận credit đúng Điều. Đây là quy tắc chấm bảo thủ, có thể bỏ credit của parent heuristic thực ra đúng; chưa phải citation resolver hay kết luận luật.

Heading Điều được tính cho mục tiêu **tìm đúng vị trí Điều**, không chứng minh đã lấy đủ body hoặc evidence. Bảng/ảnh/quoted/nguồn thiếu không được coi là bằng chứng đầy đủ bởi metric này. Policy không thay ranking BM25 và không tự mở rộng context.

Tính macro Recall@5/@10 và **MRR@5/@10 có cutoff**, không gọi MRR toàn danh sách. Mẫu số Recall là số relevant article units đã được review đầy đủ; macro mean trên các case ACCEPTED_HUMAN của split. Nếu 100 chunk không cho đủ K unique units, không lấy thêm hoặc bù; report ghi short_unit_list_at_max_k. Không dùng metric này thay chất lượng evidence/support.

`inspect` chỉ validate và ghi readiness, không search. `freeze` chỉ chạy khi split sẵn sàng, xuất dataset+manifest hash ở thư mục mới trước retrieval. `evaluate` pin frozen labels/index/code, chỉ chạy split đã freeze, ghi predictions và report riêng; không ghi vào nhãn hoặc index. T4 code/index giữ nguyên. Test hiện là `PROVISIONAL_NOT_INDEPENDENT_HELD_OUT`, không tuyên bố đánh giá held-out độc lập. Kết quả hiện tại: cả hai split cần human review, **metrics=null**, không có predictions T5 trên dữ liệu thật.

### 2.6. T6.1 — Evidence Builder đã triển khai

Phạm vi hiện hành T6 theo phê duyệt baseline-first: một retrieval, một generation, một semantic verification; chưa triển khai toàn pipeline. Các vòng search/repair và budgets nhiều lượt ở mục 3–5 dưới đây vẫn là thiết kế tương lai, **không áp dụng để mở rộng T6**. T6.1 không gọi search hoặc LLM. T5 gold vẫn chờ human review.

API Python: `EvidenceBuilder(index, EvidenceBudget()).build(retrieval_response, request_id=...)`. Index phải được nạp qua `bm25_retrieval.load_index` để kiểm manifest/hash; builder dùng bản sao public `to_dict`, không sửa index. Kiểm response thuộc đúng index/snapshot, chunk/document nguyên vẹn, rank/score hợp lệ và không nâng verification. Không tính lại BM25 score hoặc đánh giá relevance.

Output schema 1, builder `evidence-builder-v1`: query/request/index/source snapshot, budget, evidence, groups, omissions, limitations và trace. Mỗi evidence giữ document metadata, toàn chunk/ancestry, `article_id` từ parser (nullable, luôn là ứng viên chưa xác minh pháp lý), quote nguyên normalized chunk, SHA-256, normalized locator và raw source locator. Raw locator bao **toàn block**, Unicode code point `[start,end)`, không phải vị trí raw của riêng fragment. Không tạo URL/thời điểm còn thiếu.

`evidence_id = evidence:SHA256(canonical_json([builder_version,index_id,chunk_id,text_sha256]))`. `bundle_id = bundle:SHA256(canonical_json(bundle_without_bundle_id))`, bao request/query/config/content; không chứa latency biến thiên. ID/hash chỉ định danh nội dung, không chứng minh pháp lý hoặc xác thực người tạo. Downstream chỉ được nhận evidence IDs trong bundle của request hiện tại.

Giữ các seed theo rank trước; sau đó thêm fragment cùng block, heading ancestor cùng scope, và chunks của cùng Điều ứng viên theo thứ tự nguồn. Khóa cửa sổ gồm version/scope/ID phụ lục/ID mẫu/ID Điều; không nối theo số Điều. Seed REVIEW_REQUIRED hoặc quoted không mở rộng body Điều, vẫn có same-block và ancestor-heading ứng viên. HEURISTIC được mở context nhưng giữ cảnh báo, không được tự nhận credit của policy T5. Context có thể chứa các chunk REVIEW_REQUIRED và luôn giữ trạng thái từng chunk.

Mặc định tối đa 32 chunk và 24.000 Unicode code points của quote duy nhất; không cắt quote, không coi đây là token limit hay giới hạn tổng JSON. Dedupe evidence nhưng giữ nhóm theo từng hit với rank/score/role. Mỗi nhóm liệt kê `omitted_chunk_ids` và `seed_included`. `ASSEMBLED` = cửa sổ đã chọn được đóng gói; `PARTIAL` = có omission do budget; `EMPTY` = không có evidence được đưa vào (query rỗng/OOV hoặc budget quá nhỏ). **Không nhãn nào khẳng định đủ căn cứ trả lời.** `context_sufficiency=NOT_EVALUATED` ở mọi nhóm; không tự mở dẫn chiếu/ngoại lệ ngoài Điều.

STRUCTURAL → RULE_BASED_UNVERIFIED; HEURISTIC → HEURISTIC_CANDIDATE; REVIEW_REQUIRED giữ nguyên. `exact_citation_verified=false`, `legal_evidence_status=NOT_EVALUATED`, nguồn EXPERIMENTAL_ONLY/QUARANTINE/UNVERIFIED/UNKNOWN và corpus chính thức null. Bảng/ảnh/quote/heading/nguồn thiếu giữ cảnh báo, không thành evidence pháp lý đầy đủ mặc định. Không có claim verification hoặc final-answer rendering trong T6.1.

### 2.7. T6 hiện hành — Basic RAG, không Citation Verification

Phê duyệt mới nhất thay phạm vi generation + verification trước đây: T6 chỉ BM25 → Evidence Builder → một generation → draft + candidate citations + trace. Mục 2.6 giữ nguyên hợp đồng Evidence Builder; kế hoạch verification của T6 ở các đoạn lịch sử không còn áp dụng. Các state/loops/verdicts đề xuất trong mục 3 trở đi là thiết kế tương lai, chưa triển khai ở T6.

API `BasicRAG(index, provider, evidence_budget=None).answer(question, request_id=..., top_k=5)` dùng T4/T6.1 nguyên trạng. `GenerationProvider.generate(messages) -> str` có hai implementations: mock deterministic và adapter HTTP live. Không thêm verifier hoặc semantic verdict.

Generation output là JSON object đúng ba keys: `draft_answer` (nonblank, tối đa 12.000 ký tự), `candidate_evidence_ids` (list ID duy nhất trong bundle request hiện tại), `abstain` (boolean). Không abstain thì phải có ít nhất một ID; abstain thì IDs rỗng. Chặn JSON có duplicate key/non-finite constant, markdown fences, field lạ, output quá 65.536 ký tự, IDs sai/trùng/ngoài bundle. Đây chỉ là schema/reference validation; không kiểm nội dung bản nháp, citation được viết tự do trong prose, quote/hash so nguồn, hoặc semantic support. Candidate citations gắn toàn draft, chưa có claim-level mapping.

Response schema 1 gồm request/question/status/answer/candidate_citations/evidence_bundle/trace/warnings/error. Status: DRAFT_UNVERIFIED, ABSTAINED_UNVERIFIED, NO_EVIDENCE, FAILED. Luôn `verification_status=NOT_PERFORMED`, corpus chính thức null và usage EXPERIMENTAL_ONLY. Citation payload lấy từ bundle, không cho model tạo source metadata; thêm `citation_status=CANDIDATE_UNVERIFIED`. Trạng thái nguồn/hiệu lực cũ giữ nguyên. Membership hợp lệ không đồng nghĩa citation prose hoặc câu trả lời đúng.

Mỗi request tối đa một retrieval và một generation; không evidence thì không generation. Context PARTIAL vẫn có thể tạo draft nhưng giữ omissions/cảnh báo. Trace chứa retrieval response, bundle ở cấp response, prompt version/input/hash, provider mode/model, raw generation (giới hạn và đánh dấu truncation), parsed draft nếu hợp lệ, schema-check status, counters và elapsed_ms từng stage. Không log API key, HTTP error body hoặc exception text. Trace có câu hỏi và nội dung nguồn, cần xem là dữ liệu request khi chia sẻ. `llm_calls` ở live là số attempt của adapter, không xác nhận provider đã thực thi/billing. `verification_calls=0`.

Live adapter yêu cầu endpoint HTTPS cụ thể tương thích `model/messages/max_tokens/stream=false` → một `choices[0].message.content` với finish_reason=stop; không theo redirect, tools, stream hoặc retry. Cấu hình qua TILLEGAL_LLM_ENDPOINT/MODEL/API_KEY và CLI `--mode live --allow-live`. Mặc định mock; không chọn provider/model tự động. Prompt tối đa 120.000 bytes UTF-8, output token cap mặc định 1.024, socket timeout 30s, HTTP response cap 1MiB; không phải token/cost estimator hoặc hard deadline toàn request. Khả năng tương thích provider và chất lượng live chưa được kiểm chứng; chỉ test transport bằng mock offline.

CLI `python -B -m ai_core.rag_cli --question ...`: JSON mặc định, `--format text` để xem ngắn; `--output` chỉ tạo file mới, không overwrite. Full response chứa provenance đầy đủ. NO_EVIDENCE không kết luận corpus không có luật liên quan; chỉ nói bundle rỗng trong lượt retrieval này. Chưa có evaluation chất lượng RAG, benchmark mới, hoặc Citation Verification/L-MARS.

### 2.8. T6-LIVE — Anthropic Messages adapter

Provider riêng `AnthropicProvider`, URL cố định `https://api.anthropic.com/v1/messages`, API version `2026-10-21`, x-api-key từ ANTHROPIC_API_KEY. Không nhận endpoint tùy ý, không dùng proxy hệ thống/môi trường, không theo redirects. Không tự nạp .env hoặc tìm credential. `--provider anthropic --mode live --allow-live --model ...` chọn model runtime; ANTHROPIC_MODEL là fallback tùy chọn. Không sửa environment máy. `--anthropic-thinking disabled|between_tools` chỉ dùng khi đã xác minh model hỗ trợ; không tự đổi model khi lỗi.

Messages API tách system ở top-level, chỉ gửi user message cùng model/max_tokens/stream=false và thinking nếu cấu hình; không tools hoặc web search. Adapter nhận content blocks kiểu text, chỉ end_turn mới chuyển text vào schema validator. Stop max_tokens/refusal/tool/unknown bị chặn; lỗi authentication/rate limit/billing/permission/network/timeout có mã riêng, không ghi body HTTP lỗi hoặc headers chứa credential. Không tự retry. Output token cap của adapter <=1.024; input byte cap cấu hình <=121.000, smoke thực tế40.000.

`GenerationText` vẫn là str, thêm metadata theo từng response; providers cũ trả str vẫn hoạt động. Trace có requested/returned model, HTTP status, stop reason, usage input/output/cache nếu có, latency, API version, thinking và request bytes. Không dùng provider.last_response mutable giữa requests. Sau smoke đã bổ sung raw text vào lỗi provider có text-only response; text bị giới hạn 65.536 ký tự và đánh dấu cắt. Không ghi thinking/signatures. JSON/schema error giữ nguyên contract T6; không tự bỏ fence hoặc sửa output để pass.

Live smoke đã gọi Anthropic thật nhưng **chưa có live RAG E2E thành công**: một lỗi DNS trước HTTP, một output fenced JSON, một stop max_tokens. Trace request003 lịch sử không giữ partial text; không bịa lại. Đây là smoke kỹ thuật, không benchmark hay semantic/citation verification. Báo cáo T06-LIVE và manifest ghi giá, usage và limitations; T5 gold vẫn chưa human-approved.

### 2.9. T6-LIVE-FIX — Structured output và context compact

Generation prompt hiện hành `basic-rag-draft-v2-compact`. Cùng schema output ba trường và validator local cũ: không đổi ID membership, duplicate-key checks hoặc fail-closed. Sonnet5 hỗ trợ JSON Schema; `--structured-output` gửi `output_config.format={type:json_schema,schema:...}` gồm required keys và additionalProperties=false. Không bật Citations API/tools. Không normalize Markdown fence, không sửa JSON thiếu; refusal/max_tokens vẫn bị chặn và lưu raw text nếu có.

Context gửi LLM giữ mọi evidence ID và quote nguyên vẹn, cùng số lượng/thứ tự. Gộp metadata document thành bảng documents/D1… và warnings chung thành common_warnings; riêng từng evidence giữ document_ref, scope/article/clause/point/form/appendix ứng viên, attachment_status và warnings bổ sung. Group metadata chỉ giữ seed_included/omission count/context_sufficiency; rank/score/locators/hash/ancestry đầy đủ vẫn nằm trong local bundle/trace. Không cắt điều kiện hoặc ngoại lệ nguồn để giảm prompt.

Prompt yêu cầu tối đa180 từ trong draft, abstain giải thích một câu; đây là hướng dẫn mềm, không thay local max12.000chars. Provider output cap cấu hình được đến2.048 tokens. Thực tế smoke đầu sau FIX vẫn203/224 đơn vị whitespace, không tự nhận đạt soft target. JSON/schema đúng không khẳng định semantic support hoặc legal correctness.

`--input-token-cap` tùy chọn gọi count_tokens trực tiếp Anthropic trước generation, cùng model/system/messages/thinking/output_config; vượt cap thì không generation. Trace ghi token_count_http_attempts/generation_http_attempts/counted_input_tokens/output_config. Count response là estimate, không hóa đơn; smoke chặn trên12.000 và reserve2x count cap ở giá đã xác minh. Budget $0,30 cho đợt3 generations: reserve$0,20544, thực tế$0,052914. Count API miễn phí, không phải lượt generation hoặc retry. Mọi lỗi dừng script; không resume/overwrite thư mục artifact.

CLI mới: --structured-output --input-token-cap 12000 --max-output-tokens 2048, cùng provider/model/allow-live cũ. scripts/smoke_claude_live_fix.py là script cho đợt được duyệt, không automation:3 câu cố định, không agents hoặc search bổ sung. Đã dùng hết3 lượt đợt hiện tại; đợt tiếp theo cần phê duyệt mới. T5 gold vẫn chưa human-approved.

## 3. State tối thiểu

```json
{
  "request": {
    "request_id": "demo-001",
    "mode": "verify_citations",
    "original_input": "Tất cả người tham gia được nghỉ 5 ngày theo Điều 3 DEMO-A.",
    "as_of_date": null,
    "jurisdiction": "DEMO"
  },
  "corpus_version": "demo-v1",
  "query_plan": null,
  "query_history": [],
  "evidence_by_id": {},
  "original_claims": [],
  "original_citations": [],
  "drafts": [],
  "judge_result": null,
  "verification_reports": [],
  "repair_proposals": [],
  "control": {
    "search_rounds": 0,
    "search_backend_calls": 0,
    "llm_calls": 0,
    "retry_count": 0,
    "repair_rounds": 0,
    "elapsed_ms": 0,
    "tokens_used": 0
  },
  "status": "RUNNING",
  "stop_reason": null,
  "errors": []
}
```

Trước Query: `original_input` đã có vì orchestrator lưu lúc nhận request. Sau Query: chỉ thêm `query_plan`, không chuyển câu hỏi vào embedding store. Khi citation được extract: nằm trong `original_citations` hoặc draft version. Sau Search: merge evidence có định danh. Sau Verify: append report gắn đúng input/draft, không sửa raw citation.

Không dùng append reducer mù cho mọi danh sách. QueryPlan mới thay kế hoạch hiện tại nhưng lịch sử vẫn append; evidence merge theo ID có kiểm tra hash; drafts/reports append bất biến; control chỉ orchestrator ghi. Điều này tránh evidence trùng, counter sai và report bị áp cho draft mới.

## 4. Các nhãn cần tách

| Trục | Giá trị | Ý nghĩa |
|---|---|---|
| Source | RESOLVED / UNRESOLVED / UNREACHABLE / ERROR | Có lấy được nội dung hay không; thiếu trong corpus là UNRESOLVED |
| Identity | MATCH / MISMATCH / UNKNOWN | Đúng văn bản/điều/khoản/phiên bản được trích không |
| Support | SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / NOT_EVALUATED | Nguồn được trích có suy ra claim không; contradiction là reason code của UNSUPPORTED |
| Temporal | VALID / INVALID / UNKNOWN / NOT_APPLICABLE | Áp dụng với thời điểm hỏi; NULL metadata không đồng nghĩa còn hiệu lực |
| Jurisdiction | MATCH / MISMATCH / UNKNOWN / NOT_APPLICABLE | Phạm vi pháp lý/đối tượng cần xét |
| Workflow | RUNNING / COMPLETED / PARTIAL / NEEDS_CLARIFICATION / INSUFFICIENT_EVIDENCE / FAILED | Trạng thái xử lý toàn request, không phải verdict từng citation |

Nhãn audit tương thích ý tưởng paper: supported, partially_supported, unsupported, citation_unreachable, no_citation, verifier_error. Thêm unresolved_source cho trường hợp kho không resolve được; không ngụy tạo nhãn semantic cho source chưa đọc. Báo separate mapping khi so với paper, không tự nhận metric giống hệt ALCE.

Quy tắc verdict API kế thừa S9/S10:

- `VERIFIED`: identity MATCH, source RESOLVED, support SUPPORTED; temporal/jurisdiction cần thiết đã qua. Trong fixture có thể NOT_APPLICABLE, trong luật thật không được dùng N/A để lách thiếu metadata.
- `INCORRECT`: đã có bằng chứng sai identity, không hỗ trợ/không đầy đủ, sai thời điểm hoặc phạm vi. Reason bắt buộc nói rõ “citation không hỗ trợ” khác “claim sai trong thực tế”.
- `UNREACHABLE`: nguồn cần đọc hiện không truy cập được và không có snapshot đủ điều kiện để chấm. Có snapshot đúng phiên bản thì vẫn có thể chấm nội dung, đồng thời ghi live URL không truy cập được.
- `UNVERIFIED`: thiếu citation, source unresolved, metadata chưa biết hoặc lỗi verifier. Lỗi kỹ thuật vẫn ghi error code riêng.

Priority khi có nhiều lỗi: ghi tất cả axes; không để verdict đơn làm mất thông tin. Nếu input mơ hồ giữa nhiều luật cùng “Điều 3”, trả ambiguity/clarification, không chọn ngẫu nhiên.

Với nhiều citations cho một claim: lưu kiểm chứng từng cặp và một `claim_support_report` cho tập nguồn được dẫn. Tập nguồn có thể phối hợp hỗ trợ claim; vẫn đánh dấu citation thừa/sai riêng. Không lấy một citation đúng để tô xanh tất cả citations. Các dẫn chiếu luật trong nguồn chỉ được mở rộng có provenance và quy tắc annotation công khai; không ngầm thêm nguồn vào tập citation đang chấm.

## 5. Budgets và điều kiện dừng

Giá trị dưới đây là **default prototype đề xuất**, không phải yêu cầu môn hay SLA. Đặt trong config; đo dev set để chỉnh trước final test.

| Giới hạn | Giá trị ban đầu | Cách đếm |
|---|---:|---|
| max_search_rounds | 3 | Gồm lượt đầu, lượt bổ sung và lượt repair; không phải 3 lượt sau lượt đầu |
| max_subqueries_per_round | 2 | Tránh planner nở số lượng queries |
| max_search_backend_calls | 12 | Mỗi lần gọi BM25/dense/web tính riêng; không chỉ đếm vòng ngoài |
| max_llm_calls | 12 | Tính cả retry/repair; batch claims có giới hạn |
| max_repair_rounds | 1 | Chỉ chạy nếu còn ngân sách tổng |
| max_retries_per_operation | 1 | Tối đa 2 attempts; chỉ retry lỗi tạm thời/schema, không retry verdict không thích |
| request_deadline_seconds | 120 | Dùng monotonic deadline; timeout từng call nằm trong phần thời gian còn lại |
| max_claims_per_request | 20 | Vượt giới hạn trả lỗi/chia batch rõ, không cắt mất claim rồi báo đủ |

Thêm max_input_chars, max_context_tokens, max_total_tokens và cost ceiling theo provider đã chọn. Trước mỗi call reserve mức chi phí/token tối đa dự kiến; sau call cập nhật thực dùng. Nếu chưa biết giá thì dùng hard token/call caps và báo cost unknown; không ghi chi phí 0.

Stop reasons: `completed`, `clarification_required`, `unsupported_scope`, `insufficient_evidence`, `no_progress`, `search_budget_exhausted`, `model_budget_exhausted`, `token_budget_exhausted`, `deadline_exceeded`, `provider_error`, `invalid_output`, `repair_exhausted`.

“Đã tìm 2 bằng chứng” và “đã chạy 3 vòng” không bao giờ tự đổi nhãn thành VERIFIED. Hết budget chỉ quyết định dừng, không quyết định sự thật.

## 6. Trace và ranh giới bảo mật

Mỗi event có request_id, sequence, node, start/end, input/output refs, schema_version, prompt_version, model/provider/version, corpus/index revision, counters trước/sau, status/error, reason code. Giải thích ngắn và quote đủ phục vụ audit; không yêu cầu model lộ chuỗi suy nghĩ nội bộ.

Treat nội dung tài liệu/web như dữ liệu không đáng tin cậy về chỉ dẫn: câu “ignore previous instructions” trong luật/HTML không được đổi prompt, gọi tool, tắt validator hoặc thay verdict. Source fetcher giới hạn domain/scheme, chặn loopback/private IP và kiểm tra lại redirect, timeout, kích thước, content type. Đây là rủi ro thực vì mode verify có thể nhận URL người dùng.

API AI đề xuất: `POST /v1/answer`, `POST /v1/verify`, `GET /health`. Backend truyền correlation ID và context cần thiết; AI trả schema_version và semantic status. Endpoint phải dùng đúng cơ chế xác thực nội bộ khi tích hợp; phần account/authorization người dùng là nhiệm vụ backend. Test concurrency phải chứng minh không lẫn state giữa hai request.
