from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def cargar_fuentes():
    archivo = Path("fuentes.txt")

    if not archivo.exists():
        print("ERROR: No se encontró fuentes.txt")
        return []

    fuentes = []

    with archivo.open("r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()

            if linea.startswith(("https://", "http://")):
                fuentes.append(linea)

    return fuentes


def revisar_fuente(url):
    print("Revisando:", url)

    try:
        solicitud = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urlopen(solicitud, timeout=20) as respuesta:
            codigo = respuesta.status
            contenido = respuesta.read(200000)

            print("Estado HTTP:", codigo)
            print("Contenido descargado:", len(contenido), "bytes")

            return True

    except HTTPError as error:
        print("Error HTTP:", error.code)
        return False

    except URLError as error:
        print("Error de conexión:", error.reason)
        return False

    except Exception as error:
        print("Error:", str(error))
        return False


def ejecutar_radar():
    fecha = datetime.now(
        ZoneInfo("America/Argentina/Buenos_Aires")
    )

    print("RADAR DE LICITACIONES")
    print("Fecha:", fecha)
    print("Zonas: Santa Fe, Entre Ríos y Buenos Aires")

    fuentes = cargar_fuentes()

    print("Total de fuentes cargadas:", len(fuentes))

    correctas = 0
    fallidas = 0

    for numero, fuente in enumerate(fuentes, start=1):
        print()
        print("FUENTE", numero, "DE", len(fuentes))

        resultado = revisar_fuente(fuente)

        if resultado:
            correctas += 1
        else:
            fallidas += 1

    print()
    print("RESUMEN DEL RADAR")
    print("Fuentes revisadas:", len(fuentes))
    print("Con respuesta correcta:", correctas)
    print("Con errores:", fallidas)
    print("Revisión finalizada")


if __name__ == "__main__":
    ejecutar_radar()
