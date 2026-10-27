"""Secciones de convocatorias encabezadas: datos y adjuntos hasta el siguiente título."""
from urllib.parse import urlsplit, unquote
import re

def encabezados(raiz,url,config):
    from extractores import Nodo,procesos,norm,excluido,situacion,ADJUNTOS,EVENTO,url_publica
    resultados=[]
    for h in raiz.iter():
        if h.tag not in ('h1','h2','h3','h4','h5','h6') or excluido(h):continue
        titulo=h.text
        if config.get('adaptador')=='colon-pba':titulo=titulo.replace('Licitacioón','Licitación')
        ps=procesos(titulo)
        if len({p['procedimiento'] for p in ps})!=1:continue
        seccion=h
        for padre in list(h.padres())[1:]:
            if padre.tag in ('root','html','body','main') or excluido(padre):break
            normal=padre.text.replace('Licitacioón','Licitación') if config.get('adaptador')=='colon-pba' else padre.text
            def compatible(p):
                numero=p['numero'].replace('-','/');cabecera=ps[0]['numero'].replace('-','/')
                return p['tipo']==ps[0]['tipo'] and numero.split('/')[0]==cabecera.split('/')[0] and ('/' not in numero or numero==cabecera)
            if not all(compatible(p) for p in procesos(normal)) or len(normal)>16000:break
            seccion=padre
        hermanos=h.parent.children;pos=hermanos.index(h);bloques=[h]
        for otro in hermanos[pos+1:]:
            if isinstance(otro,Nodo):
                if otro.tag in ('h1','h2','h3','h4','h5','h6') and int(otro.tag[1])<=int(h.tag[1]):break
                if any(x.tag in ('h1','h2','h3','h4','h5','h6') and procesos(x.text) for x in otro.iter()):break
            bloques.append(otro)
        if seccion is not h:bloques=[seccion]
        texto=seccion.text if seccion is not h else titulo+' '+' '.join(b.text if isinstance(b,Nodo) else b for b in bloques[1:])
        links=[l for b in bloques if isinstance(b,Nodo) for l in b.enlaces(url)]
        extensiones=(*ADJUNTOS,*(('.jpg','.jpeg','.png') if config.get('documentos_imagen') else ()))
        docs=[{'url':l['url'],'titulo':l['texto'] or titulo} for l in links if urlsplit(l['url']).path.lower().endswith(extensiones) or any(re.search(p,l['url']) for p in config.get('patrones_documentos',[]))]
        if config.get('documentos_imagen'):
            for b in bloques:
                if not isinstance(b,Nodo):continue
                for n in b.iter():
                    if n.tag=='img' and n.attrs.get('src'):
                        imagen=url_publica(n.attrs['src'],url)
                        if imagen and urlsplit(imagen).path.lower().endswith(('.jpg','.jpeg','.png')):docs.append({'url':imagen,'titulo':titulo})
        detalle=next((l['url'] for l in links if re.search(r'ver detalle|mas informacion|continuar leyendo',norm(l['texto']))),None)
        objeto=re.search(r'\bobjeto\s*[:.\-]?\s*(.*?)(?=\s*(?:fecha de apertura|apertura|venta de pliego|informes y consultas)\b|$)',texto,re.I)
        publicacion=re.search(r'fecha de publicacion\s*:\s*[^\d]*(\d{1,2}/\d{1,2}/20\d{2})',norm(texto))
        apertura=re.search(r'(?:fecha de )?apertura\s*:\s*(.*)',texto,re.I)
        fecha_apertura=apertura[1] if apertura else None
        if fecha_apertura:fecha_apertura=re.sub(r'^(?:(?:fecha de )?apertura\s*:\s*)+','',fecha_apertura,flags=re.I)
        p=ps[0];evento='|'.join(sorted(set(EVENTO.findall(norm(texto))))) or None
        # Señales del anexo sólo si identifica este mismo procedimiento.
        especiales=[]
        for d in docs:
            etiqueta=d['titulo'].replace('_','/');procedimientos=procesos(etiqueta)
            if any(q['tipo']==p['tipo'] and q['numero'].replace('-','/')==p['numero'].replace('-','/') for q in procedimientos):
                especiales.extend(EVENTO.findall(norm(etiqueta)))
        if especiales:evento='|'.join(sorted(set((evento or '').split('|')+especiales)-{''}))
        # datePublished pertenece al artículo concreto, no a la fecha de apertura.
        tiempos=[n.attrs.get('datetime') for b in bloques if isinstance(b,Nodo) for n in b.iter() if n.tag=='time' and n.attrs.get('itemprop')=='datePublished' and n.attrs.get('datetime')]
        fecha_publicacion=publicacion[1] if publicacion else (tiempos[0] if len(set(tiempos))==1 else None)
        resultados.append({'titulo':texto,'objeto':objeto[1].strip() if objeto else texto,'url':detalle or url,'evidencia_url':url,'documentos':docs,'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'procedimiento':p['procedimiento'],'evento_publicado':evento,'llamado_especial':bool(evento),'situacion_publicada':situacion(texto),'fecha_publicacion_texto':fecha_publicacion,'fecha_apertura_texto':fecha_apertura,'detalle_completo':bool(objeto) or (not docs and len(texto)>len(titulo)+80),'registro_estructurado':bool(objeto)})
    return resultados

def boletin_santafe(raiz,url,config):
    """Atribuye cada aviso al organismo publicado; no al editor del boletín."""
    from extractores import Nodo,procesos,norm,excluido,ADJUNTOS,EVENTO
    from oportunidades import fecha
    if 'licitaciones' not in url and not config.get('boletin_documento'):return []
    bloques=[n for n in raiz.iter() if n.tag in ('p','h1','h2','h3','h4','h5','h6') and not excluido(n) and n.text]
    grupos=[];actual=None
    patron=r'^(?:municipalidad de|comuna de|hospital|samco|s\.a\.m\.c\.o\.|ministerio de|empresa provincial de la energia|aguas santafesinas|aeropuerto internacional|ente administrador|direccion provincial de|universidad nacional|instituto|poder judicial|administradora tributaria)\b'
    for n in bloques:
        txt=n.text
        es_org=len(txt)<180 and re.match(patron,norm(txt)) and txt.upper()==txt
        if es_org:
            actual={'organismo':txt,'bloques':[]};grupos.append(actual)
        elif actual:actual['bloques'].append(n)
    registros=[]
    aliases={'empresa provincial de la energia':'EPE','aguas santafesinas s.a.':'ASSA','aeropuerto internacional rosario':'Aeropuerto Internacional Rosario'}
    for g in grupos:
        org=aliases.get(norm(g['organismo']),g['organismo'].title())
        comuna=re.match(r'^(?:municipalidad|comuna) de (.+)$',org,re.I)
        localidad=comuna[1].strip() if comuna else None
        texto='\n'.join(n.text for n in g['bloques'])
        # Una mención repetida de un mismo llamado no crea un aviso adicional.
        ps=procesos(texto);unicos={p['procedimiento'] for p in ps}
        for proc in dict.fromkeys(p['procedimiento'] for p in ps):
            p=next(p for p in ps if p['procedimiento']==proc)
            if len(unicos)>1:
                fin=next((q['start'] for q in ps if q['start']>p['start'] and q['procedimiento']!=proc),len(texto))
                # offsets son sobre texto normalizado; conservar sólo el rango observado.
                fragmento=norm(texto)[p['start']:fin]
            else:fragmento=texto
            docs=[{'url':l['url'],'titulo':l['texto']} for n in g['bloques'] for l in n.enlaces(url) if urlsplit(l['url']).path.lower().endswith(ADJUNTOS)] if len(unicos)==1 else []
            evento='|'.join(sorted(set(EVENTO.findall(norm(fragmento))))) or None
            registros.append({'organismo':org,'localidad':localidad,'provincia':config.get('provincia','Santa Fe'),'titulo':p['procedimiento']+' '+fragmento,'objeto':fragmento,'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'procedimiento':p['procedimiento'],'url':url,'evidencia_url':url,'documentos':docs,'evento_publicado':evento,'llamado_especial':bool(evento),'detalle_completo':True,'fecha_publicacion_texto':fecha(unquote(url)),'es_fuente_complementaria':True})
    return registros


def boletin_texto(texto,url,config):
    from html import escape
    from extractores import DOM
    html=''.join('<p>'+escape(linea.strip())+'</p>' for linea in texto.splitlines() if linea.strip())
    return boletin_santafe(DOM(html).root,url,{**config,'boletin_documento':True})


def endpoints_vgg(dom,html,url):
    from extractores import url_publica
    from urllib.parse import urljoin,urlencode
    m=re.search(r"url:\s*['\"](scripts/licitaciones/licitaciones-registros\.php)['\"]",html)
    if not m:return []
    base=next((url_publica(n.attrs['href'],url) for n in dom.root.iter() if n.tag=='base' and n.attrs.get('href')),url)
    anios=sorted({n.attrs['data-valor'] for n in dom.root.iter() if re.fullmatch(r'20\d{2}',n.attrs.get('data-valor',''))},reverse=True)
    tipos={n.attrs['data-id'] for n in dom.root.iter() if n.tag=='li' and n.attrs.get('data-id') in ('apertura','licitadas')}
    actual=next((n.attrs.get('value') for n in dom.root.iter() if n.attrs.get('id')=='anioHidden'),None)
    return [urljoin(base,m[1])+'?'+urlencode({'anio':a,'tipo':t}) for a in anios for t in sorted(tipos) if t!='apertura' or a==actual]

def extraer_vgg(datos,url):
    from extractores import url_publica,procesos
    from urllib.parse import parse_qs,urlsplit,urljoin
    from decimal import Decimal,InvalidOperation
    import json
    filas=json.loads(datos)
    if not isinstance(filas,list):raise ValueError('Esquema VGG no reconocido: se esperaba listado JSON')
    registros=[];publicada=parse_qs(urlsplit(url).query).get('tipo',[''])[0]
    for f in filas:
        if not isinstance(f,dict) or not f.get('objeto'):raise ValueError('Fila VGG sin objeto reconocido')
        objeto=str(f['objeto'])
        identificacion=re.sub(r'(?i)(licitaci[oó]n\s+(?:p[uú]blica|privada))\s+(?:nacional(?:\s+e\s+internacional)?|internacional)',r'\1',objeto)
        ps=procesos(identificacion);p=ps[0] if len(ps)==1 else {}
        presupuesto=None
        if f.get('presupuesto_raw') is not None:
            try:
                importe=Decimal(str(f['presupuesto_raw']))
                if importe.is_finite():presupuesto={'importe':str(importe),'moneda':None}
            except InvalidOperation:pass
        documento=url_publica(f.get('archivo_url') or '',urljoin(url,'/')) if f.get('archivo_url') else None
        registros.append({'titulo':objeto,'objeto':objeto,'numero_procedimiento':p.get('numero'),'tipo_procedimiento':p.get('tipo'),'procedimiento':p.get('procedimiento'),'registro_estructurado':True,'detalle_completo':True,'url':documento or url,'evidencia_url':url,'documentos':[{'url':documento,'titulo':'Pliego' if publicada=='apertura' else 'Adjudicación'}] if documento else [],'fecha_apertura_texto':f.get('apertura_raw') or f.get('apertura'),'presupuesto':presupuesto,'presupuesto_texto':str(f['presupuesto']) if f.get('presupuesto') is not None else None,'evidencias_campos':{'presupuesto':{'url':url,'texto':str(f.get('presupuesto_raw'))}} if presupuesto is not None else {},'id_origen':f.get('id')})
    return registros
