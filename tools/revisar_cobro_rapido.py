"""Revisión comercial aislada de una cohorte con procedencia; nunca escribe SQLite."""
import argparse,base64,gzip,json,sys,time,concurrent.futures
from pathlib import Path
from datetime import datetime
from collections import Counter
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o,pagos,fichas,conectores,extractores
from tools.comprobar_pliegos import comprobar
from tools.radar_controlado import fuentes_configuradas


def rapido(r):
    p=r.get('pago',{})
    return p.get('estado')=='VERIFICADO' and (p.get('clasificacion') in ('ANTICIPO','CONTADO','CONTRA_ENTREGA') or bool(p.get('plazos_dias')) and max(p['plazos_dias'])<=15)


def detalle(url,config):
    inicio=time.monotonic()
    try:
        raw,tipo,final=conectores.descargar(url,conexion_timeout=3,lectura_timeout=5)
        if urlparse(final).hostname!=urlparse(url).hostname:raise ValueError('Redirección de dominio; requiere revisión')
        if 'html' not in tipo:raise ValueError('Publicación no HTML; conserva revisión documental separada')
        html=conectores.decodificar_html(raw,tipo);conectores.comprobar_acceso(html)
        rs,links,dom=extractores.extraer(html,final,config)
        for r in rs:r.update(texto_documento=r.get('titulo'),rango_evidencia=3)
        return {'url':url,'estado':'CONSULTADA','registros':rs,'segundos':round(time.monotonic()-inicio,2),'fecha':datetime.now(o.ZONA).isoformat()}
    except Exception as e:return {'url':url,'estado':'ERROR','error':str(e),'segundos':round(time.monotonic()-inicio,2)}


def informe(rs,fecha):
    fast=sorted((r for r in rs if rapido(r)),key=lambda r:(pagos.grupo_comercial(r['pago']),r.get('fecha_limite_presentacion') or r.get('fecha_apertura') or '9999'))
    texto='# Oportunidades de cobro rápido documentado\n\nNo hay mediciones de acreditación bancaria: el orden refleja el plazo contractual comprobado, no un tiempo efectivo de recuperación inventado. Todas las restantes oportunidades se conservan en el informe completo.\n\n'
    for estado in ('OBSERVADA_RECIENTEMENTE_ABIERTA_CALCULADA','SOLO_EVIDENCIA_PREVIA','VENCIDA_O_NO_CONFIRMADA'):
        grupo=[r for r in fast if r['revision_vigencia']==estado]
        texto+='## '+estado+'\n\n'+ ('Ninguna.\n\n' if not grupo else fichas.reporte(grupo,fecha)+'\n')
    return texto,fast


def main():
    p=argparse.ArgumentParser();p.add_argument('--sin-red',action='store_true');a=p.parse_args()
    origen=Path('inventario/cohorte116.json.gz.b64');datos=gzip.decompress(base64.b64decode(origen.read_text()));cohorte=json.loads(datos)['oportunidades'];fecha=datetime.now(o.ZONA).isoformat()
    rs=[o.normalizar(r,fecha) for r in cohorte];antes={r['id']:r['pago'].get('estado') for r in rs};configs={f['url']:f for f in fuentes_configuradas()};out=Path('work/cobro-rapido');out.mkdir(parents=True,exist_ok=True)
    # Últimas observaciones primero, después vencimiento. Sin limitar la cantidad de fichas.
    rs.sort(key=lambda r:(not bool(r.get('observada_esta_corrida') or 'revision_rosario_41110430956' in r.get('origenes_evidencia',[])),r.get('fecha_limite_presentacion') or r.get('fecha_apertura') or '9999'))
    consultas={};observadas=set()
    if not a.sin_red:
        urls={r['url']:configs.get(r.get('fuente'),{}) for r in rs};inicio=time.monotonic()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futuros={pool.submit(detalle,u,c):u for u,c in urls.items()}
            for futuro in concurrent.futures.as_completed(futuros):
                valor=futuro.result();consultas[valor['url']]=valor
                with (out/'publicaciones.jsonl').open('a') as f:f.write(json.dumps(valor,ensure_ascii=False)+'\n')
                print('REVISION_PUBLICACION '+json.dumps({k:v for k,v in valor.items() if k!='registros'},ensure_ascii=False),flush=True)
                for r in rs:
                    if r['url']!=valor['url']:continue
                    matches=[x for x in valor.get('registros',[]) if o.procedimiento_canonico(x)==o.procedimiento_canonico(r)]
                    for x in matches:
                        observado=o.normalizar({**r,**x},fecha)
                        if o.identidad(observado)!=o.identidad(r):continue
                        combinado=o.fusionar(r,observado,fecha);r.update(combinado);r['ultima_observacion_publicacion']=valor['fecha'];observadas.add(r['id'])
        # No OCR indiscriminado: cero páginas nuevas; reutilización automática de caché OCR existente.
        comprobar(rs,fecha,fuentes_configuradas(),total=300,salida_parcial=out/'documentos.jsonl',ocr_documentos=0)
    rs=[o.normalizar(r,fecha) for r in rs]
    for r in rs:
        r['revision_vigencia']='VENCIDA_O_NO_CONFIRMADA' if r['vigencia']!='ABIERTA' else ('OBSERVADA_RECIENTEMENTE_ABIERTA_CALCULADA' if r['id'] in observadas else 'SOLO_EVIDENCIA_PREVIA')
    nuevos=[r['id'] for r in rs if antes[r['id']]!='VERIFICADO' and r['pago']['estado']=='VERIFICADO']
    md,fast=informe(rs,fecha)
    resumen={'fecha':fecha,'cohorte':len(rs),'consultas_publicaciones':len(consultas),'publicaciones_observadas':len(observadas),'pagos_verificados_antes':sum(v=='VERIFICADO' for v in antes.values()),'pagos_verificados_despues':sum(r['pago']['estado']=='VERIFICADO' for r in rs),'de_desconocido_a_verificado':len(nuevos),'ids_mejorados':nuevos,'cobro_rapido':len(fast),'vigencia':dict(Counter(r['revision_vigencia'] for r in rs)),'sin_escritura_historial':True,'ocr_nuevo':0}
    for nombre,obj in [('resultado',resumen),('todas',rs),('rapidas',fast)]: (out/(nombre+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    (out/'COBRO_RAPIDO.md').write_text(md);(out/'TODAS.md').write_text(fichas.reporte(rs,fecha))
    print('RESULTADO_COBRO '+json.dumps(resumen,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
