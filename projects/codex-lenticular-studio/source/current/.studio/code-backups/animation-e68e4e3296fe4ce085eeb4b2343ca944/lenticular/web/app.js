'use strict';
const $ = id => document.getElementById(id);
const token = new URLSearchParams(location.search).get('t') || sessionStorage.getItem('studioToken') || '';
sessionStorage.setItem('studioToken', token);
const renderFields = ['nr','angle_deg','effect_strength','zero_reference','depth_smoothing','grid_size','repair','layers','inpaint_radius','process_res','render_long_edge','camera_axis'];
const printFields = ['width_mm','height_mm','bleed_mm','ppi','printer_dpi','nominal_lpi','effective_lpi','ne','axis','phase','tilt_deg','reverse_views','mirror','fit','stripe_sampling','crosstalk','compensation','regularization','color_mode','white_underbase','pitch_verified','viewing_distance_mm','lens_view_angle_deg','allow_unfilled','pitch_step','pitch_candidates'];
renderFields.push('edge_guard','depth_curve','front_strength','back_strength','edge_refinement','parallax_guard','max_parallax_percent');
printFields.push('gamut_guard');
renderFields.push('depth_black','depth_white','depth_gamma','detail_enabled','detail_strength','surface_strength');
let state, assetId=sessionStorage.getItem('studioAssetId')||'', jobId='', activeJob='', tab='photo', strokes=[], matrix=null, iccPath=null;
let originalImage=null, depthImage=null, depthPixels=null, brushActive=false, timer=null, view=0, direction=1;
let detailPixels=null, loadedDetail='',surfacePixels=null,loadedSurface='';
let loadedAsset='', loadedDepth='', toastTimer, referencePoint=null, assetLoadRevision=0;
const protectedUrl = url => url + (url.includes('?')?'&':'?') + 't='+encodeURIComponent(token);

function notify(message) { $('toast').textContent=message; $('toast').hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>{$('toast').hidden=true},6500); }
async function api(path, body, binary=false, filename='') {
  if(binary){
    if(body.size>512*1024*1024)throw Error('Dosya 512 MB sınırını aşıyor.');
    // Authenticate before sending the body, avoiding a mid-upload connection reset.
    await api('/api/state');
  }
  const headers={'X-Studio-Token':token};
  if(binary) headers['X-Filename']=encodeURIComponent(filename); else if(body) headers['Content-Type']='application/json';
  let response;
  try {response=await fetch(path,{method:body?'POST':'GET',headers,body:body?(binary?body:JSON.stringify(body)):undefined});}
  catch(error){throw Error('Uygulama sunucusuna ulaşılamıyor. Lenticular Studio.cmd dosyasını açıp gelen sayfadan tekrar dene.');}
  const data=await response.json(); if(!response.ok) throw Error(response.status===403?'Bu bağlantının oturumu eski. Lenticular Studio.cmd dosyasından programı yeniden aç.':data.error || 'İşlem tamamlanamadı.'); return data;
}
function value(id) { const el=$(id); return el.type==='checkbox'?el.checked:el.type==='range'||el.type==='number'||['nr','layers','process_res','render_long_edge','grid_size'].includes(id)?Number(el.value):el.value; }
function settings() { return {render:Object.fromEntries(renderFields.map(id=>[id,value(id)]).concat([['depth_strokes',strokes]])),print:Object.fromEntries(printFields.map(id=>[id,value(id)]).concat([['crosstalk_matrix',matrix],['icc_path',iccPath]]))}; }
function setSettings(data) {
  referencePoint=null;
  data={render:{...state.defaults.render,...data.render},print:{...state.defaults.print,...data.print}};
  for(const fields of [renderFields,printFields]) for(const id of fields) {
    const val=(fields===renderFields?data.render:data.print)?.[id]; if(val===undefined)continue;
    const el=$(id); if(el.type==='checkbox') el.checked=val; else {
      if(el.tagName==='SELECT' && ![...el.options].some(o=>o.value===String(val))) el.add(new Option(String(val),String(val)));
      el.value=val;
    }
  }
  strokes=data.render?.depth_strokes || []; matrix=data.print?.crosstalk_matrix || null; iccPath=data.print?.icc_path || null;
  $('matrixInfo').textContent=matrix?`${matrix.length} kanallı ölçüm matrisi`:'Ölçüm yok: komşu kanal modeli.';
  $('iccInfo').textContent=iccPath?'Yüklenmiş yazıcı profili kullanılıyor.':'Varsayılan: sRGB.';
  updateLabels(); drawEditor();
}
function updateLabels() {
  for(const id of ['angle_deg','effect_strength','zero_reference','depth_smoothing','crosstalk','compensation','front_strength','back_strength','edge_refinement','depth_black','depth_white','depth_gamma','detail_strength','surface_strength']) {
    let text=Number($(id).value).toFixed(id==='zero_reference'?3:2);
    if(id==='angle_deg')text+='°'; if(['crosstalk','compensation','depth_smoothing','edge_refinement'].includes(id))text=Math.round(Number($(id).value)*100)+'%';
    $(id+'Value').textContent=text;
  }
  const suggestion=suggestedViews();
  $('viewSuggestion').textContent=suggestion?`Örneklemeye göre başlangıç önerisi: ${suggestion} görünüş/kanal. min(PPI, DPI) ÷ LPI; optik kalite garantisi değildir. Sayıyı kendin değiştirebilirsin.`:'En az iki kanal için PPI/DPI değerlerini artır veya LPI değerini kontrol et.';
  $('useViewSuggestion').disabled=!suggestion;
  $('detailStatus').textContent=value('detail_enabled')?(detailPixels?'Yerel AI ayrıntısı etkin. Güç değişimi Derinlik sekmesinde görünür; 3D için görünüşleri yeniden oluştur.':'Ayrıntı henüz hesaplanmadı; şu an temel harita gösterilir. Yalnız derinlik haritasını oluştur düğmesine bas.'):'Ayrıntı kapalı; temel derinlik kullanılır. Açıldığında 9 genel ve 8 yakın bölge AI ile analiz edilir. Yüzey kabartısı ayrıca açılırsa ışık/gölgeden tahmini ayrıntı eklenir.';
  updateEditorHelp();
  const ratio=value('ppi')/value('effective_lpi');
  $('samplingInfo').textContent=`Lens başına ${ratio.toFixed(2)} raster piksel · Ne=${value('ne')}.`+(ratio<value('ne')?' Kanal sayısı raster örneklerini aşıyor.':'');
  const job=selectedJob();const saved={...state?.defaults.render,...job?.render};
  const stale=job?.render_folder&&(renderFields.some(id=>value(id)!==saved[id])||JSON.stringify(strokes)!==JSON.stringify(saved.depth_strokes||[]));
  $('renderStale').hidden=!stale;$('renderStale').textContent='Görünüş ayarları değişti. Ekrandaki görüntü seçili eski çalışmaya ait; yeni etkiyi görmek için Görünüşleri oluştur veya Fotoğraftan baskıya hazırla düğmesini kullan.';
}
function loadImage(url) { return new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(Error('Görüntü açılamadı.'));image.src=protectedUrl(url);}); }
async function loadAsset() {
  const selectedId=assetId,asset=state.assets[selectedId];if(!asset)return;
  const revision=++assetLoadRevision;
  $('assetInfo').textContent=`${asset.size[0]} × ${asset.size[1]} piksel · orijinal dosya korunur`;
  let changed=false;
  if(loadedAsset!==selectedId){const image=await loadImage(asset.photo_url);if(revision!==assetLoadRevision||assetId!==selectedId)return;originalImage=image;loadedAsset=selectedId;strokes=[];referencePoint=null;depthImage=null;depthPixels=null;loadedDepth='';detailPixels=null;loadedDetail='';surfacePixels=null;loadedSurface='';changed=true;}
  if(asset.depth_url && loadedDepth!==asset.depth_url){
    detailPixels=null;loadedDetail='';surfacePixels=null;loadedSurface='';
    const depth=await loadImage(asset.depth_url);if(revision!==assetLoadRevision||assetId!==selectedId)return;depthImage=depth;loadedDepth=asset.depth_url;
    const c=document.createElement('canvas');c.width=depthImage.width;c.height=depthImage.height;const ctx=c.getContext('2d');ctx.drawImage(depthImage,0,0);depthPixels=ctx.getImageData(0,0,c.width,c.height);
    changed=true;
  }
  if(asset.detail_delta_url && loadedDetail!==asset.detail_delta_url){
    const image=await loadImage(asset.detail_delta_url);if(revision!==assetLoadRevision||assetId!==selectedId)return;const c=document.createElement('canvas');c.width=image.width;c.height=image.height;const ctx=c.getContext('2d');ctx.drawImage(image,0,0);detailPixels=ctx.getImageData(0,0,c.width,c.height);loadedDetail=asset.detail_delta_url;changed=true;
  }
  if(asset.surface_delta_url && loadedSurface!==asset.surface_delta_url){
    const image=await loadImage(asset.surface_delta_url);if(revision!==assetLoadRevision||assetId!==selectedId)return;const c=document.createElement('canvas');c.width=image.width;c.height=image.height;const ctx=c.getContext('2d');ctx.drawImage(image,0,0);surfacePixels=ctx.getImageData(0,0,c.width,c.height);loadedSurface=asset.surface_delta_url;changed=true;
  }
  if(revision!==assetLoadRevision||assetId!==selectedId)return;
  if(!asset.surface_delta_url){surfacePixels=null;loadedSurface='';}
  if(!asset.detail_delta_url){detailPixels=null;loadedDetail='';surfacePixels=null;loadedSurface='';}
  if(changed)drawEditor();
}
function modifiedDepth() {
  if(!depthPixels)return null;
  const width=depthPixels.width,height=depthPixels.height;
  const vals=new Float32Array(width*height);
  const black=value('depth_black'),white=value('depth_white'),gamma=value('depth_gamma');
  const detail=value('detail_enabled')&&detailPixels&&detailPixels.width===width&&detailPixels.height===height,strength=value('detail_strength');
  const surface=detail&&surfacePixels&&surfacePixels.width===width&&surfacePixels.height===height, surfaceStrength=value('surface_strength');
  let low=0,high=1;
  for(let i=0;i<vals.length;i++){
    const delta=detail?((detailPixels.data[i*4]*256+detailPixels.data[i*4+1])/65535*2-1)*.06:0;
    const relief=surface?((surfacePixels.data[i*4]*256+surfacePixels.data[i*4+1])/65535*2-1)*.06:0;
    const d=depthPixels.data[i*4]/255+strength*delta+surfaceStrength*relief;
    vals[i]=d;low=Math.min(low,d);high=Math.max(high,d);
  }
  for(let i=0;i<vals.length;i++){
    const d=(vals[i]-low)/(high-low);
    vals[i]=Math.pow(Math.max(0,Math.min(1,(d-black)/(white-black))),1/gamma);
  }
  for(const s of strokes){
    const x=s.x*(width-1),y=s.y*(height-1),r=s.radius*Math.max(width,height);
    for(let py=Math.max(0,Math.floor(y-r));py<Math.min(height,Math.ceil(y+r)+1);py++)for(let px=Math.max(0,Math.floor(x-r));px<Math.min(width,Math.ceil(x+r)+1);px++){
      const weight=Math.max(0,1-Math.hypot(px-x,py-y)/r)*s.strength,i=py*width+px;vals[i]=vals[i]*(1-weight)+s.value*weight;
    }
  }
  return {width,height,vals};
}
function drawEditor(){
  const c=$('editCanvas'); if(!originalImage)return;
  c.width=originalImage.width;c.height=originalImage.height;
  const ctx=c.getContext('2d');ctx.drawImage(originalImage,0,0);
  const map=modifiedDepth();
  if(tab==='depth' && map){
    const overlay=document.createElement('canvas');overlay.width=map.width;overlay.height=map.height;const oc=overlay.getContext('2d');const pixels=oc.createImageData(map.width,map.height);
    for(let i=0;i<map.vals.length;i++){const v=Math.round(map.vals[i]*255);pixels.data.set([v,v,v,255],i*4);}oc.putImageData(pixels,0,0);ctx.drawImage(overlay,0,0,c.width,c.height);
  }
  if(tab==='depth'&&!map){ctx.fillStyle='#0009';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='white';ctx.font=`${Math.max(12,c.width/30)}px sans-serif`;ctx.fillText('Önce görünüşleri oluşturarak depth hesapla.',c.width*.08,c.height*.5);}
  if(referencePoint){
    const x=referencePoint.x*c.width,y=referencePoint.y*c.height,r=Math.max(7,c.width*.015);
    ctx.lineWidth=Math.max(2,c.width/300);ctx.strokeStyle='#56dbba';ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.moveTo(x-r*1.5,y);ctx.lineTo(x+r*1.5,y);ctx.moveTo(x,y-r*1.5);ctx.lineTo(x,y+r*1.5);ctx.stroke();
  }
  updateEditorHelp();
  $('emptyStage').hidden=true;
}
function switchTab(next){tab=next;stopPlayback();document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
  const edit=['photo','depth'].includes(tab);$('editCanvas').hidden=!edit;$('viewImage').hidden=edit;$('editControls').hidden=!edit;$('viewControls').hidden=edit;
  if(tab==='detail'){$('viewControls').hidden=true;showDetail();return;}
  if(tab==='parallax'){
    $('viewControls').hidden=true;showParallax();return;
  }
  $('previewNote').textContent=edit?'Orijinal renkler korunur. Fırça derinliği değiştirir; Sabit nokta seçimi derinlik haritasını kullanır.':tab==='proof'?'Lens görünüşü bir simülasyondur. Ölçülmüş karışım yüklenmediğinde varsayımsal modeli gösterir.':'Blender görünüşleri. Tahmini arka plan katmanlarını özellikle duvak ve kişi kenarlarında kontrol et.';
  edit?drawEditor():showView(0);
}
function showDetail(){const url=selectedJob()?.files.detail_depth;$('viewImage').hidden=!url;$('emptyStage').hidden=Boolean(url);if(url)$('viewImage').src=protectedUrl(url);else $('emptyStage').textContent='Ayrıntı seçeneğini açıp Yalnız derinlik haritasını oluştur düğmesine bas.';$('previewNote').textContent='Seçili çalışmada hesaplanan ayrıntılı harita. Güncel kaydırıcıları Derinlik sekmesinde gör; burası kaydedilmiş sonucu gösterir.';}
function suggestedViews(){const ppi=value('ppi'),dpi=value('printer_dpi'),lpi=value('effective_lpi');if(!Number.isFinite(ppi)||!Number.isFinite(dpi)||!Number.isFinite(lpi)||lpi<=0)return 0;const n=Math.floor(Math.min(ppi,dpi)/lpi);return n>=2?Math.min(64,n):0;}
function applyViewSuggestion(renderToo=false){const n=suggestedViews();if(!n){notify('En az iki kanal için çözünürlük / LPI oranını artır.');return;}if(matrix&&matrix.length!==n){notify(`Öneri ${n}; yüklü lens ölçümü ${matrix.length} kanal için. Ölçümü kaldır veya uygun matris yükle.`);return;}$('ne').value=n;if(renderToo)$('nr').value=n;updateLabels();}
function showParallax(){const url=selectedJob()?.files.parallax;$('viewImage').hidden=!url;$('emptyStage').hidden=Boolean(url);if(url)$('viewImage').src=protectedUrl(url);else $('emptyStage').textContent='Yeni bir görünüş çalışmasından sonra paralaks haritası oluşur.';$('previewNote').textContent='Mercan: baskının önü · mavi: arkası · siyah: sabit düzlem. Parlaklık uç görünüş farkını gösterir; gerçek optik derinlik ölçümü değildir.';}
function selectedJob(){return state?.jobs[jobId];}
function sourceForViews(){const j=selectedJob();if(!j)return null;if(tab==='proof'&&j.files.proof){const base=j.files.proof.replace('/lens-proof.png','/proof');return {base,count:j.print.ne};}if(tab==='views'&&j.view_base)return {base:j.view_base,count:j.view_count};return null;}
function showView(index){const source=sourceForViews();if(!source){$('viewImage').hidden=true;$('emptyStage').hidden=false;$('emptyStage').textContent=tab==='proof'?'Baskı hazırlanınca lens simülasyonu burada görünür.':'Önce görünüşleri oluştur.';return;}
  view=Math.max(0,Math.min(index,source.count-1));$('viewImage').hidden=false;$('emptyStage').hidden=true;$('viewImage').src=protectedUrl(`${source.base}/view_${String(view).padStart(4,'0')}.png`);$('viewSlider').max=source.count-1;$('viewSlider').value=view;$('viewLabel').textContent=`${view+1} / ${source.count}`;
}
function stopPlayback(){clearInterval(timer);timer=null;$('play').textContent='▶ Oynat';}
function play(){if(timer){stopPlayback();return;}if(!sourceForViews())return;$('play').textContent='Ⅱ Durdur';timer=setInterval(()=>{const source=sourceForViews();if(view===source.count-1)direction=-1;if(view===0)direction=1;showView(view+direction)},Number($('speed').value));}
function displayJob(){const job=selectedJob();$('downloads').replaceChildren();$('warnings').replaceChildren();if(!job){$('qualitySummary').replaceChildren();$('qualitySummary').hidden=true;$('jobBadge').textContent='Hazır';$('jobBadge').classList.remove('draft');return;}
  $('jobBadge').textContent={complete:'Tamamlandı',failed:'Hata',running:'Çalışıyor',queued:'Sırada',cancelled:'Durduruldu',interrupted:'Kesildi',cancel_requested:'Durduruluyor'}[job.status]||job.status;
  const draft=job.status==='complete'&&job.files.interlaced&&!job.print.pitch_verified;
  $('jobBadge').classList.toggle('draft',Boolean(draft));if(draft)$('jobBadge').textContent='Kalibrasyon taslağı';
  if(job.status==='complete'){
    const labels={scene:'Blender sahnesi',preview:'Hareketli önizleme',interlaced:'Lenticular TIFF',white:'Beyaz mürekkep maskesi',pitch:'Pitch testi',registration:'Hizalama işaretleri',report:'Baskı raporu',project:'Çalışma ayarları',proof:'Lens simülasyonu',response:'Kanal yanıt testi',matrix_template:'Lens ölçüm şablonu'};
    Object.assign(labels,{depth:'Kullanılan derinlik',detail_depth:'Ayrıntılı derinlik haritası',base_depth:'Temel derinlik haritası',quality:'Görünüş kalite raporu',comparison:'Ghosting karşılaştırması',handoff:'Baskı teslim notları'});
    for(const [key,label]of Object.entries(labels))if(job.files[key]){const a=document.createElement('a');a.textContent=label;a.href=protectedUrl(job.files[key]);a.target='_blank';a.rel='noreferrer';$('downloads').append(a);}
    for(const message of job.warnings || []){const p=document.createElement('p');p.className='warning';p.textContent=message;$('warnings').append(p);}
  }
  if(['views','proof'].includes(tab))showView(view);
  if(tab==='parallax')showParallax();
  if(tab==='detail')showDetail();
  const rows=[],q=job.quality,p=job.print_quality;
  if(q?.parallax){const v=q.parallax;rows.push(`Uygulanan açı ${v.effective_angle_deg.toFixed(2)}° · uç fark %${v.max_parallax_percent.toFixed(2)} · adım ${v.adjacent_view_step_px.toFixed(2)} px`);rows.push(`Derinlik kırpılması %${(q.edits.clipped_fraction*100).toFixed(2)} · boş alan %${((q.max_nonopaque_fraction||0)*100).toFixed(2)}`);}
  if(p){rows.push(`Lens başına ${p.pixels_per_lens.toFixed(2)} piksel · kaynak ayrıntısı ${p.source_native_ppi.toFixed(0)} PPI`);rows.push(`Telafisi azaltılan alan %${(p.compensation_limited_fraction*100).toFixed(1)} · renk kırpılması %${(p.compensation_clipped_fraction*100).toFixed(2)}`);const e=p.simulation_error;if(e?.before_mse>1e-10)rows.push(`Lens modelindeki hata değişimi: %${((e.after_mse/e.before_mse-1)*100).toFixed(1)} (fiziksel baskı ölçümü değil)`);}
  $('qualitySummary').replaceChildren(...rows.map(t=>{const p=document.createElement('p');p.textContent=t;return p}));$('qualitySummary').hidden=!rows.length;
}
async function refresh(){
  state=await api('/api/state');
  if(!assetId || !state.assets[assetId]){const ids=Object.keys(state.assets);assetId=ids.filter(id=>id!=='wedding').at(-1)||ids[0]||'';}
  if(assetId)sessionStorage.setItem('studioAssetId',assetId);
  fillSelect($('assetSelect'),Object.values(state.assets).map(asset=>[asset.id,asset.name]),assetId);
  const jobs=Object.values(state.jobs).filter(j=>j.asset_id===assetId).sort((a,b)=>b.created.localeCompare(a.created));
  if(!jobId||!jobs.some(j=>j.id===jobId))jobId=jobs[0]?.id||'';
  const stageNames={depth:'Derinlik',render:'Görünüş',full:'Tüm akış',print:'Baskı',pitch:'Pitch testi'}, statusNames={complete:'Tamamlandı',running:'Çalışıyor',queued:'Sırada',failed:'Hata',cancelled:'Durduruldu',interrupted:'Kesildi'};
  fillSelect($('jobSelect'),jobs.map(j=>[j.id,`${new Date(j.created).toLocaleString('tr-TR',{timeZone:'Europe/Istanbul',dateStyle:'short',timeStyle:'short'})} · ${j.stage==='depth'?'Harita':j.render.nr+' görünüş'} · ${stageNames[j.stage]||j.stage} · ${statusNames[j.status]||j.status}`]),jobId);
  const profile=$('profileSelect');fillSelect(profile,[['','Kayıtlı profil seç'],...Object.keys(state.profiles).map(name=>[name,name])],profile.value);
  const busy=Object.values(state.jobs).filter(j=>['queued','running','cancel_requested'].includes(j.status));
  activeJob=busy.find(j=>j.status==='running')?.id || busy[0]?.id || '';
  const current=state.jobs[activeJob]||selectedJob();
  $('progress').value=current?.progress || 0;$('progressText').textContent=current?.message || 'Fotoğrafını seçip ayarları düzenleyebilirsin.';$('cancel').hidden=!activeJob;
  $('messages').textContent=current?.status==='failed'?'Ayarları düzelterek yeni bir çalışma başlatabilirsin. Önceki çıktılar korunur.':busy.length>1?`${busy.length} işlem sırada`:'Derinlik dosyası tekrar kullanılır; model yeniden indirilmez.';
  $('engines').textContent=Object.values(state.engines).join('  ·  ');
  await loadAsset();displayJob();updateLabels();
}
function fillSelect(select,pairs,selected){
  if([...select.options].map(o=>o.value).join('|')!==pairs.map(p=>p[0]).join('|')){select.replaceChildren();for(const [id,label]of pairs)select.add(new Option(label,id));}
  else pairs.forEach((p,i)=>{if(select.options[i].text!==p[1])select.options[i].text=p[1]});
  select.value=selected;
}
async function start(stage,quick=false){
  if(!assetId)throw Error('Önce bir fotoğraf seç.');
  const data=settings();if(quick)data.render={...data.render,nr:2,render_long_edge:512,grid_size:384};
  const chosen=selectedJob();
  const result=await api('/api/jobs',{asset_id:assetId,stage,...data,render_job:chosen?.id});jobId=result.id;view=0;await refresh();if(stage!=='pitch')switchTab(stage==='print'?'proof':stage==='depth'?'depth':'views');
}
function safe(action){return async(...args)=>{try{await action(...args)}catch(error){notify(error.message)}};}
for(const id of ['depth_black','depth_white','depth_gamma'])$(id).addEventListener('input',()=>{if(value('depth_white')-value('depth_black')<.01){if(id==='depth_black')$('depth_white').value=Math.min(1,value('depth_black')+.01);else $('depth_black').value=Math.max(0,value('depth_white')-.01);}referencePoint=null;switchTab('depth');updateLabels()});
$('resetDepthLevels').onclick=()=>{$('depth_black').value=0;$('depth_white').value=1;$('depth_gamma').value=1;referencePoint=null;switchTab('depth');updateLabels()};
for(const id of [...renderFields,...printFields])$(id).addEventListener('input',updateLabels);
for(const id of ['ppi','printer_dpi','effective_lpi','nominal_lpi','axis','tilt_deg','mirror'])$(id).addEventListener('input',()=>{if($('pitch_verified').checked){$('pitch_verified').checked=false;notify('Lens / baskı koşulu değiştiği için pitch onayı kaldırıldı. Yeni koşulu fiziksel testle doğrula.');}});
$('assetSelect').onchange=safe(async()=>{assetLoadRevision++;assetId=$('assetSelect').value;if(assetId)sessionStorage.setItem('studioAssetId',assetId);jobId='';loadedAsset='';originalImage=null;strokes=[];$('emptyStage').textContent='Fotoğraf yükleniyor…';$('emptyStage').hidden=false;await refresh();switchTab('photo')});
$('jobSelect').onchange=()=>{jobId=$('jobSelect').value;view=0;displayJob();updateLabels()};
$('loadJobSettings').onclick=()=>{const job=selectedJob();if(job)setSettings({render:{...state.defaults.render,...job.render},print:{...state.defaults.print,...job.print}})};
$('axis').onchange=()=>{$('camera_axis').value=value('axis')==='vertical'?'x':'y'};
$('recommendChannels').onclick=()=>applyViewSuggestion(false);
$('useViewSuggestion').onclick=()=>applyViewSuggestion(true);
$('buildDepth').onclick=safe(()=>start('depth'));
for(const id of ['detail_enabled','detail_strength','surface_strength'])$(id).addEventListener('input',()=>{referencePoint=null;switchTab('depth');updateLabels()});
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>switchTab(b.dataset.tab));
$('photoFile').onchange=safe(async()=>{const file=$('photoFile').files[0];if(!file)return;const result=await api('/api/upload?kind=photo',file,true,file.name);assetLoadRevision++;assetId=result.id;sessionStorage.setItem('studioAssetId',assetId);jobId='';loadedAsset='';originalImage=null;$('emptyStage').textContent='Fotoğraf yükleniyor…';$('emptyStage').hidden=false;await refresh();switchTab('photo');$('photoFile').value=''});
$('depthFile').onchange=safe(async()=>{const file=$('depthFile').files[0];if(!assetId)throw Error('Önce fotoğraf seç.');if(file){await api(`/api/upload?kind=depth&asset=${assetId}&convention=${value('depthConvention')}`,file,true,file.name);loadedDepth='';await refresh();switchTab('depth')}});
$('iccFile').onchange=safe(async()=>{const file=$('iccFile').files[0];if(file){const r=await api('/api/upload?kind=icc',file,true,file.name);iccPath=r.path;$('iccInfo').textContent=r.name}});
$('matrixFile').onchange=safe(async()=>{const file=$('matrixFile').files[0];if(file){const r=await api('/api/upload?kind=matrix',file,true,file.name);matrix=r.matrix;$('ne').value=matrix.length;$('matrixInfo').textContent=`${r.name} · ${matrix.length} kanal`;updateLabels()}});
$('clearMatrix').onclick=()=>{matrix=null;$('matrixInfo').textContent='Ölçüm yok: komşu kanal modeli.'};
$('clearIcc').onclick=()=>{iccPath=null;$('color_mode').value='RGB';$('iccInfo').textContent='Varsayılan: sRGB.'};
$('balanceZero').onclick=()=>{const map=modifiedDepth();if(!map){notify('Önce derinliği hesaplamak için görünüşleri oluştur.');return;}const values=Array.from(map.vals).sort((a,b)=>a-b);referencePoint=null;drawEditor();$('zero_reference').value=(values[Math.floor((values.length-1)*.05)]+values[Math.floor((values.length-1)*.95)])/2;updateLabels();notify('Ön / arka derinlik dengelendi. Ana konuyu sabitlemek için Sabit nokta aracını kullanabilirsin.');};
$('render').onclick=safe(()=>start('render'));$('quickRender').onclick=safe(()=>start('render',true));$('print').onclick=safe(()=>start('print'));$('full').onclick=safe(()=>start('full'));$('pitch').onclick=safe(()=>start('pitch'));
$('cancel').onclick=safe(()=>api('/api/cancel',{id:activeJob}));
$('profileSelect').onchange=()=>{const p=state.profiles[$('profileSelect').value];if(p)setSettings(p)};
$('saveProfile').onclick=safe(async()=>{await api('/api/profile',{name:$('profileName').value,...settings()});await refresh();notify('Profil kaydedildi.')});
$('saveProject').onclick=()=>{const data={schema_version:1,asset_name:state.assets[assetId]?.name,...settings()};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='lenticular-ayarlar.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
$('projectFile').onchange=safe(async()=>{const file=$('projectFile').files[0];if(file){const data=JSON.parse(await file.text());if(data.schema_version!==1||!data.render||!data.print)throw Error('Geçerli Lenticular ayar dosyası seç.');setSettings(data);notify('Ayarlar yüklendi. Fotoğraf seçimi korunur.')}});
$('play').onclick=play;$('viewSlider').oninput=()=>{stopPlayback();showView(Number($('viewSlider').value))};$('speed').onchange=()=>{if(timer){stopPlayback();play()}};
$('undo').onclick=()=>{strokes.pop();referencePoint=null;drawEditor();updateLabels()};$('clearEdits').onclick=()=>{strokes=[];referencePoint=null;drawEditor();updateLabels()};
$('resetDefaults').onclick=()=>{stopPlayback();brushActive=false;setSettings({render:{...state.defaults.render,depth_strokes:[]},print:{...state.defaults.print}});$('editMode').value='view';$('brushValue').value=.5;$('brushRadius').value=.035;$('profileSelect').value='';$('profileName').value='';switchTab('photo');notify('Varsayılan 3D ve baskı ayarları yüklendi; fırça düzenlemeleri temizlendi. Fotoğraflar ve eski çıktılar korunur. Yeni sonuç için Hızlı önizleme oluştur.');};
$('pickReference').onclick=()=>{switchTab('photo');$('editMode').value='pin';updateEditorHelp();$('editCanvas').scrollIntoView({block:'center',behavior:'smooth'});};
$('editMode').onchange=()=>{brushActive=false;$('brushCursor').hidden=true;updateEditorHelp()};
for(const id of ['brushValue','brushRadius'])$(id).oninput=()=>{ $('brushCursor').hidden=true;updateEditorHelp() };
$('zero_reference').addEventListener('input',()=>{referencePoint=null;drawEditor()});
function updateEditorHelp(){
  const mode=value('editMode'),editing=['photo','depth'].includes(tab),brush=mode==='brush';
  $('brushValue').disabled=!brush;$('brushRadius').disabled=!brush;
  $('brushValueLabel').textContent=Number($('brushValue').value).toFixed(2)+' · 0 uzak / 1 yakın';
  $('brushRadiusLabel').textContent='Yarıçap %'+(Number($('brushRadius').value)*100).toFixed(1);
  $('referenceInfo').textContent=referencePoint?`İşaretli noktadan referans alındı: ${Number($('zero_reference').value).toFixed(3)}. Aynı derinlikteki bölgeler sabit düzleme yakın kalır.`:`Referans ${Number($('zero_reference').value).toFixed(3)} · kişi otomatik seçilmez. Fotoğraftan bir nokta seçebilirsin.`;
  $('editCanvas').style.cursor=mode==='view'?'default':'crosshair';
  if(!brush||!editing)$('brushCursor').hidden=true;
  if(editing)$('previewNote').textContent=!depthPixels?'Önce Hızlı önizleme düğmesiyle derinliği hesaplat; ardından referans veya fırça kullan.':mode==='pin'?'Fotoğrafın içinde sabit kalmasını istediğin derinliğe tıkla. İşaret bir örnek noktasıdır; bütün kişiyi kilitlemez. Sonucu görmek için yeniden Hızlı önizleme oluştur.':brush?'Resmin üzerinde basılı tutarak boya. Daire fırça alanıdır. 0 uzak, 1 yakın; referansa eşit değer sabit düzleme yaklaştırır. Değişimi Derinlik sekmesinde izle.':'İncele modu düzenleme yapmaz. Referans için Sabit nokta seç, boyamak için Derinlik fırçası seç.';
}
function moveBrushCursor(event){
  const cursor=$('brushCursor'),c=$('editCanvas');
  if(value('editMode')!=='brush'||!depthPixels){cursor.hidden=true;return;}
  const rect=c.getBoundingClientRect(),stage=$('stage').getBoundingClientRect(),r=Number($('brushRadius').value)*Math.max(c.width,c.height);
  cursor.style.width=(2*r*rect.width/c.width)+'px';cursor.style.height=(2*r*rect.height/c.height)+'px';cursor.style.left=(event.clientX-stage.left)+'px';cursor.style.top=(event.clientY-stage.top)+'px';cursor.hidden=false;
}

function editAt(event){
  const c=$('editCanvas'),rect=c.getBoundingClientRect();const x=Math.min(1,Math.max(0,(event.clientX-rect.left)/rect.width)),y=Math.min(1,Math.max(0,(event.clientY-rect.top)/rect.height));
  if(value('editMode')==='pin'){
    const map=modifiedDepth();if(!map){notify('Önce depth oluşturmak için görünüşleri hazırla.');return;}
    const px=Math.round(x*(map.width-1)),py=Math.round(y*(map.height-1));$('zero_reference').value=map.vals[py*map.width+px];referencePoint={x,y};drawEditor();updateLabels();return;
  }
  if(value('editMode')==='brush'){
    if(!depthPixels){notify('Önce depth oluşturmak için görünüşleri hazırla.');return;}
    if(strokes.length>=10000){notify('Fırça sınırına ulaştın.');return;}
    strokes.push({x,y,radius:Number($('brushRadius').value),value:Number($('brushValue').value),strength:.7});referencePoint=null;drawEditor();updateLabels();
  }
}
$('editCanvas').onpointerdown=event=>{brushActive=true;event.target.setPointerCapture(event.pointerId);editAt(event)};
$('editCanvas').onpointerleave=()=>{$('brushCursor').hidden=true};
$('editCanvas').onpointermove=event=>{moveBrushCursor(event);if(brushActive&&value('editMode')==='brush')editAt(event)};
$('editCanvas').onpointerup=()=>{brushActive=false};$('editCanvas').onpointercancel=()=>{brushActive=false};
$('shutdown').onclick=safe(async()=>{stopPlayback();clearInterval(poll);await api('/api/shutdown',{ok:true});$('progressText').textContent='Uygulama kapatıldı. Yeniden açmak için Lenticular Studio dosyasını kullan.';document.querySelectorAll('button').forEach(b=>b.disabled=true)});
const poll=setInterval(()=>refresh().catch(error=>{$('messages').textContent='Uygulama bağlantısı bekleniyor.'}),2000);
safe(async()=>{await refresh();updateLabels()})();
