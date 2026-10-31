"""Entrega completa del lote auditado: captura real + catálogo previo, sin red/OCR."""
import argparse,csv,json,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o,incremental as inc
from tools.comparar_barrido import comparar


def guardar_csv(path,filas,campos):
    campos=list(dict.fromkeys(campos))
    with Path(path).open('w',encoding='utf-8-sig',newline='') as archivo:
        w=csv.DictWriter(archivo,fieldnames=campos);w.writeheader()
        for f in filas:w.writerow({k:json.dumps(f[k],ensure_ascii=False) if isinstance(f.get(k),(dict,list)) else f.get(k) for k in campos})


def generar(base,captura,complementos,salida,comparativo=None):
    catalogo=json.load(open(base))['oportunidades'];registros=[];fuentes={};observaciones={}
    for path in [*complementos,captura]:
        d=json.load(open(path));urls={f['url'] for f in d['fuentes']}
        registros=[r for r in registros if r.get('fuente') not in urls]+d['registros']
        for f in d['fuentes']:fuentes[f['id']]=f
        for f in d['observaciones']:observaciones[f['id']]=f
    resultado=comparar({'registros':catalogo},{'registros':registros,'fecha':d['fecha']},catalogo)
    rs=resultado['oportunidades'];root=Path(salida);root.mkdir(parents=True,exist_ok=True)
    campos=['comparacion_categoria','organismo','localidad','provincia','numero_procedimiento','tipo_procedimiento','objeto','fecha_publicacion','fecha_limite_presentacion','hora_limite_presentacion','fecha_apertura','hora_apertura','vigencia','presupuesto','condiciones_pago','enlace_condiciones_pago','segundo_llamado','reapertura','url','enlace_pliego','documentos','fuentes_observadas','primera_deteccion']
    guardar_csv(root/'publicaciones_completas.csv',rs,campos)
    nuevas=[r for r in rs if r['comparacion_categoria']=='VIGENTE_NUEVA_PARA_RADAR']
    conocidas=[r for r in rs if r['comparacion_categoria']=='VIGENTE_YA_CONOCIDA']
    guardar_csv(root/'abiertas_ineditas.csv',nuevas,campos)
    guardar_csv(root/'abiertas_comprobadas.csv',nuevas+conocidas,campos)
    pendientes=[r for r in registros if r.get('clasificacion_registro')!='PROCEDIMIENTO']
    guardar_csv(root/'avisos_pendientes_validacion.csv',pendientes,campos)
    filas=[]
    for id,f in fuentes.items():
        obs=observaciones[id];extr=[r for r in rs if f['url'] in inc.fuentes_de(r)];errores=obs.get('errores',[])
        estado='PARCIAL' if obs['estado'] in ('PARCIAL','TIEMPO_FUENTE','TIEMPO_TOTAL') and extr else ('PENDIENTE' if obs['estado'] in ('TIEMPO_FUENTE','TIEMPO_TOTAL') else obs['estado'])
        filas.append({'id':id,'organismo':f.get('organismo',obs.get('organismo')),'localidad':f.get('localidad'),'provincia':f.get('provincia'),'url':f['url'],'estado':estado,'identificada':True,'accesible':obs.get('paginas_correctas',0)>0,'navegacion_funcional':obs.get('paginas_correctas',0)>1,'extraccion_comprobada':bool(extr),'convocatorias_abiertas':sum(r['vigencia']=='ABIERTA' for r in extr),'procedimientos':len(extr),'errores':errores,'limites':obs.get('limites',[]),'paginas_correctas':obs.get('paginas_correctas',0),'fecha':d['fecha']})
    columnas=['id','organismo','localidad','provincia','url','estado','identificada','accesible','navegacion_funcional','extraccion_comprobada','convocatorias_abiertas','procedimientos','paginas_correctas','errores','limites','fecha']
    guardar_csv(root/'cobertura_fuentes.csv',filas,columnas)
    guardar_csv(root/'fuentes_pendientes.csv',[f for f in filas if f['estado']!='OPERATIVA'],columnas)
    if comparativo:
        control=json.load(open(comparativo));eventos=json.load(open(Path(control['informe']).parent/'eventos.json'))['oportunidades']
        guardar_csv(root/'eventos_piloto_completos.csv',eventos,['clasificacion_novedad','primera_deteccion','ultima_observacion',*campos])
    resumen={'fecha':d['fecha'],'linea_base':'bd28813 / Actions 41213570935','fuentes_auditadas':len(filas),'estados':dict(Counter(f['estado'] for f in filas)),'procedimientos_extraidos':len(rs),'abiertas_comprobadas_en_muestra':len(nuevas)+len(conocidas),'avisos_pendientes_validacion':len(pendientes),'categorias':resultado['categorias'],'abiertas':len(nuevas)+len(conocidas),'abiertas_nuevas':len(nuevas),'abiertas_conocidas':len(conocidas),'vencidas':sum(r['vigencia']=='VENCIDA' for r in rs),'vigencia_desconocida':sum(r['vigencia']=='DESCONOCIDA' for r in rs),'cobertura_muestra_abiertas_antes':len(conocidas),'cobertura_muestra_abiertas_despues':len(nuevas)+len(conocidas),'advertencia':'Muestra de avisos recuperados y comprobados; no es un censo independiente exhaustivo ni cobertura territorial global. Nueva para el radar no equivale a fecha de publicación nueva comprobada.','recortes':False,'ocr_nuevo':0}
    (root/'resumen.json').write_text(json.dumps(resumen,ensure_ascii=False,indent=2)+'\n')
    (root/'evidencia_abiertas.json').write_text(json.dumps(nuevas+conocidas,ensure_ascii=False,indent=2)+'\n')
    return resumen

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--captura',required=True);p.add_argument('--complemento',action='append',default=[]);p.add_argument('--salida',required=True);p.add_argument('--comparativo');a=p.parse_args()
    print(json.dumps(generar(a.base,a.captura,a.complemento,a.salida,a.comparativo),ensure_ascii=False))
