"""Revisión de evidencia real, control manual y EPE, sin consultas ni escrituras de producción."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o
from tools.verificar_fuentes import guardar
from tools.comparar_control_manual import comparar,escribir,cargar
from tools.revalidar_epe import revalidar
from calidad_comercial import escribir as comercial
from estado_criticas import evaluar,CRITICAS

def main():
    plan=json.load(open('tools/plan_cobertura.json'))
    if not plan.get('revisar_efectiva'):return
    d=json.load(open('work/barrido/resultado.json'));root=Path('work/recuperacion-efectiva');root.mkdir(parents=True,exist_ok=True)
    manual=cargar('inventario/auditoria_manual_tres_provincias.json');comparacion=comparar(d['registros'],manual,d['observaciones'],d['fecha']);escribir(comparacion,root)
    epe=revalidar(json.load(open('inventario/epe_17_control.json'))['casos'],d['registros'],d['observaciones'],d['fecha']);guardar(root/'epe_revalidacion.json',epe)
    import csv
    with (root/'epe_revalidacion.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(epe['casos'][0]));w.writeheader();w.writerows(epe['casos'])
    comercial_info=comercial(d['registros'],d['fecha'],root)
    alertas=[evaluar(s,d['registros']) for s in d['observaciones'] if s['id'] in CRITICAS];guardar(root/'estados_criticos.json',{'fuentes':alertas})
    resultado={'fecha':d['fecha'],'fuentes':len(d['observaciones']),'procedimientos':sum(r.get('clasificacion_registro')=='PROCEDIMIENTO' for r in d['registros']),'abiertas_documentales':sum(r.get('vigencia')=='ABIERTA' for r in d['registros']),**comercial_info,'epe':epe['resumen'],'comparacion':comparacion['resumen'],'fuentes_criticas':alertas,'ocr_nuevo':0}
    guardar(root/'resultado.json',resultado);print('RECUPERACION_EFECTIVA '+json.dumps({k:v for k,v in resultado.items() if k!='fuentes_criticas'},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
