import json,tempfile,unittest
from pathlib import Path
import conectores,extractores,oportunidades as o,incremental as inc

ROOT=Path('tests/fixtures/rosario_issue10')
BASE='https://www.rosario.gob.ar/inicio/'

class RosarioIssue10(unittest.TestCase):
    def test_ficha_inaccesible_no_borra_objeto_publicado_ni_inventa_numero(self):
        from urllib.error import URLError
        inicio=BASE+'result-busq-compras-licitaciones?recomendada=apertura&tipoRecomendada=5'
        def fetch(u):
            if u!=inicio:raise URLError(TimeoutError('Ficha temporalmente inaccesible'))
            return (ROOT/'listado.html').read_bytes(),'text/html',u
        r=conectores.explorar(inicio,{'adaptador':'rosario','tipo_contexto':'Compra Agil','solo_descubrimiento':True,'requerir_ficha':True},fetch=fetch)
        x=next(x for x in r['oportunidades'] if x['url'].endswith('/38714'))
        self.assertIn('DESCARTABLES DE CLÍNICA',x['objeto']);self.assertEqual(x['numero_oficial_sin_interpretar'],'110881/2026')
        self.assertIsNone(x['numero_procedimiento']);self.assertFalse(x['detalle_completo'])
        self.assertEqual(x['clasificacion_registro'],'PROCEDIMIENTO');self.assertNotEqual(r['estado'],'SIN_PUBLICACIONES')

    def test_ficha_real_se_lee_en_descubrimiento_sin_descargar_pliego(self):
        url=BASE+'compras-licitaciones/detalle/38616'
        rs,_,_=extractores.extraer((ROOT/'38616.html').read_text(),url,{'adaptador':'rosario'})
        self.assertEqual(len(rs),1);r=o.normalizar(rs[0],'2026-11-05T08:00:00-03:00')
        self.assertEqual(r['numero_procedimiento'],'47/2026');self.assertEqual(r['expediente'],'20073/2026')
        self.assertEqual(r['fecha_publicacion'],'2026-10-27');self.assertEqual(r['fecha_apertura'],'2026-11-06')
        self.assertEqual(r['presupuesto']['importe'],'33185433.00');self.assertEqual(r['vigencia'],'ABIERTA')
        self.assertTrue(r['documentos']);self.assertIn('PRESENCIAL',r['modalidad_presentacion'])
        self.assertEqual(r['enlace_pliego'],r['documentos'][0]['url'])
        self.assertEqual(r['documentos'][0]['estado'],'ENLACE_PUBLICADO_SIN_DESCARGA')

    def test_listado_y_detalle_no_duplican_ni_confunden_expediente(self):
        inicio=BASE+'result-busq-compras-licitaciones?recomendada=apertura&tipoRecomendada=5';ficha=BASE+'compras-licitaciones/detalle/38714';calls=[]
        def fetch(u):
            calls.append(u)
            html=(ROOT/'listado.html').read_text() if u==inicio else (ROOT/'38714.html').read_text() if u==ficha else '<main>Ficha sin datos en este recorte de prueba</main>'
            return html.encode(),'text/html',u
        r=conectores.explorar(inicio,{'adaptador':'rosario','contextos_listado':{'5':'Compra Agil'},'solo_descubrimiento':True,'requerir_ficha':True,'enriquecer_fichas':True,'priorizar_listados':True,'seguir_patrones':[r'/inicio/compras-licitaciones/detalle/\d+'],'concurrencia_detalles':3},fetch=fetch)
        xs=[x for x in r['oportunidades'] if x['url']==ficha];self.assertEqual(len(xs),1)
        x=xs[0];self.assertEqual(x['numero_procedimiento'],'88/2026');self.assertEqual(x['fecha_publicacion'],'2026-11-04')
        self.assertTrue(x['detalle_completo']);self.assertEqual(x['rango_evidencia'],3)
        self.assertEqual(calls.count(ficha),1);self.assertTrue(all('/documentos/' not in u for u in calls))
        self.assertNotEqual(r['estado'],'SIN_PUBLICACIONES');self.assertTrue(r['errores']) # Recorte de veinte fichas; sólo una completa en el mock.

    def test_corregir_numero_conserva_historial_y_replay_no_alerta(self):
        url=BASE+'compras-licitaciones/detalle/38714'
        nuevo=extractores.extraer((ROOT/'38714.html').read_text(),url,{'adaptador':'rosario'})[0][0]
        viejo={**nuevo,'numero_procedimiento':'110881/2026','procedimiento':'compra agil 110881/2026','titulo':'Compra Agil 110881/2026 DESCARTABLES','fecha_publicacion':None,'rango_evidencia':1,'campos_oficiales':{}}
        informe={'ejecucion_id':'base','actualizado':'2026-11-05T08:00:00-03:00','estado_ejecucion':'COMPLETADA','resumen':{'configuradas':0,'finalizadas':0},'observaciones':[]}
        with tempfile.TemporaryDirectory() as tmp:
            db=inc.abrir(Path(tmp)/'estado.sqlite3')
            try:
                inc.registrar(db,[o.normalizar(viejo,informe['actualizado'])],informe)
                id_antes=db.execute('SELECT id FROM procedimientos').fetchone()[0]
                inc.registrar(db,[o.normalizar(nuevo,informe['actualizado'])],{**informe,'ejecucion_id':'correccion'})
                self.assertEqual(db.execute('SELECT id FROM procedimientos').fetchone()[0],id_antes)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM procedimientos').fetchone()[0],1)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM versiones').fetchone()[0],2)
                self.assertEqual(inc.registrar(db,[o.normalizar(nuevo,informe['actualizado'])],{**informe,'ejecucion_id':'repeticion'})['novedades'],0)
                otra={**nuevo,'url':BASE+'compras-licitaciones/detalle/38715'}
                self.assertNotEqual(o.identidad(nuevo),o.identidad(otra))
            finally:db.close()

    def test_paginacion_no_tiene_tope_cuatro_paginas(self):
        from urllib.parse import urlsplit,parse_qs
        inicio=BASE+'result-busq-compras-licitaciones?recomendada=apertura&tipoRecomendada=5';calls=[]
        def fetch(u):
            calls.append(u);n=int(parse_qs(urlsplit(u).query).get('page',['0'])[0])
            if n==2 and calls.count(u)==1:
                from urllib.error import URLError
                raise URLError(TimeoutError('Lectura temporalmente agotada'))
            html='<main><h2 class="contrataciones-resumen__total-titulo">Compra Agil</h2><div class="contrataciones-resumen__tarjeta">Compra Agil '+str(n+1)+'/2026 Provisión de caños. Apertura: 10/12/2026 10:00</div>'
            if n<5:html+='<a rel="next" href="?page='+str(n+1)+'&amp;recomendada=apertura&amp;tipoRecomendada=5">Siguiente</a>'
            return (html+'</main>').encode(),'text/html',u
        r=conectores.explorar(inicio,{'adaptador':'rosario','solo_descubrimiento':True,'priorizar_listados':True,'reintentos_transitorios':1},fetch=fetch)
        self.assertEqual(len(calls),7);self.assertEqual(len(set(calls)),6);self.assertEqual(len(r['oportunidades']),6)

if __name__=='__main__':unittest.main()
