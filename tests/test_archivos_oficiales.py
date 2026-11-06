import json,tempfile,unittest,hashlib
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
import archivos_oficiales as a,conectores,incremental as inc,oportunidades as o

class ArchivosOficiales(unittest.TestCase):
    url='https://www.santafe.gob.ar/gestionesdecompras/site/index.php'
    csv='Apertura;N° - Año;Tipo Gestión Modalidad;Objeto;Organismo Licitante\n20/11/2026;7-2026;Concurso de precios;Caños de PVC;Comuna de Ramayón\n'
    def entrada(self,root,b=None,tipo='text/csv',url=None,fuente='fuente-087',fecha='2026-11-05T12:00:00-03:00',recibo=True):
        b=b or self.csv.encode();p=Path(root)/'oficial';p.write_bytes(b);h=hashlib.sha256(b).hexdigest();u=url or self.url
        return {'fuente_id':fuente,'archivo':p.name,'url_oficial':u,'tipo':tipo,'sha256':h,'capturado_en':fecha,'recibo':{'metodo':'HTTP_OFICIAL','codigo_http':200,'url_final':u,'sha256':h} if recibo else {}}
    def test_csv_reciente_se_incorpora_sin_pliego_y_con_origen_trazable(self):
        with tempfile.TemporaryDirectory() as tmp:
            r,errs=a.leer(self.entrada(tmp),tmp,'2026-11-06T08:00:00-03:00');self.assertFalse(errs);self.assertEqual(len(r),1)
            self.assertEqual(r[0]['vigencia'],'ABIERTA');self.assertFalse(r[0]['documentos']);self.assertIsNone(r[0]['fecha_publicacion']);self.assertIn('sha256',r[0]['recuperacion_archivo'])
    def test_archivo_antiguo_no_se_rejuvenece_y_no_genera_nueva_verificada(self):
        with tempfile.TemporaryDirectory() as tmp:
            rs,_=a.leer(self.entrada(tmp,fecha='2026-10-28T08:00:00-03:00'),tmp,'2026-11-06T08:00:00-03:00');r=rs[0]
            self.assertEqual(r['vigencia_documental'],'ABIERTA');self.assertEqual(r['vigencia'],'DESCONOCIDA');self.assertEqual(inc.tipo_nuevo(r,{},'2026-11-06'),'ARCHIVO_PENDIENTE_REVALIDACION')
            r=o.normalizar(r,'2026-12-01T08:00:00-03:00');self.assertEqual(r['vigencia'],'VENCIDA')
    def test_hash_ruta_host_y_fecha_invalidos_no_se_admiten(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=self.entrada(tmp)
            for cambio in ({'sha256':'0'*64},{'archivo':'../../etc/passwd'},{'url_oficial':'https://nooficial.example/archivo'},{'capturado_en':'2027-01-01T00:00:00+00:00'},{'capturado_en':'2026-11-06'}):
                with self.assertRaises(ValueError):a.leer({**d,**cambio},tmp,'2026-11-06T08:00:00-03:00')
    def test_html_y_pdf_boletin_no_exigen_pliego_ni_presupuesto(self):
        texto='VI - LICITACIONES\nCOMUNA DE RAMAYON\nLICITACION PUBLICA N° 1/2026\nObjeto: Provisión de un tractor.\nApertura: 20 de noviembre de 2026 a las 10:00 horas.'
        with tempfile.TemporaryDirectory() as tmp:
            url='https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026/2026-11-05licitaciones.html'
            html=''.join('<p>'+x+'</p>' for x in texto.splitlines())
            d=self.entrada(tmp,html.encode(),'text/html',url,'fuente-060');r,_=a.leer(d,tmp,'2026-11-06T08:00:00-03:00');self.assertEqual(r[0]['numero_procedimiento'],'1/2026')
            d=self.entrada(tmp,b'%PDF-test','application/pdf',url,'fuente-060')
            with patch('cache_documentos.leer_texto',return_value=(texto,{})) as lector:
                r,_=a.leer(d,tmp,'2026-11-06T08:00:00-03:00');self.assertEqual(len(r),1);self.assertFalse(lector.call_args.kwargs['ocr'])
    def test_persistencia_dedup_y_recibo_evitan_reimportar_entre_procesos(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=self.entrada(tmp,recibo=False);rs,_=a.leer(d,tmp,'2026-11-06T08:00:00-03:00');path=Path(tmp)/'estado.sqlite3';db=inc.abrir(path)
            informe={'ejecucion_id':'base','actualizado':'2026-11-06T08:00:00-03:00','estado_ejecucion':'COMPLETADA','resumen':{'configuradas':0,'finalizadas':0},'observaciones':[]}
            try:
                inc.registrar(db,rs,informe);segunda=inc.registrar(db,rs,{**informe,'ejecucion_id':'segunda'});self.assertEqual(segunda['eventos_emitidos'],0)
                self.assertEqual(inc.actuales(db,informe['actualizado'],'segunda')[0]['vigencia'],'DESCONOCIDA')
                cp=Path(tmp)/'checkpoint.json';cp.write_text(json.dumps({'archivo_clave':a.clave(d),'archivo_sha256':d['sha256']}))
                a.registrar_recibos(db,{'actualizado':informe['actualizado'],'observaciones':[{'estado':'OPERATIVA','resultado_archivo':str(cp)}]})
            finally:db.close()
            self.assertIn(a.clave(d),a.vistos(path))
    def test_respaldo_inferior_no_borra_vigencia_o_datos_directos(self):
        base={'organismo':'EPE','numero_procedimiento':'7060002931','tipo_procedimiento':'licitacion publica','registro_estructurado':True,'objeto':'Aisladores','titulo':'Licitación Pública 7060002931','url':'https://www.epe.santafe.gov.ar/app2/aperturas','evidencia_url':'https://www.epe.santafe.gov.ar/app2/aperturas','fecha_apertura_texto':'20/11/2026','rango_evidencia':3,'requiere_revalidacion':False}
        viejo={**base,'fecha_apertura_texto':'10/11/2026','rango_evidencia':-1,'requiere_revalidacion':True}
        r=inc.consolidar(base,viejo);self.assertFalse(r['requiere_revalidacion']);self.assertEqual(r['fecha_apertura_texto'],'20/11/2026')
        copia={**base,'fecha_apertura_texto':'10/11/2026','recuperacion_archivo':{'metodo':'HTTP_OFICIAL'}}
        unico=a.combinar([base],[copia],'2026-11-06T08:00:00-03:00')
        self.assertEqual(len(unico),1);self.assertEqual(unico[0]['fecha_apertura'],'2026-11-20')
    def test_recibo_persistente_sobrevive_respaldo_y_restauracion(self):
        from tools import respaldo_piloto as b
        Path('work').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=Path('work').resolve()) as tmp:
            root=Path(tmp);origen=root/'origen';origen.mkdir();db=inc.abrir(origen/'estado.sqlite3')
            informe={'ejecucion_id':'uno','actualizado':'2026-11-06T08:00:00-03:00','estado_ejecucion':'COMPLETADA','resumen':{'configuradas':0,'finalizadas':0},'observaciones':[]}
            try:
                inc.registrar(db,[],informe)
                with db:db.execute('INSERT INTO meta VALUES (?,?)',('archivo_importado:abc','{}'))
            finally:db.close()
            b.exportar(origen,root/'respaldo');b.restaurar(root/'respaldo',root/'restaurado')
            self.assertEqual(a.vistos(root/'restaurado/estado.sqlite3'),{'abc'})
    def test_igual_archivo_en_distintos_organismos_no_comparte_recibo(self):
        x={'fuente_id':'uno','url_oficial':'https://uno.gob.ar/','sha256':'abc'}
        self.assertNotEqual(a.clave(x),a.clave({**x,'fuente_id':'dos','url_oficial':'https://dos.gob.ar/'}))
        self.assertNotEqual(a.clave(x),a.clave({**x,'capturado_en':'2026-11-06T08:00:00-03:00','recibo':{'metodo':'HTTP_OFICIAL'}}))

    def test_pdf_boletin_saltea_indice_y_cubre_todos_los_avisos_de_la_seccion(self):
        from fuentes_criticas import seccion_licitaciones
        texto='VI - LICITACIONES\nVII - AVISOS OFICIALES\ntexto índice\nVI - LICITACIONES\nCOMUNA DE RAMAYON\nLICITACION PUBLICA 1/2026 tractor\nVI - LICITACIONES\nCOMUNA DE OLIVEROS\nCONCURSO DE PRECIOS 8/2026 caños\nVII - AVISOS OFICIALES\nLICITACION PUBLICA 999/2026 mención ajena'
        r=seccion_licitaciones(texto);self.assertIn('1/2026',r);self.assertIn('8/2026',r);self.assertNotIn('999/2026',r)
    def test_tabla_imprimible_y_csv_no_duplican_modalidad(self):
        from fuentes_criticas import gestiones_html,gestiones_csv
        import extractores
        html='<table><tr><th>Apertura</th><th>Tipo y Número</th><th>Objeto</th><th>Organismo</th></tr><tr><td>20/11/2026</td><td>LICITACION PUBLICA 7-2026</td><td>Caños</td><td>Comuna de Ramayón</td></tr></table>'
        a1=gestiones_html(extractores.DOM(html),self.url)[0]
        csv='Apertura;N° - Año;Tipo Gestión Modalidad;Objeto;Organismo Licitante\n20/11/2026;7-2026;Licitación Pública Sin Modalidad;Caños;Comuna de Ramayón\n'
        b=gestiones_csv(csv.encode(),self.url,self.url)[0][0]
        self.assertEqual(o.identidad(a1),o.identidad(b));self.assertEqual(b['tipo_procedimiento'],'licitacion publica')

    def test_rutas_alternativas_configuradas_tienen_host_declarado(self):
        fs=json.loads(Path('inventario/fuentes.json').read_text())
        f=next(x for x in fs if x['id']=='fuente-087')
        permitidos={conectores._host(f['url']),*(conectores._host('https://'+h) for h in f.get('dominios_documentos',[]))}
        self.assertTrue(all(conectores._host(u) in permitidos for u in f['urls_inicio']))

    def test_archivo_aportado_sin_fecha_no_inventa_fecha_de_captura(self):
        from tools.importar_oficiales import registrar_archivo
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);entrada=root/'descarga.csv';entrada.write_text(self.csv)
            meta=registrar_archivo('fuente-087',self.url,entrada,root/'bandeja')
            d=json.loads(meta.read_text());self.assertIsNone(d['capturado_en'])
            rs,_=a.leer(d,meta.parent,'2026-11-06T08:00:00-03:00');self.assertEqual(rs[0]['vigencia'],'DESCONOCIDA')
    def test_archivo_fallido_no_impide_importar_el_siguiente_y_recibo_evade_relectura(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=self.entrada(root);(root/'bueno.json').write_text(json.dumps(d));(root/'malo.json').write_text(json.dumps({**d,'sha256':'0'*64}))
            rs,informe=a.importar(root/'salida',root,total=10);self.assertEqual(len(rs),1)
            self.assertEqual({x['estado'] for x in informe['observaciones']},{'OPERATIVA','ERROR_IMPORTACION'})
            (root/'malo.json').unlink();rs,inf=a.importar(root/'segunda',root,vistos={a.clave(d)})
            self.assertFalse(rs);self.assertEqual(inf['ya_importados'],1)

    def test_archivo_pendiente_no_rejuvenece_observacion_previa_ni_reemplaza_sus_datos(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=self.entrada(tmp);rs,_=a.leer(d,tmp,'2026-11-06T08:00:00-03:00');directo={**rs[0],'requiere_revalidacion':False,'rango_evidencia':3};directo.pop('recuperacion_archivo')
            db=inc.abrir(Path(tmp)/'estado.sqlite3');base={'ejecucion_id':'antes','actualizado':'2026-11-05T08:00:00-03:00','estado_ejecucion':'COMPLETADA','resumen':{'configuradas':0,'finalizadas':0},'observaciones':[]}
            try:
                inc.registrar(db,[directo],base)
                copia={**rs[0],'requiere_revalidacion':True,'rango_evidencia':-1,'objeto':'Texto viejo'}
                r=inc.registrar(db,[copia],{**base,'ejecucion_id':'archivo','actualizado':'2026-11-06T08:00:00-03:00'})
                self.assertEqual(r['eventos_emitidos'],0)
                registro=inc.actuales(db,'2026-11-06T08:00:00-03:00','archivo')[0]
                self.assertFalse(registro['observada_esta_corrida']);self.assertEqual(registro['ultima_deteccion'],base['actualizado']);self.assertEqual(registro['objeto'],'Caños de PVC')
            finally:db.close()

    @unittest.skipUnless(__import__('shutil').which('pdftotext'),'lector PDF no disponible')
    def test_pdf_con_texto_se_importa_con_lector_real_sin_ocr(self):
        # PDF sintético de regresión, no evidencia de descarga ni oportunidad nueva.
        lineas=['VI - LICITACIONES','COMUNA DE RAMAYON','LICITACION PUBLICA N 01/2026','Objeto: Provision de un tractor','Apertura: 08/10/2026 a las 10:30','VII - AVISOS OFICIALES']
        stream=('BT /F1 12 Tf 50 780 Td '+' '.join('('+l+') Tj 0 -18 Td' for l in lineas)+' ET').encode()
        objetos=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
        pdf=b'%PDF-1.4\n';offsets=[]
        for i,objeto in enumerate(objetos,1):offsets.append(len(pdf));pdf+=str(i).encode()+b' 0 obj\n'+objeto+b'\nendobj\n'
        xref=len(pdf);pdf+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{x:010d} 00000 n \n'.encode() for x in offsets)+b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+str(xref).encode()+b'\n%%EOF\n'
        with tempfile.TemporaryDirectory() as tmp,patch.dict('os.environ',{'RADAR_CACHE_DOCUMENTOS':str(Path(tmp)/'cache')}):
            url='https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026/2026-09-18licitaciones.html'
            e=self.entrada(tmp,pdf,'application/pdf',url,'fuente-060')
            rs,errores=a.leer(e,tmp,'2026-11-06T08:00:00-03:00');self.assertFalse(errores);self.assertEqual(len(rs),1);self.assertEqual(rs[0]['numero_procedimiento'],'1/2026');self.assertEqual(rs[0]['vigencia'],'VENCIDA')

    def test_busqueda_no_importa_snippets_y_no_elude_403(self):
        url='https://www.epe.santafe.gov.ar/app2/aperturas';ficha='https://www.epe.santafe.gov.ar/app2/apertura/19417';calls=[]
        def fetch(u):
            calls.append(u)
            if u==url:raise HTTPError(u,500,'Servidor',{},None)
            if 'bing.com' in u:return ('<rss><channel><item><title>Convocatoria</title><link>'+ficha+'</link></item><item><link>https://www.epen.gov.ar/licitaciones/</link></item></channel></rss>').encode(),'text/xml',u
            return Path('tests/fixtures/reales/fuente-003.html').read_bytes(),'text/html',u
        r=conectores.explorar(url,{'adaptador':'epe','consultas_respaldo':['site:epe.santafe.gov.ar licitacion'],'solo_descubrimiento':True},fetch=fetch)
        self.assertTrue(r['oportunidades']);self.assertEqual(r['estado'],'PARCIAL');self.assertTrue(r['busqueda_respaldo_intentada']);self.assertFalse(any('epen.gov' in u for u in calls))
        calls=[]
        def prohibido(u):calls.append(u);raise HTTPError(u,403,'Forbidden',{},None)
        r=conectores.explorar(url,{'adaptador':'epe','consultas_respaldo':['consulta']},fetch=prohibido)
        self.assertEqual(len(calls),1);self.assertEqual(r['estado'],'BLOQUEADA')

if __name__=='__main__':unittest.main()
