from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse, urldefrag
from html.parser import HTMLParser
import json
import re
import unicodedata

ROSARIO = 'https://www.rosario.gob.ar/inicio/compras-y-licitaciones'
ESTADO = Path('radar_estado.json')
SALIDA = Path('licitaciones_nuevas.json')

PALABRAS = (
    'licitacion',
    'concurso de precios',
    'compra directa',
    'contratacion',
    'cotizacion',
    'subasta',
    'pliego',
    'convocatoria',
    'compra agil',
    'segundo llamado'
)

DESCARTAR = (
    'buscar',
    'ir al contenido principal',
    'informacion general',
    'normativa',
    'of erentes',
    'inicio',
    'contacto',
    'tramites'
)


def normalizar(texto):
    texto = unicodedata.normalize('NFD', texto.lower())
    return ''.join(
        c for c in texto
        if unicodedata.category(c) != 'Mn'
    )


def cargar(nombre):
    ruta = Path(nombre)

    if not ruta.exists():
        print('Falta el archivo:', nombre)
        return []

    return [
        x.strip()
        for x in ruta.read_text(
            encoding='utf-8'
        ).splitlines()
        if x.strip()
        and not x.lstrip().startswith('#')
    ]


class Enlaces(HTMLParser):

    def __init__(self):
        super().__init__()
        self.resultados = []
        self.actual = None
        self.partes = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.actual = dict(attrs).get('href')
            self.partes = []

    def handle_data(self, data):
        if self.actual is not None:
            self.partes.append(data)

    def handle_endtag(self, tag):
        if tag == 'a':
            if self.actual:
                self.resultados.append(
                    (
                        ' '.join(
                            ' '.join(self.partes).split()
                        ),
                        self.actual
                    )
                )

            self.actual = None
            self.partes = []


def descargar(url):
    pedido = Request(
        url,
        headers={
            'User-Agent':
            'Mozilla/5.0 (compatible; LicitacionesRadar/1.0)'
        }
    )

    with urlopen(pedido, timeout=20) as respuesta:
        tipo = respuesta.headers.get(
            'Content-Type', ''
        )

        if 'html' not in tipo.lower():
            return []

        html = respuesta.read(2000000)

        charset = (
            respuesta.headers.get_content_charset()
            or 'utf-8'
        )

        final = respuesta.geturl()

    extractor = Enlaces()

    extractor.feed(
        html.decode(
            charset,
            errors='replace'
        )
    )

    return [
        (
            titulo,
            urldefrag(
                urljoin(final, href)
            )[0]
        )
        for titulo, href in extractor.resultados
    ]


def es_candidato(titulo, destino, patrones):
    t = normalizar(titulo).strip()
    d = normalizar(destino)

    if (
        not t
        or len(t) < 12
        or t in DESCARTAR
        or t in (
            'compras y licitaciones',
            'licitaciones',
            'buscar licitaciones'
        )
    ):
        return False

    if any(
        x in d
        for x in (
            '/result-busq',
            '/informacion-general',
            '/normativa',
            '/of erentes'
        )
    ):
        return False

    claves = (
        tuple(
            p for p in patrones
            if len(p) >= 5
        )
        or PALABRAS
    )

    return any(
        p in t or p in d
        for p in claves
    )


def ejecutar():
    fuentes = cargar('fuentes.txt')

    patrones = [
        normalizar(p)
        for p in cargar('patrones.txt')
    ]

    urls = list(
        dict.fromkeys(
            [
                u for u in fuentes
                if u.startswith(
                    ('https://', 'http://')
                )
            ] + [ROSARIO]
        )
    )

    print('RADAR DE LICITACIONES')

    print(
        'Fecha Argentina:',
        datetime.now(
            ZoneInfo(
                'America/Argentina/Buenos_Aires'
            )
        ).isoformat()
    )

    print('Fuentes:', len(urls))

    visitadas = set()
    candidatas = {}

    correctas = 0
    fallidas = 0

    for origen in urls:
        pendientes = [(origen, 0)]

        dominio = (
            urlparse(origen)
            .netloc.lower()
            .removeprefix('www.')
        )

        paginas = 0

        while pendientes and paginas < 12:
            pagina, profundidad = pendientes.pop(0)

            if pagina in visitadas:
                continue

            visitadas.add(pagina)
            paginas
