
# Tillegal AI Core

AI Core cho hệ thống trợ lý pháp luật Việt Nam, sử dụng RAG để tìm kiếm văn bản pháp luật và sinh câu trả lời kèm trích dẫn nguồn.

Hiện hỗ trợ:
- BM25, Dense và Hybrid Retrieval
- Reranker
- Evidence Builder
- LLM Generation (Claude hoặc provider tương thích)
- Candidate Citations

**Lưu ý:** AI Core hiện là thư viện Python, chưa có HTTP API. Backend cần bọc hàm `BasicRAG.answer()` thành endpoint để gọi.

## 1. Clone và cài đặt

Yêu cầu môi trường đã kiểm thử: Windows, Python 3.14.2.

```powershell
git clone https://github.com/lynkvu2901/Tilligal.git
cd Tilligal

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
```

## 2. Chuẩn bị dữ liệu và model

Hai thư mục index đã có trong GitHub:

- `data/indexes/labor-pilot-3-t4-bm25/`
- `data/indexes/labor-pilot-3-t7-dense/`

Index hiện phục vụ bộ dữ liệu thử nghiệm gồm 3 văn bản pháp luật. Không cần tải lại raw dataset để chạy inference.

Cần tải thêm embedding model và reranker về máy:

```powershell
$py = '.\.venv\Scripts\python.exe'

& $py -B -m scripts.setup_t7_models --kind embedding --revision 614241f622f53c4eeff9890bdc4f31cfecc418b3

& $py -B -m scripts.setup_t7_models --kind reranker --revision 953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e
```

Models:
- Embedding: `intfloat/multilingual-e5-small`
- Reranker: `BAAI/bge-reranker-v2-m3`

**Lưu ý:** Runtime kiểm tra tính tương thích giữa source, index và model. Nếu index không load được do checksum, phiên bản hoặc đường dẫn, cần kiểm tra nguyên nhân; không bỏ qua integrity checks.

## 3. Chạy thử RAG

Chạy Hybrid Retrieval + Reranker ở chế độ MOCK (không gọi LLM thật):

```powershell
$out = "data/demos/test-$([guid]::NewGuid().ToString('N'))"

.\.venv\Scripts\python.exe -B -m ai_core.demo_cli --retrieval hybrid --rerank --output-dir $out
```

Sau khi chương trình khởi động, nhập câu hỏi pháp luật. Gõ `exit` để thoát.

MOCK chỉ dùng để kiểm tra luồng Retrieval và Evidence, không phải câu trả lời do LLM sinh.

### Chạy với Claude thật

Cấu hình API key trong biến môi trường của process:

```powershell
$env:ANTHROPIC_API_KEY = "YOUR_API_KEY"
```

Sau đó chạy:

```powershell
$out = "data/demos/live-$([guid]::NewGuid().ToString('N'))"

.\.venv\Scripts\python.exe -B -m ai_core.demo_cli --retrieval hybrid --rerank --live --output-dir $out
```

Lệnh LIVE sẽ gọi Claude API và phát sinh chi phí.

Không commit API key hoặc file `.env` chứa secret lên GitHub.

## 4. Tích hợp Backend

Entry point Python:

`ai_core.basic_rag.BasicRAG.answer()`

Input chính:

- `question`: Câu hỏi người dùng.
- `request_id`: ID duy nhất cho request.
- `top_k`: Số lượng evidence muốn lấy.

Ví dụ sử dụng với BM25 và MOCK:

```python
from pathlib import Path
from uuid import uuid4

from ai_core.basic_rag import BasicRAG
from ai_core.bm25_retrieval import load_index
from ai_core.evidence_builder import EvidenceBudget
from ai_core.rag_generation import MockProvider
from ai_core.retrieval_runtime import make_retriever

index = load_index(
    Path("data/indexes/labor-pilot-3-t4-bm25/manifest.json")
)

retriever = make_retriever(index, mode="bm25")

rag = BasicRAG(
    index,
    MockProvider(),
    EvidenceBudget(24, 8000),
    retriever=retriever,
)

result = rag.answer(
    "Đối thoại tại nơi làm việc là gì?",
    request_id=str(uuid4()),
    top_k=3,
)

print(result["status"])
print(result["answer"])
print(result["candidate_citations"])
```

Ví dụ trên chỉ kiểm tra tích hợp Python bằng BM25 + MOCK.

Để chạy Hybrid + Rerank + LLM thật, Backend cần sử dụng retriever và generation provider tương ứng đã có trong `ai_core`. Xem `ai_core/demo_cli.py` và `ai_core/retrieval_runtime.py` để tham khảo cách khởi tạo theo source hiện tại.

Nên khởi tạo index, retriever và LLM provider **một lần khi Python service khởi động**, sau đó tái sử dụng cho các request.

### Luồng tích hợp đề xuất

```text
Frontend
   |
   v
Backend .NET
   |
   | HTTP
   v
Python API Wrapper
   |
   v
BasicRAG.answer()
   |
   v
Answer + Candidate Citations
```

Backend có thể bọc Python AI Core thành một HTTP endpoint, ví dụ `POST /api/ai/ask`.

**Endpoint này chưa được triển khai trong repository; đây là phần Backend cần xây dựng.**

## 5. Kết quả trả về

`BasicRAG.answer()` trả về dictionary có thể chuyển thành JSON.

Các trường quan trọng:

| Field | Ý nghĩa |
|---|---|
| `request_id` | ID request |
| `status` | Trạng thái xử lý |
| `answer` | Câu trả lời |
| `candidate_citations` | Các trích dẫn nguồn ứng viên |
| `evidence_bundle` | Evidence được sử dụng |
| `warnings` | Cảnh báo |
| `error` | Thông tin lỗi |
| `trace` | Dữ liệu phục vụ debug |

Các trạng thái có thể gặp:
- `DRAFT_UNVERIFIED`
- `ABSTAINED_UNVERIFIED`
- `NO_EVIDENCE`
- `FAILED`

Backend cần xử lý các trạng thái lỗi và không trả nguyên `trace`, prompt hoặc thông tin nhạy cảm cho người dùng cuối.

## 6. LLM Provider

AI Core hiện có Anthropic Provider cho Claude và Chat-Completions Provider.

Có thể tích hợp LLM khác như GPT nếu giao diện provider tương thích. Không mặc định rằng mọi model hoặc endpoint OpenAI đã được kiểm thử.

API key phải do môi trường triển khai cung cấp, không hard-code trong source.

## 7. Giới hạn hiện tại

- RAG hiện hoạt động trên corpus pilot gồm 3 văn bản pháp luật.
- Candidate citations chưa được xác minh pháp lý đầy đủ.
- Chưa triển khai Multi-Agent và Citation Verification.
- Chưa có HTTP API server.
- Chưa kiểm thử triển khai trên Linux hoặc macOS.

Mục tiêu bàn giao hiện tại: **Backend có thể chạy AI Core, truyền câu hỏi vào `BasicRAG.answer()` và lấy kết quả để trả về Frontend.**
