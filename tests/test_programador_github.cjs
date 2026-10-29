const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const r=require('../despliegue/github-actions/programador.cjs');
const NOW='2026-10-29T11:00:00Z';
const context={repo:{owner:'tobiastorrescc',repo:'Radar---Licitaciones'},runId:700,eventName:'schedule',payload:{}};
function entorno() {
 const datos={hijos:[],padres:[],post:[],avisos:[],editar:[],falloPost:false,indice:true,workflowActivo:true,exitoPasos:true};
 const actual={id:700,workflow_id:2,name:'Programador del piloto aislado',run_attempt:1,event:'schedule',head_branch:'main',head_repository:{full_name:r.REPO},created_at:NOW};
 const hijo=(extra={})=>({id:701,created_at:NOW,path:'.github/workflows/radar-diario.yml',head_branch:r.RAMA,event:'workflow_dispatch',head_repository:{full_name:r.REPO},display_title:r.planDia(NOW).titulo,status:'completed',conclusion:'success',html_url:'https://github.com/'+r.REPO+'/actions/runs/701',...extra});
 const github={rest:{actions:{
  getWorkflowRun:async x=>({data:x.run_id===700?actual:datos.hijos.find(y=>y.id===x.run_id)}),
  listWorkflowRuns:async x=>({data:{workflow_runs:x.workflow_id===r.WORKFLOW?datos.hijos:datos.padres}}),
  getWorkflow:async()=>({data:{state:datos.workflowActivo?'active':'disabled_manually'}}),
  createWorkflowDispatch:async x=>{datos.post.push(x);if(datos.falloPost)throw Error('Timeout ambiguo');},
  listJobsForWorkflowRun:async()=>({data:{jobs:datos.exitoPasos?[{name:'verificar-fuentes-rama',conclusion:'success',steps:['Restaurar respaldo duradero de Git y comprobar toda la cadena','Comprobar continuidad y ausencia de duplicados del historial restaurado','Preparar respaldo incremental y verificar restauración completa','Persistir sólo el respaldo del piloto en su rama'].map(name=>({name,conclusion:'success'}))}]:[]}})
 },repos:{getContent:async()=>({data:{type:'file',encoding:'base64',content:Buffer.from(JSON.stringify({schema_version:1,segmentos:datos.indice?[{sha256:'a'.repeat(64),cuentas:{procedimientos:3691}}]:[]})).toString('base64')}})},issues:{
  listForRepo:async()=>({data:datos.avisos}),
  create:async x=>{datos.avisos.push({...x,number:5,user:{login:'github-actions[bot]'},state:'open',html_url:'issue/5'});return {data:datos.avisos.at(-1)};},
  update:async x=>{datos.editar.push(x);return {data:{html_url:'issue/5'}};}
 }}};
 return {datos,actual,hijo,github};
}
const args=e=>({github:e.github,context,ahora:NOW});
test('fecha argentina y payload sin producción o inicialización',()=>{assert.equal(r.fechaAR('2026-10-29T01:00:00Z'),'2026-10-28');const p=r.planDia(NOW);assert.equal(p.inputs.modo,'controlado');assert.equal(p.inputs.canal,'piloto');assert.equal(p.inputs.inicializar,'false');});
test('plan requiere workflow y respaldo; POST único fijo',async()=>{const e=entorno();const p=await r.preparar(args(e));assert.equal(p.iniciar,true);await r.despachar({...args(e),plan:p.plan});assert.equal(e.datos.post.length,1);assert.equal(e.datos.post[0].ref,r.RAMA);assert.equal(e.datos.post[0].workflow_id,r.WORKFLOW);});
test('un hijo existente completo o activo impide nuevo POST',async()=>{for(const status of ['completed','queued','in_progress']){const e=entorno();e.datos.hijos=[e.hijo({status})];assert.equal((await r.preparar(args(e))).iniciar,false);assert.equal(e.datos.post.length,0);}});
test('hijo fallido o cancelado no se redispara',async()=>{for(const conclusion of ['failure','cancelled','timed_out']){const e=entorno();e.datos.hijos=[e.hijo({conclusion})];await assert.rejects(r.preparar(args(e)),/no se reintenta/);assert.equal(e.datos.post.length,0);}});
test('duplicado remoto se señala, sin un tercer POST',async()=>{const e=entorno();e.datos.hijos=[e.hijo(),e.hijo({id:702})];await assert.rejects(r.preparar(args(e)),/Más de un/);});
test('rerun del padre sin hijo queda incierto sin POST',async()=>{const e=entorno();e.actual.run_attempt=2;await assert.rejects(r.preparar(args(e)),/Intento previo/);});
test('otro padre hoy impide segundo POST incierto',async()=>{const e=entorno();e.datos.padres=[{...e.actual,id:699}];await assert.rejects(r.preparar(args(e)),/Intento previo/);});
test('respuesta POST perdida no tiene reintento interno',async()=>{const e=entorno();e.datos.falloPost=true;await assert.rejects(r.despachar({...args(e),plan:r.planDia(NOW)}),/ambiguo/);assert.equal(e.datos.post.length,1);});
test('rechaza main incorrecta, repositorio ajeno y fecha pasada',async()=>{const e=entorno();e.actual.head_branch=r.RAMA;await assert.rejects(r.preparar(args(e)),/desde main/);e.actual.head_branch='main';e.actual.created_at='2026-10-28T11:00:00Z';await assert.rejects(r.preparar(args(e)),/fecha pasada/);await assert.rejects(r.preparar({...args(e),context:{...context,repo:{owner:'otro',repo:'repo'}}}),/no autorizado/);});
test('plan manipulado no puede habilitar producción',async()=>{const e=entorno();const p=r.planDia(NOW);p.inputs.modo='produccion';await assert.rejects(r.despachar({...args(e),plan:p}),/alterado/);assert.equal(e.datos.post.length,0);});
test('sin respaldo o workflow activo no se despacha',async()=>{for(const propiedad of ['indice','workflowActivo']){const e=entorno();e.datos[propiedad]=false;await assert.rejects(r.preparar(args(e)));assert.equal(e.datos.post.length,0);}});
test('no reconoce hijos de fork, main ni de otro workflow',async()=>{for(const campo of [{head_branch:'main'},{path:'otro.yml'},{head_repository:{full_name:'fork/repo'}}]){const e=entorno();e.datos.hijos=[e.hijo(campo)];assert.equal((await r.preparar(args(e))).iniciar,true);}});
test('supervisión alerta ausencia o ejecución incompleta, sin redisparar',async()=>{const e=entorno();await assert.rejects(r.vigilar(args(e)),/No hay piloto/);e.datos.hijos=[e.hijo({status:'queued'})];await assert.rejects(r.vigilar(args(e)),/incompleto/);assert.equal(e.datos.post.length,0);});
test('supervisión exige job y pasos de restauración, continuidad y guardado',async()=>{const e=entorno();e.datos.hijos=[e.hijo()];assert.equal((await r.vigilar(args(e))).estado,'COMPLETADO_CON_RESPALDO');e.datos.exitoPasos=false;await assert.rejects(r.vigilar(args(e)),/no confirmó éxito/);});
test('workflow_run no ejecuta ni alerta por código de fork o pruebas del PR',async()=>{const e=entorno();e.datos.hijos=[e.hijo({display_title:'Radar controlado clave 2'})];const c={...context,payload:{workflow_run:{id:701}}};assert.equal((await r.revisarEvento({github:e.github,context:c})).ignorado,true);e.datos.hijos=[e.hijo({head_repository:{full_name:'fork/repo'},conclusion:'failure'})];assert.equal((await r.revisarEvento({github:e.github,context:c})).ignorado,true);});
test('workflow_run verifica fallo y respaldo de éxito',async()=>{const e=entorno();const c={...context,payload:{workflow_run:{id:701}}};e.datos.hijos=[e.hijo({conclusion:'cancelled'})];await assert.rejects(r.revisarEvento({github:e.github,context:c}),/cancelled/);e.datos.hijos=[e.hijo()];assert.equal((await r.revisarEvento({github:e.github,context:c})).estado,'COMPLETADO_CON_RESPALDO');});
test('alerta crea un issue diario y evita aviso duplicado de la misma ejecución',async()=>{const e=entorno();await r.alertar({...args(e),motivo:'timeout'});assert.equal(e.datos.avisos.length,1);const a=await r.alertar({...args(e),motivo:'timeout'});assert.equal(a.repetida,true);assert.equal(e.datos.editar.length,0);});
test('alerta nueva incidencia actualiza o reabre issue diario',async()=>{const e=entorno();await r.alertar({...args(e),motivo:'fallo'});e.datos.avisos[0].state='closed';await r.alertar({...args(e),motivo:'fallo'});assert.equal(e.datos.editar[0].state,'open');});
test('no modifica un issue humano aunque imite el marcador',async()=>{const e=entorno();e.datos.avisos=[{body:'<!-- radar-piloto-alerta:2026-10-29 -->',user:{login:'persona'},number:2}];await r.alertar({...args(e),motivo:'fallo'});assert.equal(e.datos.editar.length,0);assert.equal(e.datos.avisos.length,2);});
test('validación del PR sólo admite rama propia, canal aislado y pasos 1/2',async()=>{const e=entorno();const c={...context,eventName:'pull_request',payload:{pull_request:{head:{ref:r.RAMA,repo:{full_name:r.REPO}}}}};await r.despacharValidacion({github:e.github,context:c,clave:'a'.repeat(40),paso:'1'});assert.equal(e.datos.post[0].inputs.canal,'validacion');await assert.rejects(r.despacharValidacion({github:e.github,context,clave:'a'.repeat(40),paso:'1'}),/fuera del PR/);});
test('propuesta fuera de workflows activos, sin checkout ni secretos externos y journal antes del POST',()=>{const f=fs.readFileSync('despliegue/github-actions/programar-piloto.yml.propuesto','utf8');assert.ok(!fs.existsSync('.github/workflows/programar-piloto.yml'));assert.ok(f.includes("vars.RADAR_PILOTO_PROGRAMADOR_HABILITADO == 'true'"));assert.ok(f.includes("cron: '0 8 * * *'"));assert.ok(f.includes("cron: '30 9 * * *'"));assert.ok(!/uses: actions\/checkout|contents: write|secrets\./.test(f));assert.ok(f.indexOf('name: Guardar journal antes')<f.indexOf('name: Solicitar una sola'));assert.ok(f.includes('cancel-in-progress: false'));});
function scriptsPlantilla(){
 const text=fs.readFileSync('despliegue/github-actions/programar-piloto.yml.propuesto','utf8');
 return [...text.matchAll(/^          script: \|\n((?:            .*\n|\n)+)/gm)].map(m=>m[1].split('\n').map(l=>l.startsWith('            ')?l.slice(12):l).join('\n'));
}
test('plantilla autocontenida ejecuta preparación y despacho con el mismo payload probado',async()=>{
 const e=entorno(),os=require('node:os'),path=require('node:path');const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'radar-scheduler-'));const anterior=process.env.RUNNER_TEMP;process.env.RUNNER_TEMP=tmp;
 try{const scripts=scriptsPlantilla();assert.equal(scripts.length,3);const outputs={};const core={setOutput:(k,v)=>outputs[k]=v,info:()=>{},summary:{addHeading(){return this;},addRaw(){return this;},async write(){}}};const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
 // Fecha real: la propuesta no tiene un input que permita inyectar días pasados.
 e.actual.created_at=new Date().toISOString();
 await new AsyncFunction('require','github','context','core',scripts[0])(require,e.github,context,core);
 assert.equal(outputs.iniciar,'true');assert.equal(JSON.parse(fs.readFileSync(path.join(tmp,'piloto-journal.json'))).estado,'ANTES_DEL_POST');assert.equal(e.datos.post.length,0);
 await new AsyncFunction('require','github','context','core',scripts[1])(require,e.github,context,core);assert.equal(e.datos.post.length,1);assert.equal(e.datos.post[0].inputs.canal,'piloto');
 }finally{if(anterior===undefined)delete process.env.RUNNER_TEMP;else process.env.RUNNER_TEMP=anterior;fs.rmSync(tmp,{recursive:true,force:true});}
});
test('plantilla registra error y crea alerta sin consultar ni ejecutar producción',async()=>{
 const e=entorno(),os=require('node:os'),path=require('node:path');const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'radar-alerta-'));const anterior=process.env.RUNNER_TEMP;process.env.RUNNER_TEMP=tmp;
 try{e.actual.created_at=new Date().toISOString();e.datos.indice=false;const scripts=scriptsPlantilla();const core={setOutput(){},info(){},summary:{addHeading(){return this;},addRaw(){return this;},async write(){}}};const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
 await assert.rejects(new AsyncFunction('require','github','context','core',scripts[0])(require,e.github,context,core),/respaldo/);
 await new AsyncFunction('require','github','context','core',scripts[2])(require,e.github,context,core);assert.equal(e.datos.avisos.length,1);assert.equal(e.datos.post.length,0);
 }finally{if(anterior===undefined)delete process.env.RUNNER_TEMP;else process.env.RUNNER_TEMP=anterior;fs.rmSync(tmp,{recursive:true,force:true});}
});
