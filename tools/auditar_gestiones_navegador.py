"""Navegador oficial aislado: exportación y paginación, sin autenticación ni OCR."""
import argparse,asyncio,json,re,sys,time
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit,parse_qsl,urlencode,urlunsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores,extractores,oportunidades as o
from fuentes_criticas import gestiones_html,gestiones_csv
from tools.verificar_fuentes import guardar

HOSTS={'www.santafe.gob.ar','www.santafe.gov.ar','santafe.gob.ar','santafe.gov.ar'}

def oficial(url):
    p=urlsplit(url)
    return p.scheme in ('https','http') and p.hostname in HOSTS and p.path.startswith('/gestionesdecompras/')

def url_log(url):
    p=urlsplit(url);publicas={'a','anio','start','limit','page','idGestion','nroGestion','estado'}
    return urlunsplit((p.scheme,p.netloc,p.path,urlencode([(k,v if k in publicas else '[omitido]') for k,v in parse_qsl(p.query)]),''))

def siguiente(links,actual=None):
    for l in links:
        texto=o.norm(l['texto'])
        if ('next' in l.get('rel','').split() or texto in ('siguiente','siguiente ›','›','»')) and oficial(l['url']) and l['url']!=actual and not l.get('disabled') and not any(n.attrs.get('aria-disabled')=='true' or n.clase('disabled') for n in l.get('node',extractores.Nodo('a')).padres()):return l['url']
    return None

from fuentes_criticas import total_gestiones as total_publicado

async def auditar(plan,salida):
    root=Path(salida);root.mkdir(parents=True,exist_ok=True);inicio=time.monotonic();rs=[];errores=[];red=[];paginas=[];capturas=[];formularios=[];limites=[];total=None
    def persistir(estado):
        guardar(root/'resultado.json',{'estado':estado,'fecha':o.datetime.now(o.ZONA).isoformat(),'segundos':round(time.monotonic()-inicio,3),'convocatorias':len({o.identidad(r) for r in rs}),'oportunidades':o.deduplicar(rs,o.datetime.now(o.ZONA)),'errores':errores,'red':red,'paginas':paginas,'archivos':capturas,'formularios':formularios,'total_publicado':total,'limites':limites,'acceso_verificado_por':'CHROMIUM_ESTANDAR_TLS_VALIDADO','ocr_nuevo':0})
    persistir('INICIADA')
    try:from playwright.async_api import async_playwright
    except ImportError:
        errores.append({'tipo':'PLAYWRIGHT_NO_DISPONIBLE','categoria':'ENTORNO'});persistir('ERROR_ENTORNO');return
    fs=json.load(open('inventario/fuentes.json'));config=next(x for x in fs if x['id']=='fuente-087')
    async with async_playwright() as pw:
        try:browser=await pw.chromium.launch(channel='chrome',headless=True)
        except Exception as e:
            errores.append({'tipo':'CHROME_NO_DISPONIBLE','categoria':'ENTORNO','error':str(e)[:500]});persistir('ERROR_ENTORNO');return
        context=await browser.new_context(ignore_https_errors=False,accept_downloads=True)
        estados_http={}
        async def respuesta(r):
            if not oficial(r.url):return
            try:h=await r.all_headers()
            except Exception:return
            estados_http[r.url]=r.status
            red.append({'url':url_log(r.url),'metodo':r.request.method,'http':r.status,'tipo':h.get('content-type'),'bytes_declarados':h.get('content-length')})
        context.on('response',respuesta)
        vistas=set();paginas_firmas=set()
        try:
            for origen in plan['urls']:
                if not oficial(origen):raise ValueError('Origen fuera del portal oficial')
                if time.monotonic()-inicio>=plan.get('total_segundos',150):limites.append('TIEMPO_TOTAL');break
                page=await context.new_page();url=origen;avanzada=False;response=None
                try:
                    while url:
                        if time.monotonic()-inicio>=plan.get('total_segundos',150):limites.append('TIEMPO_TOTAL');break
                        if url in vistas and not avanzada:break
                        vistas.add(url);t=time.monotonic()
                        try:
                            if not avanzada:response=await page.goto(url,wait_until='domcontentloaded',timeout=18000)
                            avanzada=False
                        except Exception as e:
                            errores.append({'url':url_log(url),'tipo':'NAVEGACION_FALLIDA','categoria':'RED','error':str(e)[:600],'segundos':round(time.monotonic()-t,3)});persistir('EN_CURSO');break
                        if response is None:raise ValueError('Navegación sin respuesta HTTP')
                        if response.status>=400:
                            errores.append({'url':url_log(url),'tipo':'HTTP_ERROR','http':response.status,'categoria':'ACCESO' if response.status in (401,403,429) else 'RED'})
                            if response.status in (401,403,429):persistir('INACCESIBLE');return
                            break
                        if not oficial(page.url):raise ValueError('Redirección fuera del portal')
                        try:await page.wait_for_selector('table tbody tr',timeout=5000)
                        except Exception:pass
                        contenido=await page.content();conectores.comprobar_acceso(contenido)
                        forms=await page.evaluate("() => [...document.forms].map(f=>({action:f.action,method:f.method,campos:[...f.elements].map(e=>({nombre:e.name,tipo:e.type}))}))")
                        formularios.extend({**f,'action':url_log(f['action'])} for f in forms)
                        dom=extractores.DOM(contenido);nuevos=gestiones_html(dom,page.url)
                        for r in nuevos:rs.append(o.normalizar({**r,'fuente':config['url'],'rango_evidencia':3,'requiere_revalidacion':False}))
                        total=total_publicado(dom.root.text) or total
                        firma=sha256(json.dumps(sorted(o.identidad(r) for r in nuevos)).encode()).hexdigest()
                        if nuevos and firma in paginas_firmas:errores.append({'url':url_log(url),'tipo':'PAGINACION_REPETIDA','categoria':'EXTRACCION'});break
                        if nuevos:paginas_firmas.add(firma)
                        # No conservar scripts, valores de formularios, cookies ni cabeceras de autenticación.
                        html=await page.evaluate("""() => {const d=document.documentElement.cloneNode(true);d.querySelectorAll('script,style,input,textarea').forEach(n=>n.remove());d.querySelectorAll('*').forEach(n=>[...n.attributes].forEach(a=>{if(/^on|nonce|token/i.test(a.name))n.removeAttribute(a.name)}));return d.outerHTML;}""")
                        data=html.encode();digest=sha256(data).hexdigest();(root/(digest+'.html')).write_bytes(data)
                        recibo={'fuente_id':'fuente-087','url_oficial':page.url,'archivo':digest+'.html','tipo':'text/html','sha256':digest,'capturado_en':o.datetime.now(o.ZONA).isoformat(),'recibo':{'metodo':'NAVEGADOR_OFICIAL','codigo_http':response.status,'url_final':page.url,'sha256':digest}}
                        guardar(root/(digest+'.json'),recibo);capturas.append(recibo)
                        paginas.append({'url':url_log(page.url),'http':response.status,'segundos':round(time.monotonic()-t,3),'filas':len(nuevos),'sha256':digest})
                        if len(paginas)==1:
                            # Sólo la acción de exportar: nunca Ofertar, registrarse ni enviar formularios.
                            exportar=page.get_by_text(re.compile(r'^\s*(?:Descargar|Exportar)\s+CSV\s*$',re.I)).first
                            if await exportar.count():
                                try:
                                    async with page.expect_download(timeout=10000) as desc:await exportar.click(timeout=5000)
                                    descarga=await desc.value
                                    if not (oficial(descarga.url) or descarga.url.startswith('blob:')):raise ValueError('Descarga fuera del portal')
                                    path=await descarga.path()
                                    if Path(path).stat().st_size>12_000_000:raise ValueError('CSV excede 12 MB; continuar HTML')
                                    b=Path(path).read_bytes();csv_url=descarga.url if oficial(descarga.url) else page.url
                                    codigo_csv=estados_http.get(descarga.url) if oficial(descarga.url) else response.status
                                    if codigo_csv!=200:raise ValueError('CSV sin respuesta oficial HTTP 200 comprobada')
                                    datos,fallos=gestiones_csv(b,csv_url,config['url']);rs.extend(o.normalizar({**r,'fuente':config['url'],'rango_evidencia':3,'requiere_revalidacion':False}) for r in datos);errores.extend(fallos)
                                    h=sha256(b).hexdigest();(root/(h+'.csv')).write_bytes(b)
                                    csv_recibo={**recibo,'url_oficial':csv_url,'archivo':h+'.csv','tipo':'text/csv','sha256':h,'recibo':{'metodo':'NAVEGADOR_OFICIAL','codigo_http':codigo_csv,'url_final':csv_url,'url_origen':page.url,'sha256':h}}
                                    guardar(root/(h+'.json'),csv_recibo);capturas.append(csv_recibo)
                                except Exception as e:errores.append({'tipo':'CSV_NO_RECUPERADO','categoria':'EXTRACCION','error':str(e)[:500]})
                        persistir('EN_CURSO')
                        url=siguiente(dom.root.enlaces(page.url),page.url)
                        if not url:
                            boton=page.locator('.pagination a,.pagination button,.dataTables_paginate a,.dt-paging button,li.next a').filter(has_text=re.compile(r'^\s*(?:Siguiente|›|»)\s*$',re.I)).first
                            if await boton.count() and await boton.is_enabled():
                                deshabilitado=await boton.evaluate("n=>!!n.closest('.disabled,[aria-disabled=true]')")
                                if not deshabilitado:
                                    antes=await page.locator('table').all_text_contents()
                                    await boton.click(timeout=5000)
                                    try:await page.wait_for_function("anterior=>JSON.stringify([...document.querySelectorAll('table')].map(t=>t.textContent))!==JSON.stringify(anterior)",arg=antes,timeout=5000)
                                    except Exception:pass
                                    url=page.url;avanzada=True
                    if rs:break
                except Exception as e:errores.append({'url':url_log(url or origen),'tipo':type(e).__name__,'categoria':'EXTRACCION','error':str(e)[:500]})
                finally:await page.close()
        finally:await context.close();await browser.close()
    cantidad=len({o.identidad(r) for r in rs})
    if total is not None and cantidad<total:errores.append({'tipo':'TOTAL_NO_ALCANZADO','categoria':'EXTRACCION','publicadas':total,'extraidas':cantidad})
    persistir(('PARCIAL' if errores or limites else 'EXTRACCION_COMPLETA') if rs else 'INACCESIBLE' if not paginas else 'ACCESIBLE_SIN_EXTRACCION')

def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',default='tools/plan_gestiones_navegador.json');p.add_argument('--salida',default='work/gestiones-navegador');a=p.parse_args()
    try:asyncio.run(asyncio.wait_for(auditar(json.load(open(a.plan)),a.salida),timeout=180))
    except TimeoutError:
        p=Path(a.salida)/'resultado.json';d=json.loads(p.read_text()) if p.exists() else {};d['estado']='TIEMPO_TOTAL';guardar(p,d)

if __name__=='__main__':main()
