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
        mostrar("ERROR: No se encontró", nombre)
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
                (titulo, self.enlace_actual)
            )

            self.enlace_actual = None
            self.texto_actual = []

        if etiqueta in ("script", "style"):
            self.ignorar = max(0, self.ignorar - 1)


def revisar_fuente(url, patrones):
    mostrar()
    mostrar("REVISANDO:", url)

    try:
        solicitud = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urlopen(solicitud, timeout=8) as respuesta:
            contenido = respuesta.read(200000)
            tipo = respuesta.headers.get_content_charset() or "utf-8"
            url_final = respuesta.geturl()

        html = contenido.decode(tipo, errors="replace")

        extractor = ExtractorEnlaces()
        extractor.feed(html)

        encontrados = []
        vistos = set()

        for titulo, enlace in extractor.enlaces:
            direccion = urljoin(url_final, enlace)

            if urlparse(direccion).scheme not in ("http", "https"):
                continue

            texto = normalizar(titulo + " " + direccion)

            if any(normalizar(patron) in texto for patron in patrones):
                if direccion not in vistos:
                    vistos.add(direccion)
                    encontrados.append((titulo, direccion))

        mostrar("Conexión correcta")
        mostrar("Enlaces candidatos:", len(encontrados))

        for numero, (titulo, direccion) in enumerate(encontrados, 1):
            mostrar()
            mostrar("CANDIDATO", numero)
            mostrar("Título:", titulo or "Sin título")
            mostrar("Enlace:", direccion)

        return True, encontrados

    except HTTPError as error:
        mostrar("Error HTTP:", error.code)

    except URLError as error:
        mostrar("Error de conexión:", error.reason)

    except Exception as error:
        mostrar("Error:", str(error))

    return False, []


def ejecutar_radar():
    fecha = datetime.now(
        ZoneInfo("America/Argentina/Buenos_Aires")
    )

    mostrar("RADAR DE LICITACIONES")
    mostrar("Fecha:", fecha)

    fuentes = cargar_archivo("fuentes.txt")
    patrones = cargar_archivo("patrones.txt")

    fuentes = [
        fuente for fuente in fuentes
        if fuente.startswith(("http://", "https://"))
    ]

    mostrar("Fuentes cargadas:", len(fuentes))
    mostrar("Patrones cargados:", len(patrones))

    correctas = 0
    errores = 0
    candidatos = {}

    for numero, fuente in enumerate(fuentes, 1):
        mostrar()
        mostrar("FUENTE", numero, "DE", len(fuentes))

        correcta, encontrados = revisar_fuente(fuente, patrones)

        if correcta:
            correctas += 1
        else:
            errores += 1

        for titulo, direccion in encontrados:
            candidatos[direccion] = titulo

    mostrar()
    mostrar("RESUMEN FINAL")
    mostrar("Fuentes revisadas:", len(fuentes))
    mostrar("Con respuesta correcta:", correctas)
    mostrar("Con errores:", errores)
    mostrar("Total de enlaces candidatos únicos:", len(candidatos))
    mostrar("PROCESO FINALIZADO")


if __name__ == "__main__":
    ejecutar_radar()
