"""Contraste de capturas oficiales con copias de los respaldos; sin red ni OCR."""
import csv,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o
from tools.radar_controlado import fuentes_configuradas
from tools.reprocesar_lote_capturado import cerrar_barrido
from tools.verificar_fuentes import guardar
from tools.revalidar_epe import revalidar
from calidad_comercial import presentacion,escribir
from hashlib import sha256
from collections import Counter

def huellas():
 paths=['radar_estado.json','licitaciones_nuevas.json','licitaciones_nuevas.md','auditoria_fuentes.json','.github/workflows/programar-piloto.yml','.github/workflows/radar-diario.yml']
 paths+=list(map(str,Path('piloto_respaldo').rglob('*')))
 return {p:sha256(Path(p).read_bytes()).hexdigest() for p in paths if Path(p).is_file()}

def metrica(d):
 obs=d['observaciones'];rs=[r for r in d['registros'] if r.get('clasificacion_registro')=='PROCEDIMIENTO']
 estados=Counter('OPERATIVA' if x['estado'] in ('OPERATIVA','SIN_PUBLICACIONES') else 'PARCIAL' if x.get('publicaciones_detectadas',0)>0 else 'PENDIENTE' if x['estado']=='PENDIENTE' else 'INACCESIBLE' for x in obs)
 return {'fuentes_consultadas':len(obs),**dict(estados),'procedimientos':len(rs),'apertura_futura_documental':sum(r.get('vigencia')=='ABIERTA' for r in rs),'recepcion_vigente_comprobada':sum(presentacion(r,d['fecha'])['presentacion_verificada'] for r in rs)}

def main():
 plan=json.load(open('tools/plan_fase2_cierre.json'));root=Path('work/fase2-cierre');antes_h=huellas();permitidas={f['id'] for f in fuentes_configuradas()};entradas=[];base=None;ultimas={};todas={};fecha=None
 for run in plan['runs']:
  for p in sorted((root/'capturas'/str(run)).glob('lote-*/resultado.json')):
   d=json.load(open(p));fecha=max(fecha or d['fecha'],d['fecha']);todas.update({s['id']:{**s,'run':run} for s in d['observaciones']})
   if run==plan['runs'][0]:
    if base is None:base={'fecha':d['fecha'],'fuentes':[],'observaciones':[],'registros':[]}
    for k in ('fuentes','observaciones','registros'):base[k]+=d[k]
   fs=[f for f in d['fuentes'] if f['id'] in permitidas];urls={f['url'] for f in fs};ids={f['id'] for f in fs}
   filtrado={**d,'fuentes':fs,'observaciones':[s for s in d['observaciones'] if s['id'] in ids],'registros':[r for r in d['registros'] if r.get('fuente') in urls]}
   if not fs:continue
   q=p.with_name('resultado-validado.json');guardar(q,filtrado);entradas.append(str(q))
   for f in fs:ultimas[f['id']]={'fuente':f,'observacion':next(s for s in d['observaciones'] if s['id']==f['id']),'registros':[r for r in d['registros'] if r.get('fuente')==f['url']]}
 despues={'fecha':fecha,'fuentes':[x['fuente'] for x in ultimas.values()],'observaciones':[x['observacion'] for x in ultimas.values()],'registros':o.deduplicar([r for x in ultimas.values() for r in x['registros']],fecha)}
 guardar(root/'antes.json',base);guardar(root/'despues.json',despues)
 respaldo=root/'respaldo-inicial';respaldo.mkdir()
 ref=plan['respaldo_inicial'];paths=subprocess.check_output(['git','ls-tree','-r','--name-only',ref,'piloto_respaldo/diario'],text=True).splitlines()
 for p in paths:(respaldo/Path(p).name).write_bytes(subprocess.check_output(['git','show',ref+':'+p]))
 # El historial inicial sirve para medir avance. El actual evita reanunciar lo
 # que el piloto haya registrado mientras se hacía el trabajo.
 cerrar_barrido(entradas,str(root/'contra-inicial'),str(respaldo))
 cerrar_barrido(entradas,str(root/'contra-actual'),'piloto_respaldo/diario')
 cierres={k:json.load(open(root/('contra-'+k)/'resultado.json')) for k in ('inicial','actual')}
 for k,v in cierres.items():guardar(root/('cierre-'+k+'.json'),v)
 control=json.load(open('inventario/control_rosario_fase2.json'))['publicaciones'];m={r['url'] for r in control}
 def rosario(d):return {r['url'] for r in d['registros'] if r.get('organismo')=='Municipalidad de Rosario'}
 old,new=rosario(base),rosario(despues);comparacion={'muestra':len(m),'antes':len(old&m),'despues':len(new&m),'omisiones_antes':sorted(m-old),'omisiones_despues':sorted(m-new),'omisiones_recuperadas':sorted((new-old)&m),'advertencia':'Muestra oficial del 7/11; no porcentaje territorial global ni publicaciones nuevas por esa sola diferencia.'};guardar(root/'rosario.json',comparacion)
 # Conservar ejemplos de negocio y eventos separados, sin recortar cantidades.
 for k in ('inicial','actual'):
  carpeta=sorted((root/('contra-'+k)/'piloto/ejecuciones').glob('*'))[0]
  eventos=json.load(open(carpeta/'eventos.json'))['oportunidades']
  nuevas=[r for r in eventos if r.get('clasificacion_novedad')=='NUEVO_CONFIRMADO' and presentacion(r,fecha)['presentacion_verificada']]
  guardar(root/('nuevas-vigentes-'+k+'.json'),{'fecha':fecha,'total':len(nuevas),'oportunidades':nuevas})
 resumen={'fecha':fecha,'base_commit':ref,'antes':metrica(base),'despues':metrica(despues),'configuradas_antes':88,'configuradas_despues':len(permitidas),'fuentes_unicas_auditadas':len(todas),'rosario':comparacion,'continuidad':{k:{'primera':v['primera']['clasificacion'],'segunda_novedades':v['segunda']['novedades'],'segunda_eventos':v['segunda']['eventos_emitidos'],'registros_historial':v['segunda']['total_historial'],'correcta':v['repeticion_correcta']} for k,v in cierres.items()},'protegidos_intactos':antes_h==huellas(),'ocr_nuevo':0,'advertencia':'Fuentes nuevas con antecedentes no equivalen a publicaciones nuevas comerciales; ver eventos y fechas comprobadas.'}
 guardar(root/'resultado.json',resumen);guardar(root/'fuentes_auditadas.json',list(todas.values()))
 epe=revalidar(json.load(open('inventario/epe_17_control.json'))['casos'],despues['registros'],despues['observaciones'],fecha);guardar(root/'epe_17.json',epe)
 escribir(despues['registros'],fecha,root/'comercial',fuentes=despues['observaciones'])
 print('FASE2_CIERRE '+json.dumps(resumen,ensure_ascii=False),flush=True)
 if not resumen['protegidos_intactos'] or not all(v['correcta'] for v in resumen['continuidad'].values()):raise ValueError('No se comprobó integridad o ausencia de repeticiones')
if __name__=='__main__':main()
