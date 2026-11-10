"""Descubrir avisos HTML y enriquecer sólo convocatorias ya extraídas."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.fase7_barrido import validar,ROOT
from tools.verificar_fuentes import ejecutar,guardar
from tools.radar_controlado import fuentes_configuradas,registros_checkpoint
from tools.fase2_cerrar import huellas
import oportunidades as o
from calidad_comercial import escribir

def main():
 antes=huellas();cs=json.load(open('tools/plan_fase7_final.json'))['fuentes'];ds,inf=validar(cs,'validacion-final',segundos=40,total=150);auto=json.load(open('inventario/fuentes_auto.json'));prev={f['url'] for f in fuentes_configuradas()};altas=[]
 for d in ds:
  c=d['candidato'];r=d['resultado'];v=r.get('validacion',{})
  if d['auditoria']['estado']=='OPERATIVA' and v.get('estado')=='VALIDADA' and c['url'] not in prev:
   item={'id':'auto-'+c['id'],'url':c['url'],'config':r['config'],'validacion':v,'origen_busqueda':c.get('identidad_url') or c['url']};auto['fuentes'].append(item);altas.append(item);prev.add(c['url'])
 guardar('inventario/fuentes_auto.json',auto);guardar(ROOT/'final-altas.json',altas)
 fs=[{**f,'solo_descubrimiento':True,'ocr':False,'tiempo_maximo_fuente_segundos':40} for f in fuentes_configuradas() if f['id'] in {a['id'] for a in altas}];ic=ejecutar(fs,ROOT/'final-catalogo.json',concurrencia=3,por_fuente=40,total=100) if fs else {'actualizado':inf['actualizado'],'observaciones':[]}
 rs=[]
 for d in ds:rs += [o.normalizar({**r,'fuente':d['candidato']['url']},inf['actualizado']) for r in d['resultado'].get('oportunidades',[])]
 rs=o.deduplicar(rs+registros_checkpoint(ic),inf['actualizado']);controles=[]
 for e in json.load(open('inventario/fase7_control_manual.json'))['casos']:
  encontrados=[r for r in rs if r['url']==e['url'] and r['numero_procedimiento']==e['numero_procedimiento'] and r['tipo_procedimiento']==e['tipo_procedimiento']]
  for r in encontrados:r.update(fecha_limite_presentacion_texto=e['fecha_hora_limite_presentacion'],evidencia_recepcion={**e['evidencia_recepcion'],'sha256':e['sha256_documento'],'metodo':e['metodo']},modalidad_presentacion=e['modalidad_presentacion'],enlace_pliego=e['documento'],recepcion_verificada_manualmente=True)
  controles.append({'url':e['url'],'procedimiento':e['numero_procedimiento'],'detectada_automaticamente':bool(encontrados),'revalidacion_manual':bool(encontrados)})
 rs=[o.normalizar(r,inf['actualizado']) for r in rs];guardar(ROOT/'final-observadas.json',{'fecha':inf['actualizado'],'registros':rs});cc=escribir(rs,inf['actualizado'],ROOT/'final-comercial',fuentes=inf['observaciones']+ic['observaciones'])
 guardar(ROOT/'final-resumen.json',{'fecha':inf['actualizado'],'fuentes':[{k:d['auditoria'].get(k) for k in ['id','url','estado','duracion_segundos','paginas_correctas','publicaciones_detectadas','errores']} for d in ds],'altas':len(altas),'consulta_catalogo':ic['observaciones'],'control_manual':controles,'comercial':cc,'protegidos_intactos':antes==huellas()})
 if antes!=huellas():raise ValueError('Archivos protegidos alterados')
if __name__=='__main__':main()
