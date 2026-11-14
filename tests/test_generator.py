from datetime import date
from io import BytesIO
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from generator import TEMPLATE, build_docx, format_date, format_salary, to_pdf, libreoffice_path

class GeneratorTests(unittest.TestCase):
    def test_reference_values(self):
        self.assertEqual(format_salary(16), '4,000')
        self.assertEqual(format_salary(22), '5,500')
        self.assertEqual(format_salary('16.005'), '4,001.25')
        for number, suffix in [(1,'st'),(2,'nd'),(3,'rd'),(11,'th'),(12,'th'),(13,'th'),(21,'st'),(31,'st')]:
            self.assertEqual(format_date(date(2026,1,number)), f'{number}{suffix} January 2026')

    def test_only_three_tokens_change(self):
        output = build_docx('A & B <Candidate>', 16, date(2026,11,14))
        with ZipFile(TEMPLATE) as before, ZipFile(BytesIO(output)) as after:
            self.assertEqual(before.namelist(), after.namelist())
            for member in before.namelist():
                original = before.read(member)
                changed = after.read(member)
                if member == 'word/document.xml':
                    self.assertEqual(changed, original.replace(b'{{1}}', b'14th November 2026').replace(b'{{2}}', b'A &amp; B &lt;Candidate&gt;').replace(b'{{3}}', b'4,000'))
                    ET.fromstring(changed)
                else:
                    self.assertEqual(original, changed, member)

    def test_split_runs(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'split.docx'
            with ZipFile(TEMPLATE) as src, ZipFile(path,'w') as dst:
                for item in src.infolist():
                    data = src.read(item.filename)
                    if item.filename == 'word/document.xml':
                        data = data.replace(b'{{2}}', b'{{</w:t></w:r><w:r><w:t>2}}')
                    dst.writestr(item,data)
            output = build_docx('Jane',16,date(2026,11,14),path)
            with ZipFile(BytesIO(output)) as result:
                root = ET.fromstring(result.read('word/document.xml'))
                text = ''.join(root.itertext())
                self.assertIn('Jane',text)
                self.assertNotIn('{{',text)

    def test_invalid_inputs(self):
        for ctc in [0,-1,'NaN','Infinity','hello']:
            with self.assertRaises(ValueError):
                build_docx('Jane',ctc)
        with self.assertRaises(ValueError):
            build_docx(' ',16)

    @unittest.skipUnless(libreoffice_path(), 'LibreOffice is not installed')
    def test_real_pdf_conversion(self):
        self.assertTrue(to_pdf(build_docx('Test Candidate',16)).startswith(b'%PDF-'))

if __name__ == '__main__':
    unittest.main()
