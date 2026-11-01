import unittest,tempfile,json,os
from io import BytesIO
from zipfile import ZipFile
from pathlib import Path
from hashlib import sha256
from unittest.mock import patch
import documentos,cache_documentos

class TextoDocx(unittest.TestCase):
    def documento(self):
        b=BytesIO()
        with ZipFile(b,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>AÑO: 202</w:t></w:r><w:r><w:t>6 HORA: 1</w:t></w:r><w:r><w:t>1:00</w:t><w:tab/><w:t>APERTURA</w:t></w:r></w:p></w:body></w:document>')
        return b.getvalue()
    def test_runs_no_separan_digitos_y_tab_es_explicitamente_conservado(self):
        self.assertEqual(documentos.docx(self.documento()),'AÑO: 2026 HORA: 11:00\tAPERTURA')
    def test_invalida_solo_texto_docx_y_conserva_cache_pdf_sin_repetir_ocr(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'RADAR_CACHE_DOCUMENTOS':tmp}):
            for datos,url in [(self.documento(),'https://oficial.gob.ar/1.docx'),(b'%PDF-capturado','https://oficial.gob.ar/1.pdf')]:
                digest=sha256(datos).hexdigest();p=Path(tmp)/'textos'/(digest+'.json');p.parent.mkdir(exist_ok=True)
                p.write_text(json.dumps({'version':1,'sha256':digest,'texto':'texto previo','metodo':'OCR_SELECTIVO_CACHE'}))
                if url.endswith('.docx'):
                    texto,meta=cache_documentos.leer_texto(datos,'application/vnd.openxmlformats-officedocument.wordprocessingml.document',url,ocr=False)
                    self.assertIn('2026',texto);self.assertFalse(meta['cache_texto'])
                    with patch('documentos.leer',side_effect=AssertionError('No volver a procesar')):self.assertTrue(cache_documentos.leer_texto(datos,'application/zip',url)[1]['cache_texto'])
                else:
                    with patch('documentos.leer',side_effect=AssertionError('No volver a ejecutar OCR')):self.assertEqual(cache_documentos.leer_texto(datos,'application/pdf',url,ocr=True)[0],'texto previo')

if __name__=='__main__':unittest.main()
