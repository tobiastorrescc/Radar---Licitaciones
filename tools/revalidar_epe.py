"""Revalida cada antecedente EPE contra observaciones oficiales actuales, sin duplicar consultas."""
import argparse,csv,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o
from calidad_comercial import presentacion
from tools.verificar_fuentes import guardar

def revalidar(controles,registros,observaciones,fecha):
    actuales=[r for r in registros if o.norm(r.get('organismo'))=='epe' and not r.get('requiere_revalidacion') and r.get('clasificacion_registro')=='PROCEDIMIENTO']
    estado=next((s for s in observaciones if s.get('id')=='fuente-003'),{})
    filas=[]
    for original in controles:
        base=o.normalizar(original,fecha);proc=o.procedimiento_canonico(base)
        candidatos=[r for r in actuales if o.procedimiento_canonico(r)==proc]
        comprobada=next((r for r in candidatos if presentacion(r,fecha)['presentacion_verificada']),None)
        cerrada=next((r for r in candidatos if r.get('vigencia')=='VENCIDA'),None)
        if comprobada:clasificacion='VIGENTE_VERIFICADA';motivo='Plazo de recepción comprobado en evidencia oficial actual';evidencia=comprobada
        elif cerrada:clasificacion='VENCIDA_O_CERRADA';motivo='Cierre comprobado en observación oficial actual';evidencia=cerrada
        elif base.get('fecha_apertura') and base['fecha_apertura']<o.datetime.fromisoformat(fecha).astimezone(o.ZONA).date().isoformat():
            clasificacion='VENCIDA_O_CERRADA';motivo='Apertura documental superada; no se comprobó prórroga';evidencia=base
        else:clasificacion='PENDIENTE_REVALIDACION';motivo='No hay evidencia actual con recepción de ofertas vigente comprobada';evidencia=base
        filas.append({'organismo':'EPE','numero_procedimiento':base.get('numero_procedimiento'),'objeto':base.get('objeto'),'fecha_apertura_archivada':base.get('fecha_apertura'),'fecha_apertura_actual':comprobada.get('fecha_apertura') if comprobada else None,'fecha_limite_presentacion':comprobada.get('fecha_limite_presentacion') if comprobada else None,'clasificacion':clasificacion,'motivo':motivo,'url_oficial':evidencia.get('evidencia_url') or evidencia.get('url'),'consulta_compartida':estado.get('url'),'estado_acceso':estado.get('estado','NO_CONSULTADA'),'fecha_evidencia_archivada':original.get('recuperacion_archivo',{}).get('capturado_en')})
    from collections import Counter
    return {'fecha':fecha,'casos':filas,'resumen':dict(Counter(r['clasificacion'] for r in filas)),'criterio':'El listado oficial se consulta una vez para contrastar todos los números. Una copia anterior y un resultado indexado antiguo no acreditan vigencia actual.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--barrido',required=True);p.add_argument('--controles',default='inventario/epe_17_control.json');p.add_argument('--salida',default='work/revalidacion-epe');a=p.parse_args()
    d=json.load(open(a.barrido));base=json.load(open(a.controles));r=revalidar(base['casos'],d['registros'],d['observaciones'],d['fecha']);root=Path(a.salida);root.mkdir(parents=True,exist_ok=True);guardar(root/'epe_revalidacion.json',r)
    with (root/'epe_revalidacion.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(r['casos'][0]) if r['casos'] else ['clasificacion']);w.writeheader();w.writerows(r['casos'])
    print(json.dumps(r['resumen'],ensure_ascii=False))

if __name__=='__main__':main()
