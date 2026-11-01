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

class EvidenciasHistoricasConvergentes(unittest.TestCase):
    def test_dos_capturas_que_resuelven_al_mismo_legado_emiten_un_evento_y_replay_cero(self):
        import oportunidades as o
        base={'organismo':'Municipalidad de prueba','provincia':'Santa Fe','numero_procedimiento':'1/2026','tipo_procedimiento':'licitacion publica','url':'https://municipio.gob.ar/1','titulo':'Licitación Pública 1/2026','objeto':'Adquisición de materiales','fecha_apertura':'2026-12-01'}
        informe={'ejecucion_id':'base','actualizado':'2026-11-01T08:00:00-03:00','estado_ejecucion':'COMPLETADA','resumen':{'configuradas':0,'finalizadas':0},'observaciones':[]}
        with tempfile.TemporaryDirectory() as tmp:
            db=inc.abrir(Path(tmp)/'estado.sqlite3')
            try:
                inc.registrar(db,[o.normalizar(base)],informe)
                xs=[o.normalizar({**base,'identidad_ambito':str(i),'documentos':[{'url':'https://municipio.gob.ar/anexo'+str(i)+'.pdf'}]}) for i in (1,2)]
                with patch.object(o,'antecedente_complementario',return_value=o.normalizar(base)):
                    r=inc.registrar(db,xs,{**informe,'ejecucion_id':'una'})
                    self.assertEqual(r['eventos_emitidos'],1)
                    r=inc.registrar(db,xs,{**informe,'ejecucion_id':'dos'})
                    self.assertEqual(r['novedades'],0)
                dato=json.loads(db.execute('SELECT dato FROM procedimientos').fetchone()[0])
                self.assertEqual(len(dato['documentos']),2)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM procedimientos').fetchone()[0],1)
            finally:db.close()

class ComparacionLiteral(unittest.TestCase):
    def test_texto_mejorado_no_es_hallazgo_y_mismo_numero_en_otro_documento_no_se_oculta(self):
        import oportunidades as o
        base={'organismo':'Municipalidad de Arrecifes','provincia':'Buenos Aires','numero_procedimiento':'3','tipo_procedimiento':'licitacion publica','url':'https://arrecifes.gob.ar/2024/3.docx','titulo':'Licitación Pública 3','objeto':'Explotación del balneario municipal','registro_estructurado':False}
        viejo=o.normalizar(base)
        nuevo=o.normalizar({**base,'registro_estructurado':True,'fecha_apertura':'2024-10-10'})
        distinto=o.normalizar({**nuevo,'url':'https://arrecifes.gob.ar/2026/3.docx'})
        r=c.comparar({'registros':[viejo]},{'registros':[nuevo,distinto]},[viejo])
        por_url={x['url']:x for x in r['oportunidades']}
        self.assertTrue(por_url[nuevo['url']]['ya_catalogada'])
        self.assertFalse(por_url[distinto['url']]['ya_catalogada'])

if __name__=='__main__':unittest.main()
