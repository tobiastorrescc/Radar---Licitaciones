import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from types import SimpleNamespace
import conectores as c
import documentos
import extractores as e
from test_conectores import pdf

FIX=Path(__file__).parent/'fixtures'/'reales'


class ExtraccionRealTests(unittest.TestCase):
    def registros(self,nombre,**config):
        return e.extraer((FIX/(nombre+'.html')).read_text(), 'https://example.org/'+nombre,config)[0]

    def test_13_fuentes_antes_parciales_con_publicaciones_reales(self):
        casos=[('fuente-007',{},'Servicio de Mantenimiento'),('fuente-008',{},'ADJUDICA'),
          ('roldan-ficha',{},'CORTE DE CÉSPED'),('fuente-021',{},'indumentaria'),
          ('fuente-022',{},'solar'),('fuente-024',{},'Interconexión'),('fuente-025',{},'COCINA'),
          ('fuente-026',{},'agua envasada'),('fuente-038',{'tipo_tabla':'Licitación Privada'},'hormigón'),
          ('fuente-041',{},'LICITACIÓN'),('fuente-045',{},'01/2024'),
          ('fuente-046',{'incluir_aside':True},'19/2018'),('fuente-050',{},'REPAVIMENTACIÓN')]
        for nombre,config,palabra in casos:
            with self.subTest(nombre=nombre):
                regs=self.registros(nombre,**config)
                self.assertTrue(regs)
                self.assertTrue(any(palabra in r['objeto'] for r in regs))

    def test_rosario_telefono_no_es_publicacion_y_listado_si(self):
        self.assertEqual(self.registros('rosario-contacto'),[])
        regs=self.registros('rosario-resultados',adaptador='rosario')
        self.assertTrue(any(r['numero_procedimiento']=='131491/2026' for r in regs))
        self.assertTrue(any('BOMBA' in r['objeto'] for r in regs))

    def test_epe_tarjetas_sin_anchors_tienen_objeto(self):
        r=self.registros('fuente-003',adaptador='epe')
        self.assertEqual(len(r),2)
        self.assertTrue(any('PODADORAS' in x['objeto'] for x in r))
        self.assertTrue(all(x['detalle_completo'] for x in r))

    def test_baradero_datos_react_publicos_con_objeto_y_sin_duplicados(self):
        regs=self.registros('baradero-flight',adaptador='baradero')
        self.assertEqual(len(regs),68)
        self.assertEqual(len({(r['procedimiento'],r['evento_publicado']) for r in regs}),68)
        self.assertTrue(all(r['detalle_completo'] for r in regs))
        self.assertTrue(any('Alimentario' in r['objeto'] and r['numero_procedimiento']=='1/2026' for r in regs))

    def test_ater_abreviatura_y_numeros_sin_pdf(self):
        regs=self.registros('fuente-027')
        self.assertEqual(len(regs),2)
        self.assertEqual(regs[0]['procedimiento'],'licitacion privada 8/2026')
        self.assertIn('ORACLE',regs[0]['objeto'])

    def test_crespo_tabla_numero_tipo_y_objeto(self):
        r=self.registros('fuente-038',tipo_tabla='Licitación Privada')
        self.assertEqual(len(r),7)
        self.assertTrue(all(x['detalle_completo'] for x in r))
        self.assertTrue(any('310 m3' in x['objeto'] for x in r))

    def test_sanjose_publica_contexto_no_pierde_objeto(self):
        r=self.registros('fuente-032')
        self.assertTrue(any('Cafetería' in x['objeto'] for x in r))
        self.assertTrue(all(x['detalle_completo'] for x in r))

    def test_licencias_json_joomla_sin_ejecutar_js(self):
        regs=self.registros('cdelu-datos',adaptador='cdelu')
        self.assertEqual(len(regs),2)
        self.assertEqual(regs[0]['numero_procedimiento'],'37/2026')
        self.assertIn('Residuos',regs[0]['objeto'])
        self.assertTrue(regs[0]['documentos'])

    def test_rojas_descarga_javascript_recupera_url_publica(self):
        regs=self.registros('fuente-052')
        self.assertTrue(any('assets/php/download/' in d['url'] for r in regs for d in r['documentos']))

    def test_archivos_unicode_espacios_y_porcentajes_no_doble_escape(self):
        raw='https://example.org/Pliego N° 1/área%20urbana.pdf?x=a b'
        limpia=e.url_publica(raw)
        self.assertNotIn(' ',limpia);self.assertNotIn('á',limpia)
        self.assertIn('%C2%B0',limpia);self.assertNotIn('%2520',limpia)
        self.assertEqual(e.url_publica(limpia),limpia)

    def test_encoding_ater(self):
        texto='<meta charset="windows-1252">Licitación privada N° 08/2026'.encode('cp1252')
        self.assertIn('Licitación',c.decodificar_html(texto,'text/html'))

    def test_alias_tipo_y_ceros_no_duplican_procedimiento(self):
        html='<li>Licitación Pública N°003/26 – Hormigón <a href="/1.pdf">Pliego</a></li><li>Lic. Pública Nº 3/2026 – Hormigón <a href="/2.pdf">Anexo</a></li>'
        r,_,_=e.extraer(html,'https://example.org/')
        self.assertEqual(len(r),1);self.assertEqual(len(r[0]['documentos']),2)

    def test_reapertura_y_desierta_no_se_pierden_en_dedup(self):
        html='<li>Licitación pública 3/2026 pintura</li><li>Licitación pública 3/2026 pintura segundo llamado</li><li>Licitación pública 3/2026 pintura desierta</li>'
        self.assertEqual(len(e.extraer(html,'https://example.org/')[0]),3)

    def test_html_completo_no_descarga_pdf_auxiliar_por_defecto_configurado(self):
        llamadas=[]
        def fetch(url):
            llamadas.append(url)
            return (b'<li>Licitacion publica 1/2026 suministro de papel <a href="/planilla.pdf">Planilla auxiliar</a></li>','text/html',url)
        r=c.explorar('https://example.org/',{'lectura_adjuntos':'necesarios'},fetch=fetch)
        self.assertEqual(r['estado'],'OPERATIVA')
        self.assertEqual(llamadas,['https://example.org/'])
        self.assertEqual(r['oportunidades'][0]['documentos'][0]['url'],'https://example.org/planilla.pdf')

    def test_pdf_que_contiene_objeto_es_obligatorio_si_html_solo_numero(self):
        def fetch(url):
            if url.endswith('.pdf'):return pdf('Licitacion publica 1/2026 Suministro de papel'), 'application/pdf',url
            return b'<a href="/1.pdf">Licitacion publica 1/2026</a>','text/html',url
        r=c.explorar('https://example.org/',{'lectura_adjuntos':'necesarios'},fetch=fetch)
        self.assertEqual(r['documentos_leidos'],1)
        self.assertEqual(len(r['oportunidades']),1)
        self.assertEqual(r['estado'],'OPERATIVA')

    def test_vacio_explicito_distinto_de_extraccion_fallida(self):
        def ejecutar(html):return c.explorar('https://example.org/',{},fetch=lambda u:(html.encode(),'text/html',u))
        self.assertEqual(ejecutar('<main>No hay licitaciones vigentes</main>')['estado'],'SIN_PUBLICACIONES')
        self.assertEqual(ejecutar('<main>Cargando licitaciones...</main>')['estado'],'PENDIENTE')

    def test_redirect_www_valido_y_host_no_declarado_rechazado(self):
        body='<li>Licitacion publica 1/2026 provisión de papel</li>'.encode()
        r=c.explorar('https://www.example.org/',{},fetch=lambda u:(body,'text/html','https://example.org/'))
        self.assertEqual(r['estado'],'OPERATIVA')
        r=c.explorar('https://example.org/',{},fetch=lambda u:(body,'text/html','https://other.org/'))
        self.assertEqual(r['estado'],'PENDIENTE')

    def test_docx_zip_publicos_sin_ejecutar_archivos(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="w"><w:p><w:r><w:t>Licitación pública 3/2026 hormigón</w:t></w:r></w:p></w:document>')
        self.assertIn('hormigón',documentos.leer(b.getvalue(),'application/zip','a.docx'))
        zbuf=io.BytesIO()
        with zipfile.ZipFile(zbuf,'w') as z:z.writestr('../../contrato.txt','Licitación pública 3/2026 hormigón')
        self.assertIn('hormigón',documentos.leer(zbuf.getvalue(),'application/zip','a.zip'))

    def test_ocr_pdf_escaneado_con_avances_y_sin_declarar_vacio(self):
        def run(args,**kwargs):
            if args[0]=='pdftotext':return SimpleNamespace(stdout=b'')
            if args[0]=='pdfinfo':return SimpleNamespace(stdout='Pages: 2\n')
            if args[0]=='tesseract':return SimpleNamespace(stdout='Licitación pública 1/2026 Papel')
            return SimpleNamespace(stdout='')
        avances=[]
        with patch.object(documentos.subprocess,'run',side_effect=run):
            texto=documentos.pdf(b'%PDF-falso para mock',ocr=True,progreso=avances.append)
        self.assertEqual(len(avances),2);self.assertIn('Papel',texto)

    def test_nueva_url_santo_tome_es_santafesina_y_vialidad_corrige_404(self):
        rows={r['id']:r for r in json.loads(Path('inventario/fuentes.json').read_text())}
        self.assertIn('www.santotome.gob.ar',rows['fuente-017']['url'])
        self.assertIn('url_anterior_incorrecta',rows['fuente-017'])
        self.assertIn('dpver.gov.ar',rows['fuente-028']['url'])

if __name__=='__main__':unittest.main()
