'use strict';
// Lógica embebida en la plantilla de main: nunca descarga ni ejecuta código del PR.
const crypto = require('node:crypto');
const REPO = 'tobiastorrescc/Radar---Licitaciones';
const RAMA = 'mejora/radar-auditable';
const WORKFLOW = 'programar-piloto.yml';
const PATH = '.github/workflows/programar-piloto.yml';
function fechaAR(instante) {
  const partes = new Intl.DateTimeFormat('en-CA', {timeZone:'America/Argentina/Buenos_Aires',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(instante));
  return ['year','month','day'].map(k=>partes.find(x=>x.type===k).value).join('-');
}
function planDia(ahora) {
  const fecha=fechaAR(ahora);
  const clave=crypto.createHash('sha256').update('piloto-diario:'+fecha).digest('hex').slice(0,40);
  return {fecha, titulo:`Radar controlado ${clave} programado`,
    inputs:{modo:'controlado',canal:'piloto',inicializar:'false',clave_validacion:clave,paso_validacion:'programado'}};
}
function repo(context) {
  if(`${context.repo.owner}/${context.repo.repo}`!==REPO) throw new Error('Repositorio no autorizado');
  return context.repo;
}
function esPiloto(r, context) {
  return r.head_branch===RAMA && r.event==='workflow_dispatch' && r.path===PATH && r.head_repository?.full_name===REPO;
}
async function listarRuns(github, context, workflow, ahora) {
  const desde=new Date(new Date(ahora).getTime()-2*86400000).toISOString().slice(0,10);
  const result=[];
  for(let page=1;page<=5;page++) {
    const {data}=await github.rest.actions.listWorkflowRuns({...repo(context),workflow_id:workflow,branch:workflow===WORKFLOW?RAMA:'main',created:`>=${desde}`,per_page:100,page});
    result.push(...data.workflow_runs);
    if(data.workflow_runs.length<100)return result;
  }
  throw new Error('Listado truncado; no se despacha sin poder descartar duplicados');
}
async function candidato(github,context,ahora) {
  const plan=planDia(ahora);
  const runs=await listarRuns(github,context,WORKFLOW,ahora);
  const matches=runs.filter(r=>esPiloto(r,context)&&r.display_title===plan.titulo);
  if(matches.length>1)throw new Error('Más de un piloto para esta fecha; revisar duplicados');
  return {plan,run:matches[0]};
}
async function comprobarLegado(github,context) {
  const {data}=await github.rest.actions.getWorkflow({...repo(context),workflow_id:'radar-diario.yml'});
  if(!String(data.state).startsWith('disabled_'))throw new Error('El workflow antiguo debe estar deshabilitado antes de ejecutar el piloto');
  return data.state;
}
async function preparar({github,context,ahora=new Date()}) {
  repo(context);
  await comprobarLegado(github,context);
  const actual=(await github.rest.actions.getWorkflowRun({...context.repo,run_id:context.runId})).data;
  if(actual.head_branch!=='main' || !['schedule','workflow_dispatch'].includes(actual.event))throw new Error('El programador sólo puede operar desde main');
  if(fechaAR(actual.created_at)!==fechaAR(ahora))throw new Error('No redisparar una fecha pasada mediante rerun');
  const {plan,run}=await candidato(github,context,ahora);
  if(run) {
    if(run.status==='completed'&&run.conclusion!=='success')throw new Error(`El piloto ya terminó con ${run.conclusion}: ${run.html_url}; no se reintenta`);
    return {iniciar:false,plan,run};
  }
  const padres=await listarRuns(github,context,actual.workflow_id,ahora);
  if(Number(actual.run_attempt)>1 || padres.some(r=>r.id!==context.runId&&fechaAR(r.created_at)===plan.fecha&&['schedule','workflow_dispatch'].includes(r.event)&&r.head_branch==='main'&&r.head_repository?.full_name===REPO&&r.display_title===actual.display_title)) {
    throw new Error('Intento previo sin hijo confirmado; no se repite un POST incierto');
  }
  const flujo=(await github.rest.actions.getWorkflow({...context.repo,workflow_id:WORKFLOW})).data;
  if(flujo.state!=='active')throw new Error('El workflow del radar está deshabilitado');
  const {data}=await github.rest.repos.getContent({...context.repo,path:'piloto_respaldo/diario/indice.json',ref:RAMA});
  if(data.type!=='file'||data.encoding!=='base64')throw new Error('Falta índice duradero del piloto');
  const indice=JSON.parse(Buffer.from(data.content,'base64').toString('utf8'));
  const ultimo=indice.segmentos?.at(-1);
  if(indice.schema_version!==1 || !ultimo || !/^[a-f0-9]{64}$/.test(ultimo.sha256)||!(ultimo.cuentas?.procedimientos>0))throw new Error('Índice de respaldo ausente, vacío o incompatible');
  return {iniciar:true,plan};
}
async function despachar({github,context,plan}) {
  repo(context);
  await comprobarLegado(github,context);
  const esperado=planDia(`${plan.fecha}T12:00:00Z`);
  if(JSON.stringify(plan)!==JSON.stringify(esperado))throw new Error('Plan alterado');
  // Sin retry: el llamador sube el journal ANTES. Un timeout es resultado incierto.
  await github.rest.actions.createWorkflowDispatch({...context.repo,workflow_id:WORKFLOW,ref:RAMA,inputs:plan.inputs});
  return {estado:'SOLICITADO_NO_FINALIZADO',fecha:plan.fecha};
}
async function comprobarExito(github,context,run) {
  const {data}=await github.rest.actions.listJobsForWorkflowRun({...repo(context),run_id:run.id,per_page:100});
  const job=data.jobs.find(j=>j.name==='verificar-fuentes-rama');
  if(!job||job.conclusion!=='success')throw new Error('El job del piloto no confirmó éxito');
  for(const nombre of ['Restaurar respaldo duradero de Git y comprobar toda la cadena','Comprobar continuidad y ausencia de duplicados del historial restaurado','Preparar respaldo incremental y verificar restauración completa','Persistir sólo el respaldo del piloto en su rama']) {
    if(!job.steps?.some(s=>s.name===nombre&&s.conclusion==='success'))throw new Error('Falta confirmación de persistencia: '+nombre);
  }
  return {estado:'COMPLETADO_CON_RESPALDO',url:run.html_url};
}
async function vigilar({github,context,ahora=new Date()}) {
  await comprobarLegado(github,context);
  const {plan,run}=await candidato(github,context,ahora);
  if(!run)throw new Error(`No hay piloto confirmado para ${plan.fecha}; no significa ausencia de novedades`);
  if(run.status!=='completed')throw new Error(`Piloto incompleto (${run.status}): ${run.html_url}`);
  if(run.conclusion!=='success')throw new Error(`Piloto ${run.conclusion}: ${run.html_url}`);
  return comprobarExito(github,context,run);
}
async function revisarEvento({github,context,esperar=ms=>new Promise(r=>setTimeout(r,ms))}) {
  repo(context);
  const id=context.payload.client_payload?.run_id||context.payload.workflow_run?.id;
  if(!Number.isSafeInteger(Number(id))||Number(id)<=0)throw new Error('Identificador del evento inválido');
  let run=(await github.rest.actions.getWorkflowRun({...context.repo,run_id:id})).data;
  if(!esPiloto(run,context))return {ignorado:true};
  // Sólo el título diario: los ensayos independientes del PR no generan alertas operativas.
  if(run.display_title!==planDia(run.created_at).titulo)return {ignorado:true};
  for(let i=0;i<12&&run.status!=='completed';i++) {await esperar(5000);run=(await github.rest.actions.getWorkflowRun({...context.repo,run_id:Number(id)})).data;}
  if(run.status!=='completed')throw new Error('La notificación llegó antes de completar el piloto; revisar su cierre');
  if(run.conclusion!=='success')throw new Error(`Piloto ${run.conclusion}: ${run.html_url}`);
  return comprobarExito(github,context,run);
}
async function alertar({github,context,motivo,ahora=new Date()}) {
  const r=repo(context);const fecha=fechaAR(ahora);const marca=`<!-- radar-piloto-alerta:${fecha} -->`;
  const url=`https://github.com/${REPO}/actions/runs/${context.runId}`;
  const detalle=`${marca}\n\nRevisar el piloto aislado de ${RAMA}. Incidencia detectada: ${String(motivo).slice(0,1000)}\n\n${url}\n\nNo se reenvía automáticamente un despacho incierto. Consultar auditoría, continuidad, respaldos y resultados parciales. Ausencia de ejecución no equivale a ausencia de novedades.`;
  let encontrada;
  for(let page=1;page<=5;page++) {
    const {data}=await github.rest.issues.listForRepo({...r,state:'all',sort:'created',direction:'desc',per_page:100,page});
    encontrada=data.find(i=>!i.pull_request&&i.body?.startsWith(marca)&&i.user?.login==='github-actions[bot]');
    if(encontrada||data.length<100)break;
    if(page===5)throw new Error('Listado de alertas truncado; revisar Actions sin crear avisos duplicados');
  }
  if(encontrada) {
    if(encontrada.body.includes(url)&&encontrada.state==='open')return {url:encontrada.html_url,repetida:true};
    const body=encontrada.body.slice(0,50000)+'\n\n'+detalle;
    const {data}=await github.rest.issues.update({...r,issue_number:encontrada.number,state:'open',body});
    return {url:data.html_url,actualizada:true};
  }
  const {data}=await github.rest.issues.create({...r,title:`[Radar piloto] Revisar ejecución del ${fecha}`,body:detalle});
  return {url:data.html_url,creada:true};
}
module.exports={REPO,RAMA,WORKFLOW,fechaAR,planDia,preparar,despachar,vigilar,revisarEvento,alertar,comprobarLegado};
