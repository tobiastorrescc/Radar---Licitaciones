import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import oportunidades as o
import registro_fuentes
from tools import descubrir_fuentes as d

class DescubrimientoTests(unittest.TestCase):
    def candidato(self,**kw):return {'tipo':'TERRITORIAL','organismo':'Municipalidad de Colón','localidad':'Colón','provincia':'Entre Ríos',**kw}
    def test_busqueda_no_es_evidencia_y_excluye_dominios_enganosos(self):
        datos=b'<rss><channel><item><title>Compras</title><link>https://colon.gob.ar/compras</link></item><item><link>https://colon.gob.ar.ejemplo.com/</link></item><item><link>https://ejemplo.com/colon</link></item></channel></rss>'
        self.assertEqual([x['url'] for x in d.rss(datos)],['https://colon.gob.ar/compras'])
        self.assertFalse(d.oficial('https://gob.ar.ejemplo.com/'))
    def test_homonimos_y_provincia_desconocida_no_se_incorporan(self):
        html='<h1>Municipalidad de Colón</h1><p>Buenos Aires</p>'
        self.assertFalse(d.verificar_identidad(html,'https://colon.gob.ar/',self.candidato())['verificada'])
        self.assertFalse(d.verificar_identidad('<h1>Municipalidad de Colón</h1>','https://colon.gob.ar/',self.candidato())['verificada'])
        self.assertTrue(d.verificar_identidad(html.replace('Buenos Aires','Entre Ríos'),'https://colon.gob.ar/',self.candidato())['verificada'])
    def test_sector_nombre_no_se_inventa_del_dominio(self):
        c={'tipo':'SECTORIAL','provincia':'Santa Fe'}
        self.assertFalse(d.verificar_identidad('<h1>Licitaciones</h1><p>Santa Fe</p>','https://hospital.gob.ar/',c)['verificada'])
        r=d.verificar_identidad('<h1>Hospital Provincial Centenario</h1><p>Santa Fe</p>','https://hospital.gob.ar/',c)
        self.assertTrue(r['verificada']);self.assertEqual(r['organismo'],'Hospital Provincial Centenario');self.assertIsNone(r['localidad'])
    def test_http_200_sin_procedimientos_no_valida(self):
        self.assertEqual(d.aceptacion({'estado':'OPERATIVA','oportunidades':[]},{'verificada':True})['estado'],'PENDIENTE')
    def test_solo_extraccion_finalizada_y_objeto_valida(self):
        item={'titulo':'Licitación Pública 2/2026','objeto':'Compra de hormigón','detalle_completo':True,'url':'https://colon.gob.ar/pliego.pdf'}
        resultado={'estado':'OPERATIVA','oportunidades':[item]}
        self.assertEqual(d.aceptacion(resultado,{'verificada':True})['estado'],'VALIDADA')
        for r in [{**resultado,'estado':'PARCIAL'},{**resultado,'errores':[{'categoria':'RED'}]},{**resultado,'limites':['TIEMPO_TOTAL']}]:
            self.assertEqual(d.aceptacion(r,{'verificada':True})['estado'],'PENDIENTE')
    def test_rotacion_prioriza_objetivos_no_buscados(self):
        obj=[{'clave':'a'},{'clave':'b'},{'clave':'c'}]
        self.assertEqual(d.plan_busquedas(obj,{'busquedas':{'a':'2026-10-27'}},2),obj[1:])
    def test_padron_y_sectores_se_consultan_sin_inventar_urls(self):
        padron={'municipios':[{'codigo':'01','localidad':'Comuna Pequeña','provincia':'Santa Fe','tipo_gobierno':'Comuna'}]}
        r=d.objetivos(padron,[])
        self.assertEqual(len(r),10);self.assertTrue(any(i.get('organismo')=='Comuna de Comuna Pequeña' for i in r))
        self.assertTrue(all('url' not in i for i in r))
    def test_overlay_pendiente_no_carga_y_base_no_se_sustituye(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'auto.json';p.write_text(json.dumps({'schema_version':1,'fuentes':[{'url':'https://colon.gob.ar/','validacion':{'estado':'PENDIENTE'}}]}))
            with self.assertRaises(ValueError):registro_fuentes.cargar_auto(p)
        self.assertEqual(registro_fuentes.combinar({'a':{'organismo':'Legado'}},{'a':{'organismo':'Automatico'}})['a']['organismo'],'Legado')
    def test_nueva_deteccion_no_equivale_a_publicacion_nueva(self):
        base={'titulo':'Licitación Pública 2/2026','objeto':'Compra de hormigón','url':'https://colon.gob.ar/a','organismo':'Municipalidad de Colón','provincia':'Entre Ríos','detalle_completo':True}
        h={};legado={'viejo':copy.deepcopy(base)};antes=copy.deepcopy(legado)
        r=o.incorporar(h,[{**base,'fecha_publicacion_texto':'27/10/2026'}],'2026-10-27T10:00:00-03:00',desde='2026-10-26T10:00:00-03:00')[0]
        self.assertEqual(r['clasificacion_novedad'],'PUBLICACION_NUEVA_COMPROBADA')
        ambiguo=o.incorporar({},[{**base,'fecha_publicacion_texto':'26/10/2026'}],'2026-10-27T10:00:00-03:00',desde='2026-10-26T10:00:00-03:00')[0]
        self.assertEqual(ambiguo['clasificacion_novedad'],'PUBLICACION_EN_DIA_DE_CORRIDA_ANTERIOR')
        r=o.incorporar({},[{**base,'fecha_publicacion_texto':'01/01/2020'}],'2026-10-27T10:00:00-03:00',desde='2026-10-26')[0]
        self.assertEqual(r['clasificacion_novedad'],'PUBLICACION_HISTORICA_RECUPERADA')
        self.assertEqual(o.incorporar({},[base],'2026-10-27')[0]['clasificacion_novedad'],'FECHA_PUBLICACION_DESCONOCIDA')
        o.incorporar(legado,[base],'2026-10-27');self.assertEqual(legado,antes)
    def test_iafas_regresion_adjunto_segundo_llamado_y_fecha_publicacion(self):
        import extractores
        html=Path('tests/fixtures/reales/cobertura77/fuente-057.html').read_text()
        url='https://www.iafas.gov.ar/proveedores/licitaciones/'
        rs,_,_=extractores.extraer(html,url,json.loads(Path('fuentes.json').read_text())[url])
        a,b=[o.normalizar(r,'2026-10-27') for r in rs]
        self.assertEqual(a['fecha_publicacion'],'2026-10-23');self.assertEqual(b['fecha_publicacion'],'2026-10-22')
        self.assertEqual(b['fecha_apertura'],'2026-11-05');self.assertTrue(b['segundo_llamado']);self.assertFalse(a['segundo_llamado'])
        self.assertEqual(b['documentos'][0]['url'],'https://www.iafas.gov.ar/descargas/17685')

if __name__=='__main__':unittest.main()
