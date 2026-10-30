'use strict';
const $ = id => document.getElementById(id);
const state = {config:null, dataset:null, clouds:null, result:null, after:false, busy:false,
  yaw:-0.65, pitch:0.85, scale:1, pan:[0,0], center:[0,0,0], radius:30};
const canvas = $('cloud'), ctx = canvas.getContext('2d');
function status(text, error=false) {$('status').textContent=text; $('status').className='status'+(error?' error':'');}
async function api(path, payload) {
  const response = await fetch(path, payload ? {method:'POST',headers:{'Content-Type':'application/json','X-Demo-Token':state.config.token},body:JSON.stringify(payload)} : {});
  const data = await response.json(); if(!response.ok) throw Error(data.error || '服务请求失败'); return data;
}
function enable() {
  const busy=state.busy;
  for(const id of ['dataset','replay','voxel','iterations','correspondence','evaluation','max_rmse']) $(id).disabled=busy;
  $('run').disabled=busy || !state.config?.binary_ready;
  $('coarse').disabled=busy || state.dataset?.id!=='kitti';
  $('after').disabled=busy || !state.result?.report.accepted;
  $('download').disabled=busy || !state.result;
  $('run').textContent=busy?'处理中…':'运行 C++ 配准 ↗';
}
function clearResult() {
  state.result=null; state.after=false;
  for(const id of ['rmse','ratio','elapsed','converged','inliers']) $(id).textContent='—';
  $('quality').textContent='等待实验结果'; $('quality').className='quality waiting';
  $('mode-badge').textContent='尚未运行'; $('mode-badge').className='badge neutral';
  $('matrix').textContent='等待有效配准结果'; $('matrix-note').textContent='仅展示通过质量门禁的有效变换。';
  $('translation').textContent='x —　y —　z —'; $('point-counts').textContent='原始 → 有限点 → 体素输出';
  $('truth-errors').textContent=''; setView(false);
}
function number(value, digits=6) {return value==null?'—':Number(value).toFixed(digits);}
function renderResult(result) {
  state.result=result; const r=result.report, accepted=r.accepted;
  $('mode-badge').textContent=result.mode==='live'?'本次 C++ 实际计算':'已验证实验回放';
  $('mode-badge').className='badge '+(result.mode==='live'?'live':'replay');
  $('quality').textContent=accepted?'✓ 通过质量门禁':'! 质量门禁拒绝';
  $('quality').className='quality '+(accepted?'accepted':'rejected');
  $('rmse').textContent=number(r.rmse_m); $('ratio').textContent=number(r.inlier_ratio*100,2)+'%';
  $('elapsed').textContent=number(r.elapsed_ms,1); $('converged').textContent=r.converged?'已收敛':'未收敛';
  $('inliers').textContent=r.inliers.toLocaleString();
  const counts=p=>`${p.input.toLocaleString()} → ${p.finite.toLocaleString()} → ${p.output.toLocaleString()}`;
  $('point-counts').replaceChildren();
  for(const side of ['source','target']) {const row=document.createElement('div'); row.textContent=side+': '+counts(r[side+'_points']); $('point-counts').append(row);}
  $('translation').textContent=accepted?r.pose.translation_m.map((v,i)=>'xyz'[i]+' '+number(v,5)).join('　'):'已拒绝 · 不提供有效位姿';
  $('matrix').textContent=accepted?r.T_target_source.map(row=>'[ '+row.map(v=>Number(v).toFixed(6).padStart(10)).join(' ')+' ]').join('\n'):'有效 T_target_source = null\n诊断矩阵仅保留在 JSON，禁止用于累计位姿。';
  $('matrix-note').textContent=accepted?'此矩阵将 source 坐标映射至 target；不直接等同车辆运动。':'拒绝原因：'+r.rejection_reason;
  $('truth-errors').textContent=r.translation_error_m==null?'当前道路帧对未提供位姿真值。':`真值误差：平移 ${r.translation_error_m.toExponential(3)} m · 旋转 ${r.rotation_error_rad.toExponential(3)} rad`;
  status(result.message+(result.run_id?' · run '+result.run_id.slice(0,8):' · '+result.archive)+(accepted?'':'；'+r.rejection_reason));
  // Rejected transforms never become a valid "after" view.
  setView(accepted); enable();
}
async function changeDataset() {
  state.busy=true; enable(); clearResult(); state.clouds=null; draw();
  state.dataset=state.config.datasets.find(d=>d.id===$('dataset').value);
  const d=state.dataset; $('dataset-note').textContent=d.note;
  $('source-label').textContent=d.id==='kitti'?'帧 000001':'source.pcd';
  $('target-label').textContent=d.id==='kitti'?'帧 000000':'target.pcd';
  for(const [id,value] of Object.entries({voxel:d.voxel,iterations:100,correspondence:1,evaluation:d.evaluation,max_rmse:d.max_rmse})) $(id).value=value;
  $('canvas-empty').hidden=false; $('canvas-empty').textContent='正在读取本地点云…';
  try {
    state.clouds=await api('/api/clouds?dataset='+d.id); resetCamera();
    $('canvas-empty').hidden=true;
    const s=state.clouds.source,t=state.clouds.target;
    $('display-count').textContent=`显示 ${s.points.length.toLocaleString()} + ${t.points.length.toLocaleString()} 点 · 原始 ${(s.input_points+t.input_points).toLocaleString()} 点`;
    status('点云已载入，尚未运行配准。可实际计算，或加载已验证实验回放。');
  } catch(error) {$('canvas-empty').textContent='点云读取失败'; status(error.message,true);}
  finally {state.busy=false; enable(); draw();}
}
function setView(after) {
  state.after=after && Boolean(state.result?.report.accepted);
  $('before').classList.toggle('active',!state.after); $('after').classList.toggle('active',state.after);
  $('view-label').textContent=state.after?'ALIGNED SOURCE → TARGET · METRES':'ORIGINAL SOURCE + TARGET · METRES'; draw();
}
function resetCamera() {
  state.yaw=-0.65; state.pitch=0.85; state.scale=1; state.pan=[0,0];
  if(state.clouds) {
    const points=state.clouds.target.points;
    // Fit to the central 96% to keep a few very distant returns from hiding the road.
    const bounds=[0,1,2].map(k=>points.map(p=>p[k]).sort((a,b)=>a-b));
    const low=bounds.map(a=>a[Math.floor(a.length*.02)]), high=bounds.map(a=>a[Math.floor(a.length*.98)]);
    state.center=low.map((v,i)=>(v+high[i])/2); state.radius=Math.max(...high.map((v,i)=>v-low[i]),1)*.7;
  }
  draw();
}
function draw() {
  const rect=canvas.getBoundingClientRect(), w=rect.width,h=rect.height;
  if(!w || !h) return;
  const ratio=Math.min(devicePixelRatio||1,2);
  if(canvas.width!==Math.round(w*ratio)||canvas.height!==Math.round(h*ratio)){canvas.width=Math.round(w*ratio); canvas.height=Math.round(h*ratio);}
  ctx.setTransform(ratio,0,0,ratio,0,0); ctx.clearRect(0,0,w,h);
  const scale=Math.min(w,h)/state.radius*.82*state.scale;
  const cy=Math.cos(state.yaw),sy=Math.sin(state.yaw),cp=Math.cos(state.pitch),sp=Math.sin(state.pitch);
  function project(p) {const a=p.map((v,i)=>v-state.center[i]); const x=cy*a[0]-sy*a[1], depth=sy*a[0]+cy*a[1]; return [w/2+x*scale+state.pan[0], h/2+(depth*cp-a[2]*sp)*scale+state.pan[1],depth*sp+a[2]*cp];}
  function line(a,b,color) {const pa=project(a),pb=project(b); ctx.strokeStyle=color; ctx.beginPath();ctx.moveTo(pa[0],pa[1]);ctx.lineTo(pb[0],pb[1]);ctx.stroke();}
  const spacing=state.dataset?.id==='synthetic'?1:10;
  for(let i=-10;i<=10;i++){line([i*spacing,-10*spacing,0],[i*spacing,10*spacing,0],'#152235');line([-10*spacing,i*spacing,0],[10*spacing,i*spacing,0],'#152235');}
  if(!state.clouds) return;
  const transform=state.after?state.result.report.T_target_source:null;
  const points=[];
  for(const side of ['target','source']) {
    if(!$(side==='source'?'show-source':'show-target').checked) continue;
    for(let point of state.clouds[side].points) {
      if(side==='source'&&transform) point=transform.slice(0,3).map(row=>row[0]*point[0]+row[1]*point[1]+row[2]*point[2]+row[3]);
      const p=project(point); if(p[0]>0&&p[0]<w&&p[1]>0&&p[1]<h) points.push([...p,side]);
    }
  }
  points.sort((a,b)=>a[2]-b[2]);
  const size=state.dataset?.id==='synthetic'?2.1:1.65;
  ctx.globalAlpha=.78;
  for(const p of points) {ctx.fillStyle=p[3]==='source'?'#63bdff':'#ffc17e';ctx.fillRect(p[0],p[1],size,size);}
  ctx.globalAlpha=1;
  const length=spacing*1.8; ctx.font='11px Consolas';
  for(const [end,color,label] of [[[length,0,0],'#ec8d8d','X'],[[0,length,0],'#89d5aa','Y'],[[0,0,length],'#7bbcff','Z']]) {line([0,0,0],end,color); const p=project(end);ctx.fillStyle=color;ctx.fillText(label,p[0]+5,p[1]);}
}
$('run-form').addEventListener('submit',async event=>{
  event.preventDefault(); if(state.busy) return;
  state.busy=true; clearResult(); enable(); status('正在调用本地 C++ 程序：读取 → 预处理 → ICP → 质量评估。最长等待 60 秒。');
  const payload={dataset:state.dataset.id}; for(const id of ['voxel','iterations','correspondence','evaluation','max_rmse']) payload[id]=Number($(id).value);
  try {renderResult(await api('/api/run',payload));} catch(error){status(error.message,true);}
  finally{state.busy=false;enable();}
});
async function replay(coarse=false) {
  if(state.busy) return; state.busy=true; clearResult(); enable();
  try {const result=await api('/api/replay?dataset='+state.dataset.id+(coarse?'&coarse=1':'')); renderResult(result); const c=result.report.configuration; $('voxel').value=c.voxel_size_m.toFixed(3); $('iterations').value=c.max_iterations; $('correspondence').value=c.max_correspondence_distance_m; $('evaluation').value=c.evaluation_distance_m; $('max_rmse').value=c.max_rmse_m;}
  catch(error){status(error.message,true);} finally{state.busy=false; enable();}
}
$('dataset').addEventListener('change',changeDataset); $('before').onclick=()=>setView(false); $('after').onclick=()=>setView(true);
for(const id of ['voxel','iterations','correspondence','evaluation','max_rmse']) $(id).addEventListener('change',()=>{if(!state.busy){clearResult();enable();status('参数已修改，请重新运行；历史回放会恢复其归档参数。');}});
$('replay').onclick=()=>replay(); $('coarse').onclick=()=>replay(true);
$('reset').onclick=resetCamera; $('top').onclick=()=>{state.pitch=Math.PI/2;state.yaw=0;draw();};
$('fullscreen').onclick=async()=>{try {if(document.fullscreenElement) await document.exitFullscreen(); else await $('canvas-wrap').requestFullscreen();}catch(e){status('浏览器不允许全屏，可使用 F11。',true);}};
for(const id of ['show-source','show-target']) $(id).onchange=draw;
$('download').onclick=()=>{if(!state.result)return; const blob=new Blob([JSON.stringify(state.result,null,2)],{type:'application/json'}); const url=URL.createObjectURL(blob), a=document.createElement('a');a.href=url;a.download=`lidar-${state.dataset.id}-${state.result.mode}-${Date.now()}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
let drag=null;
canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);};
canvas.onpointerup=()=>{drag=null;}; canvas.onpointercancel=()=>{drag=null;};
canvas.onpointermove=e=>{if(!drag)return; const dx=e.clientX-drag[0],dy=e.clientY-drag[1];drag=[e.clientX,e.clientY];if(e.shiftKey){state.pan[0]+=dx;state.pan[1]+=dy;}else{state.yaw+=dx*.008;state.pitch=Math.max(.08,Math.min(Math.PI-.08,state.pitch+dy*.008));}draw();};
canvas.addEventListener('wheel',e=>{e.preventDefault();state.scale=Math.max(.15,Math.min(20,state.scale*Math.exp(-e.deltaY*.001)));draw();},{passive:false});
new ResizeObserver(draw).observe($('canvas-wrap'));
(async()=>{try {state.config=await api('/api/config'); $('dataset').replaceChildren(...state.config.datasets.map(d=>new Option(d.title,d.id))); $('dataset').value=state.config.datasets.some(d=>d.id==='kitti')?'kitti':state.config.datasets[0].id; await changeDataset();}catch(error){status('本地服务连接失败：'+error.message,true);$('canvas-empty').textContent='请按启动说明运行本地服务';}})();
