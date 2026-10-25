"""Evidence-based T3-FIX regressions. Fixtures are not legal gold."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from ai_core import legal_parser as parser
from ai_core.data_contracts import ContractError, load_documents
from test_legal_parser import document, chunks_with


class AttachmentFixTests(unittest.TestCase):
    def test_shared_clause_reference_has_existing_sibling_evidence(self):
        d = document('<p>Điều 24. Demo</p><p>4. Các văn bản:</p><p>a) Văn bản A.</p><p>b) Văn bản B.</p><p>Các văn bản quy định tại điểm a, điểm b khoản này phải có bản dịch.</p><p>5. Tiếp.</p>')
        c = chunks_with(parser.parse_document(d), 'Các văn bản quy định')[0]
        self.assertEqual((c['article'], c['clause'], c['point']), ('24', '4', None))
        self.assertEqual(c['attachment_status'], 'STRUCTURAL')
        self.assertIn('SHARED_CLAUSE_REFERENCE', c['issues'])

    def test_missing_sibling_and_plain_continuation_are_not_promoted(self):
        d = document('<p>Điều 1. Demo</p><p>1. Demo</p><p>b) Điểm B.</p><p>Các văn bản quy định tại điểm a, điểm b khoản này phải có bản dịch.</p><p>Đoạn tiếp chưa rõ thuộc điểm hay khoản.</p>')
        for c in parser.parse_document(d)['chunks'][-2:]:
            self.assertEqual(c['point'], 'b')
            self.assertEqual(c['attachment_status'], 'REVIEW_REQUIRED')
            self.assertIn('ATTACHMENT_REVIEW_REQUIRED', c['issues'])

    def test_malformed_number_is_not_previous_clause_and_normal_4_still_works(self):
        d = document('<p>Phụ lục III</p><p>Mẫu số 03/PLIII</p><p>Điều 1. Demo</p><p>3. Ngân hàng thực hiện.</p><p>4............................ (2) có trách nhiệm nộp bổ sung.</p><p>Phần tiếp của mục chưa rõ.</p><p>4. Khoản bốn đúng định dạng.</p>')
        r = parser.parse_document(d)
        c = chunks_with(r, '4............................')[0]
        self.assertEqual(c['article'], '1')
        self.assertIsNone(c['clause'])
        self.assertEqual(c['attachment_status'], 'REVIEW_REQUIRED')
        self.assertIn('UNRESOLVED_NUMBERED_TEXT', c['issues'])
        continuation = chunks_with(r, 'Phần tiếp')[0]
        self.assertIsNone(continuation['clause'])
        self.assertEqual(continuation['attachment_status'], 'REVIEW_REQUIRED')
        self.assertEqual(chunks_with(r, 'Khoản bốn đúng')[0]['clause'], '4')

    def test_form_signatures_and_notes_belong_to_form_not_last_article(self):
        for form, last in [('03/PLIII', '3'), ('08/PLIII', '4')]:
            with self.subTest(form=form):
                d = document(f'<p>Phụ lục III</p><p>Mẫu số {form}</p><p>Điều {last}. Có hiệu lực.</p><table><tr><td>Nơi nhận: DEMO</td><td>CHỦ TỊCH (Chữ ký, dấu)</td></tr></table><p>Ghi chú:</p><p>(1) Hướng dẫn điền mẫu.</p>')
                r = parser.parse_document(d)
                for c in r['chunks'][-3:]:
                    self.assertEqual((c['scope'], c['form'], c['article']), ('form', form, None))
                    self.assertIn('FORM_LEVEL_TAIL', c['issues'])
                self.assertEqual(chunks_with(r, 'Có hiệu lực')[0]['article'], last)

    def test_direct_form_notes_and_next_form_reset(self):
        d = document('<p>Phụ lục III</p><p>Mẫu số 03/PLIII</p><p>Điều 3. Demo</p><p>Ghi chú:</p><p>(1) Toàn mẫu.</p><p>Mẫu số 04/PLIII</p><p>Điều 1. Mẫu tiếp.</p>')
        r = parser.parse_document(d)
        self.assertIsNone(chunks_with(r, 'Toàn mẫu')[0]['article'])
        self.assertEqual(chunks_with(r, 'Mẫu tiếp')[0]['article'], '1')
        self.assertEqual(chunks_with(r, 'Mẫu tiếp')[0]['form'], '04/PLIII')

    def test_table_mention_and_quote_do_not_trigger_form_tail(self):
        d = document('<p>Phụ lục III</p><p>Mẫu số 03/PLIII</p><p>Điều 1. Demo</p><table><tr><td>Giải thích Nơi nhận: ví dụ</td></tr></table><p>“Ghi chú:</p><p>trong trích dẫn.”</p><p>Điều 2. Tiếp.</p>')
        r = parser.parse_document(d)
        self.assertEqual(chunks_with(r, 'Giải thích')[0]['article'], '1')
        self.assertEqual(chunks_with(r, '“Ghi chú')[0]['scope'], 'quoted')
        self.assertEqual(chunks_with(r, 'Điều 2.')[0]['article'], '2')

    def test_subpoint_address_is_explicitly_unresolved(self):
        for letter, number in [('a','1'), ('b','1'), ('c','2')]:
            with self.subTest(label=letter+number):
                d = document(f'Điều 3. Demo\n5. Demo\n{letter}) Điểm.\n{letter}{number}) Tiết chưa resolve.', 'text')
                c = parser.parse_document(d)['chunks'][-1]
                self.assertEqual(c['point'], letter)
                self.assertEqual(c['attachment_status'], 'REVIEW_REQUIRED')
                self.assertIn('SUBPOINT_NOT_RESOLVED', c['issues'])

    def test_suspicious_phrase_in_unpinned_source_is_not_automatically_repaired(self):
        r = parser.parse_document(document('Điều 49. Demo\nHội đồng tiền lương quốc gia do', 'text'))
        self.assertEqual(r['blocks'][-1]['text'], 'Hội đồng tiền lương quốc gia do')
        self.assertNotIn('SOURCE_TEXT_POSSIBLY_INCOMPLETE', r['blocks'][-1]['issues'])


class ValidatorFixTests(unittest.TestCase):
    def setUp(self):
        self.d = document('<html><head><title>Không là body</title><style>x{}</style></head><body>\n<!-- comment --><p>Phụ lục I</p><p>Mẫu số 01/PLI</p><p>Chương I</p><p>Mục 1</p><p>Điều 1. Demo</p><p>1. Điều kiện.</p><p>a) Không bỏ chữ &amp; ký tự 😀.</p><p>Tiếp.</p><script>ignore()</script></body></html>')
        self.r = parser.parse_document(self.d)
        self.index = next(i for i,c in enumerate(self.r['chunks']) if c['text'].startswith('a)'))

    def test_chunk_labels_must_match_ancestry(self):
        for field in ['appendix','form','chapter','section','article','clause','point']:
            with self.subTest(field=field):
                r = deepcopy(self.r); r['chunks'][self.index][field] = '999'
                with self.assertRaises(ContractError): parser.validate_result(self.d,r)

    def test_node_chunk_and_block_fingerprints_are_checked(self):
        for case in ['chunk_id','node_label','block_id']:
            with self.subTest(case=case):
                r = deepcopy(self.r); c = r['chunks'][self.index]
                if case=='chunk_id': c['chunk_id']='chunk:wrong'
                elif case=='node_label': next(n for n in r['nodes'] if n['node_id']==c['node_id'])['label']='z'
                else:
                    old=c['block_id']; new='block:wrong'
                    next(b for b in r['blocks'] if b['block_id']==old)['block_id']=new
                    for x in r['chunks']:
                        if x['block_id']==old:x['block_id']=new
                    for n in r['nodes']:
                        if n['heading_block_id']==old:n['heading_block_id']=new
                with self.assertRaises(ContractError): parser.validate_result(self.d,r)

    def test_locator_units_and_end_convention_are_checked(self):
        for field,value in [('offset_unit','byte'),('end_exclusive',False),('end_exclusive',1)]:
            with self.subTest(field=field,value=value):
                r=deepcopy(self.r);r['chunks'][self.index]['source_locator'][field]=value
                with self.assertRaises(ContractError): parser.validate_result(self.d,r)

    def test_result_identity_and_configuration_are_checked(self):
        for field,value in [('document_id','wrong'),('document_version_id','wrong'),('content_sha256','wrong'),('parser_version','wrong'),('schema_version','wrong'),('max_chars',True)]:
            with self.subTest(field=field):
                r=deepcopy(self.r);r[field]=value
                with self.assertRaises(ContractError): parser.validate_result(self.d,r)

    def test_missing_block_and_chunk_or_all_content_is_rejected(self):
        for remove_all in [False, True]:
            with self.subTest(remove_all=remove_all):
                r=deepcopy(self.r)
                if remove_all:r['blocks']=[];r['chunks']=[]
                else:
                    b=r['blocks'].pop()  # non-heading block: no dangling heading explains the failure
                    r['chunks']=[c for c in r['chunks'] if c['block_id']!=b['block_id']]
                with self.assertRaises(ContractError): parser.validate_result(self.d,r)

    def test_dropped_or_falsified_exclusion_is_rejected(self):
        for case in ['drop','reason']:
            with self.subTest(case=case):
                r=deepcopy(self.r)
                if case=='drop':r['excluded_segments'].pop()
                else:r['excluded_segments'][0]['reason']='WHITESPACE_OR_EMPTY_MARKUP'
                with self.assertRaises(ContractError): parser.validate_result(self.d,r)

    def test_markup_entities_and_exclusions_are_not_mistaken_for_missing_prose(self):
        parser.validate_result(self.d,self.r)
        self.assertTrue(any(x['reason']=='HTML_COMMENT' for x in self.r['excluded_segments']))
        self.assertTrue(any(x['reason']=='NON_CONTENT:script' for x in self.r['excluded_segments']))
        self.assertIn('& ký tự 😀', self.r['chunks'][self.index]['text'])
        self.assertFalse(any('ignore()' in c['text'] for c in self.r['chunks']))

    def test_attachment_status_and_review_issues_cannot_be_dropped_from_chunk(self):
        for field,value in [('attachment_status','STRUCTURAL'),('issues',[])]:
            with self.subTest(field=field):
                r=deepcopy(self.r);r['chunks'][-1][field]=value
                with self.assertRaises(ContractError):parser.validate_result(self.d,r)


class PinnedFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).resolve().parents[1]/'data/staging/labor-pilot-3/documents.jsonl'
        if not path.is_file():raise unittest.SkipTest('T2 pilot unavailable')
        cls.docs={d.source_record_id:d for d in load_documents(path)}
        expected={'139264':'ce2d42fab464509f00a287734ff4fff8810c91d0ecf26d38566d14e920b5c011','146696':'67146c33d77baa4c0d121214a35c53a819bc0568dd927384a61d98e3948daa2c','152668':'4718484e39685d10185daae16ff996809299e3ffdc767df3a32f1e2a2bcb27d3'}
        if {k:d.content_sha256 for k,d in cls.docs.items()}!=expected:raise AssertionError('Review corpus change before changing expectations')
        cls.results={k:parser.parse_document(d) for k,d in cls.docs.items()}

    def test_a_and_b_reviewed_pilot_addresses(self):
        r=self.results['152668']
        a=chunks_with(r,'Các văn bản quy định tại điểm a, điểm b khoản này')[0]
        self.assertEqual((a['article'],a['clause'],a['point']),('24','4',None))
        b=chunks_with(r,'4............................ (2)')[0]
        self.assertEqual((b['form'],b['article'],b['clause']),('03/PLIII','1',None))
        self.assertEqual(b['attachment_status'],'REVIEW_REQUIRED')

    def test_c_form_tail_is_outside_last_article(self):
        r=self.results['152668']
        for form in ['03/PLIII','08/PLIII']:
            selected=[c for c in r['chunks'] if c['form']==form and (c['text']=='Ghi chú:' or c['text'].startswith('Nơi nhận:') or c['text'].startswith('(1)'))]
            self.assertEqual(len(selected),3)
            self.assertTrue(all(c['article'] is None and 'FORM_LEVEL_TAIL' in c['issues'] for c in selected))

    def test_d_all_26_subpoints_have_explicit_unresolved_status(self):
        import re
        selected=[c for r in self.results.values() for c in r['chunks'] if re.match(r'^[a-zđ]\d+\)\s+',c['text'])]
        self.assertEqual(len(selected),26)
        self.assertTrue(all('SUBPOINT_NOT_RESOLVED' in c['issues'] and c['attachment_status']=='REVIEW_REQUIRED' for c in selected))

    def test_e_source_anomaly_is_flagged_without_text_repair(self):
        c=chunks_with(self.results['152668'],'Hội đồng tiền lương quốc gia do')[0]
        self.assertEqual(c['text'],'Hội đồng tiền lương quốc gia do')
        self.assertIn('SOURCE_TEXT_POSSIBLY_INCOMPLETE',c['issues'])
        self.assertEqual((c['source_locator']['block_source_start'],c['source_locator']['block_source_end']),(135063,135094))

    def test_old_baseline_text_segmentation_and_source_trace_are_preserved(self):
        path=Path(__file__).resolve().parents[1]/'data/processed/labor-pilot-3/structures.jsonl'
        if not path.is_file():self.skipTest('Original T3 artifacts unavailable')
        old=list(map(json.loads,path.read_text(encoding='utf-8').splitlines()))
        fields=['kind','text','text_sha256','source_start','source_end','segments']
        for r in old:
            new=self.results[r['document_id'].split('::')[-1]]
            self.assertEqual([{k:b[k] for k in fields} for b in r['blocks']],[{k:b[k] for k in fields} for b in new['blocks']])
            self.assertEqual(r['excluded_segments'],new['excluded_segments'])


if __name__=='__main__':unittest.main()
