import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import radar


class RadarTests(unittest.TestCase):
    def setUp(self):
        self.documentos_mock=patch.object(radar.comprobar_pliegos,'comprobar',return_value=[])
        self.documentos_mock.start();self.addCleanup(self.documentos_mock.stop)
        self.automaticas_mock=patch.object(radar.registro_fuentes,'cargar_auto',return_value={})
        self.automaticas=self.automaticas_mock.start();self.addCleanup(self.automaticas_mock.stop)

    def test_all_candidates_no_output_limit(self):
        html = ''.join(f'<a href="/licitacion/{n}">Compra menor {n}</a>' for n in range(80))
        with patch.object(radar, 'descargar', return_value=html), patch.object(radar.time, 'sleep'):
            result = radar.explorar_fuente('https://example.org/')
        self.assertEqual(len(result['oportunidades']), 80)

    def test_failure_is_not_success(self):
        with patch.object(radar, 'descargar', side_effect=OSError('bloqueo')):
            result = radar.explorar_fuente('https://example.org/')
        self.assertEqual(result['estado'], 'ERROR')
        self.assertEqual(result['paginas_correctas'], 0)

    def test_limit_reported(self):
        with patch.object(radar, 'MAX_PAGINAS', 1), patch.object(radar.time, 'sleep'), patch.object(
            radar, 'descargar', return_value='<a href="/compras/pagina/2">Compras</a>'):
            result = radar.explorar_fuente('https://example.org/')
        self.assertEqual(result['estado'], 'PARCIAL')
        self.assertIn('max_paginas', result['limites'])

    def test_history_corruption_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'history.json'
            p.write_text('{invalid')
            with self.assertRaises(RuntimeError):
                radar.cargar_json(p, {})
            self.assertEqual(p.read_text(), '{invalid')

    def test_atomic_save(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'history.json'
            radar.guardar_json(p, {'uno': 1})
            self.assertEqual(json.loads(p.read_text()), {'uno': 1})

    def test_payment_and_special_call_order(self):
        self.assertTrue(radar.prioridad_pago('Pago contra entrega'))
        self.assertFalse(radar.prioridad_pago('Pago anticipado'))
        items = [{'titulo': 'A'}, {'titulo': 'B', 'llamado_especial': True},
                 {'titulo': 'C', 'pago_prioritario': True}]
        self.assertEqual([x['titulo'] for x in sorted(items, key=radar.prioridad_comercial)], ['C','B','A'])

    def test_new_types(self):
        for title in ['Compra menor', 'Reapertura', 'Licitación desierta', 'Segundo llamado']:
            self.assertTrue(radar.es_oportunidad(title, 'https://example.org/1'))

    def test_second_run_does_not_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'fuentes.txt').write_text('https://example.org/')
            names = {'ARCHIVO_FUENTES': str(root/'fuentes.txt'), 'ARCHIVO_ESTADO': str(root/'estado.json'),
                     'ARCHIVO_RESULTADOS': str(root/'nuevas.json'), 'ARCHIVO_AUDITORIA': str(root/'auditoria.json')}
            with patch.multiple(radar, **names), patch.object(radar.time, 'sleep'), patch.object(
                radar, 'descargar', return_value='<a href="/1.pdf">Compra menor 1</a>'):
                radar.ejecutar()
                self.assertEqual(json.loads((root/'nuevas.json').read_text())['total_nuevas'], 1)
                radar.ejecutar()
                self.assertEqual(json.loads((root/'nuevas.json').read_text())['total_nuevas'], 0)

    def test_fuentes_automaticas_se_monitorean_y_no_se_duplican_en_segunda_corrida(self):
        url='https://comuna.gob.ar/compras'
        self.automaticas.return_value={url:{'conector':'publicaciones','organismo':'Comuna de Prueba','provincia':'Santa Fe'}}
        fila={'titulo':'Licitación Pública 2/2026','objeto':'Compra de hormigón','numero_procedimiento':'2/2026','tipo_procedimiento':'licitacion publica','organismo':'Comuna de Prueba','provincia':'Santa Fe','fuente':url,'url':url,'detalle_completo':True}
        resultado={'estado':'OPERATIVA','paginas_visitadas':1,'paginas_correctas':1,'oportunidades':[fila],'errores':[],'limites':[]}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'fuentes.txt').write_text('https://example.org/')
            names={'ARCHIVO_FUENTES':str(root/'fuentes.txt'),'ARCHIVO_ESTADO':str(root/'estado.json'),'ARCHIVO_RESULTADOS':str(root/'nuevas.json'),'ARCHIVO_AUDITORIA':str(root/'auditoria.json')}
            with patch.multiple(radar,**names),patch.object(radar.time,'sleep'),patch.object(radar,'descargar',return_value='<a href="/1.pdf">Compra menor 1</a>'),patch.object(radar.conectores,'explorar',return_value=resultado) as consulta:
                radar.ejecutar();self.assertEqual(json.loads((root/'nuevas.json').read_text())['total_nuevas'],2)
                anterior=(root/'estado.json').read_text();radar.ejecutar()
                self.assertEqual(json.loads((root/'nuevas.json').read_text())['total_nuevas'],0);self.assertEqual(consulta.call_count,2)
                self.assertEqual(len(json.loads(anterior)['oportunidades']),2)

    def test_registro_automatico_invalido_no_detiene_fuentes_previas(self):
        self.automaticas.side_effect=ValueError('Registro inválido')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'fuentes.txt').write_text('https://example.org/')
            names={'ARCHIVO_FUENTES':str(root/'fuentes.txt'),'ARCHIVO_ESTADO':str(root/'estado.json'),'ARCHIVO_RESULTADOS':str(root/'nuevas.json'),'ARCHIVO_AUDITORIA':str(root/'auditoria.json')}
            with patch.multiple(radar,**names),patch.object(radar.time,'sleep'),patch.object(radar,'descargar',return_value='<a href="/1.pdf">Compra menor 1</a>'):
                radar.ejecutar();self.assertEqual(json.loads((root/'nuevas.json').read_text())['total_nuevas'],1)

if __name__ == '__main__':
    unittest.main()

