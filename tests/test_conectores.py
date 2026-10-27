import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from urllib.error import URLError
import conectores as c
import radar


def pdf(text):
    # PDF mínimo real, generado sin dependencias. Contenido de prueba sintético.
    stream = ('BT /F1 12 Tf 50 750 Td (' + text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)') + ') Tj ET').encode()
    objs = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>', b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    out=b'%PDF-1.4\n';offsets=[0]
    for i,obj in enumerate(objs,1):
        offsets.append(len(out));out+=f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n'
    start=len(out);out+=b'xref\n0 6\n0000000000 65535 f \n'
    out+=b''.join(f'{n:010d} 00000 n \n'.encode() for n in offsets[1:])
    return out+b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+str(start).encode()+b'\n%%EOF'


class ConectoresTests(unittest.TestCase):
    def explore(self, pages, **kwargs):
        def fetch(url):
            value = pages[url]
            if isinstance(value, Exception): raise value
            return (value if isinstance(value, bytes) else value.encode(),
                    'application/pdf' if isinstance(value, bytes) else 'text/html', url)
        return c.explorar('https://example.org/', {'organismo':'Municipio'}, fetch=fetch, **kwargs)

    def test_navigation_is_not_publication(self):
        r=self.explore({'https://example.org/':'<a href="/licitaciones">Licitaciones 2026</a>'})
        self.assertEqual(r['estado'],'PENDIENTE');self.assertEqual(r['oportunidades'],[])

    def test_table_download_keeps_row_object(self):
        r=self.explore({'https://example.org/':'<table><tr><td>Licitación Privada 8/2026 pintura</td><td><a href="/a.pdf">Descargar</a></td></tr></table>',
                        'https://example.org/a.pdf':pdf('Licitacion Privada 8/2026 pintura')})
        self.assertEqual(r['estado'],'OPERATIVA')
        self.assertEqual(len(r['oportunidades']),1)
        self.assertIn('pintura',r['oportunidades'][0]['titulo'])
        self.assertEqual(r['documentos_leidos'],1)

    def test_rel_next_numeric_pagination_cycle(self):
        r=self.explore({'https://example.org/':'<a href="/dos" rel="next">2</a>',
          'https://example.org/dos':'<li>Compra menor 8/2026 papel</li><a href="/" rel="next">1</a>'})
        self.assertEqual(r['paginas_visitadas'],2);self.assertEqual(len(r['oportunidades']),1)

    def test_query_pagination(self):
        r=self.explore({'https://example.org/':'<a href="?pagina=2">2</a>',
          'https://example.org/?pagina=2':'<article>Concurso de precios 4/2026</article>'})
        self.assertEqual(len(r['oportunidades']),1)

    def test_all_types(self):
        for t in ['Licitación pública','Licitación privada','Concurso de precios','Concurso privado de precios',
                  'Compra directa','Compras menores','Contratación directa','Cotejo de precios']:
            with self.subTest(t=t):
                self.assertTrue(c.clasificar(t+' 42/2026')['procedimiento'])
        for t in ['desierta','segundo llamado','2do llamado','2º llamado','reapertura','nuevo llamado']:
            self.assertTrue(c.clasificar('Licitación pública 8/2026 '+t)['llamado_especial'])

    def test_same_url_multiple_procedures(self):
        r=self.explore({'https://example.org/':'<li>Licitación pública 1/2026 agua</li><li>Compra menor 2/2026 papel</li>'})
        self.assertEqual(len(r['oportunidades']),2)

    def test_reopening_changes_identity(self):
        a=c.identidad('f','Licitación pública 1/2026','https://example.org/1')
        b=c.identidad('f','Licitación pública 1/2026 segundo llamado','https://example.org/1')
        self.assertNotEqual(a,b)
        self.assertNotEqual(b,c.identidad('f','Licitación pública 1/2026 reapertura','https://example.org/1'))

    def test_pdf_actual_extraction(self):
        r=self.explore({'https://example.org/':pdf('Licitacion publica 12/2026 Compra de papel')})
        self.assertEqual(r['estado'],'OPERATIVA');self.assertEqual(len(r['oportunidades']),1)

    def test_pdf_without_text_is_pending(self):
        r=self.explore({'https://example.org/':pdf('')})
        self.assertEqual(r['estado'],'PENDIENTE');self.assertTrue(r['errores'])

    def test_pdf_invalid_is_pending(self):
        with self.assertRaises(ValueError): c.extraer_pdf(b'html')

    def test_blocked_is_not_empty(self):
        r=self.explore({'https://example.org/':URLError('Proxy no disponible')})
        self.assertEqual(r['estado'],'BLOQUEADA')

    def test_js_is_pending(self):
        r=self.explore({'https://example.org/':'<script>licitacion publica 1/2026</script>Cargando licitaciones...'})
        self.assertEqual(r['estado'],'PENDIENTE');self.assertFalse(r['oportunidades'])

    def test_partial_keeps_publications_and_errors(self):
        r=self.explore({'https://example.org/':'<li>Compra menor 2/2026</li><a rel="next" href="/2">Siguiente</a>',
          'https://example.org/2':URLError('fallo')})
        self.assertEqual(r['estado'],'PARCIAL');self.assertEqual(len(r['oportunidades']),1)

    def test_limit_reported(self):
        r=self.explore({'https://example.org/':'<a rel="next" href="/2">2</a>'},max_paginas=1)
        self.assertEqual(r['estado'],'PENDIENTE');self.assertEqual(r['limites'],['max_paginas'])

    def test_no_result_cap(self):
        r=self.explore({'https://example.org/':''.join(f'<li>Compra menor {n}/2026</li>' for n in range(500))})
        self.assertEqual(len(r['oportunidades']),500)

    def test_unknown_external_document_not_downloaded(self):
        r=self.explore({'https://example.org/':'<a href="https://other.org/a.pdf">Licitacion publica 1/2026</a>'})
        self.assertEqual(r['paginas_visitadas'],1)

    def test_integration_persistent_dedupe_and_state(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'fuentes.txt').write_text('https://example.org/')
            (root/'fuentes.json').write_text(json.dumps({'https://example.org/':{'conector':'publicaciones'}}))
            names={'ARCHIVO_FUENTES':str(root/'fuentes.txt'),'ARCHIVO_ESTADO':str(root/'estado.json'),
                   'ARCHIVO_RESULTADOS':str(root/'nuevas.json'),'ARCHIVO_AUDITORIA':str(root/'audit.json')}
            cwd=os.getcwd()
            try:
                os.chdir(root)
                with patch.multiple(radar,**names), patch.object(c,'descargar',return_value=(b'<li>Compra menor 8/2026 papel</li>','text/html','https://example.org/')),redirect_stdout(io.StringIO()),patch.object(radar.comprobar_pliegos,'comprobar',return_value=[]):
                    radar.ejecutar();radar.ejecutar()
                    self.assertEqual(json.loads((root/'nuevas.json').read_text())['total_nuevas'],0)
                    self.assertEqual(json.loads((root/'audit.json').read_text())['fuentes'][0]['estado'],'SIN_PUBLICACIONES_NUEVAS')
                    hist=json.loads((root/'estado.json').read_text())
                    self.assertEqual(len(hist['oportunidades']),1);self.assertEqual(len(hist['auditorias']),2)
            finally: os.chdir(cwd)

    def test_inventory_matches_active_configuration(self):
        inv=json.loads(Path('inventario/fuentes.json').read_text())
        active=radar.leer_lineas('fuentes.txt')
        self.assertEqual(set(active),{r['url'] for r in inv if r['incorporada']})
        self.assertEqual(set(active),set(json.loads(Path('fuentes.json').read_text())))
        self.assertEqual(len(active),len(set(active)))
