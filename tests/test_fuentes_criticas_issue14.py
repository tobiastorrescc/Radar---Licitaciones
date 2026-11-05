import csv,io,ssl,unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError,HTTPError
import conectores,extractores,oportunidades as o
from fuentes_criticas import ediciones_santafe,gestiones_csv,gestiones_html,enlaces_csv
from tools.verificar_fuentes import alertas_criticas

class CriticasIssue14(unittest.TestCase):
    url='https://www.santafe.gob.ar/gestionesdecompras/site/index.php'
    def csv(self,filas):
        b=io.StringIO();w=csv.writer(b,delimiter=';');w.writerow(['Apertura','N° - Año','Tipo Gestión Modalidad','Objeto','Organismo Licitante','URL']);w.writerows(filas);return b.getvalue().encode('utf-8-sig')
    def test_csv_oficial_sin_pliego_ni_presupuesto_y_organismos_distintos(self):
        datos=self.csv([['20/11/2026 10:00','1 - 2026','Concurso de precios','Caños de PVC','Comuna de Ramayón',self.url],['21/11/2026','1 - 2026','Concurso de precios','Caños de PVC','Comuna de Oliveros',self.url]])
        rs,errores=gestiones_csv(datos,self.url,self.url);self.assertFalse(errores);self.assertEqual(len(rs),2)
        rs=[o.normalizar(r,'2026-11-05T12:00:00-03:00') for r in rs]
        self.assertNotEqual(o.identidad(rs[0]),o.identidad(rs[1]));self.assertTrue(all(r['vigencia']=='ABIERTA' for r in rs));self.assertTrue(all(r['fecha_publicacion'] is None and not r['presupuesto'] and not r['documentos'] for r in rs))
    def test_csv_malformado_no_es_vacio_y_conserva_filas_buenas(self):
        with self.assertRaises(ValueError):gestiones_csv(b'<html>Acceso no disponible</html>',self.url,self.url)
        rs,errs=gestiones_csv(self.csv([['20/11/2026','4-2026','Compra menor','Herramientas','Hospital',self.url],['','','','','','']]),self.url,self.url)
        self.assertEqual(len(rs),1);self.assertEqual(len(errs),1);self.assertEqual(errs[0]['categoria'],'EXTRACCION')
        self.assertEqual(gestiones_csv(self.csv([]),self.url,self.url),([],[]))
    def test_html_y_csv_son_la_misma_convocatoria_y_solo_sigue_exportacion_publicada(self):
        html='<table><tr><th>Apertura</th><th>N° - Año</th><th>Tipo Gestión Modalidad</th><th>Objeto</th><th>Organismo Licitante</th></tr><tr><td>20/11/2026</td><td>4-2026</td><td>Compra menor</td><td>Herramientas</td><td>Hospital</td></tr></table><a href="?formato=csv">Descargar CSV</a>'
        rs=gestiones_html(extractores.DOM(html),self.url)
        self.assertEqual(len(rs),1);self.assertEqual(len(enlaces_csv(extractores.DOM(html),self.url)),1)
        calls=[]
        def fetch(u):
            calls.append(u)
            return (self.csv([['20/11/2026','4-2026','Compra menor','Herramientas','Hospital',self.url]]),'text/csv',u) if 'csv' in u else (html.encode(),'text/html',u)
        r=conectores.explorar(self.url,{'adaptador':'gestiones-sf','organismos_multiples':True,'solo_descubrimiento':True},fetch=fetch)
        self.assertEqual(len(r['oportunidades']),1);self.assertEqual(len(calls),2)
    def test_boletin_siembra_ediciones_completas_y_cambia_de_anio(self):
        urls=ediciones_santafe('https://www.santafe.gov.ar/boletinoficial/',3,'2027-01-02T08:00:00-03:00')
        from urllib.parse import unquote
        self.assertEqual(len(urls),4);self.assertIn('2026/2026-12-31licitaciones.html',unquote(urls[2]))
        with self.assertRaises(ValueError):ediciones_santafe('https://example.org/',3)
        with self.assertRaises(ValueError):ediciones_santafe('https://www.santafe.gov.ar/',15)
    def test_tls_eof_reintenta_sin_desactivar_validacion_y_403_no(self):
        url='https://www.epe.santafe.gov.ar/app2/aperturas';calls=[]
        def fetch(u):
            calls.append(u)
            if len(calls)==1:raise URLError(ssl.SSLEOFError('EOF'))
            return Path('tests/fixtures/reales/fuente-003.html').read_bytes(),'text/html',u
        with patch('conectores.time.sleep'):
            r=conectores.explorar(url,{'adaptador':'epe','reintentos_transitorios':1},fetch=fetch)
        self.assertEqual(len(calls),2);self.assertTrue(r['oportunidades'])
        for error in (HTTPError(url,403,'Forbidden',{},None),URLError(ssl.SSLCertVerificationError('certificate verify failed'))):
            with patch('conectores.time.sleep'),patch('conectores.descargar',side_effect=error) as f:
                r=conectores.explorar(url,{'adaptador':'epe','reintentos_transitorios':1},fetch=f)
                self.assertEqual(f.call_count,1);self.assertNotEqual(r['estado'],'SIN_PUBLICACIONES')
    def test_alerta_critica_persistente_no_confunde_fallo_con_ausencia(self):
        r=alertas_criticas([{'id':'fuente-003','url':'https://www.epe.santafe.gov.ar/app2/aperturas','estado':'BLOQUEADA','errores':[{'categoria':'RED','causa':'ERROR_CONEXION_TLS'}]},{'id':'fuente-060','url':'https://www.santafe.gov.ar/boletinoficial/','estado':'SIN_PUBLICACIONES'}])
        self.assertEqual(len(r),1);self.assertEqual(r[0]['causas'],['ERROR_CONEXION_TLS'])

if __name__=='__main__':unittest.main()
