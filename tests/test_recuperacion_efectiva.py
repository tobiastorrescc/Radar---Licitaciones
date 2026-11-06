import json,tempfile,unittest
from pathlib import Path
import extractores,oportunidades as o,incremental as inc
from calidad_comercial import presentacion,escribir
from estado_criticas import evaluar
from tools.comparar_control_manual import comparar
from tools.auditar_gestiones_navegador import siguiente,total_publicado,url_log
from tools.revalidar_epe import revalidar

class RecuperacionEfectiva(unittest.TestCase):
    fecha='2026-11-06T08:00:00-03:00'
    def r(self,**k):return o.normalizar({'organismo':'Comuna de Prueba','provincia':'Santa Fe','numero_procedimiento':'7/2026','tipo_procedimiento':'concurso de precios','titulo':'Concurso de Precios 7/2026 Caños','objeto':'Provisión de caños','fecha_apertura_texto':'20/11/2026 10:00','url':'https://prueba.gob.ar/compra/7','fuente':'https://prueba.gob.ar/compras/','registro_estructurado':True,'detalle_completo':True,**k},self.fecha)
    def test_apertura_no_sustituye_limite_presentacion(self):
        self.assertFalse(presentacion(self.r(),self.fecha)['presentacion_verificada'])
        r=self.r(fecha_limite_presentacion_texto='19/11/2026 09:00');self.assertTrue(presentacion(r,self.fecha)['presentacion_verificada'])
        self.assertFalse(presentacion({**r,'observada_esta_corrida':False},self.fecha)['presentacion_verificada'])
        self.assertFalse(presentacion({**r,'requiere_revalidacion':True},self.fecha)['presentacion_verificada'])
        vencida=self.r(fecha_apertura_texto='01/11/2026',requiere_revalidacion=True,observada_esta_corrida=False)
        self.assertEqual(presentacion(vencida,self.fecha)['estado_comercial'],'VENCIDA_O_CERRADA')
    def test_hora_de_cierre_y_fecha_publicacion_son_independientes(self):
        r=self.r(fecha_limite_presentacion_texto='06/11/2026 07:00',fecha_publicacion_texto='05/11/2026')
        self.assertFalse(presentacion(r,self.fecha)['presentacion_verificada']);self.assertEqual(r['fecha_publicacion'],'2026-11-05')
        r=self.r(fecha_limite_presentacion_texto='06/11/2026');self.assertFalse(presentacion(r,self.fecha)['presentacion_verificada'])
    def test_regla_expresa_hasta_fecha_hora_apertura_sin_inferir_antes(self):
        r=self.r(texto_documento='Recepción de ofertas hasta la fecha y hora de apertura.')
        self.assertTrue(presentacion(r,self.fecha)['presentacion_verificada'])
        self.assertFalse(presentacion(self.r(texto_documento='Recepción de ofertas hasta cinco días antes de la apertura.'),self.fecha)['presentacion_verificada'])
    def test_informe_no_excluye_montos_o_pago_desconocido(self):
        r=self.r(fecha_limite_presentacion_texto='19/11/2026')
        with tempfile.TemporaryDirectory() as d:
            s=escribir([r,self.r(numero_procedimiento='8/2026')],self.fecha,d)
            self.assertEqual(s['vigentes_presentacion_verificada'],1);self.assertIn('Pendiente de verificar',Path(d,'informe_comercial.csv').read_text())
            self.assertEqual(json.loads(Path(d,'presentacion_pendiente.json').read_text())['total'],1)
    def test_estados_criticos_no_ocultan_acceso_fallido_por_archivo_viejo(self):
        obs={'id':'fuente-003','url':'https://prueba.gob.ar/compras/','estado':'BLOQUEADA','publicaciones_detectadas':0,'errores':[{'tipo':'TLS'}]}
        viejo=self.r(recuperacion_archivo={'sha256':'abc'},requiere_revalidacion=True)
        self.assertEqual(evaluar(obs,[viejo])['estado_revision_critica'],'FUENTE_INACCESIBLE')
        fresco={**viejo,'requiere_revalidacion':False};s=evaluar(obs,[fresco]);self.assertEqual(s['estado_revision_critica'],'RECUPERADA_MEDIANTE_ARCHIVO_MANUAL');self.assertEqual(s['estado_acceso_directo'],'BLOQUEADA')
        self.assertEqual(evaluar({**obs,'estado':'OPERATIVA','errores':[]},[],[])['estado_revision_critica'],'REVISADA_CORRECTAMENTE_SIN_NOVEDADES')
    def test_comparacion_separa_tres_grupos_y_no_imputa_fuera_de_lote(self):
        a=self.r();b=self.r(numero_procedimiento='8/2026',url='https://prueba.gob.ar/compra/8')
        m={**a,'comprobada':True,'fecha_revision':'2026-11-06','evidencia_url':a['url']};omitida={**b,'comprobada':True,'fecha_revision':'2026-11-06','evidencia_url':b['url']}
        ajena={**omitida,'organismo':'Otra comuna','url':'https://otra.gob.ar/compra','evidencia_url':'https://otra.gob.ar/compra'}
        r=comparar([a,self.r(numero_procedimiento='9/2026')],[m,omitida,ajena],[{'url':a['fuente'],'estado':'PARCIAL','iniciada':True}],self.fecha)
        self.assertEqual(r['resumen']['en_ambas'],1);self.assertEqual(r['resumen']['solo_automaticas'],1);self.assertEqual(r['resumen']['solo_manuales'],2);self.assertEqual(r['resumen']['omisiones_en_fuentes_consultadas'],1)
    def test_siguiente_no_repite_pagina_ni_click_deshabilitado(self):
        u='https://www.santafe.gob.ar/gestionesdecompras/site/index.php'
        dom=extractores.DOM('<a href="#">Siguiente</a><li class="disabled"><a href="?page=2">Siguiente</a></li><a rel="next" href="?page=3">Siguiente</a>')
        self.assertTrue(siguiente(dom.root.enlaces(u),u).endswith('page=3'))
        self.assertEqual(total_publicado('Mostrando 1 a 10 de 1.250 registros'),1250)
        self.assertNotIn('SECRETO',url_log(u+'?token=SECRETO&page=2'))
    def test_boletin_municipio_no_se_atribuye_al_organismo_anterior(self):
        url='https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026/2026-10-14licitaciones.html'
        html='<p>MUNICIPALIDAD DE SANTO TOME</p><p>LICITACION PUBLICA 25/2026</p><p>Objeto: Luminarias.</p><p>MUNICIPIO DE BIGAND</p><p>LICITACION PUBLICA 03/2026</p><p>Objeto: Provisión, instalación y puesta en funcionamiento de un sistema fotovoltaico On-Grid de 15,9 kWp para la Escuela Técnica Nº 327 Víctor Bigand.</p><p>Recepción de ofertas: Hasta el 30 de OCTUBRE de 2026 a las 10:45 hs.</p>'
        rs=extractores.extraer(html,url,{'adaptador':'boletin-sf'})[0]
        b=next(r for r in rs if r['numero_procedimiento']=='3/2026');self.assertEqual(b['organismo'],'Municipio De Bigand');self.assertEqual(b['localidad'],'Bigand')
        self.assertEqual(o.normalizar(b,self.fecha)['vigencia'],'VENCIDA')
    def test_boletin_sin_numero_se_registra_y_repeticion_no_duplica(self):
        html='<p>CONSORCIO FERIAL ROSARIO</p><p>LICITACION PUBLICA</p><p>OBJETO: Servicio de limpieza para el Mercado del Rio.</p><p>RECEPCION DE OFERTAS: Hasta el 20/11/2026 a las 10:00 hs.</p>'
        urls=['https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026/2026-11-05licitaciones.html','https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026/2026-11-06licitaciones.html']
        rs=[extractores.extraer(html,u,{'adaptador':'boletin-sf','admitir_avisos_sin_numero':True})[0][0] for u in urls]
        self.assertIsNone(rs[0]['numero_procedimiento']);self.assertEqual(o.identidad(rs[0]),o.identidad(rs[1]));self.assertEqual(len(o.deduplicar(rs,self.fecha)),1)
    def test_prorroga_cambia_fecha_sin_crear_otro_numero(self):
        url='https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026/2026-11-05licitaciones.html'
        html='<p>COMUNA DE RAMAYON</p><p>LICITACION PUBLICA 1/2026</p><p>OBJETO: Tractor. PRORROGA. Apertura original 08/10/2026. NUEVA FECHA DE APERTURA: 20/11/2026 10:00</p>'
        x=extractores.extraer(html,url,{'adaptador':'boletin-sf'})[0][0];r=o.normalizar(x,self.fecha)
        self.assertEqual(r['fecha_apertura'],'2026-11-20');self.assertIn('prorroga',r['evento_publicado']);self.assertEqual(o.convocatoria(r),'1')
    def test_gestiones_pagina_todos_los_listados_y_advierte_repeticion(self):
        import conectores
        from urllib.parse import urlsplit,parse_qs
        url='https://www.santafe.gob.ar/gestionesdecompras/site/index.php';calls=[]
        def tabla(n,siguiente=True):
            return '<table><tr><th>Apertura</th><th>N° - Año</th><th>Tipo Gestión Modalidad</th><th>Objeto</th><th>Organismo Licitante</th></tr><tr><td>20/11/2026</td><td>'+str(n)+'-2026</td><td>Concurso de precios</td><td>Caños</td><td>Comuna de Prueba</td></tr></table>'+('<a rel="next" href="?page='+str(n)+'">Siguiente</a>' if siguiente else '')
        def fetch(u):
            calls.append(u);n=int(parse_qs(urlsplit(u).query).get('page',['0'])[0])+1
            return tabla(n,n<7).encode(),'text/html',u
        config={'adaptador':'gestiones-sf','organismos_multiples':True,'solo_descubrimiento':True}
        r=conectores.explorar(url,config,fetch=fetch);self.assertEqual(len(r['oportunidades']),7);self.assertEqual(len(calls),7)
        incompleta=conectores.explorar(url,config,fetch=lambda u:((tabla(1,False)+'<p>Mostrando 1 a 1 de 75 registros</p>').encode(),'text/html',u))
        self.assertEqual(incompleta['estado'],'PARCIAL');self.assertTrue(any(e['tipo']=='ConteoGestionesIncompleto' for e in incompleta['errores']))
        r=conectores.explorar(url,config,fetch=lambda u:(tabla(1).encode(),'text/html',u))
        self.assertEqual(r['estado'],'PARCIAL');self.assertTrue(any(e['tipo']=='PaginacionGestionesRepetida' for e in r['errores']))
    def test_csv_no_se_recorta_a_veinte_filas_y_conteo_incompleto_no_es_operativo(self):
        from fuentes_criticas import gestiones_csv
        csv='Apertura;N° - Año;Tipo Gestión Modalidad;Objeto;Organismo Licitante\n'+''.join(f'20/11/2026;{n}-2026;Concurso de precios;Caños;Comuna de Prueba\n' for n in range(1,76))
        rs,errs=gestiones_csv(csv.encode(),'https://www.santafe.gob.ar/export.csv','https://www.santafe.gob.ar/gestionesdecompras/site/index.php');self.assertEqual(len(rs),75);self.assertFalse(errs);self.assertEqual(rs[-1]['numero_procedimiento'],'75/2026')

    def test_entrega_no_publica_apertura_sin_recepcion_comprobada(self):
        from tools.preparar_entrega import preparar
        sin=self.r(objeto='OBJETO SIN CIERRE');con=self.r(numero_procedimiento='8/2026',objeto='OBJETO CON CIERRE',fecha_limite_presentacion_texto='19/11/2026 10:00')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);root.joinpath('eventos.json').write_text(json.dumps({'fecha':self.fecha,'oportunidades':[{**r,'clasificacion_novedad':'NUEVO_CONFIRMADO'} for r in (sin,con)]}));root.joinpath('resumen.json').write_text(json.dumps({'estado':'COMPLETA'}))
            meta=preparar(root);publicado=root.joinpath('entrega/informe.md').read_text()
            self.assertEqual(meta['totales_comerciales']['nuevas_confirmadas'],1);self.assertIn('OBJETO CON CIERRE',publicado);self.assertNotIn('OBJETO SIN CIERRE',publicado);self.assertIn('OBJETO SIN CIERRE',root.joinpath('entrega/auditoria_eventos.md').read_text())

    def test_importacion_boletin_sin_numero_no_exige_enriquecimiento(self):
        import archivos_oficiales as a
        from hashlib import sha256
        html='<p>CONSORCIO FERIAL ROSARIO</p><p>LICITACION PUBLICA</p><p>OBJETO: Reparación del techo del pabellón. Recepción de ofertas hasta el 20/11/2026 10:00.</p>'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d,'edicion.html');p.write_text(html)
            entrada={'fuente_id':'fuente-060','url_oficial':'https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026/2026-11-05licitaciones.html','archivo':p.name,'tipo':'text/html','sha256':sha256(p.read_bytes()).hexdigest()}
            rs,errs=a.leer(entrada,d,ahora=self.fecha)
            self.assertEqual(len(rs),1);self.assertFalse(rs[0]['numero_procedimiento']);self.assertTrue(rs[0]['requiere_revalidacion']);self.assertFalse(errs)

    def test_epe_archivo_con_apertura_futura_no_se_revalida_solo(self):
        r=self.r(organismo='EPE',requiere_revalidacion=True,recuperacion_archivo={'capturado_en':'2026-10-28T10:00:00-03:00'})
        d=revalidar([r],[r],[{'id':'fuente-003','url':r['fuente'],'estado':'BLOQUEADA'}],self.fecha)
        self.assertEqual(d['resumen'],{'PENDIENTE_REVALIDACION':1})

if __name__=='__main__':unittest.main()
