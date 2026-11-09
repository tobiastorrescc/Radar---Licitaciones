"""Revisión documental acotada de las 119 pendientes, sin tocar catálogo persistente."""
import argparse,json,sys,re,time,fcntl,os
from pathlib import Path
from hashlib import sha256
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores,extractores,documentos,oportunidades as o,pagos
from calidad_comercial import presentacion
from presentacion_documental import clausula
from tools.verificar_fuentes import ejecutar,guardar
from tools.radar_controlado import fuentes_configuradas
ROOT=Path('work/fase3/revalidacion')

def obtener(url):
    cache=ROOT/'cache';cache.mkdir(parents=True,exist_ok=True);p=cache/sha256(url.encode()).hexdigest()
    with p.with_suffix('.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        meta=p.with_suffix('.json')
        if meta.exists():
            m=json.load(open(meta))
            if 'error' in m:raise ValueError(m['error'])
            return p.with_suffix('.bin').read_bytes(),m
        start=time.monotonic()
        try:
            b,t,u,s=conectores.descargar(url,conexion_timeout=4,lectura_timeout=7,devolver_estado=True,max_bytes=8_000_000)
            m={'url_solicitada':url,'url':u,'http':s,'tipo':t,'bytes':len(b),'segundos':round(time.monotonic()-start,3),'sha256':sha256(b).hexdigest(),'fecha':datetime.now(o.ZONA).isoformat()}
            p.with_suffix('.bin').write_bytes(b);guardar(meta,m);return b,m
        except Exception as e:guardar(meta,{'url':url,'error':str(e),'segundos':round(time.monotonic()-start,3)});raise

def elegir(caso,rs):
    def score(r):
        n=(caso.get('numero_procedimiento') or '').lstrip('0');rn=(r.get('numero_procedimiento') or '').lstrip('0')
        sim=SequenceMatcher(None,o.norm(caso.get('objeto'))[:300],o.norm(r.get('objeto') or r.get('titulo'))[:300]).ratio()
        return sim+(0.5 if n and n==rn else 0)
    orden=sorted(rs,key=score,reverse=True)
    if not orden:return None
    if score(orden[0])<0.55:return None
    if len(orden)>1 and score(orden[0])-score(orden[1])<0.10:return None
    return orden[0]

def worker(caso,path):
    ahora=datetime.now(o.ZONA).isoformat();errors=[];evidencias=[]
    f=next((f for f in fuentes_configuradas() if f['url']==caso['fuente']),{})
    b,m=obtener(caso['url']);evidencias.append(m);tipo=m['tipo'];url=m['url'];html=None
    if b.startswith(b'%PDF-'):
        import cache_documentos
        texto,_=cache_documentos.leer_texto(b,tipo,url,ocr=False)
        if f.get('adaptador')=='boletin-er':
            from barrido_institucional import boletin_entre_rios
            rs=boletin_entre_rios(texto,url)
        else:
            from extractores_lotes import boletin_texto
            rs=boletin_texto(texto,url,f)
    else:
        html=conectores.decodificar_html(b,tipo);rs,links,dom=extractores.extraer(html,url,{**f,'admitir_avisos_sin_numero':True});texto=dom.root.text
    rs=[o.normalizar(r,ahora) for r in rs];r=elegir(caso,rs)
    if not r:
        guardar(path,{'estado':'PENDIENTE','finalizado':True,'paginas_correctas':1,'oportunidades':[],'errores':[{'tipo':'ProcedimientoNoIdentificado','timeout':False,'categoria':'EXTRACCION','error':'No se identificó inequívocamente el mismo procedimiento; no se heredan fechas de otra convocatoria'}],'caso_id':caso['caso_id'],'evidencias':evidencias});return
    r={**caso,**r,'observada_esta_corrida':True,'requiere_revalidacion':False,'evidencia_captura':m}
    # En ediciones colectivas sólo el aviso identificado, nunca texto de otros avisos.
    texto_aviso=r.get('texto_documento') or r.get('objeto') or ''
    if len(rs)==1 and html: texto_aviso=texto
    r.update(clausula(texto_aviso,r,url,m['sha256']))
    docs=r.get('documentos') or caso.get('documentos') or []
    if r.get('enlace_pliego') and not docs:docs=[{'url':r['enlace_pliego'],'titulo':'Pliego'}]
    pendientes=[]
    for d in docs[:4]:
        u=d.get('url')
        if not u:continue
        # Sólo enlaces publicados por la ficha oficial y hosts autorizados de la fuente.
        hosts={conectores._host(caso['url']),*(conectores._host('https://'+h) for h in f.get('dominios_documentos',[]))}
        if conectores._host(u) not in hosts:pendientes.append({'url':u,'motivo':'Dominio documental no validado en fuente'});continue
        try:
            bb,mm=obtener(u);evidencias.append(mm)
            import cache_documentos
            tt,cache=cache_documentos.leer_texto(bb,mm['tipo'],mm['url'],ocr=False)
            r.update(clausula(tt,r,u,mm['sha256']))
            r['pago_evidencias']=r.get('pago_evidencias',[])+pagos.extraer(tt,u,mm['sha256'],pdf=bb.startswith(b'%PDF-'))
        except Exception as e:errors.append({**conectores.clasificar_error(e,'EXTRACCION'),'url':u})
    if len(docs)>4:pendientes.extend({'url':d.get('url'),'motivo':'Cupo documental por pasada; no se declara completa'} for d in docs[4:])
    r=o.normalizar(r,ahora);r.update(presentacion(r,ahora));r['revalidacion_documental']={'caso_id':caso['caso_id'],'fecha':ahora,'evidencias':evidencias,'documentos_pendientes':pendientes,'errores':errors}
    guardar(path,{'estado':'PARCIAL' if errors or pendientes else 'OPERATIVA','finalizado':True,'paginas_correctas':len(evidencias),'oportunidades':[r],'errores':errors,'caso_id':caso['caso_id'],'evidencias':evidencias})

def main():
    p=argparse.ArgumentParser();p.add_argument('--worker');p.add_argument('--checkpoint');a=p.parse_args();casos=json.load(open('inventario/revalidacion_fase3.json'))['casos']
    if a.worker:
        caso=next(r for r in casos if r['caso_id']==a.worker)
        try:worker(caso,a.checkpoint)
        except Exception as e:guardar(a.checkpoint,{'estado':'ERROR_ACCESO','finalizado':True,'paginas_correctas':0,'oportunidades':[],'errores':[conectores.clasificar_error(e,'RED')],'caso_id':a.worker})
        return
    ROOT.mkdir(parents=True,exist_ok=True)
    casos.sort(key=lambda r:r.get('fecha_apertura') or '9999')
    fs=[{'id':r['caso_id'],'url':r['url']} for r in casos]
    informe=ejecutar(fs,ROOT/'auditoria.json',concurrencia=4,por_fuente=36,total=650,comando=lambda f,path:[sys.executable,__file__,'--worker',f['id'],'--checkpoint',str(path)])
    salida=[]
    for obs in informe['observaciones']:
        c=next(r for r in casos if r['caso_id']==obs['id']);q=Path(obs.get('resultado_archivo',''));d=json.load(open(q)) if q.is_file() else {};rs=d.get('oportunidades',[])
        salida.append({'caso_id':c['caso_id'],'original':c,'resultado':rs[0] if rs else None,'estado_acceso':obs['estado'],'errores':d.get('errores',obs['errores']),'evidencias':d.get('evidencias',[]),'segundos':obs.get('duracion_segundos')})
    guardar(ROOT/'resultado.json',{'fecha':informe['actualizado'],'run':os.environ.get('GITHUB_RUN_ID'),'casos':salida,'segundos':informe['duracion_segundos'],'ocr_nuevo':0})
if __name__=='__main__':main()
