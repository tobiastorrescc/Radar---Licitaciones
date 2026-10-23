from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
import unicodedata


def mostrar(*mensaje):
    print(*mensaje, flush=True)


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(
        letra for letra in texto
        if unicodedata.category(letra) != "Mn"
    )


def cargar_archivo(nombre):
    archivo = Path(nombre)

    if not archivo.exists():
        mostrar("Archivo no encontrado:", nombre)
        return []

    with archivo.open("r", encoding="utf-8") as f:
        return [
            linea.strip()
            for linea in f
            if linea.strip()
            and not linea.strip().startswith("#")
        ]


class ExtractorEnlaces(HTMLParser):

    def __init__(self):
        super().__init__()
        self.enlaces = []
        self.enlace_actual = None
        self.texto_actual = []
        self.ignorar = 0

    def handle_starttag(self, etiqueta, atributos):
        if etiqueta in ("script", "style"):
            self.ignorar += 1

        if etiqueta == "a" and self.ignorar == 0:
            datos = dict(atributos)
            self.enlace_actual = datos.get("href")
            self.texto_actual = []

    def handle_data(self, texto):
        if self.enlace_actual is not None:
            self.texto_actual.append(texto)

    def handle_endtag(self, etiqueta):
        if etiqueta == "a" and self.enlace_actual is not None:
            titulo = " ".join(self.texto_actual).strip()
            self.enlaces.append(
                (titulo, self.enlace_actual
