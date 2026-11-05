"""Descubrimiento ligero en fuentes críticas; formatos oficiales, sin OCR ni pagos."""
import csv,re
from io import StringIO
from datetime import datetime,timedelta
from urllib.parse import urlsplit,urlunsplit,urlencode
import extractores as e

def ediciones_santafe(base,dias=3,ahora=None):
    import oportunidades as o
    if not 0<=int(dias)<=14:raise ValueError('Ventana del Boletín fuera de rango')
    hoy=(datetime.fromisoformat(ahora) if isinstance(ahora,str) else ahora or datetime.now(o.ZONA)).astimezone(o.ZONA).date()
    p=urlsplit(base)
    if p.hostname not in ('www.santafe.gov.ar','santafe.gov.ar','www.santafe.gob.ar','santafe.gob.ar'):raise ValueError('El Boletín requiere dominio provincial oficial')
    return [urlunsplit((p.scheme,p.netloc,'/boletinoficial/ver.php',urlencode({'seccion':f'{d.year}/{d.isoformat()}licitaciones.html'}),'')) for n in range(int(dias)+1) for d in [hoy-timedelta(days=n)]]

def enlaces_csv(dom,url):
    return [l['url'] for l in dom.root.enlaces(url) if urlsplit(l['url']).hostname==urlsplit(url).hostname and re.search(r'csv',l['texto']+' '+l['url'],re.I)]

def gestiones_csv(datos,url,fuente):
    try:texto=datos.decode('utf-8-sig')
    except UnicodeDecodeError:texto=datos.decode('cp1252')
    if re.search(r'<(?:html|!doctype)',texto[:500],re.I):raise ValueError('Exportación devolvió HTML, no CSV')
    try:delimitador=csv.Sniffer().sniff(texto[:8192],delimiters=';,\t').delimiter
    except csv.Error:raise ValueError('CSV sin separador reconocible')
    reader=csv.DictReader(StringIO(texto),delimiter=delimitador)
    limpiar=lambda x:re.sub(r'[^a-z0-9]','',e.norm(x))
    campos={limpiar(k):k for k in reader.fieldnames or []}
    def campo(*nombres):return next((campos[n] for n in nombres if n in campos),None)
    numero=campo('nano','nroano','numeroano','numerodegestion','numerogestion','numero','nro');anio=campo('ano','anio')
    objeto=campo('objeto','objetodelacontratacion');organismo=campo('organismolicitante','organismocontratante','organismo');tipo=campo('tipogestionmodalidad','tipogestion','tipodegestion','tipodecontratacion','tipo')
    apertura=campo('apertura','fechadeapertura','fechaapertura');publicada=campo('fechadepublicacion','fechapublicacion');limite=campo('fechalimitepresentacion','fechalimite','vencimiento');monto=campo('presupuestooficial','presupuesto');link=campo('enlace','url','detalle')
    if not all((numero,objeto,organismo,tipo,apertura)):raise ValueError('CSV sin columnas oficiales de procedimientos; no se declara vacío')
    registros=[];errores=[]
    for n,fila in enumerate(reader,2):
        num=str(fila.get(numero) or '').strip();obj=str(fila.get(objeto) or '').strip();org=str(fila.get(organismo) or '').strip();t=str(fila.get(tipo) or '').strip()
        if anio and re.fullmatch(r'\d+',num):num+='/'+str(fila.get(anio) or '').strip()
        m=re.fullmatch(r'(\d+)\s*[-/]\s*(20\d{2})',num)
        if not m or not obj or not org or not t:
            errores.append({'tipo':'FilaCSVIncompleta','categoria':'EXTRACCION','timeout':False,'error':f'Fila {n} sin número/año, organismo, tipo u objeto comprobable'});continue
        num=str(int(m[1]))+'/'+m[2];destino=e.url_publica(fila.get(link) or '',fuente) if link else fuente
        if not destino or urlsplit(destino).hostname!=urlsplit(fuente).hostname:destino=fuente
        registros.append({'url':destino,'evidencia_url':url,'organismo':org,'provincia':'Santa Fe','localidad':None,'titulo':t+' '+num+' '+obj,'objeto':obj,'numero_procedimiento':num,'tipo_procedimiento':e.norm(t),'procedimiento':e.norm(t)+' '+num,'registro_estructurado':True,'detalle_completo':True,'fecha_apertura_texto':fila.get(apertura),'fecha_publicacion_texto':fila.get(publicada) if publicada else None,'fecha_limite_presentacion_texto':fila.get(limite) if limite else None,'presupuesto_texto':fila.get(monto) if monto else None,'documentos':[],'formato_evidencia':'CSV_PUBLICADO','es_fuente_complementaria':True})
    return registros,errores

def fecha_articulo(dom,url,patron):
    if not re.fullmatch(patron,urlsplit(url).path):return None
    fechas={n.attrs.get('content','') for n in dom.root.iter() if n.tag=='meta' and n.attrs.get('property')=='article:published_time'}
    fechas.update(n.attrs.get('datetime','') for n in dom.root.iter() if n.tag=='time' and 'published' in n.attrs.get('class','').split())
    validas={f for f in fechas if re.fullmatch(r'20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)?',f)}
    return next(iter(validas)) if len(validas)==1 else None

def gestiones_html(dom,url):
    """Misma identificación de columnas para el listado HTML y la exportación."""
    registros=[]
    for tabla in dom.root.iter():
        if tabla.tag!='table':continue
        filas=[n for n in tabla.iter() if n.tag=='tr'];cabecera=[]
        for fila in filas:
            celdas=[n for n in fila.children if isinstance(n,e.Nodo) and n.tag in ('th','td')]
            if not cabecera:
                labels=[c.text for c in celdas]
                if not any('apertura' in e.norm(k) for k in labels) or not any('organismo' in e.norm(k) for k in labels):continue
                cabecera=labels+['URL'];continue
            if len(celdas)!=len(cabecera)-1:continue
            enlaces=fila.enlaces(url);detalle=next((l['url'] for l in enlaces if urlsplit(l['url']).hostname==urlsplit(url).hostname),url)
            buffer=StringIO();w=csv.writer(buffer,delimiter=';');w.writerow(cabecera);w.writerow([c.text for c in celdas]+[detalle])
            try:rs,_=gestiones_csv(buffer.getvalue().encode(),url,url)
            except ValueError:continue
            for r in rs:r['formato_evidencia']='TABLA_HTML'
            registros.extend(rs)
    return registros
