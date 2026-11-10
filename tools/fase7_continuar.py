"""Continuación acotada: no repetir las 47 localidades ya intentadas."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.fase7_barrido import validar,ROOT
from descubrimiento_rapido import ejecutar as rapido
from tools.verificar_fuentes import ejecutar,guardar
from tools.radar_controlado import fuentes_configuradas,registros_checkpoint
from tools.fase2_cerrar import huellas
from calidad_comercial import escribir
import oportunidades as o

def main():
 antes=huellas();p=json.load(open('tools/plan_fase7_continuacion.json'));actuales=fuentes_configuradas();by={f['url']:f for f in actuales};inicio={f['url'] for f in actuales}
 cs=[c for c in p['nuevas'] if not any(f['provincia']==c['provincia'] and o.norm(f['localidad'])==o.norm(c['localidad']) for f in actuales)]
 rr,res=rapido(cs,ROOT/'continuacion-rapida',ROOT/'continuacion-estado.json',concurrencia=4)
 nuevos=[{**c,'config_publica':{'noticias_comunales':True,'documentos_para_descubrimiento':True,'foco_listado_actual':True}} for c in cs if next(r for r in rr if r['id']==c['id']).get('identidad_verificada')]
 ds,inf=validar(p['fuentes']+nuevos,'continuacion-profunda',segundos=55,total=180);auto=json.load(open('inventario/fuentes_auto.json'));altas=[]
 for d in ds:
  c=d['candidato'];r=d['resultado'];v=r.get('validacion',{})
  if d['auditoria']['estado']=='OPERATIVA' and v.get('estado')=='VALIDADA' and c['url'] not in inicio:
   a={'id':'auto-'+c['id'],'url':c['url'],'config':r['config'],'validacion':v,'origen_busqueda':c.get('identidad_url') or c['url']};auto['fuentes'].append(a);altas.append(a);inicio.add(c['url'])
 guardar('inventario/fuentes_auto.json',auto);guardar(ROOT/'continuacion-altas.json',altas)
 fs=[{**f,'solo_descubrimiento':True,'ocr':False,'tiempo_maximo_fuente_segundos':55} for f in fuentes_configuradas() if f['id'] in {a['id'] for a in altas}];ic=ejecutar(fs,ROOT/'continuacion-catalogo.json',concurrencia=3,por_fuente=55,total=120) if fs else {'actualizado':inf['actualizado'],'observaciones':[]}
 rs=[]
 for d in ds:
  rs += [o.normalizar({**r,'fuente':d['candidato']['url']},inf['actualizado']) for r in d['resultado'].get('oportunidades',[])]
 rs=o.deduplicar(rs+registros_checkpoint(ic),inf['actualizado']);guardar(ROOT/'continuacion-observadas.json',{'fecha':inf['actualizado'],'registros':rs});cc=escribir(rs,inf['actualizado'],ROOT/'continuacion-comercial',fuentes=inf['observaciones']+ic['observaciones'])
 guardar(ROOT/'continuacion-resumen.json',{'rapida':res,'altas':len(altas),'consulta_catalogo':ic['observaciones'],'fuentes_profundas':[{'localidad':d['candidato']['localidad'],'url':d['candidato']['url'],'estado':d['auditoria']['estado'],'publicaciones':len(d['resultado'].get('oportunidades',[]))} for d in ds],'comercial':cc,'protegidos_intactos':antes==huellas()})
 if antes!=huellas():raise ValueError('Cambió un archivo protegido')
if __name__=='__main__':main()
