"""Informe reproducible de capturas Fase 7 y copia del historial, sin red ni OCR."""
import json,csv,sys,zipfile
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o,incremental as inc
from tools.verificar_fuentes import guardar
from tools.respaldo_piloto import restaurar
from tools.fase2_cerrar import huellas
from calidad_comercial import escribir,presentacion
from informe_descubrimiento import clasificar,escribir as diario
ROOT=Path('informes/2026-11-10-fase7');WORK=Path('work/fase7');

def csvout(nombre,rows,keys):
 with (ROOT/nombre).open('w',newline='') as out:
  w=csv.DictWriter(out,fieldnames=keys);w.writeheader()
  for r in rows:
   fila={k:json.dumps(r.get(k),ensure_ascii=False) if isinstance(r.get(k),(dict,list)) else str(r.get(k) if r.get(k) is not None else 'Pendiente de verificar') for k in keys};w.writerow({k:"'"+v if v.startswith(('=','+','-','@')) else v for k,v in fila.items()})

def main():
 ROOT.mkdir(parents=True,exist_ok=True);antes=huellas();paths=[WORK/'territorial-native/territorial/observadas.json',WORK/'continuacion-native/territorial/continuacion-observadas.json',WORK/'validacion-native/territorial/final-observadas.json'];rs=[];fechas=[]
 for p in paths:
  d=json.load(open(p));rs+=d['registros'];fechas.append(d['fecha'])
 fecha=max(fechas);rs=o.deduplicar(rs,fecha);guardar(ROOT/'fecha_corte.json',{'fecha':fecha,'aclaracion':'Hora argentina del barrido. Las condiciones pueden cambiar después del corte.'})
 # Contraste contra respaldo completo y Fase 5 accesible; sólo sembrar coincidencias,
 # sin volver a procesar miles de textos históricos.
 referencia=json.load(open('work/fase5-cierre/observadas.json'));old=referencia['registros'];nuevosids={r['id'] for r in rs};known={r['id']:r for r in old};coincidencias=[r for r in old if r['id'] in nuevosids]
 copia=WORK/'informe-copia';restaurar('piloto_respaldo/diario',copia);db=inc.abrir(copia/'estado.sqlite3');inicial=db.execute('SELECT COUNT(*) FROM procedimientos').fetchone()[0]
 obs=[]
 for carpeta,sub,nombre in [('territorial-native','territorial/profunda','resultado.json'),('territorial-native','territorial/recuperacion','resultado.json'),('continuacion-native','territorial/continuacion-profunda','resultado.json'),('validacion-native','territorial/validacion-final','resultado.json')]:
  for d in json.load(open(WORK/carpeta/sub/nombre))['fuentes']:obs.append(d['auditoria'])
 obs=list({r['url']:r for r in obs}.values());informe={'ejecucion_id':'fase7-referencia-fase5','actualizado':referencia['fecha'],'estado_ejecucion':'COMPLETADA','observaciones':[],'resumen':{'configuradas':0,'consultadas':0,'finalizadas':0}}
 if coincidencias:inc.registrar(db,coincidencias,informe)
 previas={k:json.loads(v) for k,v in db.execute('SELECT id,dato FROM procedimientos')};previas.update(known)
 informe={**informe,'ejecucion_id':'fase7-cierre-aislado','actualizado':fecha,'observaciones':obs,'resumen':{'configuradas':len(obs),'consultadas':len(obs),'finalizadas':len(obs)}};uno=inc.registrar(db,rs,informe);actuales=inc.actuales(db,fecha,uno['corrida']);eventos=inc.eventos(db,uno['corrida'],fecha);cohorte=[r for r in actuales if r.get('observada_esta_corrida')];grupos=clasificar(cohorte,eventos,fecha,previas,inc.cargar_indice_auditorias());categorias=diario(grupos,fecha,ROOT/'descubrimiento');comercial=escribir(cohorte,fecha,ROOT/'comercial',fuentes=obs);dos=inc.registrar(db,rs,{**informe,'ejecucion_id':'fase7-cierre-repeticion'});db.close()
 # Inventario del nivel rápido; se mantiene la diferencia entre intento, HTML y validación.
 a=json.load(open(WORK/'territorial-native/territorial/rapida/resultado.json'));b=json.load(open(WORK/'continuacion-native/territorial/continuacion-rapida/resultado.json'));rapidas=a['localidades']+b['localidades'];filas=[]
 for r in rapidas:
  filas.append({'id':r['id'],'provincia':r['provincia'],'localidad':r['localidad'],'organismo':r.get('organismo'),'url':r.get('url'),'estado':r['estado'],'consulta_iniciada':bool(r['paginas']),'html_revisado':any(p['estado']=='REVISADA' for p in r['paginas']),'identidad_automatica':r.get('identidad_verificada'),'paginas':len(r['paginas']),'segundos':r.get('segundos'),'prioridad':r.get('prioridad'),'enlaces_candidatos':r.get('enlaces_candidatos'),'documentos':r.get('documentos'),'fecha':r.get('fecha')})
 csvout('cobertura_lote.csv',filas,list(filas[0]));csvout('localidades_sin_revision_efectiva.csv',[r for r in filas if not r['html_revisado']],list(filas[0]));guardar('inventario/fase7_estado.json',{'schema_version':1,'fecha':fecha,'localidades':{r['id']:{k:v for k,v in r.items() if k!='procedimientos_muestra'} for r in rapidas},'cobertura_exhaustiva':False})
 rendimiento=[{'id':r['id'],'url':r['url'],'estado':r['estado'],'duracion_segundos':r.get('duracion_segundos'),'paginas_correctas':r.get('paginas_correctas'),'publicaciones_detectadas':r.get('publicaciones_detectadas'),'timeouts':sum(bool(e.get('timeout')) for e in r.get('errores',[])),'errores_red':sum(e.get('categoria')=='RED' for e in r.get('errores',[])),'errores_extraccion':sum(e.get('categoria')=='EXTRACCION' for e in r.get('errores',[]))} for r in obs];csvout('rendimiento_fuentes.csv',rendimiento,list(rendimiento[0]));guardar(ROOT/'benchmark.json',json.load(open(WORK/'territorial-native/territorial/rendimiento.json')))
 # Campos de pago revisados manualmente, sin convertir contra entrega en pago inmediato.
 manual=json.load(open('inventario/fase7_control_manual.json'))['casos'];csvout('control_documental_manual.csv',manual,['organismo','numero_procedimiento','url','documento','sha256_documento','fecha_hora_limite_presentacion','evidencia_recepcion','forma_pago_revision_manual','modalidad_presentacion','requisito_presentacion','metodo'])
 resumen={'fecha':fecha,'rapida_localidades_programadas':len(rapidas),'sitios_intentados':sum(r['consulta_iniciada'] for r in filas),'localidades_con_html':sum(r['html_revisado'] for r in filas),'identidades_automaticas':sum(r['identidad_automatica'] is True for r in filas),'rapida_segundos':a['resumen']['segundos']+b['resumen']['segundos'],'categorias':categorias,'comercial_muestra':comercial,'coincidencias_catalogo_fase5':len(coincidencias),'registros_respaldo_inicial':inicial,'registros_observados_unicos':len(rs),'primera':uno,'segunda':dos,'protegidos_intactos':antes==huellas(),'ocr_nuevo':0,'nota':'Las dos recepciones de San Salvador se verificaron visualmente en documentos oficiales. No son extracción automática de texto de esos PDF ni publicaciones inéditas.'};guardar(ROOT/'resultado.json',resumen);print(json.dumps(resumen,ensure_ascii=False),flush=True)
 if dos['novedades'] or dos['eventos_emitidos'] or antes!=huellas():raise ValueError('Falló idempotencia o conservación')
if __name__=='__main__':main()
