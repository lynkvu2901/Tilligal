"""Prepare source-first T5 drafts. NEVER assigns human review or runs retrieval."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_core.bm25_retrieval import load_index, load_processed
from ai_core.data_contracts import canonical_json, ContractError, file_hash
from ai_core.retrieval_evaluation import EvaluationCorpus, POLICY, validate_dataset, write_new

SNAPSHOT = '8040db1bfeddb99b93e8937a1c35e634de198a703286318d459d80e90987bfb7'
INDEX_ID = 'bm25:2a751dc020052aed315bd56ac49b92c734e632db94b1f4241d18e273640117ed'
# Source selection precedes question retrieval. These are proposals, NOT gold.
SPECS = [
    ('D01', 'dev', 'probation', '139264', '26', 'Tiền lương của người lao động',
     'Theo Bộ luật Lao động 45/2019/QH14 trong snapshot, tiền lương thử việc có mức tối thiểu như thế nào?',
     'Quote có attachment HEURISTIC; phải kiểm tra ranh giới Điều từ raw trước khi nhận nhãn.'),
    ('D02', 'dev', 'probation', '139264', '25', '2. Không quá 60 ngày',
     'Trong Bộ luật Lao động 45/2019/QH14, thời gian thử việc tối đa cho công việc cần trình độ từ cao đẳng trở lên được quy định ở đâu?',
     'Đọc cả đoạn mở đầu Điều và các nhóm công việc, không chỉ số ngày.'),
    ('D03', 'dev', 'working_hours', '139264', '105', '1. Thời giờ làm việc bình thường',
     'Bộ luật Lao động 45/2019/QH14 quy định giới hạn thời giờ làm việc bình thường theo ngày và tuần như thế nào?',
     'Đọc cả khoản 1 và 2; câu hỏi có thể cần điều kiện cách tổ chức theo tuần.'),
    ('D04', 'dev', 'weekly_rest', '139264', '111', '1. Mỗi tuần, người lao động',
     'Trong Bộ luật Lao động 45/2019/QH14, người lao động được nghỉ hằng tuần tối thiểu bao lâu và xử lý chu kỳ lao động đặc biệt ra sao?',
     'Giữ ngoại lệ chu kỳ lao động, không rút câu thành một con số.'),
    ('D05', 'dev', 'contract_contents', '146696', '3', 'b) Địa điểm làm việc của người lao động:',
     'Theo Thông tư 10/2020/TT-BLĐTBXH trong snapshot, hợp đồng ghi địa điểm làm việc thế nào khi người lao động thường xuyên làm ở nhiều nơi?',
     'Kiểm tra thêm dẫn chiếu tới Bộ luật; không mặc định đây là relevant unit duy nhất.'),
    ('D06', 'dev', 'business_secrets', '146696', '4', '2. Thỏa thuận về bảo vệ bí mật',
     'Theo Thông tư 10/2020/TT-BLĐTBXH, thỏa thuận bảo vệ bí mật kinh doanh và bí mật công nghệ có thể gồm những nội dung gì?',
     'Phải đọc các điểm a–e dưới khoản 2; quote mở đầu chưa đủ để trả lời.'),
    ('D07', 'dev', 'source_incomplete', '152668', '49', 'Hội đồng tiền lương quốc gia do',
     'Trong bản Nghị định 145/2020/NĐ-CP của snapshot, có đủ nội dung để xác định ai thành lập Hội đồng tiền lương quốc gia không?',
     'Ca chẩn đoán SOURCE_TEXT_POSSIBLY_INCOMPLETE; người review quyết định ambiguous/excluded. Không tự điền câu thiếu.'),
    ('D08', 'dev', 'contract_contents', '146696', '3', 'b1) Các khoản phụ cấp lương',
     'Trong Thông tư 10/2020/TT-BLĐTBXH, khoản phụ cấp bù đắp điều kiện lao động và sinh hoạt được mô tả ở phần nào?',
     'Tiết b1 chưa resolve; chỉ đề xuất Điều để dò nguồn, không xác nhận địa chỉ tiết. Cần đọc cả khoản và raw.'),
    ('T01', 'test', 'multiple_contracts', '139264', '19', '1. Người lao động có thể giao kết nhiều',
     'Trong Bộ luật Lao động 45/2019/QH14, người lao động có thể đồng thời giao kết hợp đồng với nhiều người sử dụng lao động theo điều kiện nào?',
     'Test dự kiến, không phải held-out độc lập; chưa chạy prediction cho câu này.'),
    ('T02', 'test', 'equal_pay', '139264', '90', '3. Người sử dụng lao động phải bảo đảm trả lương',
     'Bộ luật Lao động 45/2019/QH14 yêu cầu gì về trả lương không phân biệt giới tính cho công việc có giá trị như nhau?',
     'Đọc Điều và kiểm tra nguồn thay thế; chưa chạy prediction cho câu này.'),
    ('T03', 'test', 'termination_notice', '139264', '35', 'a) Ít nhất 45 ngày',
     'Trong Bộ luật Lao động 45/2019/QH14, người lao động theo hợp đồng không xác định thời hạn thông thường phải báo trước bao lâu khi đơn phương chấm dứt?',
     'Phải giữ ngoại lệ ngành nghề đặc thù và các trường hợp không cần báo trước; chưa chạy prediction.'),
    ('T04', 'test', 'internal_rules', '139264', '118', '1. Người sử dụng lao động phải ban hành nội quy',
     'Theo Bộ luật Lao động 45/2019/QH14, khi sử dụng bao nhiêu người lao động thì nội quy lao động phải bằng văn bản?',
     'Test dự kiến cùng corpus, không đo tổng quát sang văn bản mới; chưa chạy prediction.'),
]


def prepare(index_manifest, output_dir):
    index_manifest, output_dir = Path(index_manifest).resolve(), Path(output_dir).resolve()
    index = load_index(index_manifest)
    if index.index_id != INDEX_ID:
        raise ContractError('review pack requires pinned T4 index')
    manifest = json.loads(index_manifest.read_text(encoding='utf-8'))
    documents, _, _, _ = load_processed(manifest['input_manifest_path'], SNAPSHOT)
    docs = {d.document_version_id: d for d in documents}
    corpus = EvaluationCorpus(index)
    cases, contexts = [], {}
    for qid, split, family, record, article, prefix, question, note in SPECS:
        matches = [c for c in corpus.chunks.values() if c['document_id'].endswith('::' + record)
                   and c['scope'] == 'main' and c['article'] == article and c['text'].startswith(prefix)]
        if len(matches) != 1:
            raise ContractError(f'{qid}: source selector must identify exactly one chunk')
        c = matches[0]
        uid = corpus.article_for(c)
        if uid not in contexts:
            article_chunks = sorted([x for x in corpus.chunks.values() if corpus.article_for(x) == uid],
                                    key=lambda x: (x['source_locator']['block_source_start'], x['text_start']))
            doc = docs[c['document_version_id']]
            contexts[uid] = {'unit_id': uid, 'document': {k: v for k, v in doc.to_dict().items() if k != 'content'},
                             'article_label_candidate': article, 'chunks': article_chunks,
                             'raw_blocks': [{'block_id': x['block_id'], 'source_locator': x['source_locator'],
                                             'raw_excerpt': doc.content[x['source_locator']['block_source_start']:x['source_locator']['block_source_end']]}
                                            for x in article_chunks]}
        cases.append({'question_id': qid, 'split': split, 'family_id': family, 'question': question,
                      'as_of_date': None, 'author_type': 'assistant_draft', 'answerability': 'UNKNOWN',
                      'proposed_units': [uid], 'relevant_units': [], 'draft_note': note,
                      'prediction_exposure': 'NOT_RUN_FOR_THIS_QUERY_IN_T5',
                      'evidence': [{'unit_id': uid, 'chunk_id': c['chunk_id'], 'start': 0, 'end': len(c['text']),
                                    'quote': c['text'], 'text_sha256': c['text_sha256'], 'source_locator': c['source_locator']}],
                      'review': {'status': 'PENDING_HUMAN_REVIEW', 'reviewer_type': None, 'reviewer_id': None,
                                 'reviewed_at': None, 'source_read': False, 'unit_mapping_checked': False,
                                 'alternatives_checked': False, 'relevance_complete': False,
                                 'predictions_hidden': False, 'notes': ''}})
    dataset = {'schema_version': '1', 'artifact_kind': 'retrieval_annotation_dataset',
               'dataset_id': 't5-labor-pilot-draft-v1', 'index_id': index.index_id, 'processed_snapshot_id': SNAPSHOT,
               'usage_policy': 'EXPERIMENTAL_ONLY', 'judgment_scope': 'LOCAL_SNAPSHOT_RELEVANCE_ONLY',
               'test_status': 'PROVISIONAL_NOT_INDEPENDENT_HELD_OUT', 'policy': deepcopy(POLICY), 'cases': cases}
    validate_dataset(dataset, corpus)
    lines = ['# T5 — Gói review nhãn retrieval (chưa phải gold)', '',
             'Không có prediction/rank/score trong gói này. 8 dev + 4 test dự kiến, chia theo nhóm câu hỏi và Điều nguồn.',
             'Câu hỏi do AI soạn sau khi đọc nguồn; không đại diện người dùng thật. Không xác minh luật hiện hành.', '',
             '## Cách review', '',
             '1. Tạo bản sao dataset.draft.json ở thư mục review riêng; giữ bản gốc.',
             '2. Đọc câu hỏi, quote, toàn Điều dưới đây và raw_blocks trong source_context.jsonl; kiểm tra context/ngoại lệ.',
             '3. Dò các Điều/văn bản thay thế trong toàn snapshot trước khi xác nhận relevance_complete. Các đề xuất không bảo đảm đầy đủ.',
             '4. Nếu đủ căn cứ: sửa câu hỏi/nhãn nếu cần, điền relevant_units và evidence; đặt ANSWERABLE, ACCEPTED_HUMAN.',
             '5. Điền reviewer_type=human, reviewer_id thật, reviewed_at ISO có múi giờ, notes và 5 cờ review sau khi thực sự kiểm tra.',
             '6. Nếu chưa giải quyết được thiếu nguồn/bất định: EXCLUDED_HUMAN + lý do, relevant_units=[]; không ép vào nhãn đúng/sai.',
             '7. Không xem kết quả BM25 trước khi chốt nhãn. Freeze dev trước; test vẫn chưa chạy, giữ riêng khỏi tuning.',
             'Các trường review là xác nhận của người nhập, không phải cơ chế xác thực danh tính. Không để AI tự điền người duyệt.', '',
             '## Đơn vị và giới hạn phép đo', '',
             'Đơn vị relevant là document version + node Điều, không chỉ số Điều. Heading có thể tính tìm đúng vị trí, chưa đủ evidence.',
             'Chỉ hit STRUCTURAL ngoài quoted và không nghi thiếu nguồn được map về Điều; các hit còn lại giữ slot unresolved-block.',
             'Khử trùng theo đơn vị, không xóa slot bất định để nâng điểm; lấy tối đa 100 chunk BM25. Báo Recall@5/@10 và MRR@5/@10 có giới hạn này.',
             'Nhãn chưa review hoặc chưa rà nguồn thay thế chặn phép đo. UNANSWERABLE/AMBIGUOUS chỉ thống kê loại trừ, chưa có abstention metric.', '',
             '## Câu hỏi và quote ứng viên', '']
    for case in cases:
        evidence = case['evidence'][0]
        lines.extend([f"### {case['question_id']} — {case['split']} — {case['question']}", '',
                      case['draft_note'], '', f"Unit ứng viên: `{evidence['unit_id']}`", '',
                      f"Chunk: `{evidence['chunk_id']}`; Unicode offsets [{evidence['start']},{evidence['end']}).", '',
                      '> ' + evidence['quote'], ''])
    lines.extend(['## Context theo Điều ứng viên — chưa xác nhận parent bằng chuyên gia', ''])
    for uid, context in contexts.items():
        lines.extend([f"### {context['document']['document_number']} — Điều {context['article_label_candidate']}", '', f'`{uid}`', ''])
        for c in context['chunks']:
            lines.extend([f"- [{c['attachment_status']}; {', '.join(c['issues']) or 'no issue'}] {c['text']}", ''])
    files = {'dataset.draft.json': canonical_json(dataset) + b'\n',
             'source_context.jsonl': b''.join(canonical_json(c) + b'\n' for c in contexts.values()),
             'REVIEW.md': ('\n'.join(lines) + '\n').encode('utf-8')}
    manifest_out = {'artifact_kind': 'pending_human_retrieval_review', 'schema_version': '1', 'index_id': index.index_id,
                    'processed_snapshot_id': SNAPSHOT, 'case_count': len(cases), 'split_counts': {'dev': 8, 'test': 4},
                    'source_article_count': len(contexts), 'metrics': None, 'predictions_generated': False,
                    'script_sha256': file_hash(Path(__file__)), 'index_manifest_sha256': file_hash(index_manifest),
                    'artifacts': [{'path': name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)} for name, data in files.items()]}
    files['manifest.json'] = canonical_json(manifest_out) + b'\n'
    write_new(output_dir, files, [index_manifest, Path(manifest['input_manifest_path'])])
    return manifest_out


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index-manifest', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.index_manifest, args.output_dir), ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({'status': 'ERROR', 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
