"""Comparación explícita de observaciones automáticas y controles manuales, sin escribir historial."""
import argparse,csv,json,sys
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o,metricas_territoriales as mt
from tools.verificar_fuentes import guardar

def cargar(path):
    p=Path(path)
    if p.suffix=='.csv':
        with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
    d=json.loads(p.read_text())
    if isinstance(d,list):return d
    for k in ('registros','oportunidades','publicaciones','fichas'):
        if isinstance(d.get(k),list):return d[k]
    raise ValueError('Archivo sin una lista de oportunidades')

def comparar(automaticas,manuales,observaciones,fecha):
    autos=o.deduplicar([o.normalizar(r,fecha) for r in automaticas if not r.get('recuperacion_archivo')],fecha)
    autos=[{**r,'id':r.get('id') or o.identidad(r)} for r in autos]
    controles=[]
    for r in manuales:
        n=o.normalizar(r,fecha);controles.append({**n,**{k:v for k,v in r.items() if k in ('comprobada','fecha_revision','evidencia_url','organismo_aliases')}})
    aptas=[r for r in controles if r.get('comprobada') in (True,'true','True','1') and r.get('evidencia_url') and r.get('fecha_revision')]
    contraste=mt.contraste_manual({'publicaciones':aptas,'alcance':'Muestra manual explícita; no representa cobertura territorial global'},autos,fecha)
    configuradas={f['id']:f for f in json.loads(Path('inventario/fuentes.json').read_text())}
    ambas=[];solo=[];usados=set();omisiones=[]
    for r in contraste['publicaciones']:
        if r['resultado'].startswith('DETECTADA'):
            ambas.append(r);usados.update(r['ids_radar']);continue
        host=(urlsplit(r.get('url') or r['evidencia_url']).hostname or '').removeprefix('www.')
        fuentes=[]
        objetivo=urlsplit(r.get('url') or r['evidencia_url'])
        for f in observaciones:
            config=configuradas.get(f.get('id'),{});u=urlsplit(f['url'])
            hosts={(u.hostname or '').removeprefix('www.'),*(h.removeprefix('www.') for h in config.get('dominios_documentos',[]))}
            nombres={o.norm(r.get('organismo')),*[o.norm(a) for a in r.get('organismo_aliases',[])]}
            mismo_org=o.norm(config.get('organismo')) in nombres
            prefijo=u.path.strip('/').split('/')[0];ruta=objetivo.path.strip('/').split('/')[0]
            if host in hosts and (mismo_org or not config or not prefijo or prefijo==ruta):fuentes.append(f)
        if not fuentes:causa='FUENTE_NO_CONSULTADA_EN_ESTE_LOTE';evaluada=False
        elif any(f['estado'] in ('BLOQUEADA','ERROR','NO_INICIADA','TIEMPO_TOTAL') for f in fuentes):causa='ERROR_DE_ACCESO_O_FUENTE_NO_INICIADA';evaluada=any(f.get('iniciada') for f in fuentes)
        elif any(f['estado'] in ('PARCIAL','TIEMPO_FUENTE') for f in fuentes):causa='RECORRIDO_PARCIAL_O_TIEMPO_AGOTADO';evaluada=True
        else:causa='EXTRACCION_NAVEGACION_O_IDENTIDAD_PENDIENTE_DE_AUDITAR';evaluada=True
        if r['resultado']=='AMBIGUA':causa='IDENTIDAD_AMBIGUA_NO_SE_FUERZA_UNIFICACION'
        fila={**r,'causa_probable':causa,'fuente_evaluada_en_lote':evaluada};solo.append(fila)
        if evaluada and r['resultado']=='OMITIDA':omisiones.append(fila)
    return {'fecha':fecha,'solo_automaticas':[r for r in autos if r['id'] not in usados],'solo_manuales':solo,'en_ambas':ambas,'omisiones_comprobadas_en_muestra':omisiones,'manuales_sin_evidencia_suficiente':[r for r in controles if r not in aptas],'resumen':{'automaticas':len(autos),'manuales_con_evidencia':len(aptas),'en_ambas':len(ambas),'solo_automaticas':sum(r['id'] not in usados for r in autos),'solo_manuales':len(solo),'omisiones_en_fuentes_consultadas':len(omisiones),'omisiones_con_revision_reciente':sum(r['evidencia_reciente'] for r in omisiones)},'advertencia':'Causa probable, no diagnóstico confirmado. Fuentes ajenas al lote no se cuentan como omisiones comprobadas; controles antiguos no demuestran omisiones vigentes de hoy.'}

def escribir(d,root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);guardar(root/'comparacion_manual.json',d)
    campos=['organismo','numero_procedimiento','objeto','fecha_publicacion','fecha_apertura','fecha_limite_presentacion','url','evidencia_url','fecha_revision','resultado','causa_probable','fuente_evaluada_en_lote','evidencia_reciente']
    with (root/'omisiones.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=campos,extrasaction='ignore');w.writeheader();w.writerows(d['solo_manuales'])
    (root/'comparacion_manual.md').write_text('# Comparación automática / manual\n\n'+json.dumps(d['resumen'],ensure_ascii=False,indent=2)+'\n\n'+d['advertencia']+'\n\nVéanse comparacion_manual.json y omisiones.csv para todos los registros, sin recortes.\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--automaticas',required=True);p.add_argument('--manuales',required=True);p.add_argument('--salida',default='work/control-manual');p.add_argument('--fecha');a=p.parse_args()
    data=json.loads(Path(a.automaticas).read_text());obs=data.get('observaciones',[]) if isinstance(data,dict) else []
    fecha=a.fecha or (data.get('fecha') if isinstance(data,dict) else None) or o.datetime.now(o.ZONA).isoformat()
    d=comparar(cargar(a.automaticas),cargar(a.manuales),obs,fecha);escribir(d,a.salida);print(json.dumps(d['resumen'],ensure_ascii=False))

if __name__=='__main__':main()
