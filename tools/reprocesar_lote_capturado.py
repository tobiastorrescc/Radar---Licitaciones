"""Reinterpreta una captura real contra el respaldo diario y auditorías, sin red ni OCR."""
import argparse,json,subprocess,sys
from pathlib import Path
from hashlib import sha256
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import incremental as inc
from tools.radar_controlado import generar_informe,huellas_produccion
from tools.auditar_lote_fuentes import estado_revision

def cerrar_barrido(entradas,salida,respaldo='piloto_respaldo/diario'):
    """Reutiliza capturas oficiales: nunca completa una ficha con datos manuales."""
    import extractores,oportunidades as o
    from tools.radar_controlado import ejecutar_corrida,validar_salida
    from tools.respaldo_piloto import restaurar
    root=Path(salida)
    if root.exists():raise ValueError('La copia de contraste debe ser nueva')
    validar_salida(root)
    antes=huellas_produccion();backup=Path(respaldo)
    huellas={p.name:sha256(p.read_bytes()).hexdigest() for p in backup.iterdir() if p.is_file()}
    fuentes={};observaciones={};por_fuente={};capturas={};fechas=[];sin_corregir=[]
    for entrada in entradas:
        origen=Path(entrada);paquete=json.loads(origen.read_text());fechas.append(paquete['fecha'])
        if not sin_corregir:sin_corregir=paquete['registros']
        for f in paquete['fuentes']:
            fuentes[f['url']]=f
            por_fuente[f['url']]=[r for r in paquete['registros'] if r.get('fuente')==f['url']]
        for obs in paquete['observaciones']:observaciones[obs['url']]=obs
        for meta in origen.parent.rglob('capturas/*/*.json'):
            m=json.loads(meta.read_text());txt=meta.with_suffix('.txt');u=extractores.url_publica(m.get('url',''))
            if txt.is_file() and '/inicio/compras-licitaciones/detalle/' in (u or ''):
                capturas[u]=(txt,m,paquete['fecha'],paquete.get('run'))
    fecha=max(fechas);registros=[r for rs in por_fuente.values() for r in rs];releidas=0
    for url,(txt,meta,f,run) in capturas.items():
        matches=[i for i,r in enumerate(registros) if extractores.url_publica(r.get('url',''))==url]
        if not matches:continue # No inventar oportunidades fuera del listado observado.
        nuevos=extractores.extraer(txt.read_text(),url,{'adaptador':'rosario'})[0]
        if not nuevos:continue
        i=matches[0];base=registros[i]
        nuevo=o.normalizar({**{k:base.get(k) for k in ('organismo','localidad','provincia','fuente')},**nuevos[0],
            'evidencia_url':url,'evidencia_captura':{'sha256':meta['sha256'],'fecha_captura':f,'run':run}},fecha)
        registros[i]=o.fusionar(base,nuevo,fecha);releidas+=1
    registros=o.deduplicar(registros,fecha);obs=[]
    for n,(u,s) in enumerate(observaciones.items()):
        checkpoint=root/(str(n)+'-captura.json')
        checkpoint.write_text(json.dumps({'oportunidades':[r for r in registros if r.get('fuente')==u]},ensure_ascii=False)+'\n')
        obs.append({**{k:fuentes[u].get(k) for k in ('organismo','localidad','provincia')},**s,'resultado_archivo':str(checkpoint)})
    informe={'ejecucion_id':'contraste-'+sha256(json.dumps(entradas).encode()).hexdigest()[:16],
        'actualizado':fecha,'estado_ejecucion':'COMPLETADA','observaciones':obs,
        'resumen':{'configuradas':len(obs),'consultadas':len(obs),'finalizadas':len(obs),'fuentes_error_interno':0}}
    piloto=root/'piloto'
    if not restaurar(backup,piloto):raise ValueError('Falta línea de base persistente; no se simula una nueva')
    primera,carpeta,_,_=ejecutar_corrida(piloto,informe_previo=informe)
    segunda,_,_,_=ejecutar_corrida(piloto,informe_previo={**informe,'ejecucion_id':informe['ejecucion_id']+'-replay'})
    import metricas_territoriales as mt
    manual=json.load(open('inventario/auditoria_manual_tres_provincias.json'))
    antes_manual=mt.contraste_manual(manual,sin_corregir,fecha)
    despues_manual=mt.contraste_manual(manual,registros,fecha)
    correcto=segunda['novedades']==0 and not any(segunda['clasificacion'].get(t,0) for t in ('MODIFICADO','DATOS_COMPLETADOS'))
    intacto=antes==huellas_produccion() and huellas=={p.name:sha256(p.read_bytes()).hexdigest() for p in backup.iterdir() if p.is_file()}
    resultado={'fecha_evidencia':fecha,'entradas':entradas,'fuentes_comparadas':len(obs),'registros_observados':len(registros),
        'fichas_releidas_sin_red':releidas,'primera':primera,'segunda':segunda,'repeticion_correcta':correcto,
        'produccion_y_respaldos_intactos':intacto,'consultas_nuevas':0,'ocr_nuevo':0,'informe':str(carpeta/'reporte_diario.md'),
        'muestra_antes':antes_manual,'muestra_despues':despues_manual,
        'alcance':'Capturas del mismo día; conservar errores del último acceso. No acredita cobertura total ni revalidación en vivo de fichas anteriores.'}
    (root/'resultado.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n')
    print('CIERRE_BARRIDO '+json.dumps({k:v for k,v in resultado.items() if not k.startswith('muestra_')},ensure_ascii=False),flush=True)
    if not correcto or not intacto:raise ValueError('Falló continuidad o integridad del contraste')


def main():
    p=argparse.ArgumentParser();p.add_argument('--barrido',action='append');p.add_argument('--salida',default='work/cierre-auditable');p.add_argument('--respaldo',default='piloto_respaldo/diario');a=p.parse_args()
    if a.barrido:return cerrar_barrido(a.barrido,a.salida,a.respaldo)
    origen=Path('work/captura-origen/work/cobertura');meta=json.load(open(origen/'ultima_ejecucion.json'));carpeta=origen/meta['directorio'];informe=json.load(open(carpeta/'verificacion.json'));registros=json.load(open(carpeta/'registros_observados.json'));fuentes=json.load(open(carpeta/'auditoria_fuentes.json'))['fuentes'];root=Path('work/cierre-auditable')
    if root.exists():raise ValueError('La copia de cierre debe ser nueva; no se sobrescribe un historial')
    antes=huellas_produccion();respaldo=Path('piloto_respaldo/diario');huellas={p.name:sha256(p.read_bytes()).hexdigest() for p in respaldo.iterdir() if p.is_file()}
    subprocess.run([sys.executable,'tools/respaldo_piloto.py','restaurar','--salida',str(root),'--respaldo',str(respaldo)],check=True)
    destino=root/'ejecuciones'/'captura-revisada';destino.mkdir(parents=True);informe={**informe,'ejecucion_id':informe['ejecucion_id']+'-contraste-auditorias'}
    db=inc.abrir(root/'estado.sqlite3')
    try:
        primera=inc.registrar(db,registros,informe);eventos=inc.eventos(db,primera['corrida'],primera['fecha'])
        for obs in fuentes:
            obs.update(estado_revision(obs,[r for r in registros if obs['url'] in inc.fuentes_de(r)],[r for r in eventos if obs['url'] in inc.fuentes_de(r)]))
        primera.update(fuentes_configuradas=len(fuentes),fuentes_consultadas=sum(f.get('iniciada',False) for f in fuentes),fuentes_finalizadas=sum(f.get('estado') not in ('NO_INICIADA','EN_CURSO') for f in fuentes))
        primera=generar_informe(db,primera,registros,fuentes,destino)
        segunda=inc.registrar(db,registros,{**informe,'ejecucion_id':informe['ejecucion_id']+'-segunda-sin-red'})
        total=db.execute('SELECT COUNT(*) FROM procedimientos').fetchone()[0]
    finally:db.close()
    for n,dato in [('estados_revision',{'fuentes':fuentes}),('registros_observados',registros),('verificacion',informe)]: (destino/(n+'.json')).write_text(json.dumps(dato,ensure_ascii=False,indent=2)+'\n')
    correcta=segunda['novedades']==0 and not any(segunda['clasificacion'].get(k,0) for k in ('MODIFICADO','DATOS_COMPLETADOS','NUEVO_CONFIRMADO','NUEVA_DETECCION_FECHA_DESCONOCIDA','NUEVA_DETECCION_MISMO_DIA'))
    protegidos=antes==huellas_produccion() and huellas=={p.name:sha256(p.read_bytes()).hexdigest() for p in respaldo.iterdir() if p.is_file()}
    resultado={'origen_run':json.load(open('tools/plan_cobertura.json'))['captura_run'],'fecha_evidencia':informe['actualizado'],'primera':primera,'segunda':segunda,'repeticion_correcta':correcta,'historial_completo_registros':total,'identidades_auditorias_previas':len(inc.cargar_indice_auditorias()),'produccion_y_respaldos_intactos':protegidos,'consultas_nuevas':0,'ocr_nuevo':0}
    (root/'resultado.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n')
    print('CIERRE_CAPTURA '+json.dumps(resultado,ensure_ascii=False),flush=True)
    if not correcta or not protegidos:raise ValueError('La comprobación de continuidad y duplicados requiere revisión')

if __name__=='__main__':main()
