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
        letra
        for letra in texto
        if unicodedata.category(letra) != "Mn"
    )


def cargar_archivo(nombre):
    ruta = Path(nombre)

    if not ruta.exists():
        mostrar("Archivo no encontrado:", nombre)
        return []

    return [
        linea.strip()
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if linea.strip() and not linea.strip().startswith("#")
    ]


class ExtractorEnlaces(HTMLParser):

    def __init__(self):
        super().__init__()
        self.enlaces = []
        self.enlace_actual = None
        self.texto_actual = []

    def handle_starttag(self, etiqueta, atributos):
        if etiqueta.lower() == "a":
            datos = dict(atributos)
            self.enlace_actual = datos.get("href")
            self.texto_actual = []

    def handle_data(self, datos):
        if self.enlace_actual is not None:
            self.texto_actual.append(datos)

    def handle_endtag(self, etiqueta):
        if etiqueta.lower() == "a":
            if self.enlace_actual:
                titulo = " ".join(self.texto_actual).strip()

                self.enlaces.append(
                    (titulo, self.enlace_actual)
                )

            self.enlace_actual = None
            self.texto_actual = []


def descargar_pagina(url):
    solicitud = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 RadarLicitaciones/1.0"
        }
    )

    with urlopen(solicitud, timeout=8) as respuesta:
        contenido = respuesta.read(500000)

        codificacion = respuesta.headers.get_content_charset()
        if not codificacion:
            codificacion = "utf-8"

        return contenido.decode(
            codificacion,
            errors="replace"
        )


def extraer_enlaces(html, url_base):
    extractor = ExtractorEnlaces()
    extractor.feed(html)

    resultados = []

    for titulo, enlace in extractor.enlaces:
        direccion = urljoin(url_base, enlace)

        if urlparse(direccion).scheme not in ("http", "https"):
            continue

        resultados.append(
            (titulo.strip(), direccion)
        )

    return resultados


def es_candidato(titulo, enlace, patrones):
    contenido = normalizar(titulo + " " + enlace)

    return any(
        normalizar(patron) in contenido
        for patron in patr
