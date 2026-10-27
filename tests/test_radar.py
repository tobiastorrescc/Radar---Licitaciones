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

if __name__ == '__main__':
    unittest.main()

