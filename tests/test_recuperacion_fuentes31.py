import unittest
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch
import conectores,extractores

class RecuperacionFuentes(unittest.TestCase):
    def test_epe_reintenta_500_y_exige_procedimiento(self):
        url='https://www.epe.santafe.gov.ar/app2/aperturas';calls=[]
        html=Path('tests/fixtures/reales/fuente-003.html').read_text()
        def fetch(u):
            calls.append(u)
            if len(calls)==1:raise HTTPError(u,500,'Servidor',{},None)
            return html.encode(),'text/html',u
        with patch('conectores.time.sleep'):
            r=conectores.explorar(url,{'adaptador':'epe','organismo':'EPE','provincia':'Santa Fe','reintentos_transitorios':1},fetch=fetch)
        self.assertEqual(len(calls),2);self.assertTrue(r['oportunidades'])
        self.assertTrue(r['oportunidades'][0]['objeto']);self.assertEqual(len(r['intentos_http']),2)

    def test_epe_no_reintenta_429_ni_declara_vacio(self):
        calls=[];url='https://www.epe.santafe.gov.ar/app2/aperturas'
        def fetch(u):calls.append(u);raise HTTPError(u,429,'Limite',{},None)
        r=conectores.explorar(url,{'adaptador':'epe','reintentos_transitorios':1},fetch=fetch)
        self.assertEqual(len(calls),1);self.assertEqual(r['estado'],'BLOQUEADA');self.assertFalse(r['evidencias_listado_vacio'])

    def test_epe_200_sin_estructura_no_significa_sin_publicaciones(self):
        url='https://www.epe.santafe.gov.ar/app2/aperturas'
        r=conectores.explorar(url,{'adaptador':'epe'},fetch=lambda u:(b'<main>Sin licitaciones vigentes</main>','text/html',u))
        self.assertEqual(r['estado'],'PENDIENTE');self.assertTrue(r['errores']);self.assertFalse(r['oportunidades'])

    def test_sanjose_preserva_drive_sin_inventar_descarga(self):
        url='https://sanjose.gob.ar/concursos-licitaciones/'
        doc='https://drive.google.com/file/d/archivo_publico/view?usp=drive_link'
        html='<article>Licitación pública 19/2026 Adquisición de materiales para obras <a href="'+doc+'">Pliego</a></article>'
        rs,_,_=extractores.extraer(html,url,{'enlaces_drive_publicos':True})
        self.assertEqual(rs[0]['documentos'][0]['url'],doc)
        self.assertNotIn('uc?export',str(rs))
