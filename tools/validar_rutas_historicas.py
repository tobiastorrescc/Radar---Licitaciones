"""Valida las rutas pendientes en aislamiento, sin altas ni cambios de historial."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.verificar_fuentes import ejecutar,guardar

def main():
    root=Path('work/rutas-historicas');root.mkdir(parents=True,exist_ok=True)
    fs=json.load(open('inventario/candidatas_historia.json'))['candidatos'];entradas=root/'entradas';entradas.mkdir(exist_ok=True)
    fs=[{**f,'id':'ruta-'+str(n).zfill(2)} for n,f in enumerate(fs,1)]
    for f in fs:guardar(entradas/(f['id']+'.json'),f)
    informe=ejecutar(fs,root/'verificacion.json',concurrencia=3,por_fuente=35,total=360,
        comando=lambda f,p:[sys.executable,'tools/descubrir_fuentes.py','--worker',str(entradas/(f['id']+'.json')),'--salida',str(p)])
    resultados=[]
    for f,obs in zip(fs,informe['observaciones']):
        p=Path(obs.get('resultado_archivo',''));r=json.loads(p.read_text()) if p.is_file() else {}
        resultados.append({'fuente':f,'observacion':obs,'validacion':r.get('validacion',{'estado':'PENDIENTE','motivo':'Ejecución incompleta o límite de tiempo'}),'config':r.get('config'),'oportunidades':r.get('oportunidades',[])})
    guardar(root/'resultado.json',{'github_run_id':informe['github_run_id'],'actualizado':informe['actualizado'],'fuentes':resultados,'altas_automaticas':0})
if __name__=='__main__':main()
