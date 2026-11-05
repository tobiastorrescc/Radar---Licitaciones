import json,tempfile,unittest
from pathlib import Path
import incremental as inc,oportunidades as o
import metricas_territoriales as mt

class MetricasTerritoriales(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.db=inc.abrir(Path(self.tmp.name)/'estado.sqlite3');self.addCleanup(self.db.close)
    def registro(self,n,prov='Santa Fe',**kw):
        return {'id':str(n),'organismo':'Municipio de Prueba','provincia':prov,'numero_procedimiento':str(n)+'/2026','tipo_procedimiento':'licitacion publica','objeto':'Compra de materiales','clasificacion_registro':'PROCEDIMIENTO','vigencia':'ABIERTA','observada_esta_corrida':True,'url':'https://prueba.gob.ar/'+str(n),'fecha_publicacion':'2026-10-31','fecha_apertura':'2026-11-03',**kw}
    def evento(self,r,tipo='NUEVO_CONFIRMADO',fecha='2026-11-01T01:00:00+00:00',corrida='uno'):
        self.db.execute('INSERT OR IGNORE INTO ejecuciones VALUES(?,?,?)',(corrida,fecha,'{}'))
        huella=corrida+r['id']
        self.db.execute('INSERT OR IGNORE INTO versiones VALUES(?,?,?,?,?)',(r['id'],huella,fecha,corrida,json.dumps(r)))
        self.db.execute('INSERT OR IGNORE INTO eventos VALUES(?,?,?,?,?)',(corrida,r['id'],huella,tipo,'[]'));self.db.commit()
    def test_meta_es_conjunta_y_no_recorta_mas_de_veinte(self):
        rs=[self.registro(n,mt.PROVINCIAS[n%3]) for n in range(80)]
        for r in rs:self.evento(r)
        m=mt.generar(self.db,rs,[],[],'2026-10-31T23:00:00-03:00')
        self.assertEqual(m['total_nuevas_confirmadas'],80)
        self.assertEqual(sum(x['nuevas_confirmadas'] for x in m['jurisdicciones'].values()),80)
        self.assertEqual(m['meta_promedio_diario'],20);self.assertIsNone(m['promedio_7_dias'])
    def test_historia_modificacion_fecha_desconocida_y_replay_no_cuentan(self):
        r=self.registro(1);self.evento(r);self.evento(r,corrida='repetida')
        for n,t in enumerate(['MODIFICADO','HISTORICA_RECUPERADA','RECUPERACION_LINEA_BASE','NUEVA_DETECCION_FECHA_DESCONOCIDA'],2):self.evento(self.registro(n),t)
        self.evento(self.registro(6,fecha_publicacion=None))
        self.evento(self.registro(7,fecha_publicacion='2020-01-01'))
        m=mt.generar(self.db,[],[],[],'2026-10-31T23:00:00-03:00');self.assertEqual(m['total_nuevas_confirmadas'],1)
    def test_vencidas_y_vigencia_desconocida_no_integran_meta_comercial(self):
        self.evento(self.registro(1))
        self.evento(self.registro(2,fecha_apertura='2026-10-30'))
        self.evento(self.registro(3,fecha_apertura=None))
        self.assertEqual(mt.generar(self.db,[],[],[],'2026-10-31T23:00:00-03:00')['total_nuevas_confirmadas'],1)

    def test_ficha_con_expediente_es_incompleta_no_omision_de_url(self):
        base=self.registro(1,organismo='Municipalidad de Rosario',url='https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38714',numero_procedimiento='88/2026')
        manual={'publicaciones':[{**base,'comprobada':True,'fecha_revision':'2026-10-31','evidencia_url':base['url']}]}
        anterior={**base,'numero_procedimiento':'110881/2026','fecha_publicacion':None}
        a=mt.contraste_manual(manual,[anterior],'2026-10-31T23:00:00-03:00')
        self.assertEqual(a['publicaciones'][0]['resultado'],'DETECTADA_INCOMPLETA')
        self.assertEqual(a['por_provincia']['Santa Fe']['incompletas'],1)
        self.assertEqual(mt.contraste_manual(manual,[base],'2026-10-31T23:00:00-03:00')['publicaciones'][0]['resultado'],'DETECTADA')

    def test_control_rosario_no_se_satisface_con_otro_id_del_mismo_numero(self):
        base=self.registro(1,organismo='Municipalidad de Rosario',url='https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38714')
        manual={'publicaciones':[{**base,'comprobada':True,'fecha_revision':'2026-10-31','evidencia_url':base['url']}]}
        otra={**base,'url':'https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38715'}
        self.assertEqual(mt.contraste_manual(manual,[otra],'2026-10-31T23:00:00-03:00')['publicaciones'][0]['resultado'],'OMITIDA')

    def test_abiertas_retenidas_y_pago_rapido_sin_documento_se_distinguen(self):
        valido={'estado':'VERIFICADO','clasificacion':'PLAZO','plazos_dias':[15],'documentos_respaldo':['https://prueba.gob.ar/pliego.pdf']}
        rs=[self.registro(1,pago=valido),self.registro(2,observada_esta_corrida=False,pago={**valido,'plazos_dias':[60]}),self.registro(3,pago={**valido,'documentos_respaldo':[]}),self.registro(4,vigencia='DESCONOCIDA')]
        m=mt.generar(self.db,rs,[],[],'2026-10-31T23:00:00-03:00')['jurisdicciones']['Santa Fe']
        self.assertEqual((m['abiertas_observadas'],m['abiertas_solo_historial'],m['vigencia_pendiente'],m['pago_rapido_verificado_abiertas']),(2,1,1,1))
    def test_omisiones_solo_sobre_muestra_no_infiere_cobertura_de_otra_provincia(self):
        uno=self.registro(1);dos=self.registro(2,'Buenos Aires')
        manual={'publicaciones':[{**r,'comprobada':True,'fecha_revision':'2026-10-31','evidencia_url':r['url']} for r in [uno,dos]]}
        m=mt.generar(self.db,[uno],[],[],'2026-10-31T23:00:00-03:00',manual)
        self.assertEqual(m['jurisdicciones']['Buenos Aires']['omitidas_muestra'],1)
        self.assertIsNone(m['jurisdicciones']['Entre Ríos']['omitidas_muestra'])
        self.assertEqual(m['jurisdicciones']['Santa Fe']['omitidas_muestra'],0)
    def test_mismo_numero_de_otra_provincia_no_oculta_omision(self):
        r=self.registro(1,'Buenos Aires');manual={'publicaciones':[{**r,'comprobada':True,'fecha_revision':'2026-10-31','evidencia_url':r['url']}]}
        a=mt.contraste_manual(manual,[self.registro(1,'Entre Ríos')],'2026-10-31T23:00:00-03:00')
        self.assertEqual(a['publicaciones'][0]['resultado'],'OMITIDA')
    def test_sigla_documentada_y_misma_ficha_no_crean_omision_falsa(self):
        r=self.registro(1,organismo='UNR',fecha_apertura='2026-11-04')
        m={**r,'organismo':'Universidad Nacional de Rosario','organismo_aliases':['UNR'],'comprobada':True,'fecha_revision':'2026-10-31','evidencia_url':r['url']}
        a=mt.contraste_manual({'publicaciones':[m]},[r,{**r,'id':'otra-variante','identidad_ambito':'ficha'}],'2026-10-31T23:00:00-03:00')
        self.assertEqual(a['publicaciones'][0]['resultado'],'DETECTADA')
        self.assertEqual(len(a['publicaciones'][0]['ids_radar']),2)

    def test_falla_con_cero_resultados_no_es_sin_publicaciones(self):
        f={'url':'https://caido.gob.ar/','provincia':'Entre Ríos','estado':'BLOQUEADA','errores':[{'tipo':'TimeoutError'}]}
        m=mt.generar(self.db,[],[],[f],'2026-10-31T23:00:00-03:00')
        self.assertEqual(len(m['jurisdicciones']['Entre Ríos']['fuentes_con_incidencias']),1)

if __name__=='__main__':unittest.main()
