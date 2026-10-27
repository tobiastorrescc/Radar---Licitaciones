"""Regresiones de identidad, vigencia y reportes; evidencia real se añade desde #54."""
import copy
from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest
import extractores
import oportunidades as o

AHORA='2026-10-27T09:00:00-03:00'
class RevisionAbiertasTests(unittest.TestCase):
    def base(self,numero='LPR-2026-00000002',**kw):
        r={'organismo':'Aeropuerto Internacional Rosario','localidad':'Rosario','provincia':'Santa Fe','fuente':'https://aeropuertorosario.com/institucional/licitaciones/','url':'https://aeropuertorosario.com/licitaciones/lpr-2026-00000002/','numero_procedimiento':numero,'tipo_procedimiento':'licitacion privada','procedimiento':numero.lower(),'titulo':numero+' Jardinería. Apertura 28/10/2026','objeto':'Jardinería. Apertura 28/10/2026','detalle_completo':True}
        return {**r,**kw}
    def test_codigo_termina_antes_estado_navegacion(self):
        for texto in ['LPR-2026-00000002 Estado Vigente Número LPR-2026-00000002 Fecha de apertura 28/10/2026', 'LPR-2026-00000002-APPSF-OD-COM-CON-AIR-ROS Asunto Jardinería']:
            ps=extractores.procesos(texto)
            self.assertTrue(ps)
            self.assertTrue(all(' ' not in p['numero'] for p in ps))
            self.assertTrue(all('ESTADO' not in p['numero'] and 'ASUNTO' not in p['numero'] for p in ps))
    def test_codigo_corto_largo_y_tipo_numerico_una_convocatoria(self):
        doc=[{'titulo':'LPR-2026-00000002-APPSF-OD-COM-CON-AIR-ROS.pdf','url':'https://aeropuertorosario.com/LPR-2026-00000002-APPSF-OD-COM-CON-AIR-ROS.pdf'}]
        rs=[self.base(documentos=doc),self.base('LPR-2026-00000002-APPSF-OD-COM-CON-AIR-ROS',url='https://aeropuertorosario.com/anexo.pdf'),self.base('2/2026',url='https://aeropuertorosario.com/otra',documentos=doc)]
        self.assertEqual(len({o.identidad(o.normalizar(r,AHORA)) for r in rs}),1)
    def test_convocatorias_alias_y_organismos_separados(self):
        base=self.base();segundo=self.base(titulo='Segundo llamado jardinería');otro=self.base(organismo='Municipalidad de Rosario')
        alias=self.base(titulo='2º llamado jardinería')
        self.assertEqual(o.identidad(o.normalizar(segundo,AHORA)),o.identidad(o.normalizar(alias,AHORA)))
        self.assertEqual(len(o.deduplicar([base,segundo,alias,otro],AHORA)),3)
    def test_fusion_presupuesto_y_adjuntos_sin_elegir_titulo_mas_largo(self):
        a=self.base(titulo='LPR-2026-00000002 '+('Jardinería '*100),documentos=[{'url':'https://aeropuertorosario.com/LPR-2026-00000002-APPSF-OD-COM-CON-AIR-ROS.pdf','titulo':'Pliego'}])
        b=self.base('LPR-2026-00000002-APPSF-OD-COM-CON-AIR-ROS',url='https://aeropuertorosario.com/b',texto_documento='Asunto Jardinería. Presupuesto Oficial: $36.000.000.- Fecha de apertura 28/10/2026 11:00',rango_evidencia=3,documentos=[{'url':'https://aeropuertorosario.com/b.pdf','titulo':'Anexo'}])
        rs=o.deduplicar([a,b],AHORA)
        self.assertEqual(len(rs),1)
        r=rs[0];self.assertEqual(r['presupuesto']['importe'],'36000000')
        self.assertEqual(r['fecha_apertura'],'2026-10-28');self.assertIsNone(r['fecha_publicacion'])
        self.assertEqual(len(r['documentos']),2)
        self.assertEqual(r['vigencia'],'ABIERTA')
    def test_general_sin_identidad_no_es_abierta_por_fecha_ajena(self):
        r=o.normalizar({'titulo':'Compras y contrataciones','objeto':'Información general. Apertura 28/10/2026','url':'https://x.gob.ar/licitaciones','organismo':'Municipio'},AHORA)
        self.assertEqual(r['clasificacion_registro'],'CANDIDATO_NO_VERIFICADO')
        self.assertEqual(r['vigencia'],'DESCONOCIDA')
        self.assertEqual(o.separar_vigencia([r],AHORA)['abiertas'],[])
    def test_fecha_publicacion_no_es_apertura_y_hora_de_cierre(self):
        r=self.base(objeto='Publicada el 27/10/2026. Apertura 28/10/2026 11:00')
        r=o.normalizar(r,AHORA)
        self.assertEqual(r['fecha_publicacion'],'2026-10-27');self.assertEqual(r['fecha_apertura'],'2026-10-28')
        self.assertEqual(o.normalizar(r,'2026-10-28T10:59:00-03:00')['vigencia'],'ABIERTA')
        self.assertEqual(o.normalizar(r,'2026-10-28T11:00:00-03:00')['vigencia'],'VENCIDA')
    def test_reporte_separado_conserva_historial_y_sin_tope(self):
        rs=[o.normalizar(self.base(f'{i}/2026'),AHORA) for i in range(1400)]
        rs.append(o.normalizar(self.base('1401/2026',objeto='Apertura 1/1/2020',titulo='Histórica'),AHORA))
        rs.append(o.normalizar(self.base('1402/2026',objeto='Sin fecha',titulo='Sin fecha'),AHORA))
        antes=copy.deepcopy(rs)
        with tempfile.TemporaryDirectory() as d:
            vistas=o.guardar_vistas(rs,AHORA,d)
            self.assertEqual(len(vistas['abiertas']),1400);self.assertEqual(len(vistas['proximas_a_vencer']),1400)
            self.assertEqual(json.loads((Path(d)/'oportunidades_abiertas.json').read_text())['total'],1400)
        self.assertEqual(rs,antes)
    def test_persistencia_legado_codigo_largo_no_se_borra_ni_duplica(self):
        viejo=self.base('LPR-2026-00000002-APPSF-OD-COM-CON-AIR-ROS')
        h={'clave-antigua':viejo};original=copy.deepcopy(h)
        self.assertEqual(o.incorporar(h,[self.base(documentos=[{'url':'https://aeropuertorosario.com/LPR-2026-00000002-APPSF-OD-COM-CON-AIR-ROS.pdf','titulo':'Pliego'}])],AHORA),[])
        self.assertEqual(h,original)

    def test_cinco_fichas_oficiales_presupuesto_objeto_apertura(self):
        ejemplos=[('jardineria','36000000','2026-10-28'),('liquidos','10000000','2026-10-30'),('volquetes','31200000.00','2026-10-30'),('tandems','61806395.30','2026-11-02'),('control','13200000.00','2026-10-29')]
        for nombre,importe,apertura in ejemplos:
            h=Path(f'tests/fixtures/reales/aeropuerto-{nombre}-57.html').read_text()
            rs,_,_=extractores.extraer(h,'https://aeropuertorosario.com/licitaciones/ficha/',{'adaptador':'aeropuerto'})
            self.assertEqual(len(rs),1)
            r=o.normalizar({**self.base(),**rs[0]},AHORA)
            self.assertEqual(r['presupuesto']['importe'],importe)
            self.assertEqual(r['fecha_apertura'],apertura)
            self.assertIsNone(r['fecha_publicacion'])
            self.assertNotIn('MB',r['objeto']);self.assertNotIn('Descargas',r['objeto'])
    def test_once_abiertas_originales_nueve_procedimientos(self):
        rs=json.loads(Path('tests/fixtures/reales/abiertas54.json').read_text())
        self.assertEqual(len(rs),11)
        nuevos=o.deduplicar(rs,AHORA)
        self.assertEqual(len(nuevos),9)
        self.assertEqual(len([r for r in nuevos if r.get('organismo')=='Aeropuerto Internacional Rosario']),5)
    def test_pagina_general_con_varios_codigos_no_es_un_procedimiento(self):
        h='<main><h1>Compras y contrataciones</h1><article>LPR-2026-00000002 Fecha de apertura 28/10/2026 Jardinería</article><article>LPU-2026-00000001 Fecha de apertura 30/10/2026 Volquetes</article></main>'
        rs,_,_=extractores.extraer(h,'https://aeropuertorosario.com/institucional/licitaciones/',{'adaptador':'aeropuerto'})
        self.assertEqual(len(rs),2)
        self.assertTrue(all('Volquetes' not in r['titulo'] or 'Jardinería' not in r['titulo'] for r in rs))
    def test_documento_http_200_html_no_valida_pliego(self):
        from unittest.mock import patch
        from tools import comprobar_pliegos as c
        with patch.object(c.conectores,'descargar',return_value=(b'<html>Pagina de error</html>','text/html','https://x.gob.ar/pliego.pdf')):
            self.assertEqual(c.worker('https://x.gob.ar/pliego.pdf')['estado'],'NO_ES_DOCUMENTO')
    def test_documento_pdf_comprobado_presupuesto_y_huella(self):
        from unittest.mock import patch
        from tools import comprobar_pliegos as c
        texto='LPR-2026-00000002 PLIEGO Presupuesto Oficial: $36.000.000.-'
        with patch.object(c.conectores,'descargar',return_value=(b'%PDF-datos','application/pdf','https://aeropuertorosario.com/pliego.pdf')),patch.object(c.documentos,'leer',return_value=texto):
            r=c.worker('https://aeropuertorosario.com/pliego.pdf')
        self.assertEqual(r['estado'],'DOCUMENTO_ACCESIBLE');self.assertTrue(r['sha256'])
        self.assertEqual(r['procedimientos'],['licitacion privada LPR-2026-2'])
        self.assertEqual(r['presupuesto']['importe'],'36000000')
    def test_proximas_siete_dias_sin_excluir_abiertas_mas_lejanas(self):
        rs=[o.normalizar(self.base(str(i)+'/2026',objeto=f'Apertura {dia}/11/2026',titulo='Convocatoria'),AHORA) for i,dia in enumerate([2,3,4])]
        vistas=o.separar_vigencia(rs,AHORA)
        self.assertEqual(len(vistas['abiertas']),3);self.assertEqual(len(vistas['proximas_a_vencer']),2)

    def test_series_of_legales_y_com_con_no_se_fusionan(self):
        a=self.base('LPU-2026-00000002-APPSF-OD-OF-LEGALES-AIR-ROS',tipo_procedimiento='licitacion publica')
        b=self.base('LPU-2026-00000002-APPSF-OD-COM-CON-AIR-ROS',tipo_procedimiento='licitacion publica')
        self.assertNotEqual(o.identidad(o.normalizar(a,AHORA)),o.identidad(o.normalizar(b,AHORA)))
        self.assertEqual(len(o.deduplicar([a,b],AHORA)),2)

    def test_encabezado_proveedor_adjudicado_y_condicion_no_cierra_convocatoria(self):
        self.assertIsNone(extractores.situacion('Proveedor Adjudicado:'))
        self.assertIsNone(extractores.situacion('Esta obra será adjudicada una vez concluida la evaluación'))
        self.assertEqual(extractores.situacion('Licitación 2/2026 ADJUDICADA a la firma X'),'ADJUDICADA')

    def test_listado_con_guiones_espaciados_y_ficha_una_sola_publicacion(self):
        import conectores
        url='https://aeropuertorosario.com/licitaciones/lpr-2026-00000002-appsf-od-com-con-air-ros/'
        listado='<article><a href="'+url+'">LPR-2026-00000002-APPSF-OD - COM-CON-AIR-ROS</a><p>Fecha de apertura 28/10/2026 Jardinería</p></article>'
        ficha=Path('tests/fixtures/reales/aeropuerto-jardineria-57.html').read_text()
        def fetch(u):return (listado if u.endswith('/inicio') else ficha).encode(),'text/html',u
        r=conectores.explorar('https://aeropuertorosario.com/inicio',{'organismo':'Aeropuerto Internacional Rosario','adaptador':'aeropuerto','enriquecer_fichas':True,'lectura_adjuntos':'necesarios'},fetch=fetch)
        self.assertEqual(len(r['oportunidades']),1)
        self.assertEqual(r['oportunidades'][0]['presupuesto']['importe'],'36000000')
        self.assertEqual(r['oportunidades'][0]['fecha_apertura'],'2026-10-28')

    def test_reporte_integrado_json_md_y_revision_sin_modificar_historial(self):
        from tools import reportar_oportunidades as reportador
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            raiz=Path(d);checkpoint=raiz/'fuente.json';estado=raiz/'historial.json'
            estado.write_text(json.dumps({'oportunidades':{'legado':self.base()}}));antes=estado.read_bytes()
            item=self.base('3/2026',objeto='Jardinería. Apertura 28/10/2026')
            checkpoint.write_text(json.dumps({'oportunidades':[item]}))
            informe=raiz/'auditoria.json';informe.write_text(json.dumps({'actualizado':AHORA,'github_run_id':'fixture','observaciones':[{'url':item['fuente'],'estado':'OPERATIVA','resultado_archivo':str(checkpoint)}]}))
            with patch.object(reportador.comprobar_pliegos,'comprobar',return_value=[]):resumen=reportador.ejecutar(informe,raiz/'salida',estado)
            self.assertEqual(resumen['registros_unicos'],1)
            for nombre in ['oportunidades_abiertas.json','oportunidades_proximas_a_vencer.md','revision_11_abiertas54.json','auditoria_enlaces.json','nuevas_simulacion.json']:self.assertTrue((raiz/'salida'/nombre).exists())
            self.assertEqual(estado.read_bytes(),antes)

    def test_resolucion_que_menciona_pliego_no_es_el_pliego_regresion59(self):
        from tools import comprobar_pliegos as c
        doc={'url':'https://aeropuertorosario.com/RESCONJ-2026-00000319-APPSF-ODAeroRosMEyD-AIR-ROS.pdf','encabezado_pliego':True,'procedimientos':['licitacion privada LPR-2026-2-APPSF-OD-COM-CON-AIR-ROS']}
        self.assertEqual(c.prioridad_pliego(doc,'RESCONJ-2026-00000319.pdf',doc['procedimientos'][0]),0)
        doc['url']='https://aeropuertorosario.com/Pliego-tecnico-jardineria-2026.pdf'
        self.assertEqual(c.prioridad_pliego(doc,'Pliego técnico jardinería',doc['procedimientos'][0]),2)
    def test_mencionar_pliego_en_documento_no_prueba_encabezado(self):
        from tools import comprobar_pliegos as c
        doc={'url':'https://aeropuertorosario.com/anexo.pdf','encabezado_pliego':False,'procedimientos':['licitacion privada LPR-2026-2-APPSF-OD-COM-CON-AIR-ROS']}
        self.assertEqual(c.prioridad_pliego(doc,'Anexo',doc['procedimientos'][0]),0)
    def test_pdf_numero_anual_compatible_con_ficha_sin_fusionar_series(self):
        from tools import comprobar_pliegos as c
        self.assertTrue(c.pertenece_a(['licitacion privada 2/2026'],'licitacion privada LPR-2026-2-APPSF-OD-COM-CON-AIR-ROS'))
        self.assertFalse(c.pertenece_a(['licitacion publica LPU-2026-2-APPSF-OD-OF-LEGALES-AIR-ROS'],'licitacion publica LPU-2026-2-APPSF-OD-COM-CON-AIR-ROS'))
    def test_estado_oficial_cerrado_prevalece_sobre_fecha_futura(self):
        h=Path('tests/fixtures/reales/aeropuerto-jardineria-57.html').read_text().replace('Vigente','Adjudicada')
        rs,_,_=extractores.extraer(h,'https://aeropuertorosario.com/licitaciones/ficha/',{'adaptador':'aeropuerto'})
        self.assertEqual(o.normalizar({**self.base(),**rs[0]},AHORA)['vigencia'],'VENCIDA')
