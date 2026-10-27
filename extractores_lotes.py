"""Secciones de convocatorias encabezadas: datos y adjuntos hasta el siguiente título."""
from urllib.parse import urlsplit
import re

def encabezados(raiz,url,config):
    from extractores import Nodo,procesos,norm,excluido,situacion,ADJUNTOS,EVENTO
    resultados=[]
    for h in raiz.iter():
        if h.tag not in ('h1','h2','h3','h4','h5','h6') or excluido(h):continue
        titulo=h.text
        if config.get('adaptador')=='colon-pba':titulo=titulo.replace('Licitacioón','Licitación')
        ps=procesos(titulo)
        if len({p['procedimiento'] for p in ps})!=1:continue
        hermanos=h.parent.children;pos=hermanos.index(h);bloques=[h]
        for otro in hermanos[pos+1:]:
            if isinstance(otro,Nodo):
                if otro.tag in ('h1','h2','h3','h4','h5','h6') and int(otro.tag[1])<=int(h.tag[1]):break
                if any(x.tag in ('h1','h2','h3','h4','h5','h6') and procesos(x.text) for x in otro.iter()):break
            bloques.append(otro)
        texto=titulo+' '+' '.join(b.text if isinstance(b,Nodo) else b for b in bloques[1:])
        links=[l for b in bloques if isinstance(b,Nodo) for l in b.enlaces(url)]
        extensiones=(*ADJUNTOS,*(('.jpg','.jpeg','.png') if config.get('documentos_imagen') else ()))
        docs=[{'url':l['url'],'titulo':l['texto'] or titulo} for l in links if urlsplit(l['url']).path.lower().endswith(extensiones)]
        detalle=next((l['url'] for l in links if re.search(r'ver detalle|mas informacion|continuar leyendo',norm(l['texto']))),None)
        objeto=re.search(r'\bobjeto\s*[:.\-]?\s*(.*?)(?=\s*(?:fecha de apertura|apertura|venta de pliego|informes y consultas)\b|$)',texto,re.I)
        publicacion=re.search(r'fecha de publicacion\s*:\s*[^\d]*(\d{1,2}/\d{1,2}/20\d{2})',norm(texto))
        p=ps[0];evento='|'.join(sorted(set(EVENTO.findall(norm(texto))))) or None
        resultados.append({'titulo':texto,'objeto':objeto[1].strip() if objeto else texto,'url':detalle or url,'evidencia_url':url,'documentos':docs,'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'procedimiento':p['procedimiento'],'evento_publicado':evento,'llamado_especial':bool(evento),'situacion_publicada':situacion(texto),'fecha_publicacion_texto':publicacion[1] if publicacion else None,'detalle_completo':bool(objeto) or (not docs and len(texto)>len(titulo)+80),'registro_estructurado':bool(objeto)})
    return resultados
