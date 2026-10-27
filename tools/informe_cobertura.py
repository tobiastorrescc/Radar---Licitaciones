"""Cobertura desde publicaciones auditadas; un inventario no prueba funcionamiento."""
import argparse
from collections import Counter
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o

def estado_cobertura(observacion,registros):
    validos=[r for r in registros if r.get('clasificacion_registro')=='PROCEDIMIENTO']
    completos=[r for r in validos if r.get('objeto') and r.get('detalle_completo')]
    estado=observacion.get('estado')
    if estado=='BLOQUEADA':return 'BLOQUEADA'
    if completos and estado=='OPERATIVA':return 'OPERATIVA'
    if validos:return 'PARCIAL'
    if estado=='SIN_PUBLICACIONES':return 'SIN_PUBLICACIONES_CONFIRMADO'
    return 'PENDIENTE'

def generar(informe='work/verificacion/verificacion.json',salida='work/verificacion/cobertura',padron='work/verificacion/territorio.json'):
    fuente=Path(informe);datos=json.loads(fuente.read_text())
    observadas={r['id']:r for r in datos['observaciones']}
    fs=json.loads(Path('inventario/fuentes.json').read_text())
    base=set(json.loads(Path('inventario/base_36.json').read_text())['ids'])
    territorio=json.loads(Path(padron).read_text()) if Path(padron).is_file() else json.loads(Path('inventario/territorio.json').read_text())
    estados=[];ejemplos=[]
    for f in fs:
        obs=observadas.get(f['id'],{});ruta=Path(obs.get('resultado_archivo',''))
        if not ruta.is_file() and 'verificacion_ejecuciones' in ruta.parts:
            ruta=fuente.parent/Path(*ruta.parts[ruta.parts.index('verificacion_ejecuciones'):])
        registros=[o.normalizar(r,datos['actualizado']) for r in json.loads(ruta.read_text()).get('oportunidades',[])] if ruta.is_file() else []
        estado=estado_cobertura(obs,registros)
        val=[r for r in registros if r['clasificacion_registro']=='PROCEDIMIENTO']
        estados.append({'id':f['id'],'organismo':f['organismo'],'localidad':f['localidad'],'provincia':f['provincia'],'url':f['url'],'tipo_portal':f['tipo_portal'],'incorporada':f['incorporada'],'nueva':f['id'] not in base,'estado':estado,'estado_conector':obs.get('estado','NO_CONSULTADA'),'publicaciones_detectadas':len(registros),'procedimientos_verificados':len(val),'con_objeto':sum(bool(r.get('objeto')) for r in val),'errores':obs.get('errores',[]),'resultado_archivo':str(ruta) if ruta.is_file() else None})
        if f['id'] not in base:
            for r in sorted(val,key=lambda r:(not bool(r.get('objeto')),r['vigencia']!='ABIERTA',r.get('fecha_apertura') is None)):
                ejemplos.append({'fuente_id':f['id'],**{k:r.get(k) for k in ('organismo','localidad','provincia','numero_procedimiento','tipo_procedimiento','objeto','fecha_apertura','fecha_publicacion','vigencia','url','evidencia_url','documentos','condiciones_pago')}})
    por_id={f['id']:f for f in estados};municipios=[]
    for m in territorio.get('municipios',[]):
        directas=[f for f in estados if f['provincia']==m['provincia'] and o.norm(f.get('localidad'))==o.norm(m['localidad']) and (o.norm(f['organismo']).startswith(('municipalidad','comuna','gobierno de timbues')))]
        municipios.append({**m,'fuentes_directas':[f['id'] for f in directas],'estados_fuentes':dict(Counter(f['estado'] for f in directas)),'estado_cobertura':'CON_PUBLICACIONES_COMPROBADAS' if any(f['estado']=='OPERATIVA' for f in directas) else ('PARCIAL' if any(f['estado']=='PARCIAL' for f in directas) else 'PENDIENTE')})
    nuevas=[f for f in estados if f['nueva']];resumen={'fecha':datos['actualizado'],'github_run_id':datos.get('github_run_id'),'revision':datos.get('revision'),'organismos_inventariados':len({(f['provincia'],f['organismo']) for f in fs}),'portales_inventariados':len(fs),'fuentes_incorporadas':sum(f['incorporada'] for f in fs),'base_conservada':all(por_id[i]['incorporada'] for i in base),'fuentes_nuevas':len(nuevas),'nuevas_incorporadas':sum(f['incorporada'] for f in nuevas),'estados_nuevas':dict(Counter(f['estado'] for f in nuevas)),'estados_total':dict(Counter(f['estado'] for f in estados)),'territorio_padron':dict(Counter(m['provincia'] for m in municipios)),'territorio_con_portal_operativo':dict(Counter(m['provincia'] for m in municipios if m['estado_cobertura']=='CON_PUBLICACIONES_COMPROBADAS')),'cobertura_completa':False}
    destino=Path(salida);destino.mkdir(parents=True,exist_ok=True)
    (destino/'auditoria_cobertura.json').write_text(json.dumps({'resumen':resumen,'fuentes':estados,'municipios':municipios,'ejemplos_fuentes_nuevas':ejemplos},ensure_ascii=False,indent=2)+'\n')
    lineas=['# Cobertura territorial auditada','',f"Ejecución {resumen['github_run_id']}; observación {resumen['fecha']}.",'','No se declara cobertura completa. Los gobiernos locales sin portal o sin extracción comprobada permanecen pendientes. Las 36 fuentes anteriores se conservan.','',f"Organismos: {resumen['organismos_inventariados']}; portales: {len(fs)}; incorporadas: {resumen['fuentes_incorporadas']}.",f"Fuentes adicionales a la base: {len(nuevas)}; estados: {resumen['estados_nuevas']}.",'','Operativa requiere procedimientos identificados con objeto recuperado y conector finalizado sin incidencias. Parcial conserva procedimientos y sus incidencias. Vacío confirmado no se cuenta como operativa con publicaciones.','', '| Organismo | Provincia | Nueva | Estado | Procedimientos | URL |','|---|---|---|---|---:|---|']
    lineas.extend(f"| {f['organismo']} | {f['provincia']} | {'Sí' if f['nueva'] else 'No'} | {f['estado']} | {f['procedimientos_verificados']} | [Portal]({f['url']}) |" for f in estados)
    lineas+=['','## Padrón territorial','',territorio.get('advertencia','Padrón pendiente de comprobar.'),'',f"Registros por provincia: {resumen['territorio_padron']}",f"Con portal directo operativo observado: {resumen['territorio_con_portal_operativo']}",'','Cada municipio/comuna pendiente está enumerado en el JSON. Los organismos sectoriales y boletines complementarios no se contabilizan como un portal municipal propio. El radio bonaerense es geodésico y no certifica trayectos viales de 280 km.','', '## Preservación y próximos lotes','','Se conservan historial, todas las novedades, pago comprobado/desconocido y llamados especiales. No hay filtros de monto, rubro, modalidad o viabilidad, ni cálculos de rentabilidad o búsqueda de proveedores.','', 'Continuar con endpoints públicos dinámicos, PDF/OCR, paginación restante, municipios sin portal y padrón sectorial de hospitales/SAMCo, universidades y entes. Cada incorporación exige evidencia de publicaciones.']
    (destino/'INFORME_COBERTURA.md').write_text('\n'.join(lineas)+'\n')
    print('COBERTURA_RESUMEN '+json.dumps(resumen,ensure_ascii=False),flush=True)
    vistos=set()
    for e in ejemplos:
        if e['fuente_id'] in vistos:continue
        vistos.add(e['fuente_id']);print('EJEMPLO_FUENTE_NUEVA '+json.dumps(e,ensure_ascii=False),flush=True)
    return resumen

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--informe',default='work/verificacion/verificacion.json');p.add_argument('--salida',default='work/verificacion/cobertura');p.add_argument('--padron',default='work/verificacion/territorio.json');a=p.parse_args();generar(a.informe,a.salida,a.padron)
