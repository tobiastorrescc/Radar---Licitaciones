"""Informe diario A/B/C/D, con recepción comprobada y sin recorte comercial."""
import csv,json
from pathlib import Path
from datetime import datetime
import oportunidades as o
from calidad_comercial import presentacion
from descubrimiento_territorial import ventanas
from fuentes_fase4 import naturaleza_convocatoria

CAMPOS=('organismo','provincia','localidad','numero_procedimiento','objeto','presupuesto','fecha_publicacion','primera_deteccion','ultima_deteccion','fecha_limite_presentacion','fecha_hora_limite_presentacion','condiciones_pago','modalidad_presentacion','url','enlace_pliego','urgencia','logistica_presencial')

def urgencia(r,fecha):
 limite=presentacion(r,fecha)['limite_presentacion_comprobado']
 if not limite or 'T' not in limite:return 'HORA_LIMITE_PENDIENTE'
 dt=datetime.fromisoformat(limite);ahora=datetime.fromisoformat(fecha)
 if not dt.tzinfo:dt=dt.replace(tzinfo=o.ZONA)
 if not ahora.tzinfo:ahora=ahora.replace(tzinfo=o.ZONA)
 h=(dt-ahora).total_seconds()/3600
 return 'VENCIDA' if h<=0 else 'MENOS_24H' if h<24 else '24_A_48H' if h<48 else '48H_A_7DIAS' if h<=168 else 'MAS_7DIAS'

def clasificar(actuales,eventos,fecha,previas,referencias=()):
 grupos={k:[] for k in ('A_PUBLICACIONES_NUEVAS_VIGENTES','B_VIGENTES_DESCONOCIDAS','C_CONOCIDAS_RECUPERADAS','D_PENDIENTES','VENTAS_MUNICIPALES','CONOCIDAS_VIGENTES')};por_id={r['id']:r for r in eventos}
 for r in actuales:
  r={**r,'ventanas_publicacion':ventanas(r.get('fecha_publicacion'),fecha),'urgencia':urgencia(r,fecha),'logistica_presencial':'PRESENCIAL' in (r.get('modalidad_presentacion') or [])}
  if not presentacion(r,fecha)['presentacion_verificada']:
   if r.get('vigencia')!='VENCIDA':grupos['D_PENDIENTES'].append(r)
   continue
  if naturaleza_convocatoria(r)=='VENTA_BIENES_PUBLICOS':grupos['VENTAS_MUNICIPALES'].append(r);continue
  ids=r.get('ids_historial',[r['id']]);conocida=any(i in previas or i in referencias for i in ids)
  ev=next((por_id[i] for i in ids if i in por_id),{})
  if not conocida and ev.get('clasificacion_novedad') in ('NUEVO_CONFIRMADO','NUEVA_DETECCION_MISMO_DIA','NUEVA_DETECCION_FECHA_DESCONOCIDA','RECUPERACION_LINEA_BASE'):
   grupo='A_PUBLICACIONES_NUEVAS_VIGENTES' if r['ventanas_publicacion']['168h'] else 'B_VIGENTES_DESCONOCIDAS'
  elif any(i in previas and not presentacion({**previas[i],'observada_esta_corrida':True},fecha)['presentacion_verificada'] for i in ids):grupo='C_CONOCIDAS_RECUPERADAS'
  else:grupo='CONOCIDAS_VIGENTES'
  grupos[grupo].append(r)
 return {k:sorted(rs,key=o.prioridad) for k,rs in grupos.items()}

def escribir(grupos,fecha,destino):
 root=Path(destino);root.mkdir(parents=True,exist_ok=True);md=['# Descubrimiento diario', '',fecha,'','Todas las oportunidades sin top-N; ventas municipales y pendientes separados.'];resumen={k:len(v) for k,v in grupos.items()}
 for nombre,rs in grupos.items():
  filas=[{k:r.get(k) for k in CAMPOS} for r in rs]
  (root/(nombre+'.json')).write_text(json.dumps({'fecha':fecha,'total':len(rs),'oportunidades':filas},ensure_ascii=False,indent=2)+'\n')
  with (root/(nombre+'.csv')).open('w',newline='') as out:
   w=csv.DictWriter(out,fieldnames=CAMPOS);w.writeheader()
   for r in filas:
    fila={k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else str(v or 'Pendiente de verificar') for k,v in r.items()};w.writerow({k:"'"+v if v.startswith(('=','+','-','@')) else v for k,v in fila.items()})
  md+=['','## '+nombre+' ('+str(len(rs))+')','']+[f"- {r.get('organismo')}: {r.get('objeto')} — cierre {r.get('fecha_hora_limite_presentacion') or r.get('fecha_limite_presentacion') or 'pendiente'}; {r.get('urgencia')}; {'PRESENCIAL; evaluar logística' if r.get('logistica_presencial') else 'modalidad '+str(r.get('modalidad_presentacion') or 'pendiente')}; [aviso oficial]({r['url']})" for r in rs]
 (root/'informe.md').write_text('\n'.join(md)+'\n');(root/'resumen.json').write_text(json.dumps(resumen,ensure_ascii=False,indent=2)+'\n');return resumen

def desde_db(db,actuales,eventos,fecha,corrida,destino):
 previas={}
 for id,dato in db.execute('SELECT procedimiento,dato FROM versiones WHERE corrida<>? ORDER BY fecha DESC',(corrida,)):previas.setdefault(id,json.loads(dato))
 import incremental as inc
 return escribir(clasificar(actuales,eventos,fecha,previas,inc.cargar_indice_auditorias()),fecha,destino)
