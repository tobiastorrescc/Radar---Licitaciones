"""Construye una propuesta autocontenida; nunca instala ni habilita workflows."""
import argparse
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SALIDA=ROOT/'despliegue/github-actions/programar-piloto.yml.propuesto'
SCRIPT='f28e40c7f34bde8b3046d885e986cb6290c5673b'
UPLOAD='ea165f8d65b6e75b540449e92b4886f43607fa02'

def generar(habilitado=False):
    codigo=(ROOT/'despliegue/github-actions/programador.cjs').read_text()
    paso='''const fs=require('node:fs');
const path=require('node:path');
function cargarRadar() {
  const module={exports:{}};
CODIGO
  return module.exports;
}
const archivo=path.join(process.env.RUNNER_TEMP,'radar-programador.cjs');
fs.writeFileSync(archivo,'module.exports=('+cargarRadar.toString()+')();');
const radar=cargarRadar();
try {
  if(context.eventName==='workflow_dispatch' && context.payload.inputs?.accion==='probar_alerta') {
    throw new Error('PRUEBA CONTROLADA AUTORIZADA: fallo deliberado del programador sin despachar el piloto ni cambiar su historial');
  } else if(context.eventName==='workflow_run') {
    const r=await radar.revisarEvento({github,context});
    core.info(JSON.stringify(r));
  } else if((context.eventName==='schedule' && context.payload.schedule==='30 9 * * *') || context.payload.inputs?.accion==='supervisar') {
    const r=await radar.vigilar({github,context});
    await core.summary.addHeading('Supervisión del piloto').addRaw(JSON.stringify(r)).write();
  } else {
    const p=await radar.preparar({github,context});
    core.setOutput('iniciar',String(p.iniciar));
    fs.writeFileSync(path.join(process.env.RUNNER_TEMP,'piloto-plan.json'),JSON.stringify(p.plan));
    fs.writeFileSync(path.join(process.env.RUNNER_TEMP,'piloto-journal.json'),JSON.stringify({fecha:p.plan.fecha,padre:context.runId,estado:'ANTES_DEL_POST',plan:p.plan}));
    await core.summary.addHeading('Programador del piloto').addRaw(p.iniciar?'Preparado: subir journal antes de solicitar.':`Sin nuevo despacho: ${p.run.html_url}`).write();
  }
} catch(e) {
  fs.writeFileSync(path.join(process.env.RUNNER_TEMP,'piloto-error.txt'),String(e.message).slice(0,2000));
  throw e;
}'''.replace('CODIGO','\n'.join('  '+l for l in codigo.splitlines()))
    dispatch='''const fs=require('node:fs');
const path=require('node:path');
const radar=require(path.join(process.env.RUNNER_TEMP,'radar-programador.cjs'));
try {
  const plan=JSON.parse(fs.readFileSync(path.join(process.env.RUNNER_TEMP,'piloto-plan.json'),'utf8'));
  const r=await radar.despachar({github,context,plan});
  await core.summary.addHeading('Solicitud enviada; no confirma finalización').addRaw(JSON.stringify(r)).write();
} catch(e) {
  fs.writeFileSync(path.join(process.env.RUNNER_TEMP,'piloto-error.txt'),String(e.message).slice(0,2000));
  throw e;
}'''
    alert='''const fs=require('node:fs');
const path=require('node:path');
const radar=require(path.join(process.env.RUNNER_TEMP,'radar-programador.cjs'));
const f=path.join(process.env.RUNNER_TEMP,'piloto-error.txt');
const motivo=fs.existsSync(f)?fs.readFileSync(f,'utf8'):'Falló un paso del programador, incluido el journal. Revisar logs.';
const r=await radar.alertar({github,context,motivo});
await core.summary.addHeading('ALERTA: revisar piloto').addRaw(r.url).write();'''
    def ind(s):return '\n'.join('            '+l for l in s.splitlines())+'\n'
    resultado='''# Programador autorizado: sólo este archivo se instala en main.
# Sin checkout, PAT, secretos externos ni escritura de contenidos.
name: Programador del piloto aislado
run-name: Programador piloto ${{ inputs.accion == 'probar_alerta' && 'prueba-alerta' || 'diario' }}
on:
  workflow_dispatch:
    inputs:
      accion:
        description: 'Ejecutar una vez, supervisar sin consulta o probar una alerta con fallo deliberado'
        type: choice
        options: [ejecutar, supervisar, probar_alerta]
        default: ejecutar
  schedule:
    - cron: '0 8 * * *' # GitHub no garantiza puntualidad.
      timezone: 'America/Argentina/Buenos_Aires'
    - cron: '30 9 * * *' # 09:30 Argentina: supervisar sin redisparar.
      timezone: 'America/Argentina/Buenos_Aires'
  workflow_run:
    workflows: ['Programador del piloto aislado', 'Radar piloto aislado']
    types: [completed]
    branches: ['mejora/radar-auditable']
permissions:
  contents: read
  actions: write
  issues: write
concurrency:
  group: programador-piloto-${{ github.event_name == 'workflow_run' && github.event.workflow_run.id || 'diario' }}
  cancel-in-progress: false
jobs:
  programar-o-supervisar:
    if: github.repository == 'tobiastorrescc/Radar---Licitaciones' && github.ref == 'refs/heads/main' && (github.event_name != 'schedule' || (PROGRAMACION_HABILITADA && vars.RADAR_PILOTO_PROGRAMADOR_HABILITADO != 'false')) && (github.event_name != 'workflow_run' || (github.event.workflow_run.event == 'workflow_dispatch' && contains(github.event.workflow_run.display_title, ' programado')))
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Preparar o supervisar sin ejecutar código de la rama del piloto
        id: preparar
        uses: actions/github-script@'''+SCRIPT+'''
        with:
          retries: 0
          script: |
'''+ind(paso)+'''      - name: Guardar journal antes de cualquier POST
        if: steps.preparar.outputs.iniciar == 'true'
        uses: actions/upload-artifact@'''+UPLOAD+'''
        with:
          name: piloto-journal-${{ github.run_id }}
          path: ${{ runner.temp }}/piloto-journal.json
          retention-days: 90
          if-no-files-found: error
      - name: Solicitar una sola ejecución del piloto
        if: success() && steps.preparar.outputs.iniciar == 'true'
        uses: actions/github-script@'''+SCRIPT+'''
        with:
          retries: 0
          script: |
'''+ind(dispatch)+'''      - name: Alertar fallos de despacho, ejecución, supervisión o respaldo
        if: failure()
        uses: actions/github-script@'''+SCRIPT+'''
        with:
          retries: 0
          script: |
'''+ind(alert)

    return resultado.replace('PROGRAMACION_HABILITADA','true' if habilitado else 'false')

def main():
    p=argparse.ArgumentParser();p.add_argument('--comprobar',action='store_true');a=p.parse_args()
    esperado=generar()
    if a.comprobar:
        if not SALIDA.exists() or SALIDA.read_text()!=esperado:raise SystemExit('Propuesta desactualizada respecto de la lógica probada')
        print('Propuesta coincide con la lógica probada; no instalada ni activada')
    else:SALIDA.write_text(esperado);print(SALIDA.relative_to(ROOT))
if __name__=='__main__':main()
