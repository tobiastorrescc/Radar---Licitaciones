import unittest,json,gzip,base64
from tools.inventariar_historial import referencias,normalizar_url,tipo_url,extraer_texto,contexto_json

class HistorialFuentes(unittest.TestCase):
    def test_rutas_internas_y_no_oficiales_sin_confundir_documentos(self):
        texto='https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026%2F2026-09-18licitaciones.html https://privado.com/aviso https://aeropuertorosario.com/pliego.pdf'
        us=referencias(texto,{'aeropuertorosario.com'})
        self.assertEqual(len(us),2)
        self.assertEqual(tipo_url(next(u for u in us if 'boletin' in u)),'AVISO_O_BOLETIN_INTERNO')
        self.assertEqual(tipo_url(next(u for u in us if 'pliego' in u)),'DOCUMENTO')
    def test_indices_comprimidos_se_reutilizan_sin_ocr(self):
        b=json.dumps({'fuentes':[{'url':'https://oficial.gob.ar/licitaciones/'}]}).encode()
        self.assertEqual(extraer_texto(base64.b64encode(gzip.compress(b)),'historial.json.gz.b64'),b.decode())
    def test_plantilla_y_url_con_credenciales_no_se_promueven(self):
        self.assertEqual(tipo_url('https://www.santafe.gov.ar/ver.php?seccion='),'PLANTILLA_INCOMPLETA')
        self.assertIsNone(normalizar_url('https://usuario:clave@oficial.gob.ar/'))
    def test_contexto_preserva_organismo_localidad_y_numero(self):
        rs=list(contexto_json({'registros':[{'organismo':'Comuna de Ramayón','provincia':'Santa Fe','localidad':'Ramayón','numero_procedimiento':'1/2026','url':'https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026/2026-09-18licitaciones.html'}]}))
        self.assertEqual(rs[0][1]['localidad'],'Ramayón');self.assertTrue(rs[0][2])

class DelimitadoresHistorial(unittest.TestCase):
    def test_csv_no_concatena_estado_u_otra_url_al_enlace(self):
        from tools.inventariar_historial import textos_json
        datos=b'url,pliego,estado\nhttps://oficial.gob.ar/compras/,https://oficial.gob.ar/aviso.pdf,PARCIAL\n'
        obj=json.loads(extraer_texto(datos,'reporte.csv'));us=set()
        for t in textos_json(obj):us.update(referencias(t,set()))
        self.assertEqual(us,{'https://oficial.gob.ar/compras/','https://oficial.gob.ar/aviso.pdf'})
    def test_markdown_no_incluye_cierre_ni_columnas_y_respeta_parentesis_de_archivo(self):
        texto='| [aviso](https://oficial.gob.ar/aviso.php) | 64 | [PDF](https://oficial.gob.ar/pliego(1).pdf) |'
        self.assertEqual(referencias(texto,set()),{'https://oficial.gob.ar/aviso.php','https://oficial.gob.ar/pliego(1).pdf'})
    def test_documento_hereda_organismo_y_localidad_del_procedimiento(self):
        obj={'organismo':'Hospital de Prueba','localidad':'Rosario','provincia':'Santa Fe','numero_procedimiento':'1/2026','documentos':[{'url':'https://oficial.gob.ar/anexo.pdf'}]}
        rs=list(contexto_json(obj));self.assertEqual(rs[0][1]['localidad'],'Rosario');self.assertEqual(rs[0][1]['organismo'],'Hospital de Prueba')

if __name__=='__main__':unittest.main()
