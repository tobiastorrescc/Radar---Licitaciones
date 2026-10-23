from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
import unicodedata


ROSARIO = "https://www.rosario.gob.ar/inicio/compras-y-licitaciones"


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )


def cargar(nombre):
    ruta = Path(nombre)

    if not ruta.exists():
        print("Falta el archivo:", nombre, flush=True)
        return []

    return [
        x.strip()
        for x in ruta.read_text(encoding="utf-8").splitlines()
        if x.strip() and not x.lstrip().startswith("#")
    ]


class Enlaces(HTMLParser):

    def __init__(self):
        super().__init__()
        self.resultados = []
        self.href = None
        self.partes = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.partes = []

    def handle_data(self, data):
        if self.href is not None:
            self.partes.append(data)

    def handle_endtag(self, tag):
        if tag == "a":
            if self.href:
                self.resultados.append(
                    (" ".join(self.partes).strip(), self.href)
                )

            self.href = None
            self.partes = []


def descargar(url):
    pedido = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urlopen(pedido, timeout=12) as respuesta:
        html = respuesta.read(1000000)
        charset = (
            respuesta.headers.get_content_charset()
            or "utf-8"
        )
        final = respuesta.geturl()

    extractor = Enlaces()

    extractor.feed(
        html.decode(charset, errors="replace")
    )

    return [
        (titulo, urljoin(final, href))
        for titulo, href in extractor.resultados
    ]


def ejecutar():
    fuentes = cargar("fuentes.txt")

    patrones = [
        normalizar(p)
        for p in cargar("patrones.txt")
    ]

    urls = list(
        dict.fromkeys(
            [
                u for u in fuentes
                if u.startswith(("http://", "https://"))
            ] + [ROSARIO]
        )
    )

    print("RADAR DE LICITACIONES", flush=True)

    print(
        "Fecha Argentina:",
        datetime.now(
            ZoneInfo("America/Argentina/Buenos_Aires")
        )
    )

    print("Paginas programadas:", len(urls))
    print("Patrones:", len(patrones))

    correctas = 0
    fallidas = 0
    candidatos = {}

    for url in urls:
        print("\nREVISANDO:", url, flush=True)

        try:
            enlaces = descargar(url)

            correctas += 1

            print(
                "Conexion correcta. Enlaces:",
                len(enlaces)
            )

            for titulo, destino in enlaces:
                if urlparse(destino).scheme not in (
                    "http",
                    "https"
                ):
                    continue

                texto = normalizar(
                    titulo + " " + destino
                )

                if patrones and any(
                    p in texto for p in patrones
                ):
                    candidatos.setdefault(
                        destino,
                        titulo
                    )

        except Exception as error:
            fallidas += 1

            print(
                "ERROR:",
                type(error).__name__,
                str(error),
                flush=True
            )

    print(
        "\nCANDIDATOS ENCONTRADOS:",
        len(candidatos)
    )

    for numero, (url, titulo) in enumerate(
        candidatos.items(), 1
    ):
        print(
            numero,
            "-",
            titulo or "Sin titulo"
        )

        print(url)

    print("\nRESUMEN FINAL")
    print("Paginas correctas:", correctas)
    print("Paginas con error:", fallidas)
    print("Candidatos unicos:", len(candidatos))
    print("PROCESO FINALIZADO")


if __name__ == "__main__":
    ejecutar()
