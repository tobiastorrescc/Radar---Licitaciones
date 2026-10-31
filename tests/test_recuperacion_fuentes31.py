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

    def test_identidad_no_se_deriva_del_dominio(self):
        from tools.descubrir_fuentes import verificar_identidad
        c={'tipo':'TERRITORIAL','organismo':'Municipalidad de Campana','localidad':'Campana','provincia':'Buenos Aires'}
        self.assertTrue(verificar_identidad('<title>Compras – Municipalidad de Campana</title><p>Campana, Bs. As. - Argentina</p>','https://www.campana.gob.ar/compras/',c)['verificada'])
        self.assertFalse(verificar_identidad('<title>Municipalidad de Campana</title>','https://www.campana.gob.ar/',c)['verificada'])
        c.update(organismo='Municipalidad de Carmen de Areco',localidad='Carmen de Areco')
        self.assertTrue(verificar_identidad('<title>Transparencia | Carmen de Areco - Municipio</title><p>Buenos Aires</p>','https://carmendeareco.gob.ar/transparencia/',c)['verificada'])

    def test_tarjeta_carmen_usa_anio_publicado_no_fecha_actual(self):
        from extractores_lotes import carmen_areco
        html='<article data-cda-section="licitaciones" data-cda-year="2023" data-cda-title="Licitación Privada N°7 Adquisición de conchilla" data-cda-url="/pliego.pdf" data-cda-period="Apertura 27/11/2023"></article>'
        r=carmen_areco(extractores.DOM(html).root,'https://carmendeareco.gob.ar/transparencia/')[0]
        self.assertEqual(r['numero_procedimiento'],'7/2023');self.assertEqual(r['fecha_apertura_texto'],'27/11/2023');self.assertNotIn('fecha_publicacion',r)

    def test_drive_solo_enlace_publico_observado_sin_confirmacion(self):
        from tools.comprobar_pliegos import descargar_drive_publico
        url='https://drive.google.com/file/d/archivo_publico/view'
        html=b'<script>"https://drive.usercontent.google.com/uc?id\\u003darchivo_publico\\u0026export\\u003ddownload"</script>'
        with patch('conectores.descargar',side_effect=[(html,'text/html',url),(b'%PDF-publico','application/pdf','https://drive.usercontent.google.com/uc?id=archivo_publico&export=download')]) as d:
            r=descargar_drive_publico(url)
            self.assertTrue(r[0].startswith(b'%PDF-'));self.assertEqual(d.call_count,2)
        with patch('conectores.descargar',return_value=(b'<p>Iniciar sesion</p>','text/html',url)) as d:
            with self.assertRaises(ValueError):descargar_drive_publico(url)
            self.assertEqual(d.call_count,1)

    def test_error_de_acceso_nunca_sin_novedades(self):
        from tools.auditar_lote_fuentes import estado_revision
        r=estado_revision({'estado':'BLOQUEADA','errores':[{'categoria':'RED','http_status':500}]},[],[])
        self.assertEqual(r['estado_revision'],'ERROR_DE_ACCESO');self.assertTrue(r['pendiente'])
        r=estado_revision({'estado':'OPERATIVA','errores':[]},[{'id':'existente'}],[])
        self.assertEqual(r['estado_revision'],'REVISADA_SIN_NOVEDADES')
