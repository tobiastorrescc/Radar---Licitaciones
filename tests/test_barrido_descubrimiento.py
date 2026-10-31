import unittest
from unittest.mock import patch
import conectores, extractores

class BarridoDescubrimiento(unittest.TestCase):
    def test_aviso_sin_numero_pliego_o_presupuesto(self):
        html='<main><article>Se solicitan cotizaciones para la provisión de caños para desagües.</article></main>'
        rs,_,_=extractores.extraer(html,'https://oficial.gob.ar/compras/',{'admitir_avisos_sin_numero':True})
        self.assertEqual(len(rs),1)
        self.assertTrue(rs[0]['aviso_oficial_sin_numero'])
        self.assertFalse(rs[0]['documentos'])

    def test_no_confundir_registro_proveedores(self):
        html='<main><article>Solicitud de cotización para provisión: normativa del registro de proveedores.</article></main>'
        rs,_,_=extractores.extraer(html,'https://oficial.gob.ar/',{'admitir_avisos_sin_numero':True})
        self.assertFalse(rs)

    def test_mismo_indice_no_oculta_procedimiento_distinto(self):
        from tools.comparar_barrido import comparar
        uno={'organismo':'Comuna','provincia':'Santa Fe','url':'https://oficial.gob.ar/compras/','fuente':'https://oficial.gob.ar/compras/','numero_procedimiento':'1/2026','tipo_procedimiento':'licitacion publica','clasificacion_registro':'PROCEDIMIENTO','vigencia':'ABIERTA','fecha_apertura':'2026-11-04'}
        dos={**uno,'numero_procedimiento':'2/2026'}
        r=comparar({'registros':[uno]},{'registros':[dos]},[uno])
        self.assertEqual(r['categorias'],{'VIGENTE_NUEVA_PARA_RADAR':1})

    def test_unr_aviso_real_conserva_objeto_y_fechas_sin_descargar_pliego(self):
        from pathlib import Path
        import oportunidades as o
        url='https://unr.edu.ar/convocatoria-licitacion-publica-n-5-2026-aulas-2-piso-escuela-preuniversitaria-de-ciencias-sociales-y-humanisticas/'
        html=Path('tests/fixtures/reales/unr5-aviso.html').read_text()
        rs,_,_=extractores.extraer(html,url,{})
        r=o.normalizar(rs[0],'2026-10-31T11:00:00-03:00')
        self.assertIn('Aulas 2° Piso',r['objeto'])
        self.assertEqual(r['fecha_apertura'],'2026-11-04')
        self.assertEqual(r['fecha_limite_presentacion'],'2026-11-04')
        self.assertEqual(r['fecha_publicacion'],'2026-10-02')
        self.assertEqual(r['vigencia'],'ABIERTA')

    def test_sigue_boletines_oficiales_plural(self):
        calls=[]
        def fetch(url):
            calls.append(url)
            html='<main><a href="/boletines/">Boletines oficiales</a></main>' if len(calls)==1 else '<main>Archivo municipal</main>'
            return html.encode(),'text/html',url
        conectores.explorar('https://oficial.gob.ar/',{'descubrir_contrataciones':True,'descubrir_menu':True,'solo_descubrimiento':True},fetch=fetch)
        self.assertIn('https://oficial.gob.ar/boletines/',calls)

if __name__=='__main__':unittest.main()
