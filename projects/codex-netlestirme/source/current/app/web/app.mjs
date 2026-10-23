import './layout.mjs';
import {AreaSelection,ResultEditor,cloneCanvas} from './editor.mjs';
import {removeBackground} from './background.mjs';
const $=id=>document.getElementById(id);
let selected,sourceCrop,job,busy=false,kind,started,timer,controller,previewUrl,downloadUrl,revision=0,saveChain=Promise.resolve(),resultState='Seçilen kaynak · henüz yeniden oluşturulmadı';
const editIds=['upscale','remove','view','erase','restore','edges','trim','tones','brush-size','zoom','brightness','contrast','contract'];
const selection=new AreaSelection($('source'),region=>{
  $('selection-info').textContent=region?`Seçili alan: ${region.width} × ${region.height} piksel. Sağda bu alanın kaynağı görünüyor.`:'Görselin tamamı seçili. Alan belirlemek için üzerinde sürükle.';
  if(selection.mode==='quad')$('selection-info').textContent=`Perspektif: ${selection.points.length}/4 köşe. Sıra: sol üst → sağ üst → sağ alt → sol alt. Sağdaki görüntü henüz düzeltilmemiş kaynaktır.`;
  const r=region||{left:0,top:0,width:selection.canvas.width,height:selection.canvas.height};
  sourceCrop=document.createElement('canvas');sourceCrop.width=r.width;sourceCrop.height=r.height;
  sourceCrop.getContext('2d').drawImage(selection.image,r.left,r.top,r.width,r.height,0,0,r.width,r.height);
  job=null;revision++;resultState='Seçilen kaynak · henüz yeniden oluşturulmadı';$('report').hidden=true;$('export-save').hidden=true;$('export-report').hidden=true;
  editor.set(sourceCrop,{reset:true});sync();publish().catch(error=>message(error.message,true));
  message('Seçilen alan sağda. Yeniden oluştur, içeriği yeniden üreten AI motorunu çalıştırır.');$('progress').value=0;
});
const editor=new ResultEditor($('result'),()=>{sync();publish().catch(error=>message(error.message,true));});
function message(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function progress(text,value){message(text);if(Number.isFinite(value))$('progress').value=Math.max(0,Math.min(100,value));else $('progress').removeAttribute('value');}
function reported(text){const match=text.match(/%(\d+)/);progress(text,match?Number(match[1]):undefined);}
function elapsed(){if(!started)return;const seconds=Math.floor((Date.now()-started)/1000);$('elapsed').textContent=`${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;}
function sync(){
  $('upload').disabled=busy;$('all').disabled=busy||!selected;$('enhance').disabled=busy||!selected||selection.mode==='quad'&&!selection.quad;$('task').disabled=busy;$('selection-mode').disabled=busy;
  $('export').disabled=busy||!job;$('export-size').disabled=busy;$('export-dpi').disabled=busy;
  for(const id of editIds)$(id).disabled=busy||!editor.ready;
  $('undo').disabled=busy||!editor.history.length;
  $('cancel').hidden=!busy||!['ai','upscale'].includes(kind);
  selection.locked=busy;editor.locked=busy;
  if(editor.ready){$('result').hidden=false;$('result-empty').hidden=true;$('result-info').textContent=`${resultState} · ${editor.canvas.width} × ${editor.canvas.height} piksel`;}
}
function begin(task,label){busy=true;kind=task;started=Date.now();elapsed();timer=setInterval(elapsed,500);controller=new AbortController();sync();progress(label);}
function end(){busy=false;clearInterval(timer);elapsed();controller=null;sync();}
async function request(path,body,headers={}){
  const response=await fetch(path,{method:'POST',headers:{'X-App-Token':window.APP_TOKEN,...headers},body});
  const data=await response.json();if(!response.ok)throw Error(data.error||'İşlem tamamlanamadı.');return data;
}
const toBlob=canvas=>new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(Error('PNG oluşturulamadı.')),'image/png'));
async function publish(){
  if(!editor.ready)return;const current=++revision,target=job?.id,blob=await toBlob(editor.canvas);
  if(current!==revision)return;
  if(downloadUrl)URL.revokeObjectURL(downloadUrl);downloadUrl=URL.createObjectURL(blob);
  $('save').href=downloadUrl;$('save').hidden=false;
  if(target){saveChain=saveChain.catch(()=>{}).then(()=>current===revision?request('/api/edited/'+target,blob):null);await saveChain;}
}
async function loadResult(url){const img=new Image();img.src=url;await img.decode();return cloneCanvas(img,img.naturalWidth,img.naturalHeight);}
async function runJob(){
  if(busy||!sourceCrop)return;
  const task=$('task').value;
  begin('ai',task==='extract-design'?'Tasarım yeniden oluşturulmak üzere hazırlanıyor…':'Görsel yeniden oluşturulmak üzere hazırlanıyor…');
  try{
    // Always reference the original crop: repeated runs must not compound generated detail or brush edits.
    const headers=selection.quad?{'X-Quad':JSON.stringify(selection.quad)}:selection.region?{'X-Region':JSON.stringify(selection.region)}:{};
    let running=await request('/api/recover?task='+encodeURIComponent(task),selected,headers);
    while(running.status==='running'){
      const p=running.progress||{stage:'İşleniyor'};
      progress(p.stage+(p.total?` · ${p.done}/${p.total}`:''),p.total?100*p.done/p.total:undefined);
      await new Promise(resolve=>setTimeout(resolve,750));
      const response=await fetch('/api/jobs/'+running.id);if(!response.ok)throw Error('İşlem durumu alınamadı.');running=await response.json();
    }
    if(running.status==='cancelled'){message('İşlem iptal edildi. Önceki sonuç korundu.');return;}
    if(running.status!=='completed')throw Error(running.error||'Yeni görüntü oluşturulamadı. Önceki sonuç korundu.');
    const result=await loadResult(running.output);job=running;resultState='Kurtarma çıktısı · baskı kabulü yapılmadı';editor.set(result);$('report').href=running.report;$('report').hidden=false;sync();await publish();
    progress('Kurtarma çıktısı hazır. Yazı, logo, renk ve yüzey kalıntılarını kontrol et. Rapor kalite kabulü yerine geçmez.',100);
  }catch(error){message(error.message,true);$('progress').value=0;}finally{end();}
}
async function operation(task,label,fn){
  if(busy||!editor.ready)return;begin(task,label);
  try{const result=await fn(controller.signal);controller.signal.throwIfAborted();
    if(result){editor.set(result.canvas||result,{recovery:result.recovery});sync();}
    await publish();progress('İşlem tamamlandı. Sonuç ekranda; PNG olarak indirebilirsin.',100);
  }catch(error){message(error.name==='AbortError'?'İşlem iptal edildi. Önceki sonuç korundu.':error.message,true);$('progress').value=0;}finally{end();}
}
$('upload').onchange=async()=>{
  if(busy)return;const file=$('upload').files[0];if(!file)return;
  try{
    if(file.size>25*1024*1024)throw Error('En fazla 25 MB görsel seçin.');
    const url=URL.createObjectURL(file),img=new Image();img.src=url;
    try{await img.decode();}catch{URL.revokeObjectURL(url);throw Error('Görsel okunamadı. PNG, JPEG veya WebP seçin.');}
    if(img.naturalWidth*img.naturalHeight>16e6){URL.revokeObjectURL(url);throw Error('Girdi en fazla 16 megapiksel olabilir.');}
    if(previewUrl)URL.revokeObjectURL(previewUrl);previewUrl=url;selected=file;job=null;revision++;
    editor.ready=false;editor.history=[];$('result').hidden=true;$('result-empty').hidden=false;$('save').hidden=true;
    $('source').hidden=false;$('source-empty').hidden=true;selection.load(img);
    $('brightness').value=$('contrast').value=100;$('elapsed').textContent='';sync();
  }catch(error){message(error.message,true);}
};
$('all').onclick=()=>{$('selection-mode').value='rectangle';selection.setMode('rectangle');};
$('selection-mode').onchange=()=>selection.setMode($('selection-mode').value);
$('enhance').onclick=()=>runJob();
$('upscale').onclick=()=>operation('upscale','Yerel 2× büyütme motoru hazırlanıyor…',async signal=>{
  const {enhanceCanvas}=await import('./enhance.mjs');
  const result=await enhanceCanvas(editor.canvas,reported,{signal});
  return {canvas:result,recovery:cloneCanvas(editor.recovery,result.width,result.height)};
});
$('remove').onclick=()=>operation('background','Arka plan ayıklanıyor…',async()=>{
  const recovery=cloneCanvas(editor.canvas),canvas=await removeBackground(editor.canvas,reported,{contract:$('contract').checked});
  return {canvas,recovery};
});
$('export').onclick=async()=>{
  if(busy||!job)return;begin('export','PNG dışa aktarılıyor…');
  try{
    await publish();await saveChain;
    const output=await request('/api/export/'+job.id,JSON.stringify({input:'edited',longEdge:Number($('export-size').value),dpi:Number($('export-dpi').value)})),d=output.details;
    $('export-save').href=output.output+'?v='+Date.now();$('export-save').hidden=false;$('export-report').href=output.report;$('export-report').hidden=false;
    progress(`${d.width} × ${d.height} PNG hazır. ${d.resampling==='none'?'Piksel boyutu korundu.':'Boyut yeniden örneklendi; bu işlem yeni ayrıntı üretmez.'} Baskı için görsel kontrol gerekli.`,100);
  }catch(error){message(error.message,true);}finally{end();}
};
$('cancel').onclick=async()=>{if(!busy)return;try{if(kind==='ai')await request('/api/cancel','');else controller?.abort();message('İşlem durduruluyor…');}catch(error){message(error.message,true);}};
for(const tool of ['view','erase','restore'])$(tool).onclick=()=>{
  editor.tool=tool;for(const id of ['view','erase','restore'])$(id).setAttribute('aria-pressed',String(id===tool));
  message(tool==='erase'?'Sonuç üzerinde sürükleyerek sil.':tool==='restore'?'Sonuç üzerinde sürükleyerek silinen ayrıntıyı geri getir.':'Görseli inceleyebilirsin.');
};
$('brush-size').oninput=()=>{editor.size=Number($('brush-size').value);$('brush-value').textContent=editor.size+' px';};
$('zoom').oninput=()=>{editor.zoom=Number($('zoom').value)/100;$('zoom-value').textContent='%'+$('zoom').value;editor.fit();};
$('undo').onclick=()=>editor.undo();
$('edges').onclick=()=>{editor.edges($('contract').checked);message('Kenarlar düzeltildi. Geri al ile geri dönebilirsin.');};
$('trim').onclick=()=>{try{editor.trim();}catch(error){message(error.message,true);}};
$('tones').onclick=()=>{editor.tones(Number($('brightness').value),Number($('contrast').value));$('brightness').value=$('contrast').value=100;message('Parlaklık ve kontrast uygulandı.');};
window.addEventListener('resize',()=>{editor.fit();selection.draw();});
sync();
