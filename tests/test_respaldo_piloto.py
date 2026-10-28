import gzip
import json
from pathlib import Path
import tempfile
import unittest
import incremental as inc
from tools import respaldo_piloto as b

class RespaldoTests(unittest.TestCase):
    def setUp(self):
        Path('work').mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=Path('work').resolve());self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.s=self.root/'origen';self.s.mkdir();self.p=self.root/'respaldo'
        self.db=inc.abrir(self.s/'estado.sqlite3');self.addCleanup(self.db.close)
    def corrida(self,id='uno',filas=None,estado='OPERATIVA'):
        filas=filas if filas is not None else [{'organismo':'Comuna de Prueba','provincia':'Santa Fe','fuente':'https://prueba.gob.ar/','url':'https://prueba.gob.ar/uno','tipo_procedimiento':'licitacion publica','numero_procedimiento':'1/2026','objeto':'Compra de materiales','detalle_completo':True}]
        return inc.registrar(self.db,filas,{'ejecucion_id':id,'actualizado':'2026-10-28T10:00:00-03:00','estado_ejecucion':'COMPLETADA','resumen':{'finalizadas':1,'configuradas':1},'observaciones':[{'url':'https://prueba.gob.ar/','estado':estado,'errores':[],'limites':[]}]})
    def test_dos_procesos_restauran_base_y_delta_con_historia_exacta(self):
        self.corrida();b.exportar(self.s,self.p)
        otro=self.root/'otra-maquina';self.assertTrue(b.restaurar(self.p,otro))
        db=inc.abrir(otro/'estado.sqlite3');self.assertEqual(b.estado(self.db),b.estado(db));db.close()
        self.corrida('dos',estado='BLOQUEADA',filas=[]);d=b.exportar(self.s,self.p)
        self.assertEqual(len(d['segmentos']),2)
        tercer=self.root/'tercera-maquina';b.restaurar(self.p,tercer);db=inc.abrir(tercer/'estado.sqlite3')
        self.assertEqual(b.estado(self.db),b.estado(db));db.close()
        self.assertLess((self.p/d['segmentos'][1]['archivo']).stat().st_size,(self.p/d['segmentos'][0]['archivo']).stat().st_size)
    def test_idempotente_sin_nueva_ejecucion(self):
        self.corrida();a=b.exportar(self.s,self.p);self.assertEqual(a,b.exportar(self.s,self.p));self.assertEqual(len(a['segmentos']),1)
    def test_segmento_corrupto_no_crea_ni_reinicia_estado(self):
        self.corrida();d=b.exportar(self.s,self.p);(self.p/d['segmentos'][0]['archivo']).write_bytes(b'alterado')
        out=self.root/'restaurado'
        with self.assertRaises(ValueError):b.restaurar(self.p,out)
        self.assertFalse((out/'estado.sqlite3').exists())
    def test_segmento_ausente_falla_sin_declarar_vacio(self):
        self.corrida();d=b.exportar(self.s,self.p);(self.p/d['segmentos'][0]['archivo']).unlink()
        with self.assertRaises(FileNotFoundError):b.restaurar(self.p,self.root/'otra')
    def test_no_sobrescribe_estado_existente(self):
        self.corrida();b.exportar(self.s,self.p)
        before=(self.s/'estado.sqlite3').read_bytes()
        with self.assertRaises(ValueError):b.restaurar(self.p,self.s)
        self.assertEqual(before,(self.s/'estado.sqlite3').read_bytes())
    def test_perdida_de_procedimiento_rechaza_nuevo_respaldo(self):
        self.corrida();b.exportar(self.s,self.p);before=(self.p/b.INDICE).read_bytes()
        self.db.execute('DELETE FROM procedimientos');self.db.commit();self.corrida('dos',filas=[])
        with self.assertRaises(ValueError):b.exportar(self.s,self.p)
        self.assertEqual(before,(self.p/b.INDICE).read_bytes())
    def test_historia_inmutable_no_se_reescribe(self):
        self.corrida();b.exportar(self.s,self.p)
        self.db.execute("UPDATE versiones SET dato='{}'");self.db.commit();self.corrida('dos',filas=[])
        with self.assertRaises(ValueError):b.exportar(self.s,self.p)
    def test_rutas_y_nombres_fuera_del_piloto_rechazados(self):
        with self.assertRaises(ValueError):b.directorio('/tmp/no-es-piloto')
        with self.assertRaises(ValueError):list(b.leer_cadena(self.p,{'segmentos':[{'archivo':'../../radar_estado.json'}]}))
    def test_continuidad_sin_duplicados_en_restauracion_independiente(self):
        self.corrida();b.exportar(self.s,self.p);out=self.root/'segundo';b.restaurar(self.p,out);b.continuidad(out,'antes')
        db=inc.abrir(out/'estado.sqlite3');old=b.estado(db)[0]['procedimientos'][0]['dato'];fila=json.loads(old)
        inc.registrar(db,[fila],{'ejecucion_id':'dos','actualizado':'2026-10-28T11:00:00-03:00','estado_ejecucion':'COMPLETADA','resumen':{'finalizadas':1,'configuradas':1},'observaciones':[{'url':'https://prueba.gob.ar/','estado':'OPERATIVA','errores':[],'limites':[]}]});db.close()
        b.continuidad(out,'despues');r=json.loads((out/'continuidad.json').read_text());self.assertTrue(r['correcta']);self.assertEqual(r['repetidas_como_nuevas'],0)
    def test_continuidad_falla_si_desaparece_historial(self):
        self.corrida();b.continuidad(self.s,'antes');self.db.execute('DELETE FROM procedimientos');self.db.commit();self.corrida('dos',filas=[])
        with self.assertRaises(ValueError):b.continuidad(self.s,'despues')
    def test_exportar_no_crea_base_vacia_si_falta_estado(self):
        with self.assertRaises(ValueError):b.exportar(self.root/'no-existe',self.p)
