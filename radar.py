from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def mostrar(*mensaje):
    print(*mensaje, flush=True)


def cargar_fuentes():
    archivo = Path("fuentes.txt")

    if not archivo.exists():
        mostrar("ERROR: No se encontró fuentes.txt")
        return []

    fuentes = []

    with archivo.open("r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()

            if linea.startswith(("https://", "http://")):
                fuentes.append(linea)

    return fuentes


def revisar_fuente(url):
    mostrar("Revisando:", url)

    try:
        solicitud = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urlopen(solicitud, timeout=8) as respuesta:
            codigo = respuesta.status
            contenido = respuesta.read(50000)

            mostrar("Estado HTTP:", codigo)
            mostrar("Bytes descargados:", len(contenido))

            return True

    except HTTPError as error:
        mostrar("Error HTTP:", error.code)
        return False

    except URLError as error:
        mostrar("Error de conexión:", error.reason)
        return False

    except TimeoutError:
        mostrar("Tiempo de espera agotado")
        return False

    except Exception as error:
        mostrar("Error:", str(error))
        return False


def ejecutar_radar():
    fecha = datetime.now(
        ZoneInfo("America/Argentina/Buenos_Aires")
    )

    mostrar("RADAR DE LICITACIONES")
    mostrar("Fecha:", fecha)
    mostrar("Zonas: Santa Fe, Entre Ríos y Buenos Aires")

    fuentes = cargar_fuentes()

    mostrar("Total de fuentes:", len(fuentes))

    correctas = 0
    fallidas = 0

    for numero, fuente in enumerate(fuentes, start=1):
        mostrar()
        mostrar("FUENTE", numero, "DE", len(fuentes))

        if revisar_fuente(fuente):
            correctas += 1
        else:
            fallidas += 1

    mostrar()
    mostrar("RESUMEN FINAL")
    mostrar("Fuentes revisadas:", len(fuentes))
    mostrar("Con respuesta correcta:", correctas)
    mostrar("Con errores:", fallidas)
    mostrar("PROCESO FINALIZADO")


if __name__ == "__main__":
    ejecutar_radar()
