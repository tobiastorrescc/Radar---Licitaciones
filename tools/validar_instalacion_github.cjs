'use strict';
// Ensayo de instalación autorizado; no escribe archivos ni historial de main.
const fs=require('node:fs');
const crypto=require('node:crypto');
const radar=require('../despliegue/github-actions/programador.cjs');
const RAMA=radar.RAMA, WORKFLOW=radar.WORKFLOW;
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function instalar({github,context,core}) {
 if(context.eventName!=='pull_request'||context.payload.pull_request?.number!==1||context.payload.pull_request?.head?.repo?.full_name!==radar.REPO||context.payload.pull_request?.head?.ref!==RAMA)throw Error('Instalación fuera del PR #1 autorizado');
 const plan=JSON.parse(fs.readFileSync('despliegue/github-actions/instalacion.json','utf8'));
 if(!plan.ejecutar_validacion)throw Error('Ensayo desactivado');
 const repo=context.repo;const out={iniciado:new Date().toISOString(),main_esperado:plan.main_sha_esperado,variable_programador:process.env.RADAR_GUARD||''};
 if(process.env.RADAR_GUARD==='false')throw Error('Una variable existente bloquea el cron: revisar antes de instalar');
 const guardar=()=>fs.writeFileSync('work/resultado_instalacion.json',JSON.stringify(out,null,2));fs.mkdirSync('work',{recursive:true});guardar();
 async function runList(branch,event) {
  const {data}=await github.rest.actions.listWorkflowRuns({...repo,workflow_id:WORKFLOW,branch,event,per_page:100});return data.workflow_runs;
 }
 async function manual(accion,esperado='success') {
  const anteriores=new Set((await runList('main','workflow_dispatch')).map(x=>x.id));
  await github.rest.actions.createWorkflowDispatch({...repo,workflow_id:WORKFLOW,ref:'main',inputs:{accion}});
  for(let i=0;i<40;i++) {
   await pause(10000);
   const runs=(await runList('main','workflow_dispatch')).filter(r=>!anteriores.has(r.id)&&r.head_sha===plan.main_sha_esperado&&r.display_title===`Programador piloto ${accion==='probar_alerta'?'prueba-alerta':'diario'}`);
   if(runs.length>1)throw Error('Más de un padre nuevo para el ensayo');
   const run=runs[0];if(!run)continue;
   core.info(`Ensayo ${accion}: ${run.html_url} ${run.status}`);
   if(run.status==='completed') {
    if(run.conclusion!==esperado)throw Error(`Ensayo ${accion}: esperado ${esperado}, recibido ${run.conclusion}: ${run.html_url}`);
    out[accion+'_'+Object.keys(out).length]={id:run.id,url:run.html_url,conclusion:run.conclusion};guardar();return run;
   }
  }
  throw Error(`Plazo esperando ${accion}; consultar Actions sin repetir POST automáticamente`);
 }
 async function huellas() {
  const h={};for(const path of ['radar_estado.json','licitaciones_nuevas.json','licitaciones_nuevas.md','auditoria_fuentes.json']) {
   try{const {data}=await github.rest.repos.getContent({...repo,path,ref:'main'});h[path]=data.sha;}
   catch(e){if(e.status===404)h[path]=null;else throw e;}
  }return h;
 }
 try {
  const main=(await github.rest.repos.getBranch({...repo,branch:'main'})).data;
  if(main.commit.sha!==plan.main_sha_esperado)throw Error('Main cambió antes del ensayo; revisar sin desactivar ni despachar');
  const contenido=(await github.rest.repos.getContent({...repo,path:'.github/workflows/programar-piloto.yml',ref:'main'})).data;
  const texto=Buffer.from(contenido.content,'base64').toString('utf8');
  if(crypto.createHash('sha256').update(texto).digest('hex')!==plan.sha256_programador||!texto.includes('(false && vars.RADAR'))throw Error('El programador no coincide con la revisión pausada autorizada');
  out.produccion_antes=await huellas();guardar();
  const legacy=(await github.rest.actions.getWorkflow({...repo,workflow_id:'radar-diario.yml'})).data;
  const nuevo=(await github.rest.actions.getWorkflow({...repo,workflow_id:WORKFLOW})).data;
  if(legacy.id===nuevo.id||nuevo.state!=='active')throw Error('No hay IDs separados y activos para el piloto nuevo');
  const {data:viejos}=await github.rest.actions.listWorkflowRuns({...repo,workflow_id:legacy.id,branch:'main',per_page:100});
  if(viejos.workflow_runs.some(r=>r.status!=='completed'))throw Error('Hay una ejecución antigua en main activa: revisar antes de continuar');
  await github.rest.actions.disableWorkflow({...repo,workflow_id:legacy.id});
  out.legado=(await github.rest.actions.getWorkflow({...repo,workflow_id:legacy.id})).data.state;out.workflow_nuevo_id=nuevo.id;guardar();
  if(out.legado!=='disabled_manually')throw Error('No quedó deshabilitado el cron antiguo');
  core.info('CRON_ANTIGUO_DESHABILITADO '+legacy.id+'; NUEVO '+nuevo.id);
  const inicio=(await manual('ejecutar')).created_at;
  const diario=radar.planDia(new Date());let hijo;
  for(let i=0;i<120;i++) {
   const runs=(await runList(RAMA,'workflow_dispatch')).filter(r=>r.display_title===diario.titulo);
   if(runs.length>1)throw Error('Hay pilotos diarios duplicados');
   hijo=runs[0];
   if(hijo){core.info(`PILOTO ${hijo.html_url} ${hijo.status}`);if(hijo.status==='completed')break;}
   await pause(10000);
  }
  if(!hijo||hijo.status!=='completed')throw Error('Piloto sin finalizar; no se presume éxito');
  out.piloto={id:hijo.id,url:hijo.html_url,conclusion:hijo.conclusion,fecha:diario.fecha};guardar();
  if(hijo.conclusion!=='success') {
   await manual('supervisar','failure');throw Error('El piloto falló: revisar alerta y artefactos');
  }
  out.supervision=await radar.vigilar({github,context});guardar();
  // Comprobar además el evento real workflow_run del programador en main.
  let supervisor;
  for(let i=0;i<30;i++) {
   const runs=await runList('main','workflow_run');
   supervisor=runs.find(r=>r.created_at>=inicio&&r.head_sha===plan.main_sha_esperado);
   if(supervisor?.status==='completed')break;
   await pause(10000);
  }
  if(!supervisor||supervisor.conclusion!=='success')throw Error('No se confirmó supervisor automático workflow_run');
  out.supervisor_automatico={id:supervisor.id,url:supervisor.html_url,conclusion:supervisor.conclusion};guardar();
  await manual('supervisar');
  const prueba=await manual('probar_alerta','failure');
  const {data:issues}=await github.rest.issues.listForRepo({...repo,state:'open',per_page:100});
  const aviso=issues.find(i=>i.user?.login==='github-actions[bot]'&&i.body?.includes(prueba.html_url)&&i.body.includes('PRUEBA CONTROLADA AUTORIZADA'));
  if(!aviso)throw Error('El fallo deliberado no generó Issue de alerta');
  out.alerta={numero:aviso.number,url:aviso.html_url,fallo_deliberado:prueba.html_url};guardar();
  // Cerrar sólo una alerta que contenga exclusivamente la incidencia deliberada del ensayo.
  if(aviso.body.includes('Incidencia detectada: PRUEBA CONTROLADA AUTORIZADA')&&aviso.body.split('Incidencia detectada:').length===2) {
   await github.rest.issues.update({...repo,issue_number:aviso.number,state:'closed',state_reason:'completed'});out.alerta.cerrada_tras_comprobar=true;
  }
  await manual('ejecutar');
  const hijos=(await runList(RAMA,'workflow_dispatch')).filter(r=>r.display_title===diario.titulo);
  if(hijos.length!==1||hijos[0].id!==hijo.id)throw Error('La repetición del programador generó otra consulta');
  out.despachos_piloto=1;out.produccion_despues=await huellas();
  if(JSON.stringify(out.produccion_antes)!==JSON.stringify(out.produccion_despues))throw Error('Cambió producción durante el ensayo');
  out.correcta=true;out.finalizado=new Date().toISOString();guardar();
  await core.summary.addHeading('Instalación y ensayo real comprobados').addRaw(JSON.stringify(out,null,2)).write();
  core.info('INSTALACION_VALIDADA '+JSON.stringify(out));
 } catch(e){out.correcta=false;out.error=String(e.message);guardar();throw e;}
}
module.exports={instalar};
