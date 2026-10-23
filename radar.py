from datetime import datetime
from zoneinfo import ZoneInfo

def ejecutar_radar():
    print("RADAR DE LICITACIONES")
    print("Fecha:", datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")))
    print("Zonas: Santa Fe, Entre Ríos y Buenos Aires")
    print("Estado: programa iniciado")

if _name_ == "_main_":
    ejecutar_radar()
