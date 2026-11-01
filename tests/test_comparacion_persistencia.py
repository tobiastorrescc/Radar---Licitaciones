"""Regresión: candidata incorporada cambia de ID, mantiene URL y auditoría única."""
import json,sys,tempfile,unittest
from contextlib import chdir
from pathlib import Path
from unittest.mock import patch
import incremental as inc
from tools import comparar_barrido as c

class ComposicionAuditorias(unittest.TestCase):
    def test_candidata_y_fuente_incorporada_no_duplican_clave_sqlite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);url='https://municipio.gob.ar/compras/'
            antes=root/'antes.json';antes.write_text(json.dumps({'registros':[]}))
            cat=root/'catalogo.json';cat.write_text(json.dumps({'oportunidades':[]}))
            paths=[]
            for nombre,id in [('anterior','candidata'),('actual','fuente-082')]:
                d=root/nombre;d.mkdir();p=d/'resultado.json';paths.append(p)
                p.write_text(json.dumps({'registros':[],'fecha':'2026-10-31T23:00:00-03:00','fuentes':[{'id':id,'url':url,'provincia':'Entre Ríos'}]}))
                (d/'verificacion.json').write_text(json.dumps({'ejecucion_id':'captura','actualizado':'2026-10-31T23:00:00-03:00','estado_ejecucion':'COMPLETADA','resumen':{'configuradas':1,'consultadas':1,'finalizadas':1},'observaciones':[{'id':id,'url':url,'estado':'OPERATIVA','errores':[],'limites':[]}]}))
            # Respaldo sintético vacío en el temporal; no se toca el real.
            (root/'piloto_respaldo/diario').mkdir(parents=True)
            db=inc.abrir(root/'estado.sqlite3')
            def ejecutar(raiz,informe_previo):
                # El INSERT real falla si llegan dos auditorías para la misma URL.
                r=inc.registrar(db,[],informe_previo)
                self.assertEqual(len(informe_previo['observaciones']),1)
                self.assertEqual(informe_previo['observaciones'][0]['id'],'fuente-082')
                self.assertEqual(informe_previo['observaciones'][0]['provincia'],'Entre Ríos')
                return r,root,None,None
            argv=['comparar','--antes',str(antes),'--despues',str(paths[1]),'--complemento',str(paths[0]),'--catalogo',str(cat),'--salida',str(root/'salida')]
            try:
                with chdir(root),patch.object(sys,'argv',argv),patch.object(c,'restaurar'),patch.object(c,'ejecutar_corrida',side_effect=ejecutar),patch('builtins.print'):
                    c.main()
                self.assertEqual(db.execute('SELECT COUNT(*) FROM auditorias').fetchone()[0],2) # Una por corrida.
            finally:db.close()

if __name__=='__main__':unittest.main()
