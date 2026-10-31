import json,unittest
from pathlib import Path
import conectores,extractores_lotes as lotes, oportunidades as o

class EntreRiosAPI(unittest.TestCase):
    def test_listado_real_recupera_todos_sin_pliegos(self):
        datos=Path('tests/fixtures/reales/er-contrataciones-publicas.json').read_bytes()
        url='https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones'
        r=conectores.explorar(url,{'adaptador':'entre-rios-api','solo_descubrimiento':True},fetch=lambda u:(datos,'application/json',u))
        self.assertEqual(len(r['oportunidades']),32)
        self.assertEqual(r['estado'],'OPERATIVA')
        self.assertTrue(all(x['objeto'] for x in r['oportunidades']))
        self.assertTrue(all(x['vigencia']=='ABIERTA' for x in r['oportunidades']))
        self.assertTrue(all(x.get('fecha_publicacion') is None for x in r['oportunidades']))
        self.assertTrue(all(not x['documentos'] for x in r['oportunidades']))
    def test_categoria_generica_no_duplica_cotejos_del_mismo_objeto(self):
        datos=Path('tests/fixtures/reales/er-contrataciones-publicas.json').read_bytes()
        rs=lotes.extraer_entre_rios_api(datos,'https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones')
        cotejos=[r for r in rs if r['tipo_procedimiento']=='cotejo de precios']
        self.assertEqual(len(cotejos),6)
        self.assertTrue(all(r['campos_oficiales']['tipo_licitacion']=='SOLICITUD DE COTIZACIÓN' for r in cotejos))

    def test_respuesta_incompleta_no_es_sin_novedades(self):
        with self.assertRaises(ValueError):lotes.extraer_entre_rios_api(b'{"code":200,"success":true}', 'https://portal.entrerios.gov.ar/')
    def test_api_sin_resultados_requiere_success_explicito(self):
        self.assertEqual(lotes.extraer_entre_rios_api(b'{"code":200,"success":true,"data":[]}', 'https://portal.entrerios.gov.ar/'),[])
        with self.assertRaises(ValueError):lotes.extraer_entre_rios_api(b'{"code":200,"success":false,"data":[]}', 'https://portal.entrerios.gov.ar/')
