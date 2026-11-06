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
    fechas=[];d=hoy
    while len(fechas)<int(dias)+1:
        if d.weekday()<5:fechas.append(d)
        d-=timedelta(days=1)
    return [urlunsplit((p.scheme,p.netloc,'/boletinoficial/ver.php',urlencode({'seccion':f'{d.year}/{d.isoformat()}licitaciones.html'}),'')) for d in fechas]

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
        num=str(int(m[1]))+'/'+m[2]
        tipo_normalizado=re.match(r'^('+e.TIPO+r')\b',e.norm(t))
        tipo_normalizado=tipo_normalizado[1] if tipo_normalizado else e.norm(t)
        destino=e.url_publica(fila.get(link) or '',fuente) if link else fuente
        if not destino or urlsplit(destino).hostname!=urlsplit(fuente).hostname:destino=fuente
        registros.append({'url':destino,'evidencia_url':url,'organismo':org,'provincia':'Santa Fe','localidad':None,'titulo':t+' '+num+' '+obj,'objeto':obj,'numero_procedimiento':num,'tipo_procedimiento':tipo_normalizado,'modalidad_procedimiento_texto':t,'procedimiento':tipo_normalizado+' '+num,'registro_estructurado':True,'detalle_completo':True,'fecha_apertura_texto':fila.get(apertura),'fecha_publicacion_texto':fila.get(publicada) if publicada else None,'fecha_limite_presentacion_texto':fila.get(limite) if limite else None,'presupuesto_texto':fila.get(monto) if monto else None,'documentos':[],'formato_evidencia':'CSV_PUBLICADO','es_fuente_complementaria':True})
    return registros,errores

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
            campos=cabecera;valores=[c.text for c in celdas]+[detalle]
            if len(celdas)==4:
                combinado=re.fullmatch(r'(.*?)\s+(\d+\s*[-/]\s*20\d{2})',celdas[1].text.strip())
                if not combinado:continue
                campos=['Apertura','N° - Año','Tipo Gestión Modalidad','Objeto','Organismo Licitante','URL']
                valores=[celdas[0].text,combinado[2],combinado[1],celdas[2].text,celdas[3].text,detalle]
            buffer=StringIO();w=csv.writer(buffer,delimiter=';');w.writerow(campos);w.writerow(valores)
            try:rs,_=gestiones_csv(buffer.getvalue().encode(),url,url)
            except ValueError:continue
            for r in rs:r['formato_evidencia']='TABLA_HTML'
            registros.extend(rs)
    return registros


def pdf_santafe(base,ahora=None):
    from urllib.parse import parse_qs
    html=ediciones_santafe(base,0,ahora)[0]
    fecha=parse_qs(urlsplit(html).query)['seccion'][0].split('/')[1][:10]
    d=datetime.fromisoformat(fecha)
    p=urlsplit(base)
    return urlunsplit((p.scheme,p.netloc,f'/boletinoficial/recursos/boletines/pdf/{d.year}/{d.month:02d}/BO{d:%d%m%Y}.pdf','',''))


def seccion_licitaciones(texto):
    cabeceras=list(re.finditer(r'(?im)^\s*(?:VI\s*[-.–:]?\s*)?LICITACIONES\s*$',texto))
    if not cabeceras:raise ValueError('PDF completo sin cabecera identificable de Licitaciones; no se presume extracción completa')
    secciones=[]
    for i,cabecera in enumerate(cabeceras):
        resto=texto[cabecera.end():cabeceras[i+1].start() if i+1<len(cabeceras) else len(texto)]
        fin=re.search(r'(?im)^\s*(?:(?:VII|VIII|IX)\s*[-.–:]?\s*)?(?:AVISOS OFICIALES|CONVOCATORIAS|CONTRATOS,? ESTATUTOS|REMATES)\b',resto)
        seccion=resto[:fin.start()] if fin else resto
        if e.procesos(seccion):secciones.append(seccion)
    if not secciones:raise ValueError('Sección localizada pero sin convocatorias reconocidas; requiere revisión')
    return '\n'.join(secciones)
