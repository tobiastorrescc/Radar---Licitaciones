from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse, urldefrag
from html.parser import HTMLParser
import json
import re
import unicodedata

ROSARIO = "https://www.rosario.gob.ar/inicio/compras-y-licitaciones"

ESTADO = Path("radar_estado.json")
SALIDA = Path("licitaciones_nuevas.json")

PALABRAS = (
    "licitacion",
    "concurso de precios",
    "compra directa",
    "contratacion",
    "cotizacion",
    "subasta",
    "pliego",
    "convocatoria",
    "compra agil",
    "segundo llamado",
    "pedido de precios",
    "solicitud de cotizacion",
    "licitacion privada",
    "licitacion publica",
)

DESCARTAR = (
    "buscar",
    "ir al contenido principal",
    "informacion general",
    "normativa",
    "inicio",
    "contacto",
    "tramites",
    "compras y licitaciones",
    "licitaciones",
    "buscar licitaciones",
    "oferentes y/o adjudicatarios",
)


def normalizar(texto):
    texto = unicodedata.normalize(
        "NFD",
        texto.lower()
    )

    return "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )


def cargar(nombre):
    ruta = Path(nombre)

    if not ruta.exists():
        print(
            "AVISO: falta el archivo:",
            nombre,
            flush=True
        )
        return []

    return [
        x.strip()
        for x in ruta.read_text(
            encoding="utf-8"
        ).splitlines()
        if x.strip()
        and not x.lstrip().startswith("#")
    ]


class Enlaces(HTMLParser):

    def __init__(self):
        super().__init__()
        self.resultados = []
        self.actual = None
        self.partes = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.actual = dict(attrs).get("href")
            self.partes = []

    def handle_data(self, data):
        if self.actual is not None:
            self.partes.append(data)

    def handle_endtag(self, tag):
        if tag == "a":
            if self.actual:
                titulo = " ".join(
                    " ".join(self.partes).split()
                )

                self.resultados.append(
                    (titulo, self.actual)
                )

            self.actual = None
            self.partes = []


def descargar(url):
    pedido = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urlopen(
        pedido,
        timeout=20
    ) as respuesta:

        tipo = respuesta.headers.get(
            "Content-Type",
            ""
        )

        if "html" not in tipo.lower():
            return []

        html = respuesta.read(2000000)

        charset = (
            respuesta.headers.get_content_charset()
            or "utf-8"
        )

        final = respuesta.geturl()

    extractor = Enlaces()

    extractor.feed(
        html.decode(
            charset,
            errors="replace"
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
    titulo_normal = normalizar(titulo).strip()
    destino_normal = normalizar(destino)

    if not titulo_normal:
        return False

    if len(titulo_normal) < 12:
        return False

    if titulo_normal in DESCARTAR:
        return False

    if any(
        x in destino_normal
        for x in (
            "/result-busq",
            "/informacion-general",
            "/normativa",
            "/oferentes"
        )
    ):
        return False

    claves = list(PALABRAS)

    claves.extend(
        p for p in patrones
        if len(p) >= 5
    )

    return any(
        palabra in titulo_normal
        or palabra in destino_normal
        for palabra in claves
    )


def ejecutar():

    print(
        "INICIANDO RADAR DE LICITACIONES",
        flush=True
    )

    ahora = datetime.now(
        ZoneInfo(
            "America/Argentina/Buenos_Aires"
        )
    )

    print(
        "Fecha Argentina:",
        ahora.isoformat(),
        flush=True
    )

    fuentes = cargar("fuentes.txt")

    patrones = [
        normalizar(p)
        for p in cargar("patrones.txt")
    ]

    urls = list(
        dict.fromkeys(
            [
                u for u in fuentes
                if u.startswith(
                    ("https://", "http://")
                )
            ] + [ROSARIO]
        )
    )

    print(
        "Fuentes programadas:",
        len(urls),
        flush=True
    )

    print(
        "Patrones cargados:",
        len(patrones),
        flush=True
    )

    visitadas = set()
    candidatas = {}

    correctas = 0
    fallidas = 0

    for origen in urls:

        print(
            "\nREVISANDO FUENTE:",
            origen,
            flush=True
        )

        pendientes = [(origen, 0)]

        dominio = (
            urlparse(origen)
            .netloc.lower()
            .removeprefix("www.")
        )

        paginas = 0

        while pendientes and paginas < 12:

            pagina, profundidad = pendientes.pop(0)

            if pagina in visitadas:
                continue

            visitadas.add(pagina)
            paginas += 1

            try:
                enlaces = descargar(pagina)

                correctas += 1

                print(
                    "CONEXION CORRECTA:",
                    pagina,
                    "| Enlaces:",
                    len(enlaces),
                    flush=True
                )

            except Exception as error:

                fallidas += 1

                print(
                    "ERROR:",
                    pagina,
                    type(error).__name__,
                    str(error),
                    flush=True
                )

                continue

            for titulo, destino in enlaces:

                parsed = urlparse(destino)

                if parsed.scheme
