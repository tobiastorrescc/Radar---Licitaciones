import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import incremental as inc
import oportunidades as o
from tools import radar_controlado as piloto

class IncrementalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.db=inc.abrir(Path(self.tmp.name)/'estado.sqlite3');self.addCleanup(self.db.close)
    def fila(self,numero='1/2026',**kw):
        return o.normalizar({'titulo':'Licitación Pública '+numero,'objeto':'Adquisición de hormigón','numero_procedimiento':numero,'tipo_procedimiento':'licitacion publica','organismo':'Comuna de Prueba','provincia':'Santa Fe','fuente':'https://prueba.gob.ar/','url':'https://prueba.gob.ar/licitacion','evidencia_url':'https://prueba.gob.ar/licitacion','detalle_completo':True,**kw},'2026-10-27T10:00:00-03:00')
    def informe(self,id='uno',estado='OPERATIVA',fecha='2026-10-26T10:00:00-03:00',**kw):
        return {'ejecucion_id':id,'actualizado':fecha,'estado_ejecucion':'COMPLETADA','resumen':{'finalizadas':1,'configuradas':1,'fuentes_error_interno':0},'observaciones':[{'url':'https://prueba.gob.ar/','estado':estado,'errores':[],'limites':[]}],**kw}
    def test_primera_linea_base_no_informa_antiguas_como_nuevas(self):
        filas=[self.fila(str(n)+'/2020',fecha_apertura_texto='01/01/2020') for n in range(1200)]
        r=inc.registrar(self.db,filas,self.informe())
        self.assertEqual(r['novedades'],0);self.assertEqual(r['clasificacion']['LINEA_BASE'],1200);self.assertEqual(r['total_historial'],1200)
    def test_segunda_identica_y_replay_son_estables(self):
        inc.registrar(self.db,[self.fila()],self.informe())
        r=inc.registrar(self.db,[self.fila()],self.informe('dos'))
        self.assertEqual(r['novedades'],0);self.assertEqual(r['clasificacion'],{'SIN_CAMBIOS':1})
        antes=self.db.execute('SELECT COUNT(*) FROM versiones').fetchone()[0]
        r=inc.registrar(self.db,[self.fila()],self.informe('dos'));self.assertTrue(r['reprocesamiento']);self.assertEqual(r['eventos_emitidos'],0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM versiones').fetchone()[0],antes)
    def test_nuevo_con_fecha_posterior_y_fecha_desconocida_son_distintos(self):
        inc.registrar(self.db,[self.fila()],self.informe())
        r=inc.registrar(self.db,[self.fila(),self.fila('2/2026',fecha_publicacion_texto='27/10/2026'),self.fila('3/2026')],self.informe('dos',fecha='2026-10-27T12:00:00-03:00'))
        self.assertEqual(r['clasificacion']['NUEVO_CONFIRMADO'],1);self.assertEqual(r['clasificacion']['NUEVA_DETECCION_FECHA_DESCONOCIDA'],1)
    def test_historica_tardia_y_fuente_parcial_no_inundan_novedades(self):
        inc.registrar(self.db,[self.fila()],self.informe(estado='PARCIAL'))
        r=inc.registrar(self.db,[self.fila(),self.fila('2/2020')],self.informe('dos'))
        self.assertEqual(r['clasificacion']['RECUPERACION_LINEA_BASE'],1);self.assertEqual(r['novedades'],0)
        r=inc.registrar(self.db,[self.fila('3/2020')],self.informe('tres'))
        self.assertEqual(r['clasificacion']['HISTORICA_ANIO_PROCEDIMIENTO'],1)
    def test_cambio_de_presupuesto_y_apertura_genera_version_sin_repetir_al_otro_dia(self):
        inc.registrar(self.db,[self.fila(presupuesto={'importe':'100','moneda':None})],self.informe())
        modificada=self.fila(presupuesto={'importe':'200','moneda':None},fecha_apertura_texto='30/10/2026')
        r=inc.registrar(self.db,[modificada],self.informe('dos'))
        self.assertEqual(r['clasificacion']['MODIFICADO'],1)
        r=inc.registrar(self.db,[modificada],self.informe('tres'));self.assertEqual(r['novedades'],0)
        evento=inc.eventos(self.db,'dos',r['fecha'])[0];self.assertIn('presupuesto',evento['campos_modificados'])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM versiones').fetchone()[0],2)
    def test_red_y_datos_vacios_no_borran_historial_ni_pago_verificado(self):
        fila=self.fila(presupuesto={'importe':'100','moneda':None},rango_evidencia=3)
        inc.registrar(self.db,[fila],self.informe())
        antes=self.db.execute('SELECT dato FROM procedimientos').fetchone()[0]
        r=inc.registrar(self.db,[],self.informe('dos',estado='BLOQUEADA'))
        self.assertEqual(self.db.execute('SELECT dato FROM procedimientos').fetchone()[0],antes)
        self.assertEqual(r['mensaje'],'SIN_NOVEDADES_CONFIRMADAS_CON_INCIDENCIAS')
        inc.registrar(self.db,[self.fila(objeto=None,detalle_completo=False)],self.informe('tres',estado='PARCIAL'))
        actual=json.loads(self.db.execute('SELECT dato FROM procedimientos').fetchone()[0])
        self.assertEqual(actual['presupuesto']['importe'],'100');self.assertEqual(actual['objeto'],fila['objeto'])
    def test_vigencia_por_reloj_no_es_modificacion_de_publicacion(self):
        fila=self.fila(fecha_apertura_texto='27/10/2026 10:00')
        inc.registrar(self.db,[fila],self.informe())
        r=inc.registrar(self.db,[fila],self.informe('dos',fecha='2026-10-28T10:00:00-03:00'))
        self.assertEqual(r['novedades'],0);self.assertEqual(inc.actuales(self.db,r['fecha'],'dos')[0]['vigencia'],'VENCIDA')
    def test_documento_misma_url_con_otro_hash_es_cambio(self):
        url='https://prueba.gob.ar/pliego.pdf'
        fila=self.fila(documentos=[{'url':url,'titulo':'Pliego'}],auditoria_documentos=[{'url':url,'estado':'DOCUMENTO_ACCESIBLE','sha256':'a'}])
        inc.registrar(self.db,[fila],self.informe())
        fila['auditoria_documentos'][0]['sha256']='b'
        r=inc.registrar(self.db,[fila],self.informe('dos'));self.assertEqual(r['clasificacion']['MODIFICADO'],1)
        self.assertIn('documentos_versiones',inc.eventos(self.db,'dos',r['fecha'])[0]['campos_modificados'])
    def test_versiones_pasadas_no_cambian_al_modificar_actual(self):
        inc.registrar(self.db,[self.fila(objeto='Hormigón')],self.informe())
        inc.registrar(self.db,[self.fila(objeto='Acero')],self.informe('dos'))
        self.assertEqual(inc.eventos(self.db,'uno','2026-10-27')[0]['objeto'],'Hormigón')
    def test_incompleta_no_se_confunde_con_cero_novedades(self):
        inc.registrar(self.db,[self.fila()],self.informe())
        r=inc.registrar(self.db,[],self.informe('dos',estado='NO_INICIADA',estado_ejecucion='TIEMPO_TOTAL',resumen={'finalizadas':0,'configuradas':1}))
        self.assertEqual(r['estado'],'INCOMPLETA');self.assertEqual(r['total_historial'],1)
    def test_estado_corrupto_no_se_reinicializa(self):
        p=Path(self.tmp.name)/'corrupto.sqlite3';p.write_bytes(b'corrupto')
        with self.assertRaises(sqlite3.DatabaseError):inc.abrir(p)
        self.assertEqual(p.read_bytes(),b'corrupto')
    def test_piloto_rechaza_rutas_de_produccion(self):
        with self.assertRaises(ValueError):piloto.validar_salida('.')
        with self.assertRaises(ValueError):piloto.validar_salida('radar_estado.json')
    def test_html_no_ejecuta_textos_de_portales_y_muestra_todo(self):
        fila=self.fila(objeto='<script>alert(1)</script>')
        r=inc.registrar(self.db,[fila],self.informe())
        destino=Path(self.tmp.name)/'informe';destino.mkdir()
        piloto.generar_informe(self.db,r,[fila],[],destino)
        html=(destino/'index.html').read_text();self.assertIn('&lt;script&gt;alert(1)',html)
        self.assertNotIn('<script>alert(1)</script>',html);self.assertIn('LINEA_BASE',html)
    def test_revisar_pendientes_no_repite_urls_ni_requiere_esperar_siete_dias(self):
        from tools.descubrir_fuentes import seleccionar_validaciones
        from datetime import datetime,timezone
        c={'url':'https://prueba.gob.ar/','id':'a','ultima_revision':datetime.now(timezone.utc).isoformat(),'version_verificador':4,'validacion':{'estado':'PENDIENTE'}}
        self.assertEqual(seleccionar_validaciones([c],set(),{},100),[])
        self.assertEqual(len(seleccionar_validaciones([c,{**c,'id':'b'}],set(),{},100,True)),1)
    def test_pago_previamente_verificado_no_desaparece_en_consulta_parcial(self):
        import pagos
        fila=self.fila(pago_evidencias=pagos.extraer('El pago se efectuará contra entrega.','https://prueba.gob.ar/pliego.pdf',hash_documento='a'))
        inc.registrar(self.db,[fila],self.informe())
        inc.registrar(self.db,[self.fila()],self.informe('dos',estado='PARCIAL'))
        r=inc.actuales(self.db,'2026-10-27','dos')[0]
        self.assertEqual(r['pago']['estado'],'VERIFICADO');self.assertEqual(r['pago']['clasificacion'],'CONTRA_ENTREGA')
    def test_enriquecer_hash_desconocido_no_afirma_cambio_del_documento(self):
        url='https://prueba.gob.ar/pliego.pdf';fila=self.fila(documentos=[{'url':url,'titulo':'Pliego'}])
        inc.registrar(self.db,[fila],self.informe())
        fila['auditoria_documentos']=[{'url':url,'sha256':'a','estado':'DOCUMENTO_ACCESIBLE'}]
        r=inc.registrar(self.db,[fila],self.informe('dos'))
        self.assertEqual(r['clasificacion']['DATOS_COMPLETADOS'],1)
    def test_nueva_version_no_conserva_prioridad_de_pago_del_documento_anterior(self):
        import pagos
        url='https://prueba.gob.ar/pliego.pdf'
        fila=self.fila(pago_evidencias=pagos.extraer('El pago se efectuará contra entrega.',url,hash_documento='a'),auditoria_documentos=[{'url':url,'sha256':'a','estado':'DOCUMENTO_ACCESIBLE'}])
        inc.registrar(self.db,[fila],self.informe())
        nueva=self.fila(auditoria_documentos=[{'url':url,'sha256':'b','estado':'DOCUMENTO_ACCESIBLE'}])
        inc.registrar(self.db,[nueva],self.informe('dos'))
        self.assertEqual(inc.actuales(self.db,'2026-10-27','dos')[0]['pago']['estado'],'PENDIENTE')
        self.assertEqual(inc.eventos(self.db,'uno','2026-10-27')[0]['pago']['estado'],'VERIFICADO')
    def test_sello_de_estado_detecta_alteracion_sin_resetear(self):
        from hashlib import sha256
        Path('work').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='work') as tmp:
            raiz=Path(tmp);destino=sqlite3.connect(raiz/'estado.sqlite3')
            try:self.db.backup(destino)
            finally:destino.close()
            piloto.sellar_estado(raiz);piloto.comprobar_estado(raiz)
            p=raiz/'estado.sqlite3';antes=p.read_bytes();p.write_bytes(antes+b'x')
            with self.assertRaises(ValueError):piloto.comprobar_estado(raiz)
            self.assertEqual(p.read_bytes(),antes+b'x')
    def test_cli_produccion_permanece_desactivada(self):
        import os,subprocess,sys
        env=dict(os.environ);env.pop('RADAR_PRODUCCION_AUTORIZADA',None)
        antes=piloto.huellas_produccion()
        r=subprocess.run([sys.executable,'radar.py'],capture_output=True,text=True,env=env,timeout=5)
        self.assertNotEqual(r.returncode,0);self.assertIn('Producción deshabilitada',r.stderr);self.assertEqual(antes,piloto.huellas_produccion())
    def test_publicacion_del_mismo_dia_no_se_afirma_antigua_ni_hora_comprobada(self):
        inc.registrar(self.db,[self.fila()],self.informe())
        r=inc.registrar(self.db,[self.fila('2/2026',fecha_publicacion_texto='26/10/2026')],self.informe('dos',fecha='2026-10-26T12:00:00-03:00'))
        self.assertEqual(r['clasificacion']['NUEVA_DETECCION_MISMO_DIA'],1);self.assertEqual(r['novedades'],1)
    def test_orquestacion_doble_y_replay_persisten_sin_red_en_prueba_unitaria(self):
        Path('work').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='work') as tmp:
            raiz=Path(tmp);checkpoint=raiz/'fake.json';checkpoint.write_text(json.dumps({'oportunidades':[self.fila()]}))
            a=self.informe();a['resumen']['consultadas']=1;a['observaciones'][0]['resultado_archivo']=str(checkpoint.resolve())
            b=copy.deepcopy(a);b['ejecucion_id']='dos'
            with patch.object(piloto,'fuentes_configuradas',return_value=[]),patch.object(piloto,'ejecutar',side_effect=[a,b]),patch.object(piloto.comprobar_pliegos,'comprobar',return_value=[]):
                r=piloto.prueba_doble(raiz)
            self.assertTrue(r['correcta']);self.assertEqual(r['segunda']['novedades'],0);piloto.comprobar_estado(raiz)
    def test_resumen_html_no_rebaja_la_calidad_del_pliego_en_corridas_posteriores(self):
        inc.registrar(self.db,[self.fila(objeto='Objeto detallado del pliego oficial',rango_evidencia=3)],self.informe())
        resumen=self.fila(objeto='Resumen de la ficha',rango_evidencia=1)
        a=inc.registrar(self.db,[resumen],self.informe('dos'));b=inc.registrar(self.db,[resumen],self.informe('tres'))
        self.assertEqual(a['novedades'],0);self.assertEqual(b['novedades'],0)
        actual=json.loads(self.db.execute('SELECT dato FROM procedimientos').fetchone()[0])
        self.assertEqual(actual['rango_evidencia'],3);self.assertEqual(actual['objeto'],'Objeto detallado del pliego oficial')
    def test_fecha_nueva_comprobada_se_informa_aun_si_la_fuente_anterior_fallo(self):
        inc.registrar(self.db,[],self.informe(estado='BLOQUEADA'))
        r=inc.registrar(self.db,[self.fila('2/2026',fecha_publicacion_texto='27/10/2026')],self.informe('dos',estado='PARCIAL',fecha='2026-10-27T12:00:00-03:00'))
        self.assertEqual(r['clasificacion']['NUEVO_CONFIRMADO'],1)

    def test_contadores_reales107_no_generan_modificacion_pero_cantidades_si(self):
        for host,a,b in [
            ('timbues.gob.ar','Adquisición 20 luminarias Publicado -- 1246 vistas alumbrado',
             'Adquisición 20 luminarias Publicado -- 1247 vistas alumbrado'),
            ('armstrong.gov.ar','Adquisición 20 luminarias Creado por Carga Noticias Descargas 490 Licencia Precio',
             'Adquisición 20 luminarias Creado por Carga Noticias Descargas 491 Licencia Precio')]:
            numero='1/2026' if host.startswith('timbues') else '2/2026'
            base=self.fila(numero,objeto=a,url='https://'+host+'/detalle',evidencia_url='https://'+host+'/detalle')
            nueva={**base,'objeto':b}
            inc.registrar(self.db,[base],self.informe(host+'-base'))
            r=inc.registrar(self.db,[nueva],self.informe(host+'-visita'))
            self.assertEqual(r['clasificacion'],{'SIN_CAMBIOS':1})
            self.assertEqual(r['novedades'],0)
            cambio={**nueva,'objeto':b.replace('20 luminarias','30 luminarias')}
            r=inc.registrar(self.db,[cambio],self.informe(host+'-cantidad'))
            self.assertEqual(r['clasificacion']['MODIFICADO'],1)

    def test_contadores_no_se_eliminan_de_la_evidencia_ni_de_otro_portal(self):
        fila=self.fila(objeto='Adquisición 20 vistas',evidencia_url='https://otro.gob.ar/detalle')
        self.assertEqual(inc.contenido(fila)['objeto'],'Adquisición 20 vistas')
        fila['evidencia_url']='https://timbues.gob.ar/detalle'
        self.assertEqual(inc.compacto(fila)['objeto'],'Adquisición 20 vistas')

    def test_resumen_completado_con_ficha_se_informa_como_datos_completados(self):
        base=self.fila(objeto='Adquisición...',rango_evidencia=1)
        inc.registrar(self.db,[base],self.informe())
        detalle=self.fila(objeto='Adquisición de ropa de trabajo',rango_evidencia=3,fecha_apertura_texto='30/10/2026')
        r=inc.registrar(self.db,[detalle],self.informe('detalle'))
        self.assertEqual(r['clasificacion'],{'DATOS_COMPLETADOS':1})
        r=inc.registrar(self.db,[detalle],self.informe('repeticion'))
        self.assertEqual(r['novedades'],0)

if __name__=='__main__':unittest.main()


class AuditoriasPreviasTests(unittest.TestCase):
    setUp=IncrementalTests.setUp
    fila=IncrementalTests.fila
    informe=IncrementalTests.informe
    def test_conocida_en_otra_auditoria_no_se_alerta_como_inedita(self):
        inc.registrar(self.db,[self.fila()],self.informe())
        r=self.fila('88/2026',fecha_publicacion='2026-10-27')
        with patch('incremental.cargar_indice_auditorias',return_value={o.identidad(r):{'github_run_id':40984204463,'fecha':'2026-10-26T10:00:00-03:00','url':r['url']}}):
            res=inc.registrar(self.db,[r],self.informe('otra',fecha='2026-10-27T12:00:00-03:00'))
        self.assertEqual(res['clasificacion'].get('RECUPERACION_LINEA_BASE'),1)
        self.assertFalse(res['clasificacion'].get('NUEVO_CONFIRMADO',0))
