"""Planificación territorial y ventanas recientes; no presupone cobertura ni vigencia."""
from datetime import datetime,timedelta
from pathlib import Path
import json,re
import oportunidades as o

DEPARTAMENTOS_SF=('Belgrano','Caseros','Castellanos','Constitución','Garay','General López','General Obligado','Iriondo','La Capital','Las Colonias','9 de Julio','Rosario','San Cristóbal','San Javier','San Jerónimo','San Justo','San Lorenzo','San Martín','Vera')
BA_PRIORIZADAS=('San Nicolás','Ramallo','San Pedro','Baradero','Arrecifes','Pergamino','Rojas','Colón')

def departamentos():
 return [{'clave':'departamento:Santa Fe:'+o.norm(d),'tipo':'DEPARTAMENTAL','provincia':'Santa Fe','departamento':d,'consulta':'"'+d+'" "Santa Fe" (licitaciones OR "concursos de precios" OR cotizacion) municipio comuna sitio oficial'} for d in DEPARTAMENTOS_SF]

def resultado_pertinente(resultado,objetivo):
 if objetivo.get('metodo')=='ENLACES_OFICIALES':return True
 if objetivo.get('tipo')!='TERRITORIAL' or not objetivo.get('localidad'):return True
 t=o.norm(resultado.get('titulo','')+' '+resultado.get('descripcion',''))
 return bool(re.search(r'\b'+re.escape(o.norm(objetivo['localidad']))+r'\b',t))

def alcance_ba(candidato,padron=None):
 if candidato.get('provincia')!='Buenos Aires':return {'verificado':True,'criterio':'PROVINCIA_DENTRO_DEL_ALCANCE'}
 padron=padron or json.loads(Path('inventario/territorio.json').read_text())
 localidad=o.norm(candidato.get('localidad'))
 m=next((m for m in padron['municipios'] if m['provincia']=='Buenos Aires' and o.norm(m['localidad'])==localidad),None)
 ok=bool(m and m.get('centroide',{}).get('lat') is not None and (localidad in {o.norm(x) for x in BA_PRIORIZADAS} or m.get('distancia_por_ruta_km') is not None and m['distancia_por_ruta_km']<=280))
 return {'verificado':ok,'criterio':'LOCALIDAD_EXPLICITAMENTE_SOLICITADA_Y_PADRON_OFICIAL' if ok and localidad in {o.norm(x) for x in BA_PRIORIZADAS} else 'DISTANCIA_VIAL_DOCUMENTADA' if ok else 'DISTANCIA_VIAL_O_LOCALIDAD_PENDIENTE','codigo':m.get('codigo') if m else None,'centroide':m.get('centroide') if m else None,'distancia_por_ruta_km':m.get('distancia_por_ruta_km') if m else None}

def ventanas(publicacion,ahora):
 if not publicacion:return {'24h':False,'48h':False,'72h':False,'precision':'FECHA_DESCONOCIDA'}
 actual=datetime.fromisoformat(ahora) if isinstance(ahora,str) else ahora
 if not actual.tzinfo:actual=actual.replace(tzinfo=o.ZONA)
 try:d=datetime.fromisoformat(publicacion)
 except ValueError:return {'24h':False,'48h':False,'72h':False,'precision':'FECHA_INVALIDA'}
 if 'T' not in publicacion:
  edad=(actual.astimezone(o.ZONA).date()-d.date()).days
  # Ventanas por días de calendario; sin atribuir una hora inexistente.
  return {'24h':0<=edad<=1,'48h':0<=edad<=2,'72h':0<=edad<=3,'precision':'DIA_CALENDARIO_SIN_HORA'}
 if not d.tzinfo:return {'24h':False,'48h':False,'72h':False,'precision':'HORA_SIN_ZONA'}
 horas=(actual-d).total_seconds()/3600
 return {**{str(n)+'h':0<=horas<=n for n in (24,48,72)},'precision':'INSTANTE_PUBLICADO'}
