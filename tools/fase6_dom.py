"""Revisión excepcional de una SPA oficial, con Chrome estándar y TLS validado."""
import asyncio,json,sys
from pathlib import Path
from hashlib import sha256
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.verificar_fuentes import guardar

async def main():
 root=Path('work/fase6/dom-totoras');root.mkdir(parents=True,exist_ok=True);r={'url':'https://www.mtotoras.gob.ar/','estado':'PENDIENTE','urls_revisadas':[],'tls_verificado':True,'datos':[]}
 try:
  from playwright.async_api import async_playwright
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(channel='chrome',headless=True);page=await browser.new_page(ignore_https_errors=False)
   async def capturar(resp):
    if 'mtotoras.gob.ar' not in resp.url or 'json' not in resp.headers.get('content-type',''):return
    try:
     t=await resp.text()
     if len(t)>2000000:return
     name=sha256(resp.url.encode()).hexdigest();(root/(name+'.json')).write_text(t);r['datos'].append({'url':resp.url,'http':resp.status,'archivo':name+'.json'})
    except Exception:pass
   page.on('response',capturar)
   await page.goto(r['url'],wait_until='networkidle',timeout=20000);r['urls_revisadas'].append(page.url);(root/'portada.html').write_text(await page.content())
   links=await page.locator('a[href]').evaluate_all("els=>els.map(x=>({url:x.href,texto:x.innerText}))");r['links']=links
   import re
   urls=[x['url'] for x in links if x['url'].startswith(r['url']) and re.search(r'licit|compras|contrata|noticia|transparen|decret|resoluc',x['texto'],re.I)]
   for i,u in enumerate(list(dict.fromkeys(urls))[:3]):
    await page.goto(u,wait_until='networkidle',timeout=12000);r['urls_revisadas'].append(page.url);(root/(str(i)+'.html')).write_text(await page.content())
   r['estado']='REVISADA_CON_DOM_RENDERIZADO';await browser.close()
 except Exception as e:r['error']=type(e).__name__+': '+str(e)[:400]
 guardar(root/'resultado.json',r)
if __name__=='__main__':asyncio.run(main())
