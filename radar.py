from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen
from html.parser import HTMLParser
import json
import re
import unicodedata
import time


# ==========================================
# CONFIGURACION GENERAL
# ==========================================

ROSARIO = (
    "https://www.rosario.gob.ar/"
    "inicio/compras-y-licitaciones"
)

ARCHIVO_FUENTES = "fuentes.txt"
ARCHIVO_ESTADO = "radar_estado.json"
ARCHIVO_RESULTADOS = "licitaciones_nuevas.json"
ARCHIVO_AUDITORIA = "auditoria_fuentes.json"

MAX_PAGINAS = 40
MAX_PROFUNDIDAD = 3
TIMEOUT = 15

EXTENSIONES = (
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
)

PALABRAS_OPORTUNIDAD = (
    "licitacion",
    "concurso de precios",
    "compra directa",
    "contratacion directa",
    "contratacion",
    "pedido de cotizacion",
    "solicitud de cotizacion",
    "compra agil",
    "compulsa",
    "segundo llamado",
    "primer llamado",
    "adquisicion",
    "provision",
    "orden de compra",
    "pedido de precios",
    "subasta",
    "pliego",
    "convocatoria",
)

PALABRAS_NAVEGACION = (
    "licitaciones",
    "compras",
    "contrataciones",
    "proveedores",
    "concursos",
    "transparencia",
    "boletin oficial",
    "convocatorias",
    "publicaciones",
)

PALABRAS_PAGO_PRIORITARIO = (
    "pago contado",
    "pago al contado",
    "contra entrega",
    "pago inmediato",
    "pago anticipado",
)


# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def normalizar(texto):
    texto = str(texto or "").lower()

    texto = unicodedata.normalize(
        "NFKD", texto
    )

    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    return re.sub(
        r"\s+", " ", texto
    ).strip()


def url_limpia(url):
    url, _ = urldefrag(url)
    return url.strip()


def leer_lineas(archivo):
    ruta = Path(archivo)

    if not ruta.exists():
        return []

    lineas = ruta.read_text(
        encoding="utf-8"
    ).splitlines()

    return [
        linea.strip()
        for linea in lineas
        if linea.strip()
        and not linea.strip().startswith("#")
    ]


def guardar_json(archivo, datos):
    Path(archivo).write_text(
        json.dumps(
            datos,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def cargar_json(archivo, defecto):
    ruta = Path(archivo)

    if not ruta.exists():
        return defecto

    try:
        return json.loads(
            ruta.read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return defecto


# ==========================================
# EXTRACCION DE ENLACES
# ==========================================

class Enlaces(HTMLParser):

    def __init__(self):
        super().__init__()
        self.enlaces = []
        self.actual = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return

        atributos = dict(attrs)
        href = atributos.get("href")

        if href:
            self.actual = {
                "url": href,
                "texto": "",
            }

    def handle_data(self, data):
        if self.actual is not None:
            self.actual["texto"] += data

    def handle_endtag(self, tag):
        if tag.lower() == "a":
            if self.actual is not None:
                self.enlaces.append(self.actual)

            self.actual = None


# ==========================================
# DESCARGA DE PAGINAS
# ==========================================

def descargar(url):
    solicitud = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "RadarLicitaciones/1.0"
            )
        },
    )

    with urlopen(
        solicitud,
        timeout=TIMEOUT,
    ) as respuesta:

        tipo = respuesta.headers.get(
            "Content-Type", ""
        ).lower()

        contenido = respuesta.read(
            2_000_000
        )

        if "html" not in tipo:
            return ""

        return contenido.decode(
            "utf-8",
            errors="replace",
        )


# ==========================================
# IDENTIFICACION DE OPORTUNIDADES
# ==========================================

def es_oportunidad(texto, url):
    contenido = normalizar(
        texto + " " + url
    )

    return any(
        palabra in contenido
        for palabra in PALABRAS_OPORTUNIDAD
    )


def es_navegacion(texto, url):
    contenido = normalizar(
        texto + " " + url
    )

    return any(
        palabra in contenido
        for palabra in PALABRAS_NAVEGACION
    )


def prioridad_pago(texto):
    contenido = normalizar(texto)

    return any(
        palabra in contenido
        for palabra in PALABRAS_PAGO_PRIORITARIO
    )


def prioridad_comercial(item):
    if item.get("pago_prioritario"):
        return 0

    return 1


def dominio(url):
    return urlparse(url).netloc.lower()


def enlace_valido(url):
    parsed = urlparse(url)

    return parsed.scheme in (
        "http",
        "https",
    ) and bool(parsed.netloc)


# ==========================================
# EXPLORACION DE FUENTES
# ==========================================

def explorar_fuente(fuente):
    pendientes = [(fuente, 0)]
    visitadas = set()
    oportunidades = {}
    errores = []

    dominio_base = dominio(fuente)

    while pendientes:
        if len(visitadas) >= MAX_PAGINAS:
            break

        url, profundidad = pendientes.pop(0)

        url = url_limpia(url)

        if url in visitadas:
            continue

        if not enlace_valido(url):
            continue

        if dominio(url) != dominio_base:
            continue

        visitadas.add(url)

        try:
            html = descargar(url)

        except Exception as error:
            errores.append({
                "url": url,
                "error": str(error),
            })
            continue

        if not html:
            continue

        parser = Enlaces()

        try:
            parser.feed(html)
        except Exception as error:
            errores.append({
                "url": url,
                "error": str(error),
            })
            continue

        for enlace in parser.enlaces:
            destino = url_limpia(
                urljoin(
                    url,
                    enlace["url"],
                )
            )

            titulo = re.sub(
                r"\s+",
                " ",
                enlace["texto"],
            ).strip()

            if not enlace_valido(destino):
                continue

            if not titulo:
                titulo = destino.split("/")[-1]

            if es_oportunidad(titulo, destino):
                oportunidades[destino] = {
                    "titulo": titulo,
                    "url": destino,
                    "fuente": fuente,
                    "pago_prioritario": (
                        prioridad_pago(titulo)
                    ),
                    "estado": (
                        "CANDIDATO_NO_VERIFICADO"
                    ),
                }

            if profundidad >= MAX_PROFUNDIDAD:
                continue

            if dominio(destino) != dominio_base:
                continue

            if destino in visitadas:
                continue

            ruta = urlparse(destino).path.lower()

            if ruta.endswith(EXTENSIONES):
                continue

            if es_navegacion(titulo, destino):
                pendientes.append(
                    (destino, profundidad + 1)
                )

        time.sleep(0.1)

    return {
        "oportunidades": list(
            oportunidades.values()
        ),
        "paginas_visitadas": len(visitadas),
        "errores": errores,
    }


# ==========================================
# EJECUCION PRINCIPAL
# ==========================================

def ejecutar():
    ahora = datetime.now().astimezone()
    fecha = ahora.isoformat()

    print("=" * 60)
    print("RADAR DE LICITACIONES")
    print("Inicio:", fecha)
    print("=" * 60)

    fuentes = leer_lineas(
        ARCHIVO_FUENTES
    )

    fuentes.append(ROSARIO)

    fuentes = list(
        dict.fromkeys(
            url_limpia(f)
            for f in fuentes
            if enlace_valido(f)
        )
    )

    print(
        "Fuentes configuradas:",
        len(fuentes),
    )

    estado_anterior = cargar_json(
        ARCHIVO_ESTADO,
        {},
    )

    if not isinstance(
        estado_anterior, dict
    ):
        estado_anterior = {}

    if "oportunidades" in estado_anterior:
        historial = estado_anterior[
            "oportunidades"
        ]
    else:
        historial = estado_anterior

    if not isinstance(historial, dict):
        historial = {}

    nuevas = []
    auditoria = []
    encontradas = {}

    for numero, fuente in enumerate(
        fuentes,
        start=1,
    ):
        print()
        print(
            f"[{numero}/{len(fuentes)}]",
            fuente,
        )

        resultado = explorar_fuente(
            fuente
        )

        oportunidades = resultado[
            "oportunidades"
        ]

        print(
            "Paginas visitadas:",
            resultado["paginas_visitadas"],
        )

        print(
            "Candidatos encontrados:",
            len(oportunidades),
        )

        for oportunidad in oportunidades:
            url = oportunidad["url"]

            encontradas[url] = oportunidad

            if url not in historial:
                oportunidad[
                    "primera_deteccion"
                ] = fecha

                nuevas.append(
                    oportunidad
                )

                historial[url] = oportunidad

                print(
                    "NUEVA:",
                    oportunidad["titulo"],
                )

        auditoria.append({
            "fuente": fuente,
            "fecha": fecha,
            "paginas_visitadas": resultado[
                "paginas_visitadas"
            ],
            "candidatos": len(oportunidades),
            "errores": resultado["errores"],
        })

    nuevas.sort(key=prioridad_comercial)

    guardar_json(
        ARCHIVO_RESULTADOS,
        {
            "fecha": fecha,
            "total_nuevas": len(nuevas),
            "oportunidades": nuevas,
        },
    )

    guardar_json(
        ARCHIVO_ESTADO,
        {
            "ultima_ejecucion": fecha,
            "oportunidades": historial,
        },
    )

    guardar_json(
        ARCHIVO_AUDITORIA,
        {
            "fecha": fecha,
            "fuentes": auditoria,
        },
    )

    print("Fuentes revisadas:", len(fuentes))
    print("Candidatos detectados:", len(encontradas))
    print("Oportunidades nuevas:", len(nuevas))
    print("Radar finalizado correctamente.")


if __name__ == "__main__":
    ejecutar()
