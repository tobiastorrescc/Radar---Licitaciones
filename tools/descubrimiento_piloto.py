"""Descubrimiento cada tres días, después del respaldo diario y sin bloquearlo."""
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.descubrir_fuentes import ejecutar_descubrimiento


def corresponde(estado,ahora):
    previo=estado.get('ultima_ejecucion')
    if not previo:return True
    fecha=datetime.fromisoformat(previo)
    if fecha.tzinfo is None:return True
    return ahora-fecha>=timedelta(days=3)


def main():
    p=Path('inventario/descubrimiento_estado.json');estado=json.loads(p.read_text())
    if not corresponde(estado,datetime.now(timezone.utc)):
        print('DESCUBRIMIENTO_NO_VENCE: revisión cada tres días; escaneo diario conservado.',flush=True);return
    ejecutar_descubrimiento('work/descubrimiento-piloto',total=180,busquedas=12,candidatos=36)

if __name__=='__main__':main()
