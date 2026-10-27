"""Reporta evidencia de la verificación en un área aislada, sin escribir producción."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades


def ejecutar(informe,salida,historial):
    raiz=Path(salida).resolve()
    if raiz==Path.cwd().resolve():raise ValueError('Usar un directorio aislado de producción')
    raiz.mkdir(parents=True,exist_ok=True)
    r=json.loads(Path(informe).read_text());fecha=r['actualizado']
    estado=json.loads(Path(historial).read_text()) if Path(historial).exists() else {}
    h=estado.get('oportunidades',estado)
    if not isinstance(h,dict):raise ValueError('Historial inválido: no se modifica')
    registros=[]
    for fuente in r['observaciones']:
        checkpoint=Path(fuente.get('resultado_archivo',''))
        if not checkpoint.is_file():continue
        for raw in json.loads(checkpoint.read_text()).get('oportunidades',[]):
            item=oportunidades.normalizar(raw,fecha)
            item['fuente_estado']=fuente['estado'];item['verificacion_github_run_id']=r.get('github_run_id')
            registros.append(item)
    dedup={}
    for item in registros:
        k=oportunidades.identidad(item)
        if k not in dedup or len(item.get('campos_desconocidos',[]))<len(dedup[k].get('campos_desconocidos',[])):dedup[k]=item
    registros=list(dedup.values())
    nuevas=oportunidades.incorporar(h,registros,fecha)
    resumen={'registros_unicos':len(registros),'nuevas_detecciones':len(nuevas),'vigencia':dict(Counter(i['vigencia'] for i in registros)),
             'con_numero':sum(bool(i['numero_procedimiento']) for i in registros),'con_presupuesto':sum(bool(i['presupuesto']) for i in registros),
             'con_fecha_apertura':sum(bool(i['fecha_apertura']) for i in registros),'con_fecha_publicacion':sum(bool(i['fecha_publicacion']) for i in registros),
             'con_pliego_identificado':sum(bool(i['enlace_pliego']) for i in registros)}
    for nombre,datos in [('oportunidades_normalizadas.json',{'fecha':fecha,'resumen':resumen,'oportunidades':registros}),('nuevas_simulacion.json',{'total_nuevas':len(nuevas),'oportunidades':nuevas})]:
        (raiz/nombre).write_text(json.dumps(datos,ensure_ascii=False,indent=2),encoding='utf-8')
    (raiz/'reporte_diario_simulacion.md').write_text(oportunidades.reporte(nuevas,fecha),encoding='utf-8')
    print('CALIDAD_OPORTUNIDADES '+json.dumps(resumen,ensure_ascii=False))
    for f in r['observaciones']:
        filas=[i for i in registros if i.get('fuente')==f['url']]
        if filas:
            mejor=min(filas,key=lambda i:(len(i['campos_desconocidos']),i['vigencia']!='ABIERTA'))
            print('EJEMPLO_VERIFICADO '+json.dumps(mejor,ensure_ascii=False))
    return resumen

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--informe',default='work/verificacion/verificacion.json');p.add_argument('--salida',default='work/verificacion/comercial');p.add_argument('--historial',default='radar_estado.json');a=p.parse_args()
    ejecutar(a.informe,a.salida,a.historial)
