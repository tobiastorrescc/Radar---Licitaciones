"""Cláusulas de recepción explícitas: nunca equipara apertura a cierre sin texto."""
import re
from datetime import datetime,timedelta
import oportunidades as o

def clausula(texto,registro,url,sha256=None):
    # No concatenar párrafos de otros avisos. El llamador debe identificar la ficha.
    t=o.norm(texto)
    apertura=registro.get('fecha_hora_apertura')
    for m in re.finditer(r'\b(?:presentacion\s+(?:de\s+)?(?:(?:las|los)\s+)?(?:ofertas|propuestas|sobres)|recepcion\s+(?:de\s+)?(?:ofertas|propuestas|sobres)|(?:ofertas|propuestas|sobres)\s+se\s+recibiran|se\s+recibiran\s+(?:las\s+)?(?:ofertas|propuestas)|presentacion\s*:\s*hasta)',t):
        cita=t[m.start():m.start()+450]
        cita=re.split(r'\b(?:consultas|valor del pliego|presupuesto oficial|lugar de apertura|forma de pago)\b',cita)[0]
        cita=re.split(r'\bapertura\s+(?:de\s+)?(?:las\s+)?(?:ofertas|sobres|propuestas)\s*:',cita)[0]
        if re.search(r'\b(?:salvo|excepto|siempre que)\b',cita):continue
        limite=None;fragmento=None
        hasta=re.search(r'\bhasta\b\s*(.{0,160})',cita)
        if hasta:
            raw=hasta[1];fecha=o.fecha(cita)
            h=re.search(r'(?<!\d)([01]?\d|2[0-3]):([0-5]\d)|(?<!\d)([01]?\d|2[0-3])\.([0-5]\d)\s*(?:hs|h|horas)\b',raw)
            if fecha:
                limite=fecha+(f'T{int(h[1] or h[3]):02d}:{h[2] or h[4]}:00-03:00' if h else '')
                fragmento=raw
            elif apertura and re.search(r'^(?:(?:el|la)\s+)?(?:mismo\s+)?(?:dia y hora|fecha y hora|momento|horario)\s+(?:fijad[oa]s?\s+para\s+)?(?:de\s+)?(?:la\s+)?apertura',raw):
                limite=apertura;fragmento=raw
        minutos=re.search(r'hasta\s+(\d{1,2})\s*minutos\s+antes\s+de\s+(?:la\s+)?apertura',cita)
        if minutos and apertura:
            limite=(datetime.fromisoformat(apertura)-timedelta(minutes=int(minutos[1]))).isoformat();fragmento=minutos[0]
        if limite:
            return {'fecha_limite_presentacion_texto':limite,'evidencia_recepcion':{'url':url,'sha256':sha256,'cita':cita,'fragmento_fecha':fragmento,'regla':'CLAUSULA_EXPLICITA'},'evidencia_url':url}
    return {}
