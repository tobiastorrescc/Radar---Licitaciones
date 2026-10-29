import unittest
import conectores

class PrioridadArchivosTests(unittest.TestCase):
    def test_recientes_primero_sin_descartar_archivos_anteriores(self):
        pedidos=[]
        def fetch(url):
            pedidos.append(url)
            if url.endswith('/'):
                html='<a href="licitaciones-2013">2013</a><a href="licitaciones-2026">2026</a><a href="licitaciones-2025">2025</a>'
            else:
                anio=url.rsplit('-',1)[1]
                html='<article>Licitación Pública N° 1/'+anio+' Objeto: Compra de materiales de construcción</article>'
            return html.encode(),'text/html',url
        r=conectores.explorar('https://prueba.gob.ar/',{'seguir_patrones':['/licitaciones-20[0-9]{2}'],'lectura_adjuntos':'necesarios'},fetch=fetch)
        self.assertEqual(pedidos,['https://prueba.gob.ar/','https://prueba.gob.ar/licitaciones-2026','https://prueba.gob.ar/licitaciones-2025','https://prueba.gob.ar/licitaciones-2013'])
        self.assertEqual(len(r['oportunidades']),3)

    def test_limite_de_seguridad_informa_recorrido_parcial(self):
        def fetch(url):return b'<a href="licitaciones-2013">2013</a><a href="licitaciones-2026">2026</a>','text/html',url
        r=conectores.explorar('https://prueba.gob.ar/',{'seguir_patrones':['/licitaciones-20[0-9]{2}']},fetch=fetch,max_paginas=2)
        self.assertIn('max_paginas',r['limites']);self.assertFalse(r['cobertura_completa'])
