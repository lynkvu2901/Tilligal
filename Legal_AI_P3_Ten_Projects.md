

## P R E S E N T A T I O N  3 ·   P R O J E C T   C A T A L O G U E
10 Projects for
## Student Teams
6 Engineering · 4 R&D · từ ★★ đến ★★★★
TS. Dương Lê Minh    Giảng viên
Bộ môn Mạng và Truyền thông máy tính
minhdl@vnu.edu.vn   ·   0943 197 688

## S L I D E  1 ·   P R O J E C T   S E L E C T I O N
Chọn project theo năng lực, không theo độ “ngầu”
## 1
Interest — hứng thú của nhóm
## 2
Team skills — kỹ năng sẵn có
## 3
Data availability — có data không
## 4
Technical difficulty — độ khó
## 5
Research ambition — tham vọng
nghiên cứu
## 6
Time available — thời gian
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications1

## S L I D E   2   ·   P R O J E C T   P O R T F O L I O
Danh mục 10 đề tài — từ dễ đến khó
#ProjectTypeĐộ khó
1Vietnamese Legal RAG AssistantEngineering★★★
2Legal Document Semantic SearchEngineering★★
3Contract Risk AnalyzerEngineering★★★
4Contract Clause ExtractionEngineering★★
5Legal Judgment SummarizerEngineering★★
6Legal Compliance CheckerEngineering★★★★
7Legal Document Change DetectionEngineering / R&D★★★
8Vietnamese Legal Retrieval BenchmarkR&D★★★
9Legal Citation VerificationR&D★★★★
10Legal Reasoning / Multi-hop QAR&D★★★★
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications2

## P R O J E C T   1   ·   E N G I N E E R I N G   ·  ★★★
Vietnamese Legal RAG Assistant
## T H E   P R O B L E M
Người dùng đặt câu hỏi pháp lý bằng tiếng
Việt. Hệ thống truy xuất văn bản pháp luật
liên quan và để LLM sinh câu trả lời có căn
cứ (grounded).
Đây là “reference architecture” của Legal AI
— nền tảng cho hầu hết các đề tài khác.
## B U I L D   /   S Y S T E M
▪Query processing
▪Hybrid retrieval (BM25 + dense)
▪Reranking → context
▪LLM + citation
## T A R G E T
▪Top-K retrieval ≥ 85% recall
▪Citation correctness ≥ 90%
▪Answer quality ≥ baseline
## E V A L U A T I O N
▪Recall@5 · MRR
▪Citation accuracy
▪Expert answer score · Hallucination rate
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications3

## P R O J E C T   2   ·   E N G I N E E R I N G   ·  ★★
## Vietnamese Legal Semantic Search
## T H E   P R O B L E M
Keyword search bỏ sót các văn bản liên
quan về mặt ngữ nghĩa. Cần chứng minh
semantic/hybrid search thực sự tốt hơn
keyword trên dataset của nhóm.
Rất hợp với nhóm thiên về backend / AI
engineering.
## B U I L D   /   S Y S T E M
▪BM25 baseline
▪Dense retrieval
▪Hybrid retrieval
▪Reranker
## T A R G E T
▪Hybrid > BM25
▪Cải thiện Recall@10
▪Latency benchmark
## E V A L U A T I O N
▪Recall@5 · Recall@10
## ▪MRR · NDCG
▪Latency / query
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications4

## P R O J E C T   3   ·   E N G I N E E R I N G   ·  ★★★
AI Contract Risk Analyzer
## T H E   P R O B L E M
Nhận diện các điều khoản rủi ro trong hợp
đồng. Nên chọn MỘT loại hợp đồng
(employment / NDA / service / lease /
sales) để có dataset đủ sâu, thay vì “mọi
loại hợp đồng”.
## B U I L D   /   S Y S T E M
▪Document parser
▪Clause segmentation
▪Risk classifier
▪LLM explanation + recommendation
## T A R G E T
▪Clause detection F1 ≥ 0.85
▪Risk classification F1 ≥ 0.80
▪Human agreement ≥ 80%
## E V A L U A T I O N
▪Clause extraction F1
▪Risk classification F1
▪False negative rate · Expert review
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications5

## P R O J E C T   4   ·   E N G I N E E R I N G   ·  ★★
## Legal Clause Extraction
## T H E   P R O B L E M
Bóc tách thông tin pháp lý có cấu trúc từ
hợp đồng: các bên, ngày, số tiền, nghĩa vụ,
termination, liability, governing law. Output
là JSON — rất dễ đánh giá.
Thiên về Information Extraction.
## B U I L D   /   S Y S T E M
▪PDF / OCR parser
▪Field extractor (NLP + LLM)
▪JSON schema validator
▪Output: structured JSON
## T A R G E T
▪Field-level F1 ≥ 0.90
▪JSON validity ≥ 99%
## E V A L U A T I O N
▪Precision · Recall · F1
▪Exact match
▪JSON schema validity
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications6

## P R O J E C T   5   ·   E N G I N E E R I N G   ·  ★★
## Legal Judgment Summarization
## T H E   P R O B L E M
Input: một bản án đầy đủ. Output: facts,
legal issue, arguments, court reasoning,
decision.
Cẩn thận: summary ngắn KHÔNG có nghĩa
là summary tốt — bỏ mất quyết định chính
của tòa là thất bại.
## B U I L D   /   S Y S T E M
▪Judgment parser
▪Section identification
▪Structured summarizer
▪Checklist-based QA
## T A R G E T
▪Factual accuracy ≥ 90%
▪Critical-fact omission < 10%
▪Expert quality ≥ 4/5
## E V A L U A T I O N
▪Factual consistency
▪Key-fact recall
▪Expert score · Hallucination rate
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications7

## P R O J E C T   6   ·   E N G I N E E R I N G   ·  ★★★★
AI Legal Compliance Checker
## T H E   P R O B L E M
Input: một quy định, một internal policy,
một business process. Output: requirement
→ evidence → compliance status → risk →
recommendation.
Đề tài khó: cần cả retrieval lẫn reasoning. Ví
dụ: “Chính sách bảo mật của công ty có đáp
ứng các yêu cầu pháp lý được chọn
không?”
## B U I L D   /   S Y S T E M
▪Requirement extraction
▪Evidence matching
▪Gap analysis
▪Risk report
## T A R G E T
▪Requirement retrieval ≥ 90%
▪Compliance classification F1 ≥ 0.80
## E V A L U A T I O N
▪Requirement extraction F1
▪Evidence retrieval Recall
▪Compliance F1 · Expert assessment
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications8

## P R O J E C T   7   ·   E N G I N E E R I N G   /   R & D   ·  ★★★
## Legal Document Change Detection
## T H E   P R O B L E M
Phát hiện các thay đổi CÓ Ý NGHĨA giữa hai
phiên bản văn bản — không chỉ diff text mà
là semantic diff.
Ví dụ: “Payment within 30 days” →
“Payment within 15 days”. Text diff rất nhỏ,
nhưng legal significance rất lớn.
## B U I L D   /   S Y S T E M
▪Version aligner
▪Semantic diff engine
▪Change classifier
▪Significance scorer
## T A R G E T
▪Change detection F1 ≥ 0.90
▪Critical change recall ≥ 95%
## E V A L U A T I O N
▪Change precision / recall
▪Semantic classification accuracy
▪Critical-change recall
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications9

## P R O J E C T   8   ·   R & D   ·  ★★★
## Vietnamese Legal Retrieval Benchmark
## T H E   P R O B L E M
Research question: các phương pháp
retrieval hiện nay tốt đến đâu với văn bản
pháp luật tiếng Việt?
Nhóm không cần xây product — mà tạo ra
dataset + benchmark + kết quả thực
nghiệm. Đây là một contribution khoa học.
## B U I L D   /   S Y S T E M
▪Query collection (≥ 500)
▪Human relevance labels
▪So sánh: BM25 / dense / hybrid / rerank / LLM
▪Public benchmark format
## T A R G E T
▪Dataset ≥ 500 queries
▪Human relevance labels
▪Định dạng benchmark công khai
## E V A L U A T I O N
▪Recall@K · MRR · NDCG
▪Statistical significance
▪Error analysis
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications10

## P R O J E C T   9   ·   R & D   ·  ★★★★
## Legal Citation Verification
## T H E   P R O B L E M
LLM sinh câu trả lời pháp lý kèm citation.
Câu hỏi: nguồn được trích dẫn có THỰC SỰ
chống đỡ cho khẳng định không?
Ví dụ AI nói “Theo Điều 15...” nhưng Điều
15 thực tế không nói điều đó.
## B U I L D   /   S Y S T E M
▪Claim extraction
▪Citation extraction
▪Source retrieval
▪Entailment / support classifier
## T A R G E T
▪Citation precision ≥ 90%
▪Unsupported-claim detection F1 ≥ 0.80
## E V A L U A T I O N
▪Citation correctness
▪Entailment F1
▪False positive / negative rate
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications11

## P R O J E C T   1 0   ·   R & D   ·  ★★★★
## Vietnamese Legal Multi-hop Reasoning
## T H E   P R O B L E M
Một số câu hỏi pháp lý cần nhiều bước suy
luận: Facts → Applicable regulation →
## Exception → Cross-reference → Conclusion.
Đây là project khó nhất trong danh mục.
## B U I L D   /   S Y S T E M
▪Standard LLM baseline
## ▪RAG
▪Multi-step RAG
▪Agentic approach
## T A R G E T
▪Cải thiện final-answer accuracy qua các bước
▪Truy vết được chuỗi suy luận
## E V A L U A T I O N
▪Final answer accuracy
▪Intermediate retrieval accuracy
▪Reasoning-step accuracy · Citation · Hallucination
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications12

## S L I D E   1 3   ·   E N G I N E E R I N G   V S   R & D   P R O J E C T S
Chọn theo năng lực — cả hai đều có thể điểm cao
## Engineering
–Build a useful system
–Optimize architecture
–Reliability
## –UX
–Performance
## R&D
–Research question
–Hypothesis
–Baseline
–Experiment
–Analysis
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications13

## S L I D E   1 4   ·   R E C O M M E N D E D   T E C H N O L O G Y   S T A C K
Đừng dành cả học kỳ để học hạ tầng
## 1
## Frontend
## React / Next.js
## 2
## Backend
Python · FastAPI
## 3
## AI
OpenAI / Gemini / Claude / open
models
## 4
## Retrieval
Elasticsearch · PostgreSQL +
pgvector · Qdrant
## 5
Document processing
PyMuPDF · OCR
## 6
## Evaluation
Python · RAGAS / custom evaluation
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications14

## S L I D E  1 5  ·   M I N I M U M   A R C H I T E C T U R E
Vẽ kiến trúc ngay từ đầu, không phải cuối kỳ
## 1
Web UI
## 2
## API
## 3
## Application / Agent
## 4
## Retrieval
## 5
## Legal Knowledge Base
## 6
LLM → Evaluation / Logging
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications15

## S L I D E  1 6  ·   M I N I M U M   D A T A S E T   R E Q U I R E M E N T
Bắt buộc có evaluation dataset RIÊNG
## 1
Dataset description
## 2
Data source
## 3
Data volume
## 4
Data quality
## 5
Train / test split
(nếu có)
## 6
Ground truth
## 7
## Annotation
methodology
## 8
Nguyên tắc
Không develop →
tune → evaluate trên
cùng một tập.
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications16

## S L I D E  1 7  ·   B A S E L I N E   R E Q U I R E M E N T
Mọi project phải có ≥ 1 baseline
## 1
## BM25
## 2
Keyword search
## 3
Zero-shot LLM
## 4
Standard RAG
## 5
Existing model
## 6
Rule-based system
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications17

## S L I D E  1 8  ·   E V A L U A T I O N   R E Q U I R E M E N T
Viết evaluation plan TRƯỚC khi hoàn thành hệ thống
## 1
Primary metric
## 2
Secondary metrics
## 3
Test dataset
## 4
Evaluation procedure
## 5
Error analysis
## 6
Ví dụ mục tiêu
“Our goal is Recall@10 ≥ 90%.”
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications18

## S L I D E   1 9   ·   D E M O   R E Q U I R E M E N T
Demo phải có cả một failure case
## 1
Real problem → Real input
## 2
AI processing
## 3
Final result
## 4
Evidence / citations
## 5
Failure case
## 6
Evaluation results
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications19

S L I D E   2 0   ·   F I N A L   P R O J E C T   S U C C E S S   C R I T E R I A
Checklist cuối cùng — bảy yếu tố
## 1
## Problem
✓ meaningful — có ý
nghĩa
## 2
## Data
✓ sufficient — đủ
dùng
## 3
## AI
✓ appropriate — phù
hợp
## 4
## Engineering
✓ working — chạy
được
## 5
## Evaluation
✓ quantitative —
định lượng
## 6
## Demo
✓ realistic — thực tế
## 7
## Research
✓ evidence-based —
dựa trên bằng chứng
## 8
Kết luận
Đạt cả 7 → project
nhỏ vẫn rất tốt.
Presentation 3 — 10 Projects  ·  Legal AI and Its Applications20

## S L I D E   2 1   ·   F I N A L   M E S S A G E   T O   S T U D E N T S
Đừng hỏi “Dùng AI nào?”.
Hãy hỏi “Giải được bài toán pháp lý nào, và chứng
minh solution hiệu quả bằng cách nào?”
Các em học Computer Science. Điều quan trọng nhất không phải “biết dùng một model”, mà là: Problem →
## Design → Build → Measure → Improve.
## Presentation 3 — 10 Projects