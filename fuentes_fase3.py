"""Avisos municipales intercalados con <br>; no convertir el índice en una compra."""
import re
import extractores as e

def santaana(dom,url):
    raiz=next((n for n in dom.root.iter() if n.clase('entry-content')),None)
    if raiz is None:return []
    salida=[]
    for parrafo in raiz.children:
        if not isinstance(parrafo,e.Nodo) or parrafo.tag!='p':continue
        grupos=[];grupo=None
        for n in parrafo.children:
            texto=n.text if isinstance(n,e.Nodo) else n
            ps=e.procesos(texto)
            if isinstance(n,e.Nodo) and n.tag=='a' and len(ps)==1:
                grupo={'p':ps[0],'titulo':texto,'textos':[],'documentos':n.enlaces(url)};grupos.append(grupo)
            elif grupo:
                grupo['textos'].append(texto)
                if isinstance(n,e.Nodo):grupo['documentos']+=n.enlaces(url)
        for g in grupos:
            texto=' '.join(g['textos']).strip();p=g['p'];ap=re.search(r'(?:se establece|se fija)\s+el\s+dia\s+(.{0,160}?)\s+la\s+fecha\s+para\s+la\s+apertura',e.norm(texto))
            obj=re.split(r'(?i)se establece el dia|se establece el día|se fija el día',texto)[0].strip(' —\n')
            docs=[{'url':x['url'],'titulo':x['texto']} for x in g['documentos'] if x['url'].lower().split('?')[0].endswith(e.ADJUNTOS)]
            secundarios={q['numero'] for q in e.procesos(texto)}
            conflicto=bool(secundarios and p['numero'] not in secundarios)
            salida.append({'url':url,'evidencia_url':url,'titulo':g['titulo']+' '+obj,'objeto':obj,'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'procedimiento':p['procedimiento'],'fecha_apertura_texto':ap[1] if ap else None,'documentos':docs,'texto_documento':texto,'registro_estructurado':True,'detalle_completo':bool(obj and ap and not conflicto),'numero_conflictivo_publicado':conflicto,'observacion_extraccion':'El número del enlace difiere del texto del aviso' if conflicto else None})
    return salida
