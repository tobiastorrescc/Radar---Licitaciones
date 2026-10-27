"""Reporta evidencia de la verificación en un área aislada, sin escribir producción."""
import argparse
from datetime import datetime
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades
import pagos
import cache_documentos
from tools import comprobar_pliegos


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
    crudos=registros
    registros=oportunidades.deduplicar(registros,fecha)
    configuraciones=json.loads(Path('inventario/fuentes.json').read_text())
    enlaces=comprobar_pliegos.comprobar(registros,fecha,configuraciones,salida_parcial=raiz/'auditoria_documentos_parcial.jsonl')
    fecha=datetime.now(oportunidades.ZONA).isoformat()
    registros=[oportunidades.normalizar(i,fecha) for i in registros]
    vistas=oportunidades.guardar_vistas(registros,fecha,raiz)
    base=Path('tests/fixtures/reales/abiertas54.json')
    if base.exists():
        originales=json.loads(base.read_text())
        vistos={};revision=[];actuales={oportunidades.identidad(i):i for i in registros}
        for indice,anterior in enumerate(originales,1):
            normal=oportunidades.normalizar(anterior,fecha);clave=oportunidades.identidad(normal)
            dato={'fila_original':indice,'numero_original':anterior.get('numero_procedimiento'),'url_original':anterior.get('url'),'identidad_corregida':clave,'procedimiento_canonico':normal.get('procedimiento_canonico'),'duplicada_de':vistos.get(clave),'estado_actual':actuales.get(clave,{}).get('vigencia','NO_RECUPERADA_EN_ESTA_CORRIDA'),'presupuesto_actual':actuales.get(clave,{}).get('presupuesto')}
            vistos.setdefault(clave,indice);revision.append(dato)
            print('REVISION_ABIERTAS54 '+json.dumps(dato,ensure_ascii=False),flush=True)
        (raiz/'revision_11_abiertas54.json').write_text(json.dumps(revision,ensure_ascii=False,indent=2),encoding='utf-8')
    pagos_resumen=pagos.resumen(registros)
    (raiz/'auditoria_pagos.json').write_text(json.dumps({'fecha':fecha,'resumen':pagos_resumen,'oportunidades':registros},ensure_ascii=False,indent=2),encoding='utf-8')
    print('RESUMEN_PAGOS '+json.dumps(pagos_resumen,ensure_ascii=False),flush=True)
    ejemplos_pagos=Counter()
    for i in sorted(registros,key=lambda r:r.get('vigencia')!='ABIERTA'):
        cat=i.get('pago',{}).get('clasificacion')
        if i.get('pago',{}).get('estado')=='VERIFICADO' and ejemplos_pagos[cat]<3:
            ejemplos_pagos[cat]+=1
            print('PAGO_VERIFICADO '+json.dumps({k:i.get(k) for k in ('organismo','numero_procedimiento','fuente','vigencia','pago','condiciones_pago')},ensure_ascii=False),flush=True)
    print('CACHE_DOCUMENTOS '+json.dumps(cache_documentos.limpiar()),flush=True)
    nuevas=oportunidades.incorporar(h,registros,fecha)
    resumen={'registros_antes_deduplicar':len(crudos),'duplicados_unificados':len(crudos)-len(registros),'registros_unicos':len(registros),'proximas_a_vencer':len(vistas['proximas_a_vencer']),'candidatos_no_verificados':sum(i['clasificacion_registro']!='PROCEDIMIENTO' for i in registros),'pliegos_comprobados_abiertas':sum(i.get('comprobacion_pliego',{}).get('estado')=='DOCUMENTO_ACCESIBLE' for i in vistas['abiertas']),'nuevas_detecciones':len(nuevas),'vigencia':dict(Counter(i['vigencia'] for i in registros)),
             'con_numero':sum(bool(i['numero_procedimiento']) for i in registros),'con_presupuesto':sum(bool(i['presupuesto']) for i in registros),
             'con_fecha_apertura':sum(bool(i['fecha_apertura']) for i in registros),'con_fecha_publicacion':sum(bool(i['fecha_publicacion']) for i in registros),
             'con_pliego_identificado':sum(bool(i['enlace_pliego']) for i in registros)}
    for nombre,datos in [('auditoria_enlaces.json',enlaces),('oportunidades_normalizadas.json',{'fecha':fecha,'resumen':resumen,'oportunidades':registros}),('nuevas_simulacion.json',{'total_nuevas':len(nuevas),'oportunidades':nuevas})]:
        (raiz/nombre).write_text(json.dumps(datos,ensure_ascii=False,indent=2),encoding='utf-8')
    (raiz/'reporte_diario_simulacion.md').write_text(oportunidades.reporte(nuevas,fecha),encoding='utf-8')
    for item in vistas['abiertas']:print('OPORTUNIDAD_ABIERTA '+json.dumps(item,ensure_ascii=False),flush=True)
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
