import fcntl
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import programar_piloto as p

AHORA=datetime(2026,10,29,11,0,tzinfo=timezone.utc)
class ProgramadorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.dir=Path(self.tmp.name);self.posts=[];self.runs=[];self.fail=False;self.activo=True;self.backup=True
 def run_data(self,**kw):
  return {'id':123,'html_url':'https://github.com/ejemplo/run/123','head_branch':p.RAMA,'event':'workflow_dispatch','display_title':p.plan(AHORA)['titulo'],'status':'completed','conclusion':'success',**kw}
 def api(self,ruta,datos=None):
  if datos is not None:
   self.posts.append(datos)
   if self.fail:raise TimeoutError('respuesta perdida')
   self.runs=[self.run_data()];return {}
  if '/runs?' in ruta:return {'workflow_runs':self.runs}
  if ruta.startswith('contents/'):
   if not self.backup:raise RuntimeError('GitHub HTTP 404')
   return {'type':'file'}
  if ruta.startswith('actions/runs/'):return self.runs[0]
  return {'state':'active' if self.activo else 'disabled_manually'}
 def ejecutar(self,**kw):return p.ejecutar(self.api,self.dir,AHORA,pausa=lambda _:None,**kw)
 def test_zona_fecha_y_aislamiento(self):
  plan=p.plan(datetime(2026,10,29,1,tzinfo=timezone.utc));self.assertEqual(plan['fecha_argentina'],'2026-10-28')
  self.assertEqual(plan['ref'],'mejora/radar-auditable');self.assertEqual(plan['inputs']['modo'],'controlado');self.assertEqual(plan['inputs']['inicializar'],'false')
 def test_dispara_una_vez_y_confirma_exito(self):
  self.assertEqual(self.ejecutar()['estado'],'EXITO');self.assertEqual(self.ejecutar()['estado'],'EXITO');self.assertEqual(len(self.posts),1)
 def test_reconcilia_aceptada_sin_post_duplicado(self):
  self.fail=True
  with self.assertRaises(TimeoutError):self.ejecutar()
  self.runs=[self.run_data()];self.assertEqual(self.ejecutar()['estado'],'EXITO');self.assertEqual(len(self.posts),1)
 def test_post_ambiguo_no_reintenta(self):
  self.fail=True
  with self.assertRaises(TimeoutError):self.ejecutar()
  with self.assertRaisesRegex(RuntimeError,'sin confirmar'):self.ejecutar()
  self.assertEqual(len(self.posts),1)
 def test_otra_ejecucion_activa_no_se_solapa(self):
  self.runs=[self.run_data(display_title='manual',status='in_progress')]
  with self.assertRaisesRegex(RuntimeError,'otra ejecución'):self.ejecutar()
  self.assertFalse(self.posts)
 def test_bloqueo_local(self):
  with (self.dir/'programador.lock').open('a') as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   with self.assertRaisesRegex(RuntimeError,'local activo'):self.ejecutar()
 def test_fallo_queda_registrado_sin_reintento(self):
  self.runs=[self.run_data(conclusion='failure')]
  with self.assertRaisesRegex(RuntimeError,'Falló'):self.ejecutar()
  self.assertEqual(json.loads((self.dir/'2026-10-29.json').read_text())['estado'],'FALLO');self.assertFalse(self.posts)
 def test_sin_workflow_o_respaldo_no_dispara(self):
  for atributo in ('activo','backup'):
   setattr(self,atributo,False)
   with self.assertRaises(RuntimeError):self.ejecutar()
   setattr(self,atributo,True)
  self.assertFalse(self.posts)
 def test_plazo_total_sin_reintentar(self):
  self.runs=[self.run_data(status='in_progress')]
  t=iter([0,0,2])
  with self.assertRaisesRegex(RuntimeError,'Plazo total'):self.ejecutar(reloj=lambda:next(t),plazo=1)
  self.assertFalse(self.posts)
 def test_duplicados_remotos_requieren_revision(self):
  self.runs=[self.run_data(),self.run_data(id=124)]
  with self.assertRaisesRegex(RuntimeError,'duplicados'):self.ejecutar()
 def test_configuracion_entregada_desactivada(self):
  self.assertIs(json.loads(Path('despliegue/piloto.json').read_text())['habilitado'],False)
  timer=Path('despliegue/systemd/radar-piloto.timer').read_text()
  self.assertIn('08:00:00 America/Argentina/Buenos_Aires',timer);self.assertIn('Persistent=false',timer)
  with patch('sys.argv',['programar_piloto.py','--ejecutar']):
   with self.assertRaisesRegex(SystemExit,'desactivado'):p.main()
