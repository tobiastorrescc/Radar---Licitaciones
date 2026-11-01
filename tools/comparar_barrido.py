"""Compara capturas reales y ensaya el informe contra una copia del respaldo; sin red/OCR."""
import argparse,json,sys
from pathlib import Path
from collections import Counter
from hashlib import sha256
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o,incremental as inc
from tools.radar_controlado import ejecutar_corrida,huellas_produccion
from tools.respaldo_piloto import restaurar

def comparar(antes,despues,catalogo):
    previos={o.identidad(r) for r in catalogo}|set(inc.cargar_indice_auditorias());urls={(r.get('url'),o.procedimiento_canonico(r) or o.norm(r.get('titulo'))) for r in catalogo}
    anteriores={o.identidad(r) for r in antes['registros']}
    salida=[];publicaciones={};indice=o.indice_complementarias(catalogo)
    for r in despues['registros']:
        if r.get('clasificacion_registro')!='PROCEDIMIENTO':continue
        clave=(r.get('url'),o.procedimiento_canonico(r) or o.norm(r.get('titulo')),o.norm(r.get('organismo')))
        publicaciones[clave]=o.fusionar(publicaciones.get(clave),r,despues.get('fecha'))
    for r in publicaciones.values():
        if r.get('clasificacion_registro')!='PROCEDIMIENTO':continue
        antecedente=o.antecedente_complementario(r,o.candidatos_complementarios(r,indice))
        conocida=bool(antecedente) or o.identidad(r) in previos or (r.get('url'),o.procedimiento_canonico(r) or o.norm(r.get('titulo'))) in urls
        categoria=('VIGENTE_YA_CONOCIDA' if conocida else 'VIGENTE_NUEVA_PARA_RADAR') if r.get('vigencia')=='ABIERTA' else 'HISTORICA_RECUPERADA' if r.get('vigencia')=='VENCIDA' and not conocida else 'FECHA_O_VIGENCIA_PENDIENTE' if not conocida else 'YA_CONOCIDA_NO_ABIERTA'
        salida.append({**r,'comparacion_categoria':categoria,'detectada_barrido_inicial':o.identidad(r) in anteriores,'ya_catalogada':conocida})
    return {'categorias':dict(Counter(r['comparacion_categoria'] for r in salida)),'antes':len(antes['registros']),'despues':len(despues['registros']),'oportunidades':salida}

def main():
    p=argparse.ArgumentParser();p.add_argument('--antes',required=True);p.add_argument('--despues',required=True);p.add_argument('--catalogo',required=True);p.add_argument('--salida',required=True);p.add_argument('--complemento',action='append',default=[]);p.add_argument('--base-auditada',action='store_true');a=p.parse_args()
    antes=json.loads(Path(a.antes).read_text());despues=json.loads(Path(a.despues).read_text());cat=json.loads(Path(a.catalogo).read_text())['oportunidades'];root=Path(a.salida);root.mkdir(parents=True,exist_ok=False)
    # Los complementos son capturas anteriores de otras fuentes, sin reconsultarlas.
    paquetes=[(Path(p).parent,json.loads(Path(p).read_text())) for p in a.complemento]+[(Path(a.despues).parent,despues)]
    registros=[];observaciones={};fuentes={}
    for origen,paquete in paquetes:
        urls={f['url'] for f in paquete['fuentes']}
        registros=[r for r in registros if r.get('fuente') not in urls]+paquete['registros']
        for f in paquete['fuentes']:fuentes[f['url']]=f
        verificacion=json.loads((origen/'verificacion.json').read_text())
        for obs in verificacion['observaciones']:
            obs=dict(obs);original=obs.get('resultado_archivo')
            if original:obs['resultado_archivo']=str(origen/str(original).split('work/barrido/',1)[-1])
            observaciones[obs['url']]=obs
    # La captura conserva jurisdicción aun para rutas complementarias que no
    # forman parte del inventario diario de conectores independientes.
    observaciones={u:{**{k:fuentes.get(u,{}).get(k) for k in ('organismo','localidad','provincia')},**obs} for u,obs in observaciones.items()}
    despues={**despues,'registros':registros,'fuentes':list(fuentes.values())}
    resultado=comparar(antes,despues,cat)
    (root/'comparacion.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n')
    # Sólo se reparan rutas de la captura copiada. Ninguna solicitud a sitios.
    informe={**verificacion,'observaciones':list(observaciones.values()),'resumen':{**verificacion['resumen'],'configuradas':len(observaciones),'consultadas':len(observaciones),'finalizadas':len(observaciones)}}
    protegidos=huellas_produccion();backup={p.name:sha256(p.read_bytes()).hexdigest() for p in Path('piloto_respaldo/diario').iterdir() if p.is_file()}
    piloto=root/'piloto';restaurar('piloto_respaldo/diario',piloto)
    if a.base_auditada:
        # Copia de trabajo: todas las observaciones de la auditoría anterior ya son conocidas.
        db=inc.abrir(piloto/'estado.sqlite3')
        try:inc.registrar(db,cat,{**informe,'ejecucion_id':'base-auditada-'+sha256(json.dumps(cat,sort_keys=True).encode()).hexdigest()[:16],'observaciones':[]})
        finally:db.close()
    primera,carpeta,_,_=ejecutar_corrida(piloto,informe_previo={**informe,'ejecucion_id':informe['ejecucion_id']+'-comparativo'})
    segunda,_,_,_=ejecutar_corrida(piloto,informe_previo={**informe,'ejecucion_id':informe['ejecucion_id']+'-repeticion'})
    resultado={'categorias':resultado['categorias'],'primera':primera,'segunda':segunda,'informe':str(carpeta/'reporte_diario.md'),'produccion_intacta':protegidos==huellas_produccion(),'respaldo_intacto':backup=={p.name:sha256(p.read_bytes()).hexdigest() for p in Path('piloto_respaldo/diario').iterdir() if p.is_file()},'ocr_nuevo':0,'consultas_adicionales':0,'capturas_complementarias':a.complemento,'fuentes_comparadas':len(observaciones),'alcance':'Sólo fuentes del barrido; no es una ejecución completa de todos los organismos'}
    (root/'resultado.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n');print(json.dumps(resultado,ensure_ascii=False),flush=True)
    if segunda['novedades']!=0 or not resultado['produccion_intacta'] or not resultado['respaldo_intacto']:raise RuntimeError('Falló continuidad o integridad')
if __name__=='__main__':main()
