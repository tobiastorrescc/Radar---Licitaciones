"""Secciones de convocatorias encabezadas: datos y adjuntos hasta el siguiente título."""
from urllib.parse import urlsplit, unquote
import re

def fichas_ramirez(raiz,url):
    """Número en h2; modalidad en la sección, nunca en teléfonos o importes."""
    from extractores import norm,procesos,ADJUNTOS,EVENTO,excluido
    cabeceras=[re.sub(r'^historico:\s*','',norm(n.text)) for n in raiz.iter()
               if n.tag=='h1' or (n.tag=='h2' and norm(n.text).startswith('historico:'))]
    tipos={'licitaciones publicas':'licitacion publica',
           'licitaciones privadas':'licitacion privada',
           'concursos de precios':'concurso de precios'}
    tipo=next((tipos[t] for t in cabeceras if t in tipos),None)
    if not tipo:return []
    registros=[]
    for ficha in raiz.iter():
        if not ficha.clase('ficha-listado') or excluido(ficha):continue
        numeros=[n.text for n in ficha.iter() if n.tag=='h2' and re.fullmatch(r'\d{1,6}\s*/\s*20\d{2}',n.text)]
        objetos=[n.text for n in ficha.iter() if n.tag=='h3' and n.text]
        if len(numeros)!=1 or len(objetos)!=1:continue
        p=procesos(tipo+' '+numeros[0])[0]
        campos={}
        for dl in ficha.iter():
            if dl.tag!='dl':continue
            etiquetas=[norm(n.text).rstrip(':') for n in dl.iter() if n.tag=='dt']
            valores=[n.text for n in dl.iter() if n.tag=='dd']
            if len(etiquetas)==1 and len(valores)==1:campos[etiquetas[0]]=valores[0]
        docs=[{'url':l['url'],'titulo':l['texto']} for l in ficha.enlaces(url)
              if urlsplit(l['url']).path.lower().endswith(ADJUNTOS)]
        evento='|'.join(sorted(set(EVENTO.findall(norm(ficha.text))))) or None
        registros.append({'titulo':p['procedimiento']+' '+objetos[0],
            'objeto':objetos[0],'procedimiento':p['procedimiento'],
            'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],
            'url':url,'evidencia_url':url,'documentos':docs,
            'fecha_apertura_texto':campos.get('apertura'),
            'presupuesto_texto':campos.get('presupuesto'),
            'fecha_publicacion_texto':None,
            'situacion_publicada':'ADJUDICADA' if campos.get('adjudicado') else None,
            'evento_publicado':evento,'llamado_especial':bool(evento),
            'campos_oficiales':campos,'detalle_completo':True,'registro_estructurado':True})
    return registros

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

def acordeones_zarate(raiz,url):
    """La convocatoria hereda año del acordeón padre, nunca de otra licitación."""
    from extractores import Nodo,norm,ADJUNTOS,EVENTO
    resultado=[]
    def resumen(n):return next((c.text for c in n.children if isinstance(c,Nodo) and c.tag=='summary'),'')
    for n in raiz.iter():
        if n.tag!='details':continue
        titulo=resumen(n);m=re.match(r'n[º°o.]*\s*(\d+)\s+["“]?(.*)',norm(titulo))
        if not m:continue
        anio=next((a[1] for p in list(n.padres())[1:] if (a:=re.search(r'licitaciones publicas\s*\|?\s*ano\s*(20\d{2})',norm(resumen(p))))),None)
        if not anio:continue
        numero=str(int(m[1]))+'/'+anio
        # Objeto literal publicado en summary, con número aislado del texto.
        objeto=re.sub(r'^N[º°o.]*\s*\d+\s*','',titulo,flags=re.I).strip(' "“”')
        if len(objeto)<8:continue
        docs=[{'url':l['url'],'titulo':l['texto']} for l in n.enlaces(url) if urlsplit(l['url']).path.lower().endswith(ADJUNTOS)]
        evento='|'.join(sorted(set(EVENTO.findall(norm(titulo))))) or None
        resultado.append({'titulo':'Licitación Pública '+numero+' '+objeto,'objeto':objeto,'procedimiento':'licitacion publica '+numero,
            'numero_procedimiento':numero,'tipo_procedimiento':'licitacion publica','url':url,'evidencia_url':url,
            'documentos':docs,'detalle_completo':True,'registro_estructurado':True,'evento_publicado':evento,'llamado_especial':bool(evento)})
    return resultado

def endpoint_funes(html,url):
    """Endpoint y método publicados en el inicializador DataTables de licitaciones."""
    from extractores import url_publica
    if 'id="licitacionesTable"' not in html and "id='licitacionesTable'" not in html:return None
    m=re.search(r'''const\s+url\s*=\s*['"]([^'"]*/data-licitaciones-web\.ajax\.php)['"]''',html)
    if not m or not re.search(r"type:\s*['\"]POST['\"]",html):return None
    destino=url_publica(m[1],url)
    return destino if destino and urlsplit(destino).hostname==urlsplit(url).hostname else None

def extraer_funes(datos,url):
    from extractores import procesos,url_publica
    import json
    data=json.loads(datos)
    if not isinstance(data,dict) or not isinstance(data.get('data'),list):raise ValueError('DataTables de Funes sin listado data')
    total=data.get('recordsTotal');filtrado=data.get('recordsFiltered')
    if not isinstance(total,int) or total<0 or filtrado!=total:raise ValueError('Total DataTables ausente o respuesta filtrada')
    resultado=[]
    for f in data['data']:
        if not isinstance(f,dict) or not isinstance(f.get('titulo_licitacion'),str):raise ValueError('Fila de Funes sin título verificable')
        titulo=f['titulo_licitacion'];rotulo=str(f.get('numero_licitacion') or '')
        ps=procesos(rotulo) or procesos(titulo);p=ps[0] if len(ps)==1 else {}
        docs=[]
        for d in f.get('documentos') or []:
            if not isinstance(d,dict):raise ValueError('Documento de Funes no reconocido')
            enlace=url_publica(d.get('url') or '',url)
            if enlace:docs.append({'url':enlace,'titulo':d.get('titulo') or 'Documento'})
        objeto_valido=bool(re.search(r'[A-Za-zÀ-ÿ]{3,}',titulo))
        resultado.append({'titulo':rotulo+' '+titulo,'objeto':titulo if objeto_valido else None,'numero_procedimiento':p.get('numero'),'tipo_procedimiento':p.get('tipo'),'procedimiento':p.get('procedimiento'),
            'registro_estructurado':True,'detalle_completo':objeto_valido,'url':url,'evidencia_url':url,'documentos':docs,
            'fecha_publicacion_texto':f.get('date_created_licitacion'),'id_origen':f.get('id_licitacion'),'numero_oficial_sin_interpretar':f.get('numero_licitacion')})
    return resultado,total,data['data']


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


def fichas_villaelisa(raiz,url):
    """Columnas N°, decretos, pliego y concepto, separadas por fila publicada."""
    from extractores import norm,procesos,excluido,ADJUNTOS,EVENTO
    tipos={'licitaciones publicas':'licitacion publica','licitaciones privadas':'licitacion privada','concursos de precios':'concurso de precios'}
    modo=next((tipos.get(norm(n.text)) for n in raiz.iter() if n.tag=='h1' and norm(n.text) in tipos),None)
    if not modo:return []
    grillas=[n for n in raiz.iter() if n.clase('dvmd_tm_rblock') and not excluido(n)]
    if grillas:
        registros=[]
        for bloque in grillas:
            celdas={}
            for celda in bloque.iter():
                col=re.search(r'\bdvmd_tm_col_(\d+)\b',celda.attrs.get('class',''))
                if col and celda.clase('dvmd_tm_tdata'):celdas[int(col[1])]=celda
            if 0 not in celdas:continue
            numero=celdas[0].text
            if re.fullmatch(r'\d{1,6}\s*/\s*(?:20)?\d{2}',numero):numero=modo+' '+numero
            ps=procesos(numero)
            if len(ps)!=1:continue
            p=ps[0];objeto=celdas[4].text if 4 in celdas else None
            docs={}
            for col,celda in celdas.items():
                if col not in (1,2,3):continue
                for l in celda.enlaces(url):
                    if not urlsplit(l['url']).path.lower().endswith(ADJUNTOS):continue
                    es_decreto=col in (1,2) or 'decreto' in norm(l['texto']) or 'decreto' in norm(urlsplit(l['url']).path.rsplit('/',1)[-1])
                    titulo=('Decreto ' if es_decreto else 'Pliego ')+l['texto']
                    if l['url'] in docs and docs[l['url']]['titulo'].startswith('Decreto '):continue
                    docs[l['url']]={'url':l['url'],'titulo':titulo}
            evento='|'.join(sorted(set(EVENTO.findall(norm(bloque.text))))) or None
            registros.append({'titulo':p['procedimiento']+' '+(objeto or ''),'objeto':objeto,
                'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'procedimiento':p['procedimiento'],
                'url':url,'evidencia_url':url,'documentos':list(docs.values()),'detalle_completo':bool(objeto),
                'registro_estructurado':bool(objeto),'evento_publicado':evento,'llamado_especial':bool(evento),
                'fecha_apertura_texto':None,'fecha_publicacion_texto':None})
        return registros
    def numero(n):
        if excluido(n) or n.tag not in ('p','span','td'):return None
        t=n.text
        if re.fullmatch(r'\d{1,6}\s*/\s*(?:20)?\d{2}',t):
            if n.tag not in ('p','td'):return None
            t=modo+' '+t
        ps=procesos(t)
        return ps[0] if len(ps)==1 and ps[0]['start']==0 and ps[0]['end']==len(norm(t)) else None
    candidatos=[(n,numero(n)) for n in raiz.iter() if numero(n)]
    registros={}
    for n,p in candidatos:
        for cont in n.padres():
            if cont.tag in ('root','html','body'):break
            conceptos=[x for x in cont.iter() if x.tag in ('h4','h5','h6') and norm(x.text).rstrip(':')=='concepto']
            claves={x['procedimiento'] for el,x in candidatos if any(padre is cont for padre in el.padres())}
            if len(claves)>1:break
            if len(conceptos)!=1:continue
            campo=conceptos[0]
            for padre in campo.padres():
                if padre is cont:break
                if len(padre.text)>len(campo.text):campo=padre;break
            objeto=re.sub(r'^concepto\s*:?\s*','',campo.text,flags=re.I).strip()
            if norm(objeto)=='concepto':objeto=None
            docs={}
            for l in cont.enlaces(url):
                if not urlsplit(l['url']).path.lower().endswith(ADJUNTOS):continue
                titulo=l['texto'];anterior=docs.get(l['url'])
                if anterior and 'decreto' in norm(anterior['titulo']):continue
                docs[l['url']]={'url':l['url'],'titulo':titulo}
            evento='|'.join(sorted(set(EVENTO.findall(norm(cont.text))))) or None
            r={'titulo':p['procedimiento']+' '+(objeto or ''),'objeto':objeto,'numero_procedimiento':p['numero'],
               'tipo_procedimiento':p['tipo'],'procedimiento':p['procedimiento'],'url':url,'evidencia_url':url,
               'documentos':list(docs.values()),'detalle_completo':bool(objeto),'registro_estructurado':bool(objeto),
               'evento_publicado':evento,'llamado_especial':bool(evento),'fecha_apertura_texto':None,'fecha_publicacion_texto':None}
            registros[p['procedimiento']]=r;break
    return list(registros.values())


def extraer_assa(datos,url):
    """API pública observada en assets oficiales. Sin filtros por tipo, rubro o estado."""
    import json
    from datetime import datetime
    import oportunidades as o
    from extractores import DOM,norm,url_publica
    data=json.loads(datos)
    if data.get('success') is not True or not isinstance(data.get('content'),dict):raise ValueError('ASSA: respuesta pública no reconocida')
    content=data['content'];detalle='elements' not in content
    filas=[content] if detalle else content['elements']
    if not isinstance(filas,list):raise ValueError('ASSA: elements no es listado')
    meta=content.get('page',{}) if not detalle else {}
    if not detalle and not all(k in meta for k in ('totalElements','totalPages','number')):raise ValueError('ASSA: paginación sin total comprobable')
    registros=[]
    def fecha_local(valor):
        if not valor:return None
        d=datetime.fromisoformat(valor.replace('Z','+00:00'))
        if d.tzinfo is None:raise ValueError('ASSA: fecha API sin zona horaria')
        return d.astimezone(o.ZONA).strftime('%Y-%m-%d %H:%M')
    for f in filas:
        uuid=f.get('uuid');numero=f.get('numeroPliego');tipo=(f.get('tipoPliego') or {}).get('nombreTipo');titulo=f.get('titulo')
        if not uuid or not numero or not tipo or not titulo:raise ValueError('ASSA: ficha sin identidad/objeto comprobable')
        objeto=DOM(f.get('objetoLicitacion') or titulo).root.text
        ficha=url_publica('/api/v1/publico/pliego/'+uuid,url)
        apertura=sorted(a['fechaApertura'] for a in f.get('aperturasSobre',[]) if a.get('fechaApertura'))
        documentos=[]
        for adjunto in f.get('documentosAdjuntos',[])+f.get('documentosGenericos',[])+f.get('circulares',[]):
            for campo in ('url','urlDocumento','enlace'):
                u=url_publica(adjunto.get(campo) or '',url)
                if adjunto.get(campo) and u:documentos.append({'url':u,'titulo':adjunto.get('nombre') or adjunto.get('titulo') or 'Adjunto oficial'});break
        estados={'ESTADO_ADJUDICADO':'ADJUDICADA','ESTADO_DESIERTO':'DESIERTA','ESTADO_EN_EVALUACION':'EN_EVALUACION','ESTADO_DADO_DE_BAJA':'FINALIZADA'}
        registros.append({'titulo':tipo+' Nº '+str(numero)+' — '+titulo,'objeto':objeto,'url':ficha,'evidencia_url':ficha,
            'numero_procedimiento':str(numero),'tipo_procedimiento':norm(tipo),'registro_estructurado':True,
            'id_origen':uuid,'identidad_ambito':uuid,'numero_oficial_sin_interpretar':str(numero),
            'fecha_apertura_texto':fecha_local(apertura[0]) if apertura else None,
            'fecha_limite_presentacion_texto':fecha_local(f.get('fechaLimiteOferta')),
            # Fecha sugerida no prueba publicación. Se conserva íntegra en la evidencia.
            'fecha_publicacion':None,'campos_oficiales':f,'documentos':documentos,
            'situacion_publicada':estados.get(f.get('estado')),'detalle_completo':bool(objeto),'rango_evidencia':3})
    return registros,meta,detalle


def extraer_chajari(datos,url):
    """Consultas públicas POST del cliente municipal; no registra oferentes ni ofertas."""
    import json
    from datetime import datetime,timezone
    import oportunidades as o
    from extractores import procesos,url_publica
    data=json.loads(datos)
    if data.get('error') or not isinstance(data.get('result'),list):raise ValueError('Chajarí: consulta pública no reconocida')
    filas=data['result'];registros=[]
    for f in filas:
        tipo={'publica':'Licitación pública','privada':'Licitación privada'}.get(f.get('type'))
        if not tipo or not f.get('name') or not f.get('id') or not f.get('title'):raise ValueError('Chajarí: procedimiento sin identidad/objeto comprobable')
        ps=procesos(tipo+' Nº '+f['name'])
        if len(ps)!=1:raise ValueError('Chajarí: número de procedimiento no reconocido')
        p=ps[0];ficha=url_publica('/licitaciones?state='+f['state']+'?id='+str(f['id']),url)
        def fecha_local(valor):
            if not valor:return None
            # El cliente oficial observado utiliza Date.UTC al mostrar estos campos.
            return datetime.fromisoformat(valor).replace(tzinfo=timezone.utc).astimezone(o.ZONA).strftime('%Y-%m-%d %H:%M')
        documentos=[]
        adjunto=f.get('pliego_y_decreto_id')
        if adjunto:
            documentos=[{'url':ficha,'titulo':'Pliego y decreto — descarga pública desde el procedimiento',
                'consulta_post':{'url':url_publica('/return_file',url),'json':{'atta_id':str(adjunto),'file_name':'pliego_y_decreto','licitacion_id':f['id']}}}]
        monto=f.get('presupuesto_oficial');presupuesto={'importe':str(monto),'moneda':None} if isinstance(monto,(int,float)) and monto>=0 else None
        registros.append({'titulo':tipo+' Nº '+f['name']+' — '+f['title'],'objeto':f['title'],
            'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'procedimiento':p['procedimiento'],
            'registro_estructurado':True,'id_origen':str(f['id']),'url':ficha,'evidencia_url':ficha,
            'evidencias_campos':{'presupuesto':{'url':ficha,'consulta_url':url,'metodo':'POST','texto':'presupuesto_oficial: '+str(monto)}},
            'fecha_apertura_texto':fecha_local(f.get('fecha_hora_apertura')),'fecha_limite_presentacion_texto':fecha_local(f.get('fecha_hora_cierre')),
            'presupuesto':presupuesto,'documentos':documentos,
            'situacion_publicada':{'adjudicada':'ADJUDICADA','en_evaluacion':'EN_EVALUACION'}.get(f.get('state')),
            'campos_oficiales':{k:f.get(k) for k in ('id','name','title','type','state','fecha_hora_apertura','fecha_hora_cierre','presupuesto_oficial','pliego_y_decreto_id')},
            'detalle_completo':True,'rango_evidencia':3})
    return registros,len(filas)


def carmen_areco(raiz,url):
    """Tarjetas oficiales: el año rotulado no se sustituye por el año de descarga."""
    from extractores import procesos,url_publica,situacion,norm
    import re
    rs=[]
    for n in raiz.iter():
        if n.tag!='article' or n.attrs.get('data-cda-section')!='licitaciones':continue
        titulo=n.attrs.get('data-cda-title','');anio=n.attrs.get('data-cda-year','');ps=procesos(titulo)
        if not ps or not re.fullmatch(r'20\d{2}',anio):continue
        p=ps[0];numero=p['numero'] if '/' in p['numero'] else p['numero']+'/'+anio
        doc=url_publica(n.attrs.get('data-cda-url',''),url)
        if not doc:continue
        apertura=re.search(r'apertura\s+(\d{1,2}/\d{1,2}/20\d{2})',norm(n.attrs.get('data-cda-period','')))
        rs.append({'titulo':titulo,'objeto':titulo,'numero_procedimiento':numero,'tipo_procedimiento':p['tipo'],'procedimiento':p['tipo']+' '+numero,'url':doc,'evidencia_url':url,'documentos':[{'url':doc,'titulo':titulo}],'fecha_apertura_texto':apertura[1] if apertura else None,'detalle_completo':True,'registro_estructurado':True,'situacion_publicada':situacion(n.text),'evento_publicado':None})
    return rs
