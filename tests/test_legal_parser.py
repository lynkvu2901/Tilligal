"""T3: trace, boundaries and retention; synthetic legal-looking text is not law."""
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import unittest
from unittest.mock import patch
from uuid import uuid4

from ai_core.data_contracts import build_document, canonical_json, content_hash, ContractError, file_hash, load_documents
from ai_core import legal_parser as parser


def document(text, fmt="html", record="1"):
    return build_document(source_id="neutral-fixture", source_record_id=record, source_snapshot_id="fixture-v1",
                          source_version=None, document_number="DEMO", title="Not law", document_type=None,
                          issuing_authority=None, language="vi", content_format=fmt, content=text,
                          raw_ref={"uri": "file:///fixture.txt", "file_sha256": "a" * 64, "record_key": "id", "record_value": record},
                          source_url=None, collected_at=None, issued_on=None, effective_from=None, effective_to=None,
                          effect_status_reported=None, status_observed_at=None, processing_steps=["FIXTURE"], issues=[])


def chunks_with(result, text):
    return [c for c in result["chunks"] if text in c["text"]]


class LegalParserTests(unittest.TestCase):
    def test_hierarchy_and_inline_words_entities_unicode_offsets(self):
        raw = '<html><head><title>Ignore</title></head><body>\r\n<p>Giới thiệu</p><p>Chương I</p><p>Mục 1</p><p>Điều 7. DEMO</p><p>1. Không <b>được</b> phép &amp; phải giữ.</p><p>đ) Lao <em>động</em> Việt&#160;Nam.</p></body></html>'
        d = document(raw)
        r = parser.parse_document(d)
        c = chunks_with(r, 'đ) Lao động Việt Nam.')[0]
        self.assertEqual((c['scope'], c['chapter'], c['section'], c['article'], c['clause'], c['point']), ('main', 'I', '1', '7', '1', 'đ'))
        self.assertIn('Không được phép & phải giữ.', chunks_with(r, 'Không')[0]['text'])
        self.assertFalse(chunks_with(r, 'Ignore'))
        self.assertTrue(any(x['reason'] == 'NON_CONTENT:head' for x in r['excluded_segments']))
        b = next(b for b in r['blocks'] if b['block_id'] == c['block_id'])
        self.assertTrue(raw[b['source_start']:b['source_end']].startswith('đ) Lao'))
        self.assertNotEqual(b['source_start'], len(raw[:b['source_start']].encode('utf-8')))

    def test_appendix_form_numbers_do_not_replace_main_article(self):
        d = document('<p>Điều 7. Nội dung chính</p><p>1. Chính.</p><p>Phụ lục V</p><table><tr><td>Mẫu số 01/PLV</td><td>Điều 7. Mục lục</td></tr></table><p>Mẫu số 01/PLV</p><p>Điều 7. Mẫu</p><p>1. Mẫu.</p>')
        r = parser.parse_document(d)
        nodes = [n for n in r['nodes'] if n['kind'] == 'article']
        self.assertEqual([n['scope'] for n in nodes], ['main', 'form'])
        self.assertNotEqual(nodes[0]['node_id'], nodes[1]['node_id'])
        self.assertEqual(len([n for n in r['nodes'] if n['kind'] == 'form']), 1)
        c = chunks_with(r, '1. Mẫu.')[0]
        self.assertEqual((c['appendix'], c['form'], c['article']), ('V', '01/PLV', '7'))

    def test_table_nested_cells_empty_table_and_images_are_retained(self):
        raw = '<p>Điều 1. DEMO</p><table><tr><td rowspan="2">A</td><td>B<table><tr><td>C</td></tr></table></td></tr><tr><td>D<img src="https://invalid.example/x"/></td></tr></table><table></table>'
        r = parser.parse_document(document(raw))
        tables = [b for b in r['blocks'] if b['kind'] == 'table']
        self.assertEqual(len(tables), 2)
        self.assertEqual(tables[0]['text'], 'A B C D [IMAGE]')
        self.assertEqual(tables[1]['text'], '[EMPTY_TABLE]')
        self.assertIn('rowspan="2"', raw[tables[0]['source_start']:tables[0]['source_end']])
        self.assertIn('IMAGE_NOT_INTERPRETED', tables[0]['issues'])
        self.assertIn('EMPTY_TABLE_PRESERVED', tables[1]['issues'])

    def test_quoted_amendments_are_opaque_and_restore_outer_point(self):
        raw = '<p>Điều 219. DEMO</p><p>1. Sửa đổi:</p><p>a) Nội dung:</p><p>“Điều 54. Trích</p><p>1. Không tạo khoản ngoài.</p><p>a) Trích.”;</p><p>b) Tiếp theo.</p><p>Điều 220. Sau trích</p>'
        r = parser.parse_document(document(raw))
        self.assertEqual([n['label'] for n in r['nodes'] if n['kind'] == 'article'], ['219', '220'])
        self.assertEqual(chunks_with(r, '1. Không')[0]['scope'], 'quoted')
        self.assertEqual(chunks_with(r, 'b) Tiếp')[0]['point'], 'b')
        self.assertEqual(chunks_with(r, 'b) Tiếp')[0]['clause'], '1')
        self.assertIn('QUOTED_STRUCTURE_NOT_RESOLVED', chunks_with(r, '1. Không')[0]['issues'])

    def test_duplicate_label_warns_without_overwriting(self):
        r = parser.parse_document(document('<p>Chương XI</p><p>Điều 1. A</p><p>Chương XI</p><p>Điều 2. B</p>'))
        chapters = [n for n in r['nodes'] if n['kind'] == 'chapter']
        self.assertEqual(len(chapters), 2)
        self.assertNotEqual(chapters[0]['node_id'], chapters[1]['node_id'])
        self.assertEqual(chapters[1]['issues'], ['DUPLICATE_LABEL_UNDER_PARENT'])

    def test_form_suffix_mismatch_is_not_silently_corrected(self):
        r = parser.parse_document(document('<p>Phụ lục III</p><p>Mẫu số 07/PLII</p><p>Giữ nguyên nguồn.</p>'))
        c = chunks_with(r, 'Giữ nguyên')[0]
        self.assertEqual((c['appendix'], c['form']), ('III', '07/PLII'))
        self.assertIn('FORM_APPENDIX_LABEL_MISMATCH', c['issues'])

    def test_unknown_text_and_numbering_are_not_discarded(self):
        raw = '1. Danh sách ngoài điều\n<weird>Không mất chữ</weird><p>Điều 1. A</p><p>Đoạn tiếp chưa rõ khoản</p><p>1a. Khoản bổ sung</p>'
        r = parser.parse_document(document(raw))
        self.assertIn('UNKNOWN_HTML_TAG:weird', r['issues'])
        self.assertIn('UNRESOLVED_NUMBERED_TEXT', chunks_with(r, 'Danh sách')[0]['issues'])
        self.assertIn('UNNUMBERED_TEXT_CONTEXT_HEURISTIC', chunks_with(r, 'Đoạn tiếp')[0]['issues'])
        self.assertTrue(chunks_with(r, 'Không mất chữ'))
        self.assertEqual(chunks_with(r, 'Khoản bổ sung')[0]['clause'], '1a')

    def test_closing_is_separate_from_last_article(self):
        r = parser.parse_document(document('<p>Điều 12. Kết thúc</p><p>1. Nội dung</p><table><tr><td>BỘ TRƯỞNG (Đã ký) DEMO</td></tr></table>'))
        c = chunks_with(r, 'BỘ TRƯỞNG')[0]
        self.assertEqual(c['scope'], 'closing')
        self.assertIsNone(c['article'])

    def test_long_blocks_split_with_exact_no_overlap_coverage(self):
        raw = 'Điều 1. A\r\n1. ' + 'Không được bỏ phủ định. ' * 15 + 'X' * 160
        d = document(raw, 'text')
        r = parser.parse_document(d, 80)
        long_block = r['blocks'][1]
        chunks = [c for c in r['chunks'] if c['block_id'] == long_block['block_id']]
        self.assertGreater(len(chunks), 3)
        self.assertTrue(all(len(c['text']) <= 80 for c in chunks))
        self.assertEqual(''.join(c['text'] for c in chunks), long_block['text'])
        self.assertTrue(all(c['clause'] == '1' for c in chunks))
        self.assertTrue(all('SPLIT_BLOCK_REQUIRES_CONTEXT' in c['issues'] for c in chunks))
        parser.validate_result(d, r)

    def test_malformed_table_and_unclosed_quote_are_flagged(self):
        r = parser.parse_document(document('<p>Điều 1. DEMO</p><table><tr><td>Nội dung giữ'))
        self.assertIn('UNCLOSED_HTML_SCOPE_REVIEW', r['issues'])
        self.assertTrue(chunks_with(r, 'Nội dung giữ'))
        r = parser.parse_document(document('Điều 1. DEMO\n“Trích chưa đóng\n1. Vẫn giữ', 'text'))
        self.assertIn('UNCLOSED_QUOTATION_REVIEW', r['issues'])
        self.assertEqual(r['chunks'][-1]['scope'], 'quoted')

    def test_source_replay_coverage_and_status_tampering_rejected(self):
        d = document('<p>Điều 1. DEMO</p><p>1. Không bỏ chữ.</p>')
        original = parser.parse_document(d)
        for field, value in [('text_start', 1), ('text', 'Sửa'), ('legal_approval', 'VERIFIED'),
                             ('scope', 'form'), ('ancestor_ids', []), ('document_id', 'wrong')]:
            with self.subTest(field=field):
                r = deepcopy(original)
                r['chunks'][0][field] = value
                with self.assertRaises(ContractError): parser.validate_result(d, r)
        r = deepcopy(original)
        r['blocks'][0]['segments'][0]['start'] += 1
        with self.assertRaises(ContractError): parser.validate_result(d, r)
        r = deepcopy(original)
        r['chunks'].pop()
        with self.assertRaises(ContractError): parser.validate_result(d, r)

    def test_deterministic_ids_and_configuration_identity(self):
        d = document('Điều 1. DEMO\n1. Nội dung.', 'text')
        first = parser.parse_document(d, 80)
        self.assertEqual(first, parser.parse_document(d, 80))
        self.assertNotEqual(first['chunks'][0]['chunk_id'], parser.parse_document(d, 90)['chunks'][0]['chunk_id'])
        changed = document('Điều 1. DEMO\n1. Nội dung.', 'text', record='2')
        self.assertNotEqual(first['nodes'][0]['node_id'], parser.parse_document(changed)['nodes'][0]['node_id'])

    def test_empty_input_and_bad_budget_fail(self):
        with self.assertRaises(ContractError): parser.parse_document(document('<p> </p><script>ignore</script>'))
        for size in (0, 63, True, 80.5):
            with self.subTest(size=size), self.assertRaises(ContractError):
                parser.parse_document(document('DEMO','text'), size)


class ParserExportTests(unittest.TestCase):
    def setUp(self):
        self.parent = Path(__file__).resolve().parent
        self.root = self.parent / ('.tmp-tillegal-t3-' + uuid4().hex)
        self.root.mkdir()
        self.addCleanup(self.cleanup)
        self.staging = self.root / 'staging'
        self.staging.mkdir()
        self.docs = [document('<p>Điều 1. DEMO</p><p>1. Không phải luật.</p>', record=str(i)) for i in range(3)]
        (self.staging/'documents.jsonl').write_bytes(b''.join(canonical_json(d.to_dict())+b'\n' for d in self.docs))
        self.manifest = {'artifact_kind':'staging_documents','usage_policy':'EXPERIMENTAL_ONLY', 'source_snapshot_id':'fixture-v1',
                         'record_count':3, 'documents':[{'document_id':d.document_id,'document_version_id':d.document_version_id,'content_sha256':d.content_sha256} for d in self.docs],
                         'artifacts':[{'path':'documents.jsonl','sha256':file_hash(self.staging/'documents.jsonl')}]}
        self.manifest['staging_snapshot_id'] = content_hash(canonical_json({a['path']:a['sha256'] for a in self.manifest['artifacts']}).decode('utf-8'))
        self.path = self.staging/'manifest.json'
        self.save_manifest()

    def save_manifest(self):
        self.path.write_bytes(canonical_json(self.manifest))

    def cleanup(self):
        resolved = self.root.resolve()
        if resolved.parent != self.parent or not resolved.name.startswith('.tmp-tillegal-t3-'):
            raise ValueError('unsafe cleanup path')
        shutil.rmtree(resolved)

    def test_export_roundtrip_preserves_input_and_is_reproducible(self):
        before = {p:file_hash(p) for p in self.staging.iterdir()}
        one, validation = parser.export_pilot(self.path, self.root/'one')
        two, _ = parser.export_pilot(self.path, self.root/'two')
        self.assertEqual(one['processed_snapshot_id'], two['processed_snapshot_id'])
        self.assertEqual(one['record_count'], 3)
        self.assertIsNone(one['corpus_snapshot_id'])
        self.assertFalse(one['approved_for_legal_verification'])
        for p,h in before.items(): self.assertEqual(file_hash(p),h)
        for a in one['artifacts']: self.assertEqual(file_hash(self.root/'one'/a['path']),a['sha256'])
        structures = [json.loads(s) for s in (self.root/'one'/'structures.jsonl').read_text(encoding='utf-8').splitlines()]
        chunks = [json.loads(s) for s in (self.root/'one'/'chunks.jsonl').read_text(encoding='utf-8').splitlines()]
        for d,r in zip(self.docs, structures):
            r['chunks'] = [c for c in chunks if c['document_version_id']==d.document_version_id]
            parser.validate_result(d,r)
        self.assertTrue(all(d['trace_and_chunk_coverage']=='PASS' for d in validation['documents']))

    def test_export_rejects_overwrite_input_path_and_changed_hash(self):
        for out in (self.staging, self.staging/'nested'):
            with self.assertRaises(ContractError): parser.export_pilot(self.path,out)
        (self.staging/'documents.jsonl').write_text('changed', encoding='utf-8')
        with self.assertRaises(ContractError): parser.export_pilot(self.path,self.root/'out')
        self.assertFalse((self.root/'out').exists())

    def test_export_rejects_snapshot_and_declaration_mismatch(self):
        self.manifest['staging_snapshot_id']='wrong'
        self.save_manifest()
        with self.assertRaises(ContractError): parser.export_pilot(self.path,self.root/'out')
        self.manifest['staging_snapshot_id']=content_hash(canonical_json({a['path']:a['sha256'] for a in self.manifest['artifacts']}).decode('utf-8'))
        self.manifest['documents'][0]['content_sha256']='f'*64
        self.save_manifest()
        with self.assertRaises(ContractError): parser.export_pilot(self.path,self.root/'out')

    def test_input_change_during_parsing_prevents_output(self):
        original = parser.parse_document
        def changing(d, max_chars):
            result = original(d,max_chars)
            self.path.write_bytes(self.path.read_bytes()+b' ')
            return result
        with patch.object(parser,'parse_document',side_effect=changing):
            with self.assertRaises(ContractError): parser.export_pilot(self.path,self.root/'out')
        self.assertFalse((self.root/'out').exists())


class LocalPilotParserTests(unittest.TestCase):
    """Pinned local regression samples, not legal gold or corpus-wide accuracy."""
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / 'data/staging/labor-pilot-3/documents.jsonl'
        if not path.is_file():
            raise unittest.SkipTest('T2 local pilot unavailable; real-data checks not run')
        cls.documents = {d.source_record_id: d for d in load_documents(path)}
        expected = {'139264':'ce2d42fab464509f00a287734ff4fff8810c91d0ecf26d38566d14e920b5c011',
                    '146696':'67146c33d77baa4c0d121214a35c53a819bc0568dd927384a61d98e3948daa2c',
                    '152668':'4718484e39685d10185daae16ff996809299e3ffdc767df3a32f1e2a2bcb27d3'}
        if {k:d.content_sha256 for k,d in cls.documents.items()} != expected:
            raise AssertionError('Pilot changed: review parsing expectations before replacing baseline')
        cls.results = {k:parser.parse_document(d) for k,d in cls.documents.items()}

    def test_main_article_sequences_and_separate_form_scopes(self):
        for key, count in [('139264',220),('146696',12),('152668',115)]:
            with self.subTest(document=key):
                nodes = self.results[key]['nodes']
                labels = [n['label'] for n in nodes if n['kind']=='article' and n['scope']=='main']
                self.assertEqual(labels,[str(i) for i in range(1,count+1)])
        n = self.results['152668']['nodes']
        self.assertEqual([x['label'] for x in n if x['kind']=='appendix'],['I','II','III','IV','V','VI'])
        self.assertEqual(len([x for x in n if x['kind']=='form']),19)
        self.assertEqual(len([x for x in n if x['kind']=='article' and x['scope']=='form']),18)

    def test_reviewed_local_boundary_samples(self):
        cases = [
            ('139264','Điều 7. Xây dựng quan hệ lao động',{'scope':'main','article':'7'}),
            ('139264','“Điều 54. Điều kiện hưởng lương hưu',{'scope':'quoted','article':'219','clause':'1','point':'a'}),
            ('139264','b) Sửa đổi, bổ sung Điều 55 như sau:',{'scope':'main','article':'219','clause':'1','point':'b'}),
            ('139264','Bộ luật này được Quốc hội',{'scope':'closing','article':None}),
            ('146696','Điều 3. Nội dung chủ yếu của hợp đồng lao động',{'scope':'main','article':'3'}),
            ('146696','BỘ TRƯỞNG (Đã ký)',{'scope':'closing','article':None,'block_kind':'table'}),
            ('152668','Điều 7. Thời hạn báo trước',{'scope':'main','article':'7','appendix':None}),
            ('152668','Điều 7. Quyền và nghĩa vụ của người sử dụng lao động',{'scope':'form','appendix':'V','form':'01/PLV','article':'7'}),
            ('152668','Tiền lương làm thêm giờ = Tiền lương giờ',{'block_kind':'table','article':'55','clause':'1'}),
        ]
        for key, text, expected in cases:
            with self.subTest(document=key,text=text):
                found = chunks_with(self.results[key],text)
                self.assertEqual(len(found),1)
                for field,value in expected.items(): self.assertEqual(found[0][field],value)
        results = self.results['152668']
        form = next(n for n in results['nodes'] if n['kind']=='form' and n['label']=='07/PLII')
        self.assertIn('FORM_APPENDIX_LABEL_MISMATCH',form['issues'])
        self.assertEqual(len([n for n in results['nodes'] if 'DUPLICATE_LABEL_UNDER_PARENT' in n['issues']]),1)
        images = [c for c in results['chunks'] if c['text']=='[IMAGE]']
        self.assertEqual([(c['article'],c['clause']) for c in images],[('56','1'),('56','2'),('57','2')])

    def test_visible_character_coverage_with_independent_html_reader(self):
        from bs4 import BeautifulSoup
        for key, d in self.documents.items():
            with self.subTest(document=key):
                soup = BeautifulSoup(d.content,'html.parser')
                expected_tables = len(soup.find_all('table'))
                expected_images = len(soup.find_all('img'))
                for tag in soup.find_all(['head','style','script']): tag.decompose()
                expected = re.sub(r'\s+','',soup.get_text())
                blocks = self.results[key]['blocks']
                actual = re.sub(r'\s+','',''.join(b['text'] for b in blocks)).replace('[IMAGE]','')
                self.assertEqual(expected,actual)
                self.assertEqual(sum(b['kind']=='table' for b in blocks),expected_tables)
                self.assertEqual(sum(s['kind']=='image' for b in blocks for s in b['segments']),expected_images)


if __name__ == '__main__':
    unittest.main()
