"""Inventario histórico con validación actual separada; no promueve fuentes."""
import argparse,csv,gzip,json,re,sys
from pathlib import Path
from urllib.parse import urlsplit
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o

def consolidar(historial,capturas,salida):
    root=Path(salida);root.mkdir(parents=True,exist_ok=True)
    historia=json.loads(Path(historial).read_text());filas=historia['fuentes'];indice={r['url']:r for r in filas}
    for ruta in capturas:
        paquete=json.loads(Path(ruta).read_text());obs={r['url']:r for r in paquete['observaciones']}
        for f in paquete['fuentes']:
            u=f['url'];r=indice.get(u)
            if not r:continue
            resultados=[x for x in paquete['registros'] if x.get('fuente')==u and x.get('clasificacion_registro')=='PROCEDIMIENTO']
            actuales=obs.get(u,{})
            r.update(estado_extraccion=actuales.get('estado','PENDIENTE_VALIDACION_ACTUAL'),estado_es_historico=False,
                ultima_revision_efectiva=paquete['fecha'],github_run=paquete.get('run'),
                procedimientos_extraidos=len(resultados),abiertas_extraidas=sum(x.get('vigencia')=='ABIERTA' for x in resultados),
                oportunidades_abiertas_ineditas=None,
                incidencias=actuales.get('errores',[]),
                advertencia='Extraída no implica nueva: comparar contra historial. Estado de la captura, no garantía permanente.')
    fuentes=json.loads(Path('inventario/fuentes.json').read_text());hosts={urlsplit(f['url']).netloc.removeprefix('www.'):f for f in fuentes}
    configuradas={f['url'].rstrip('/') for f in fuentes}
    auto=Path('inventario/fuentes_auto.json')
    if auto.exists():configuradas.update(f['url'].rstrip('/') for f in json.loads(auto.read_text()).get('fuentes',[]))
    normal=lambda u:(urlsplit(u).netloc.removeprefix('www.'),urlsplit(u).path.rstrip('/').lower())
    existentes={normal(u) for u in configuradas};vistos=set()
    candidatos=[]
    for r in filas:
        u=r['url'];p=urlsplit(u);f=hosts.get(p.netloc.removeprefix('www.'))
        # Sólo índices estables en dominios ya asociados a organismos del radar.
        # Los demás permanecen íntegros en el inventario para contraste de identidad.
        if not f or normal(u) in existentes or normal(u) in vistos or r['tipo_url']!='PORTAL_O_SECCION':continue
        if p.query or p.fragment or re.search(r'\d{4}|%7B|%7D|[{},;|]|\\|\.(?:html?|php|aspx|pdf|docx?)$',u,re.I):continue
        if len([x for x in p.path.split('/') if x])>4:continue
        if not re.fullmatch(r'licitaciones(?:-publicas|-privadas)?|compras(?:-y-licitaciones|-y-contrataciones)?|contrataciones|concursos(?:-de-precios|-y-licitaciones)?|boletin(?:-oficial(?:-municipal)?)?|boletin_oficial|index_boletin|precios-y-licitaciones|privada|compras-licitaciones-y-concursos|noticias-compras-y-licitaciones|contratacionesuep|concurso-de-precios',p.path.rstrip('/').split('/')[-1],re.I):continue
        vistos.add(normal(u))
        candidatos.append({'url':u,'organismo':f['organismo'],'localidad':f.get('localidad'),'provincia':f['provincia'],
            'tipo':'TERRITORIAL' if o.norm(f['organismo']).startswith(('municipalidad','comuna')) else 'SECTORIAL',
            'estado':'PENDIENTE','evidencia_descubrimiento':u,
            'evidencia_historial':r['evidencias'][0],
            'motivo_previo':'Ruta histórica de dominio conocido. Exige identidad y extracción actual; no fuente confiable todavía.'})
    (root/'candidatas_historia.json').write_text(json.dumps({'fecha':'2026-11-01','candidatos':candidatos,'criterio':'Sólo índices estables; las fichas/documentos no se convierten en fuentes. Pendiente validación estricta antes de alta.'},ensure_ascii=False,indent=2)+'\n')
    cols=['url','tipo_url','organismo','localidad','provincia','publicaciones','incorporada_exactamente','estado_extraccion','estado_previo','ultima_revision_efectiva','github_run','procedimientos_extraidos','abiertas_extraidas','oportunidades_abiertas_ineditas','registros_historicos_asociados','cantidad_evidencias','incidencias']
    with (root/'inventario_completo.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for r in filas:w.writerow({k:json.dumps(r.get(k),ensure_ascii=False) if isinstance(r.get(k),(list,dict)) else r.get(k) for k in cols})
    (root/'inventario_evidencias.json.gz').write_bytes(gzip.compress(json.dumps(historia,ensure_ascii=False).encode(),mtime=0))
    resumen={**historia['resumen'],'estados_actuales':dict(Counter(r['estado_extraccion'] for r in filas)),'candidatas_para_validacion':len(candidatos),'organismos_identificados':len({(r.get('provincia'),r.get('organismo')) for r in filas if r.get('organismo')}),'advertencia_adicional':'URLs incluyen documentos, avisos y referencias; no equivalen a organismos ni a portales operativos. Metadatos históricos pueden ser candidatos erróneos. Fuentes no probadas quedan pendientes.'}
    (root/'resumen.json').write_text(json.dumps(resumen,ensure_ascii=False,indent=2)+'\n');return resumen
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--historial',required=True);p.add_argument('--captura',action='append',default=[]);p.add_argument('--salida',required=True);a=p.parse_args();print(json.dumps(consolidar(a.historial,a.captura,a.salida),ensure_ascii=False))
