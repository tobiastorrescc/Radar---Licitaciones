from io import BytesIO
from pathlib import Path
import tempfile
import unittest
import documentos
import oportunidades as o
import pagos
import incremental as inc

FECHA='2026-10-29T12:00:00-03:00'

class MejorasCoberturaTests(unittest.TestCase):
    def registro(self,texto):
        return o.normalizar({'titulo':'Licitación pública 1/2026','objeto':texto,'detalle_completo':True,
            'organismo':'Municipalidad de Prueba','provincia':'Santa Fe','fuente':'https://oficial.gob.ar/licitaciones',
            'url':'https://oficial.gob.ar/1'},FECHA)

    def test_identidad_corregida_reutiliza_id_persistente_sin_reescribir_versiones(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            db=inc.abrir(Path(d)/'estado.sqlite3');r=self.registro('Materiales para el segundo semestre.')
            informe={'ejecucion_id':'primera','actualizado':FECHA,'estado_ejecucion':'COMPLETADA','resumen':{'finalizadas':1,'configuradas':1},'observaciones':[{'url':r['fuente'],'estado':'OPERATIVA'}]}
            with patch('oportunidades.identidad',return_value='identidad-legada'):inc.registrar(db,[r],informe)
            versiones=db.execute('SELECT * FROM versiones').fetchall()
            resumen=inc.registrar(db,[r],{**informe,'ejecucion_id':'segunda'})
            self.assertEqual(resumen['novedades'],0);self.assertEqual(resumen['total_historial'],1)
            self.assertEqual(db.execute('SELECT * FROM versiones').fetchall(),versiones)
            self.assertEqual(db.execute('SELECT id FROM procedimientos').fetchone()[0],'identidad-legada');db.close()

    def test_catalogo_unifica_duplicados_legados_y_conserva_filas_y_versiones(self):
        with tempfile.TemporaryDirectory() as d:
            db=inc.abrir(Path(d)/'estado.sqlite3');r=self.registro('Materiales. Apertura 30/10/2026.')
            informe={'ejecucion_id':'primera','actualizado':FECHA,'estado_ejecucion':'COMPLETADA','resumen':{'finalizadas':1,'configuradas':1},'observaciones':[{'url':r['fuente'],'estado':'OPERATIVA'}]}
            inc.registrar(db,[r],informe)
            db.execute("INSERT INTO procedimientos SELECT 'alias-historico',primera,ultima,corrida,huella,dato FROM procedimientos LIMIT 1");db.commit()
            versiones=db.execute('SELECT * FROM versiones').fetchall()
            actual,=inc.actuales(db,FECHA,'primera')
            self.assertEqual(len(actual['ids_historial']),2)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM procedimientos').fetchone()[0],2)
            self.assertEqual(db.execute('SELECT * FROM versiones').fetchall(),versiones);db.close()

    def test_segundo_semestre_y_anexos_no_son_segundo_llamado(self):
        a=self.registro('Insumos para el segundo semestre. Apertura 30/10/2026.')
        b={**a,'objeto':'Circular aclaratoria: segunda etapa de entrega. Apertura 30/10/2026.','url':'https://oficial.gob.ar/circular'}
        self.assertEqual(o.convocatoria(a),'1');self.assertEqual(o.convocatoria(b),'1')
        self.assertEqual(len(o.deduplicar([a,b],FECHA)),1)

    def test_limite_presentacion_anterior_a_apertura_cierra_oportunidad(self):
        r=self.registro('Apertura 30/10/2026 10:00. Presentación de ofertas hasta 29/10/2026 11:00. Publicado el 25/10/2026.')
        self.assertEqual(r['fecha_limite_presentacion'],'2026-10-29')
        self.assertEqual(r['fecha_apertura'],'2026-10-30')
        self.assertEqual(r['fecha_publicacion'],'2026-10-25')
        self.assertEqual(r['vigencia'],'VENCIDA')

    def test_sin_hora_de_cierre_hoy_no_se_asegura_abierta(self):
        r=self.registro('Apertura 31/10/2026. Fecha límite de presentación: 29/10/2026.')
        self.assertEqual(r['vigencia'],'DESCONOCIDA')
        self.assertIsNone(r['hora_limite_presentacion'])

    def test_modalidad_necesita_contexto_presentacion(self):
        r=self.registro('Presentar ofertas por correo electrónico. Recepción en mesa de entradas.')
        self.assertEqual(set(r['modalidad_presentacion']),{'CORREO_ELECTRONICO','PRESENCIAL'})
        self.assertEqual(self.registro('Consultas: correo electrónico. Pago online de tasas.')['modalidad_presentacion'],[])

    def test_pago_corto_anticipos_parciales_y_aprobacion(self):
        for n in [5,10,15,30,60,90]:
            p=pagos.consolidar(pagos.extraer(f'Forma de pago: {n} días desde la entrega, previa aprobación administrativa.','https://oficial.gob.ar/p.pdf','a'*64))
            self.assertEqual(p['clasificacion'],f'PLAZO_{n}_DIAS')
            self.assertIn('APROBACION_ADMINISTRATIVA',p['hitos_inicio'])
            self.assertIn('ENTREGA',p['hitos_inicio'])
        for texto,cat in [('Forma de pago: pagos parciales por certificación.','PAGOS_PARCIALES'),('Forma de pago: anticipo del 20 por ciento y saldo contra entrega.','MIXTO')]:
            self.assertEqual(pagos.consolidar(pagos.extraer(texto,'https://oficial.gob.ar/p.pdf','b'*64))['clasificacion'],cat)

    def test_circular_y_anexos_unifican_sin_perder_enlaces(self):
        a=self.registro('Compra de materiales. Apertura 30/10/2026.')
        b={**a,'url':'https://oficial.gob.ar/circular-1','titulo':'Circular aclaratoria Licitación pública 1/2026','documentos':[{'url':'https://oficial.gob.ar/anexo.pdf','titulo':'Anexo'}]}
        r,=o.deduplicar([a,b],FECHA)
        self.assertIn('https://oficial.gob.ar/circular-1',r['urls_publicacion'])
        self.assertEqual(len(r['documentos']),1)
        c={**b,'numero_convocatoria':2}
        self.assertEqual(len(o.deduplicar([a,b,c],FECHA)),2)

    def test_orden_y_reporte_incluyen_mas_de_80_sin_filtrar(self):
        contado=self.registro('Materiales')
        contado['pago']=pagos.consolidar(pagos.extraer('Forma de pago: contado.','https://oficial.gob.ar/pliego.pdf','a'*64))
        desierta={**self.registro('Segundo llamado, llamado anterior desierto'),'llamado_especial':True}
        self.assertIs(sorted([contado,desierta],key=o.prioridad)[0],desierta)
        registros=[{**contado,'numero_procedimiento':f'{i}/2026','titulo':f'Procedimiento {i}'} for i in range(105)]
        reporte=o.reporte(registros,FECHA)
        self.assertIn('104/2026',reporte)
        self.assertEqual(sum(l.startswith('| Municipalidad') for l in reporte.splitlines()),105)
        self.assertIn('Límite de presentación',reporte)

    def test_xlsx_lee_fechas_y_no_ejecuta_formulas(self):
        import openpyxl
        from datetime import datetime
        book=openpyxl.Workbook();ws=book.active;ws.title='Licitaciones públicas'
        ws.append(['Licitación pública 12/2026','Objeto: materiales','Apertura',datetime(2026,11,2),'Presupuesto oficial',36000000])
        ws.append(['=HYPERLINK("https://no-ejecutar.invalid","clic")'])
        buf=BytesIO();book.save(buf)
        texto=documentos.leer(buf.getvalue(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','https://oficial.gob.ar/archivo.xlsx')
        self.assertIn('36000000',texto);self.assertIn('2026-11-02',texto)
        self.assertNotIn('no-ejecutar',texto)

    def test_no_crea_cambios_por_huella_antigua_sin_diferencia_semantica(self):
        with tempfile.TemporaryDirectory() as d:
            db=inc.abrir(Path(d)/'estado.sqlite3');r=self.registro('Materiales. Apertura 30/10/2026.')
            informe={'ejecucion_id':'primera','actualizado':FECHA,'estado_ejecucion':'COMPLETADA','resumen':{'finalizadas':1,'configuradas':1},'observaciones':[{'url':r['fuente'],'estado':'OPERATIVA'}]}
            inc.registrar(db,[r],informe)
            db.execute("UPDATE procedimientos SET huella='representacion-anterior'");db.commit()
            resumen=inc.registrar(db,[r],{**informe,'ejecucion_id':'segunda'})
            self.assertEqual(resumen['novedades'],0)
            self.assertEqual(resumen['clasificacion'],{'SIN_CAMBIOS':1});db.close()


class EntregaIntegraTests(unittest.TestCase):
    def test_eml_y_csv_incluyen_todas_las_filas_sin_enviar(self):
        from email import policy
        from email.parser import BytesParser
        import csv,json
        from tools.preparar_entrega import preparar
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);registros=[]
            for i in range(105):
                registros.append({'organismo':'Prueba','numero_procedimiento':str(i)+'/2026','titulo':'Objeto '+str(i),'objeto':'=no ejecutar' if i==0 else 'Materiales',
                                  'url':'https://oficial.gob.ar/'+str(i),'clasificacion_novedad':'NUEVO_CONFIRMADO'})
            registros.append({**registros[0],'clasificacion_novedad':'RECUPERACION_LINEA_BASE'})
            (root/'eventos.json').write_text(json.dumps({'fecha':FECHA,'oportunidades':registros}))
            (root/'resumen.json').write_text(json.dumps({'estado':'COMPLETA_CON_INCIDENCIAS'}))
            meta=preparar(root);self.assertEqual(meta['total_informadas'],106);self.assertEqual(meta['totales']['nuevas_confirmadas'],105)
            self.assertFalse(meta['envio_activado'])
            mensaje=BytesParser(policy=policy.default).parsebytes((root/'entrega/informe.eml').read_bytes())
            self.assertIsNone(mensaje['To']);self.assertEqual(len(list(mensaje.iter_attachments())),2)
            with (root/'entrega/oportunidades.csv').open(encoding='utf-8-sig') as f:filas=list(csv.DictReader(f))
            self.assertEqual(len(filas),106);self.assertTrue(filas[0]['objeto'].startswith("'="))

class ASSAPublicaTests(unittest.TestCase):
    def test_api_real_recupera_cuatro_sin_inventar_fecha_publicacion(self):
        from extractores_lotes import extraer_assa
        import json
        raw=(Path(__file__).parent/'fixtures/assa-publica-20261029.json').read_bytes()
        registros,meta,detalle=extraer_assa(raw,'https://www.aguassantafesinas.com.ar/api/v1/publico/pliego/all?page=0&pageSize=100')
        self.assertEqual(len(registros),4);self.assertEqual(meta['totalElements'],4)
        for r in registros:
            r=o.normalizar({**r,'organismo':'ASSA','provincia':'Santa Fe'},FECHA)
            self.assertEqual(r['clasificacion_registro'],'PROCEDIMIENTO')
            self.assertIsNone(r['fecha_publicacion']);self.assertIsNotNone(r['fecha_limite_presentacion'])
            self.assertIsNotNone(r['fecha_apertura']);self.assertEqual(r['hora_apertura'],'10:00')
            self.assertIn('2026-',r['campos_oficiales']['fechaSugeridaPublicacion'])
            self.assertEqual(o.identidad(r),o.identidad({**r,'url':r['url']+'?otra=1'}))
            self.assertEqual(o.identidad(r),o.identidad({**r,'titulo':'Circular modificatoria '+r['titulo']}))

    def test_respuesta_incompleta_no_puede_declarar_vacio(self):
        from extractores_lotes import extraer_assa
        for datos in [b'{"success":false,"content":{}}',b'{"success":true,"content":{"elements":[]}}']:
            with self.assertRaises(ValueError):extraer_assa(datos,'https://oficial.gob.ar/')

if __name__=='__main__':unittest.main()

class DescubrimientoPeriodicoTests(unittest.TestCase):
    def test_revision_rotativa_cada_tres_dias(self):
        from datetime import datetime,timezone
        from tools.descubrimiento_piloto import corresponde
        ahora=datetime(2026,10,29,12,tzinfo=timezone.utc)
        self.assertTrue(corresponde({},ahora))
        self.assertFalse(corresponde({'ultima_ejecucion':'2026-10-28T12:00:00+00:00'},ahora))
        self.assertTrue(corresponde({'ultima_ejecucion':'2026-10-26T12:00:00+00:00'},ahora))

class ChajariPublicaTests(unittest.TestCase):
    def test_objeto_presupuesto_y_hora_sin_inventar_publicacion_o_moneda(self):
        from extractores_lotes import extraer_chajari
        raw=(Path(__file__).parent/'fixtures/chajari-publica-20261029.json').read_bytes()
        rs,cantidad=extraer_chajari(raw,'https://licitaciones.chajari.gob.ar/licitaciones/para_apertura/0')
        self.assertEqual(cantidad,1)
        r=o.normalizar({**rs[0],'organismo':'Municipalidad de Chajarí','provincia':'Entre Ríos'},FECHA)
        self.assertEqual(r['numero_procedimiento'],'19/2026');self.assertEqual(r['hora_apertura'],'10:00')
        self.assertEqual(r['fecha_apertura'],'2026-11-19');self.assertEqual(r['presupuesto']['importe'],'59500000.0')
        self.assertIsNone(r['presupuesto']['moneda']);self.assertIsNone(r['fecha_publicacion']);self.assertEqual(r['vigencia'],'ABIERTA')
        self.assertNotIn('inscripcion_ids',r['campos_oficiales'])
        self.assertNotIn('adjudicado_ids',r['campos_oficiales'])

    def test_recorrido_post_paginado_sin_repetir_ni_filtrar(self):
        import json,conectores
        raw=(Path(__file__).parent/'fixtures/chajari-publica-20261029.json').read_bytes();muestra=json.loads(raw)['result'][0]
        filas=[{**muestra,'id':1000+i,'name':str(i+1)+'/2026'} for i in range(50)]
        llamadas=[];inicio='https://licitaciones.chajari.gob.ar/licitaciones/para_apertura/0'
        def fetch(u,datos_post=None):
            llamadas.append((u,datos_post));r=filas if u.endswith('/0') else [muestra]
            return json.dumps({'result':r}).encode(),'application/json',u
        r=conectores.explorar(inicio,{'adaptador':'chajari-api','organismo':'Municipalidad de Chajarí','provincia':'Entre Ríos'},fetch=fetch)
        # Un número presente en ambas páginas se unifica; todos los demás quedan.
        self.assertEqual(r['estado'],'OPERATIVA');self.assertEqual(len(r['oportunidades']),50)
        self.assertEqual(len(llamadas),2);self.assertTrue(llamadas[-1][0].endswith('/50'))
        self.assertTrue(all(body==b'{"":""}' for _,body in llamadas))
