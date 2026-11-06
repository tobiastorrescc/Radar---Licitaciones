"""Acceso y recuperación documental explícitos, sin convertir errores en ceros."""
import oportunidades as o
CRITICAS={'fuente-003','fuente-087','fuente-060'}

def evaluar(obs,registros,eventos=()):
    registros=[r for r in registros if obs['url'] in ({r.get('fuente')}|set(r.get('fuentes_observadas',[])))]
    archivos=[r for r in registros if r.get('recuperacion_archivo')]
    comprobados=[r for r in archivos if not r.get('requiere_revalidacion')]
    estado=obs['estado'];correcta=estado in ('OPERATIVA','SIN_PUBLICACIONES') and not obs.get('errores') and not obs.get('limites')
    if comprobados and not correcta:revision='RECUPERADA_MEDIANTE_ARCHIVO_MANUAL'
    elif correcta:revision='REVISADA_CON_NOVEDADES' if any(e.get('fuente')==obs['url'] and e.get('clasificacion_novedad')=='NUEVO_CONFIRMADO' for e in eventos) else 'REVISADA_CORRECTAMENTE_SIN_NOVEDADES'
    elif registros and obs.get('publicaciones_detectadas',0)>0:revision='REVISADA_PARCIALMENTE'
    else:revision='FUENTE_INACCESIBLE' if estado in ('BLOQUEADA','ERROR','TIEMPO_FUENTE','TIEMPO_TOTAL','CANCELADA') else 'PENDIENTE_DE_REVISION'
    return {'id':obs.get('id'),'url':obs['url'],'estado_revision_critica':revision,'estado_acceso_directo':estado,'publicaciones_directas':obs.get('publicaciones_detectadas',0),'archivos_comprobados':len(comprobados),'archivo_pendiente_revalidacion':len(archivos)-len(comprobados),'no_equivale_a_cero_publicaciones':not correcta,'errores':obs.get('errores',[])}
