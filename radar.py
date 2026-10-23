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
        letra
        for letra in texto
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

        texto = normalizar(extractor.obtener_texto())

        encontrados = []

        for patron in patrones:
            if normalizar(patron) in texto:
                encontrados.append(patron)

        mostrar("Conexión correcta")
        mostrar("Palabras clave encontradas:", len(encontrados))

        for patron in encontrados:
            mostrar(" -", patron)

        return True

    except HTTPError as error:
        mostrar("Error HTTP:", error.code)

    except URLError as error:
        mostrar("Error de conexión:", error.reason)

    except Exception as error:
        mostrar("Error:", str(error))

    return False


def ejecutar_radar():
    fecha = datetime.now(
        ZoneInfo("America/Argentina/Buenos_Aires")
    )

    mostrar("RADAR DE LICITACIONES")
    mostrar("Fecha:", fecha)

    fuentes = cargar_archivo("fuentes.txt")
    patrones = cargar_archivo("patrones.txt")

    fuentes = [
        fuente
        for fuente in fuentes
        if fuente.startswith(("http://", "https://"))
    ]

    mostrar("Fuentes cargadas:", len(fuentes))
    mostrar("Patrones cargados:", len(patrones))

    correctas = 0
    errores = 0

    for numero, fuente in enumerate(fuentes, start=1):
        mostrar()
        mostrar("FUENTE", numero, "DE", len(fuentes))

        if revisar_fuente(fuente, patrones):
            correctas += 1
        else:
            errores += 1

    mostrar()
    mostrar("RESUMEN FINAL")
    mostrar("Fuentes revisadas:", len(fuentes))
    mostrar("Con respuesta correcta:", correctas)
    mostrar("Con errores:", errores)
    mostrar("PROCESO FINALIZADO")


if __name__ == "__main__":
    ejecutar_radar()
