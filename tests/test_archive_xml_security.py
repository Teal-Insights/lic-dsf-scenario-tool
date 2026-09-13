"""Small valid ZIPs isolate declaration rejection from unrelated package errors."""
from pathlib import Path
import tempfile
import unittest
import zipfile

from lic_dsf.workbooks import check_archive, IntakeError


class ArchiveXmlSecurityTests(unittest.TestCase):
    def make_archive(self, folder, extra_name, content):
        path = Path(folder) / 'example.xlsx'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('[Content_Types].xml', '<Types/>')
            archive.writestr('xl/workbook.xml', '<workbook/>')
            archive.writestr('xl/_rels/workbook.xml.rels', '<Relationships/>')
            archive.writestr(extra_name, content)
        return path

    def test_rejects_doctype_across_encoding_and_part_name(self):
        for encoding in ('utf-8', 'utf-16', 'utf-16-le', 'utf-16-be'):
            for name in ('xl/demo.xml', 'xl/demo.XML', 'xl/demo.data'):
                with self.subTest(encoding=encoding, name=name), tempfile.TemporaryDirectory() as folder:
                    declared = 'UTF-8' if encoding == 'utf-8' else 'UTF-16'
                    text = ('<?xml version="1.0" encoding="' + declared + '"?>'
                            '<!DOCTYPE root [<!ENTITY demo "harmless">]><root>&demo;</root>')
                    path = self.make_archive(folder, name, text.encode(encoding))
                    with self.assertRaisesRegex(IntakeError, '^xml_declaration_not_supported$'):
                        check_archive(path)

    def test_valid_encoded_xml_and_binary_parts_remain_accepted(self):
        for name, content in [('xl/demo.data', '<?xml version="1.0" encoding="UTF-16"?><root>Example</root>'.encode('utf-16')),
                              ('xl/vbaProject.bin', bytes(range(256)))]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                result = check_archive(self.make_archive(folder, name, content))
                self.assertEqual(result['macro_part_present'], name.endswith('vbaProject.bin'))


if __name__ == '__main__':
    unittest.main()
