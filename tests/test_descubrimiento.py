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
    def test_buscador_alternativo_solo_enlaces_de_resultados_publicados(self):
        html='<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fcolon.gob.ar%2Fcompras">Compras</a><a href="https://otro.gob.ar/">Publicidad</a>'
        self.assertEqual(d.resultados_html(html,'https://html.duckduckgo.com/'),[{'url':'https://colon.gob.ar/compras','titulo':'Compras'}])
    def test_worker_lento_o_bloqueado_no_promociona(self):
        with tempfile.TemporaryDirectory() as tmp:
            entrada=Path(tmp)/'entrada.json';salida=Path(tmp)/'resultado.json'
            entrada.write_text(json.dumps({**self.candidato(),'url':'https://colon.gob.ar/'}))
            with patch('conectores.descargar',side_effect=TimeoutError('lectura agotada')):d.worker(entrada,salida)
            r=json.loads(salida.read_text());self.assertEqual(r['validacion']['estado'],'PENDIENTE');self.assertTrue(r['errores'][0]['timeout'])
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
    def test_zarate_acordeones_no_mezclan_anios_ni_pliegos(self):
        import extractores
        html='<main><details><summary>LICITACIONES PÚBLICAS | AÑO 2025</summary><details><summary>N° 14 "Alquiler de maquinaria vial"</summary><p><a href="a.pdf">Descargá el pliego acá</a></p></details></details><details><summary>LICITACIONES PÚBLICAS | AÑO 2024</summary><details><summary>N° 14 "Pavimentación de calle"</summary><p><a href="b.pdf">Pliego</a></p></details></details></main>'
        rs,_,_=extractores.extraer(html,'https://zarate.gob.ar/licitaciones-publicas/',{'adaptador':'zarate'})
        self.assertEqual([r['numero_procedimiento'] for r in rs],['14/2025','14/2024'])
        self.assertEqual(rs[0]['documentos'],[{'url':'https://zarate.gob.ar/licitaciones-publicas/a.pdf','titulo':'Descargá el pliego acá'}])
        self.assertNotIn('Pavimentación',rs[0]['objeto'])
    def test_junin_no_asocia_documentos_salariales_al_procedimiento(self):
        import extractores
        html='<main><div><a href="sueldos.pdf">PLANTA PERSONAL</a><div class="panel panel-info"><h2>LICITACIÓN PÚBLICA N° 25/2023</h2><p>OBJETO: REPARACIÓN FACHADA MUNICIPAL</p><a href="aviso.pdf">AVISO PUBLICADO</a></div></div></main>'
        rs,_,_=extractores.extraer(html,'https://www.junin.gob.ar/licitacione-publica/licitacion-publica-109',{'adaptador':'junin'})
        self.assertEqual(len(rs),1);self.assertEqual(len(rs[0]['documentos']),1);self.assertTrue(rs[0]['documentos'][0]['url'].endswith('aviso.pdf'))
    def test_documentos_recientes_primero_sin_eliminar_historicos(self):
        import conectores
        visitas=[]
        html='<h2>Licitación Pública 1/2020</h2><img src="a.jpg"><h2>Licitación Pública 1/2026</h2><img src="z.jpg">'
        def fetch(url):
            visitas.append(url)
            return (html.encode(),'text/html',url) if url.endswith('/') else (b'imagen','image/jpeg',url)
        with patch('cache_documentos.leer_texto',return_value=('Objeto: compra de hormigón',{})):
            r=conectores.explorar('https://colon.gob.ar/',{'adaptador':'colon-pba','documentos_imagen':True,'lectura_adjuntos':'necesarios'},fetch=fetch)
        self.assertEqual(visitas[1],'https://colon.gob.ar/z.jpg');self.assertEqual(len(r['oportunidades']),2)
    def test_funes_post_publicado_pagina_hasta_total_sin_confundir_fechas(self):
        import conectores
        from urllib.parse import parse_qs
        html='<h1>Municipalidad de Funes</h1><table id="licitacionesTable"></table><script>const url = "/ajax/data-licitaciones-web.ajax.php";ajax: {type: "POST"}</script>'
        cuerpos=[]
        def fetch(url,datos_post=None):
            if datos_post is None:return html.encode(),'text/html',url
            q=parse_qs(datos_post.decode());cuerpos.append(q);inicio=int(q['start'][0]);numero=inicio+1
            fila={'id_licitacion':numero,'numero_licitacion':str(numero),'titulo_licitacion':f'Licitación Pública {numero}/2026 Objeto: compra de hormigón elaborado para obras','date_created_licitacion':'2026-10-22 10:00:00','documentos':[]}
            return json.dumps({'recordsTotal':2,'recordsFiltered':2,'data':[fila]}).encode(),'application/json',url
        r=conectores.explorar('https://funes.gob.ar/boletin_oficial',{'organismo':'Municipalidad de Funes'},fetch=fetch)
        self.assertEqual(r['estado'],'OPERATIVA');self.assertEqual(len(r['oportunidades']),2);self.assertEqual([q['start'][0] for q in cuerpos],['0','1'])
        self.assertTrue(all(i['fecha_publicacion']=='2026-10-22' and i['fecha_apertura'] is None for i in r['oportunidades']))
    def test_funes_esquema_invalido_y_paginacion_repetida_no_se_declaran_exitosos(self):
        from extractores_lotes import extraer_funes
        with self.assertRaises(ValueError):extraer_funes('{}','https://funes.gob.ar/')
        with self.assertRaises(ValueError):extraer_funes('{"data":[],"recordsTotal":20,"recordsFiltered":10}','https://funes.gob.ar/')
    def test_funes_regresion_campos_separados_numero_y_objeto(self):
        from extractores_lotes import extraer_funes
        datos={'recordsTotal':1,'recordsFiltered':1,'data':[{'numero_licitacion':'CONCURSO DE PRECIOS N° 014/2026','titulo_licitacion':'ADQUISICIÓN DE 1.850 MENSULAS O BRAZOS PARA ALUMBRADO PÚBLICO DE LA CIUDAD DE FUNES','date_created_licitacion':'2026-10-22','documentos':[]}]}
        r=extraer_funes(json.dumps(datos),'https://funes.gob.ar/ajax/data-licitaciones-web.ajax.php')[0][0]
        self.assertEqual(r['numero_procedimiento'],'14/2026');self.assertEqual(r['tipo_procedimiento'],'concurso de precios')
        self.assertEqual(r['objeto'],datos['data'][0]['titulo_licitacion']);self.assertTrue(r['detalle_completo'])
        datos['data'][0]['titulo_licitacion']='F'
        r=extraer_funes(json.dumps(datos),'https://funes.gob.ar/ajax/data-licitaciones-web.ajax.php')[0][0]
        self.assertIsNone(r['objeto']);self.assertFalse(r['detalle_completo'])

if __name__=='__main__':unittest.main()
