"""Reinterpreta una captura real contra el respaldo diario y auditorías, sin red ni OCR."""
import json,subprocess,sys
from pathlib import Path
from hashlib import sha256
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import incremental as inc
from tools.radar_controlado import generar_informe,huellas_produccion
from tools.auditar_lote_fuentes import estado_revision


def main():
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
