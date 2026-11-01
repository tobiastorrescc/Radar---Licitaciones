import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from hashlib import sha256
import conectores,incremental as inc,oportunidades as o

class NumeroDocumental(unittest.TestCase):
    def test_documento_del_mismo_numero_completa_anio_sin_doble_ficha(self):
        inicio='https://arrecifes.gob.ar/licitaciones/';doc='https://arrecifes.gob.ar/1.docx'
        html='<main><article><h2><a href="/1.docx">Licitación Pública 1</a></h2><p>Objeto: Adquisición de materiales</p></article></main>'
        def fetch(u):return (html.encode(),'text/html',u) if u==inicio else (b'PK-prueba','application/vnd.openxmlformats-officedocument.wordprocessingml.document',u)
        with patch('cache_documentos.leer_texto',return_value=('LICITACIÓN PÚBLICA 1/2026\nObjeto: Adquisición de materiales\nApertura: 03/11/2026',{})):
            r=conectores.explorar(inicio,{'organismo':'Municipalidad de Arrecifes','provincia':'Buenos Aires','solo_descubrimiento':True,'documentos_para_descubrimiento':True,'lectura_adjuntos':'todos','resolver_numero_documental':True},fetch=fetch)
        self.assertEqual(len(r['oportunidades']),1)
        x=r['oportunidades'][0];self.assertEqual(x['numero_procedimiento'],'1/2026');self.assertEqual(x['numero_documental_previo'],'1');self.assertEqual(x['evidencia_numero_documental']['url'],doc)
    def test_mismo_numero_en_documentos_distintos_y_fecha_rotulada(self):
        inicio='https://arrecifes.gob.ar/licitaciones/'
        html='<main><a href="/2024/3.docx">Licitación Pública 3</a><a href="/2026/3.docx">Licitación Pública 3</a></main>'
        def fetch(u):return (html.encode(),'text/html',u) if u==inicio else (b'PK-prueba','application/vnd.openxmlformats-officedocument.wordprocessingml.document',u)
        def texto(datos,mime,url,**kwargs):return ('LLAMADO A LICITACION PUBLICA 3\nOBJETO: Explotación de servicios del balneario municipal\nAPERTURA: DIA: 5 MES: OCTUBRE AÑO: '+('2024' if '/2024/' in url else '2026')+' HORA: 11:00',{})
        with patch('cache_documentos.leer_texto',side_effect=texto):
            r=conectores.explorar(inicio,{'organismo':'Municipalidad de Arrecifes','provincia':'Buenos Aires','solo_descubrimiento':True,'documentos_para_descubrimiento':True,'lectura_adjuntos':'todos','resolver_numero_documental':True},fetch=fetch)
        xs=r['oportunidades'];self.assertEqual(len(xs),2)
        self.assertEqual({x['numero_procedimiento'] for x in xs},{'3'})
        self.assertEqual({x['fecha_apertura'] for x in xs},{'2024-10-05','2026-10-05'})
        self.assertEqual(len({o.identidad(x) for x in xs}),2)

    def test_historial_bare_se_actualiza_sin_borrar_versiones_y_replay_cero(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=inc.abrir(Path(tmp)/'estado.sqlite3');url='https://arrecifes.gob.ar/1.docx'
            base={'titulo':'Licitación Pública 1','objeto':'Adquisición de materiales','organismo':'Municipalidad de Arrecifes','provincia':'Buenos Aires','url':url,'fuente':'https://arrecifes.gob.ar/licitaciones/','numero_procedimiento':'1','tipo_procedimiento':'licitacion publica','registro_estructurado':True}
            informe={'ejecucion_id':'uno','actualizado':'2026-11-01T08:00:00-03:00','estado_ejecucion':'COMPLETADA','resumen':{'configuradas':0,'finalizadas':0},'observaciones':[]}
            try:
                inc.registrar(db,[o.normalizar(base)],informe)
                nuevo={**base,'titulo':'Licitación Pública 1/2026','numero_procedimiento':'1/2026','numero_documental_previo':'1','evidencia_numero_documental':{'url':url,'numero':'1/2026','sha256':sha256(b'PK-prueba').hexdigest()}}
                inc.registrar(db,[o.normalizar(nuevo)],{**informe,'ejecucion_id':'dos'})
                self.assertEqual(db.execute('SELECT COUNT(*) FROM procedimientos').fetchone()[0],1)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM versiones').fetchone()[0],2)
                r=inc.registrar(db,[o.normalizar(nuevo)],{**informe,'ejecucion_id':'tres'});self.assertEqual(r['novedades'],0)
            finally:db.close()

if __name__=='__main__':unittest.main()
