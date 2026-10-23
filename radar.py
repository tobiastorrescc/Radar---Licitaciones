from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def cargar_fuentes():
    archivo = Path("fuentes.txt")

    if not archivo.exists():
        print("ERROR: No se encontró fuentes.txt")
        return []

    fuentes = []

    with archivo.open("r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()

            if linea.startswith("http"):
                fuentes.append(linea)

    return fuentes


def ejecutar_radar():
    fecha = datetime.now(
        ZoneInfo("America/Argentina/Buenos_Aires")
    )

    print("RADAR DE LICITACIONES")
    print("Fecha:", fecha)
    print("Zonas: Santa Fe, Entre Ríos y Buenos Aires")

    fuentes = cargar_fuentes()

    print("Total de fuentes cargadas:", len(fuentes))

    for numero, fuente in enumerate(fuentes, start=1):
        print(numero, fuente)

    print("Lectura de fuentes finalizada")


if __name__ == "__main__":
    ejecutar_radar()
