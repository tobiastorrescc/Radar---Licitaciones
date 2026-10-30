import unittest
import oportunidades as o
class FechasTests(unittest.TestCase):
    def test_estado_publicada_para_apertura_no_es_fecha_de_publicacion(self):
        r=o.normalizar({'titulo':'Compra Agil 110861/2026 Publicada para Apertura INMUNOSEROLOGIA. Apertura: 03/11/2026 10:00','objeto':'Compra Agil 110861/2026 Publicada para Apertura INMUNOSEROLOGIA. Apertura: 03/11/2026 10:00'},'2026-10-29T21:00:00-03:00')
        self.assertEqual(r['fecha_apertura'],'2026-11-03');self.assertEqual(r['hora_apertura'],'10:00')
        self.assertIsNone(r['fecha_publicacion'])
    def test_etiqueta_vacia_no_toma_fecha_del_campo_siguiente(self):
        r=o.normalizar({'titulo':'Licitación Pública 2/2026','objeto':'Fecha de publicación: Apertura: 03/11/2026 10:00'},'2026-10-29T21:00:00-03:00')
        self.assertIsNone(r['fecha_publicacion']);self.assertEqual(r['fecha_apertura'],'2026-11-03')
    def test_fecha_modificacion_no_es_publicacion(self):
        r=o.normalizar({'titulo':'Licitación Pública 2/2026','objeto':'Última modificación 29/10/2026. Apertura 03/11/2026 10:00'},'2026-10-29T21:00:00-03:00')
        self.assertIsNone(r['fecha_publicacion'])

class RosarioListadoTests(unittest.TestCase):
    def test_numero_repetido_en_distintas_unidades_no_se_fusiona(self):
        import extractores
        html='<main><h2 class="contrataciones-resumen__total-titulo">Compra Agil</h2>'
        for id,obj in [(38640,'Repuestos para tránsito'),(38628,'Ascensores de la Ex Aduana')]:
            html+=f'<div class="contrataciones-resumen__tarjeta"><a href="/inicio/compras-licitaciones/detalle/{id}">48/2026</a>Publicada para Apertura {obj} Apertura: 03/11/2026 10:00</div>'
        html+='</main>'
        rs,_,_=extractores.extraer(html,'https://www.rosario.gob.ar/inicio/result-busq-compras-licitaciones',{'adaptador':'rosario'})
        rs=[o.normalizar({**r,'organismo':'Municipalidad de Rosario','provincia':'Santa Fe'}) for r in rs]
        self.assertEqual(len(rs),2);self.assertNotEqual(o.identidad(rs[0]),o.identidad(rs[1]))
        self.assertTrue(all(len(r['objeto'])<250 for r in rs))
    def test_contenedor_legado_no_se_presenta_como_procedimiento(self):
        r=o.normalizar({'fuente':'https://www.rosario.gob.ar/inicio/compras-y-licitaciones','titulo':'Compra Agil 24/2026','objeto':'24/2026 Publicada para Apertura zapato 48/2026 Publicada para Apertura ascensor'})
        self.assertEqual(r['clasificacion_registro'],'CANDIDATO_NO_VERIFICADO')

    def test_migracion_ficha_conserva_id_y_no_absorbe_otro_procedimiento(self):
        import tempfile
        import incremental as inc
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            db=inc.abrir(Path(d)/'estado.sqlite3')
            texto='Compra Agil 48/2026 Publicada para Apertura Repuestos para tránsito Apertura: 03/11/2026 11:00'
            raw={'organismo':'Municipalidad de Rosario','provincia':'Santa Fe','titulo':texto,'objeto':texto,'numero_procedimiento':'48/2026','tipo_procedimiento':'compra agil','fuente':'https://www.rosario.gob.ar/inicio/compras-y-licitaciones','url':'https://www.rosario.gob.ar/inicio/listado'}
            def informe(id):return {'ejecucion_id':id,'actualizado':'2026-10-29T12:00:00-03:00','estado_ejecucion':'COMPLETADA','resumen':{'finalizadas':1,'configuradas':1,'fuentes_error_interno':0},'observaciones':[{'url':raw['fuente'],'estado':'OPERATIVA','errores':[],'limites':[]}]}
            inc.registrar(db,[o.normalizar(raw)],informe('antes'))
            id_antes=db.execute('SELECT id FROM procedimientos').fetchone()[0]
            nueva={**raw,'texto_listado':texto,'id_origen':'38640','identidad_ambito':'ficha-rosario-38640'}
            inc.registrar(db,[o.normalizar(nueva)],informe('despues'))
            self.assertEqual(db.execute('SELECT id FROM procedimientos').fetchone()[0],id_antes)
            otra={**nueva,'objeto':'Mantenimiento de ascensores Ex Aduana','titulo':'Compra Agil 48/2026 ascensores','texto_listado':'Compra Agil 48/2026 ascensores','id_origen':'38628','identidad_ambito':'ficha-rosario-38628'}
            inc.registrar(db,[o.normalizar(nueva),o.normalizar(otra)],informe('dos_fichas'))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM procedimientos').fetchone()[0],2)
            db.close()

class FechaTablaTests(unittest.TestCase):
    def test_publicacion_rotulada_en_tabla_no_toma_apertura_ni_actualizacion(self):
        import extractores
        html='<table><tr><th>Número</th><th>Objeto</th><th>Fecha Publicación</th><th>Fecha apertura</th><th>Actualización</th></tr><tr><td>3/2026</td><td>Reparación de calles</td><td>29/10/2026</td><td>05/11/2026</td><td>30/10/2026</td></tr></table>'
        rs,_,_=extractores.extraer(html,'https://oficial.gob.ar/compras',{'tipo_tabla':'Licitación Pública'})
        self.assertTrue(rs)
        self.assertEqual(o.normalizar(rs[0])['fecha_publicacion'],'2026-10-29')
