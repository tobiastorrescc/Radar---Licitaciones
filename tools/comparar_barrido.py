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
    previos={o.identidad(r) for r in catalogo};urls={(r.get('url'),o.procedimiento_canonico(r) or o.norm(r.get('titulo'))) for r in catalogo}
    anteriores={o.identidad(r) for r in antes['registros']}
    salida=[]
    for r in despues['registros']:
        if r.get('clasificacion_registro')!='PROCEDIMIENTO':continue
        conocida=o.identidad(r) in previos or (r.get('url'),o.procedimiento_canonico(r) or o.norm(r.get('titulo'))) in urls
        categoria=('VIGENTE_YA_CONOCIDA' if conocida else 'VIGENTE_NUEVA_PARA_RADAR') if r.get('vigencia')=='ABIERTA' else 'HISTORICA_RECUPERADA' if r.get('vigencia')=='VENCIDA' and not conocida else 'FECHA_O_VIGENCIA_PENDIENTE' if not conocida else 'YA_CONOCIDA_NO_ABIERTA'
        salida.append({**r,'comparacion_categoria':categoria,'detectada_barrido_inicial':o.identidad(r) in anteriores,'ya_catalogada':conocida})
    return {'categorias':dict(Counter(r['comparacion_categoria'] for r in salida)),'antes':len(antes['registros']),'despues':len(despues['registros']),'oportunidades':salida}

def main():
    p=argparse.ArgumentParser();p.add_argument('--antes',required=True);p.add_argument('--despues',required=True);p.add_argument('--catalogo',required=True);p.add_argument('--salida',required=True);a=p.parse_args()
    antes=json.load(open(a.antes));despues=json.load(open(a.despues));cat=json.load(open(a.catalogo))['oportunidades'];root=Path(a.salida);root.mkdir(parents=True,exist_ok=False)
    resultado=comparar(antes,despues,cat)
    (root/'comparacion.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n')
    # Sólo se reparan rutas de la captura copiada. Ninguna solicitud a sitios.
    origen=Path(a.despues).parent;informe=json.load(open(origen/'verificacion.json'))
    for obs in informe['observaciones']:
        original=obs.get('resultado_archivo')
        if original:
            sufijo=str(original).split('work/barrido/',1)[-1];obs['resultado_archivo']=str(origen/sufijo)
    protegidos=huellas_produccion();backup={p.name:sha256(p.read_bytes()).hexdigest() for p in Path('piloto_respaldo/diario').iterdir() if p.is_file()}
    piloto=root/'piloto';restaurar('piloto_respaldo/diario',piloto)
    primera,carpeta,_,_=ejecutar_corrida(piloto,informe_previo={**informe,'ejecucion_id':informe['ejecucion_id']+'-comparativo'})
    segunda,_,_,_=ejecutar_corrida(piloto,informe_previo={**informe,'ejecucion_id':informe['ejecucion_id']+'-repeticion'})
    resultado={'categorias':resultado['categorias'],'primera':primera,'segunda':segunda,'informe':str(carpeta/'reporte_diario.md'),'produccion_intacta':protegidos==huellas_produccion(),'respaldo_intacto':backup=={p.name:sha256(p.read_bytes()).hexdigest() for p in Path('piloto_respaldo/diario').iterdir() if p.is_file()},'ocr_nuevo':0,'consultas_adicionales':0,'alcance':'Sólo fuentes del barrido; no es una ejecución completa de todos los organismos'}
    (root/'resultado.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n');print(json.dumps(resultado,ensure_ascii=False),flush=True)
    if segunda['novedades']!=0 or not resultado['produccion_intacta'] or not resultado['respaldo_intacto']:raise RuntimeError('Falló continuidad o integridad')
if __name__=='__main__':main()
