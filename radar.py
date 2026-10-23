from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser
import unicodedata


class ExtractorTexto(HTMLParser):
    def __init__(self):
        super().__init__()
        self.textos = []
        self.ignorar = 0

    def handle_starttag(self, etiqueta, atributos):
        if etiqueta in ("script", "style"):
            self.ignorar += 1

    def handle_endtag(self, etiqueta):
        if etiqueta in ("script", "style"):
            self.ignorar = max(0, self.ignorar - 1)

    def handle_data(self, texto):
        if self.ignorar == 0:
            self.textos.append(texto)

    def obtener_texto(self):
        return " ".join(self.textos)


def mostrar(*mensaje):
    print(*mensaje, flush=True)


def normalizar(texto):
    texto = texto.lower()

    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        letra for letra in texto
        if unicodedata.category(letra) != "Mn"
    )


def cargar_archivo(nombre):
    archivo = Path(nombre)

    if not archivo.exists():
        mostrar("ERROR: No se encontró", nombre)
        return []

    with archivo.open("r", encoding="utf-8") as f:
        return [
            linea.strip()
            for linea in f
            if linea.strip()
            and not linea.strip().startswith("#")
        ]


def revisar_fuente(url, patrones):
    mostrar("Revisando:", url)

    try:
        solicitud = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urlopen(solicitud, timeout=8) as respuesta:
            contenido = respuesta.read(200000)
            tipo = respuesta.headers.get_content_charset() or "utf-8"

        html = contenido.decode(tipo, errors="replace")

        extractor = ExtractorTexto()
        extractor.feed(html)

        texto = normalizar(extractor
