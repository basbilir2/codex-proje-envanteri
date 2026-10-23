'use strict';
const $ = id => document.getElementById(id);
const token = new URLSearchParams(location.search).get('t') || sessionStorage.getItem('studioToken') || '';
sessionStorage.setItem('studioToken', token);
const renderFields = ['nr','angle_deg','effect_strength','zero_reference','depth_smoothing','grid_size','repair','layers','inpaint_radius','process_res','render_long_edge','camera_axis'];
const printFields = ['width_mm','height_mm','bleed_mm','ppi','printer_dpi','nominal_lpi','effective_lpi','ne','axis','phase','tilt_deg','reverse_views','mirror','fit','stripe_sampling','crosstalk','compensation','regularization','color_mode','white_underbase','pitch_verified','viewing_distance_mm','lens_view_angle_deg','allow_unfilled','pitch_step','pitch_candidates'];
renderFields.push('edge_guard','depth_curve','front_strength','back_strength','edge_refinement','parallax_guard','max_parallax_percent');
printFields.push('gamut_guard','lens_angle_verified','raster_ppi_verified');
renderFields.push('depth_black','depth_white','depth_gamma','detail_enabled','detail_strength','surface_strength');
renderFields.push('front_parallax_percent','back_parallax_percent','repair_quality');
renderFields.push('depth_normalization');
let objectRegions=[],objectDraft=[],objectSelected=-1,objectKeyboardPoint=[.5,.5];
let state, assetId=sessionStorage.getItem('studioAssetId')||'', jobId='', activeJob='', tab='photo', strokes=[], matrix=null, iccPath=null;
let originalImage=null, depthImage=null, depthPixels=null, brushActive=false, timer=null, view=0, direction=1;
let detailPixels=null, loadedDetail='',surfacePixels=null,loadedSurface='';
let loadedAsset='', loadedDepth='', toastTimer, referencePoint=null, assetLoadRevision=0;
let animationSources=[], pendingMorph=null, morphRevision=0;
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
function animationSettings(){return {mode:value('animationMode'),engine:value('animationEngine'),nt:value('animationNt'),long_edge:value('animationEdge'),pingpong:value('animationPingpong'),easing:value('animationEasing'),points:JSON.parse($('morphPoints').value||'[]'),weights:$('flipWeights').value.trim()?$('flipWeights').value.split(',').map(Number):[],preview_fps:value('animationFps'),zoom_start:value('zoomStart'),zoom_end:value('zoomEnd'),anchor_x:value('anchorX'),anchor_y:value('anchorY'),device:value('animationDevice')};}
function settings() { return {render:Object.fromEntries(renderFields.map(id=>[id,value(id)]).concat([['depth_strokes',strokes],['reference_point',referencePoint],['object_regions',objectRegions]])),print:Object.fromEntries(printFields.map(id=>[id,value(id)]).concat([['crosstalk_matrix',matrix],['icc_path',iccPath]])),animation:value('workMode')==='animation'?animationSettings():{...state.defaults.animation}}; }
function setSettings(data) {
  referencePoint=data.render?.reference_point || null;
  objectRegions=structuredClone(data.render?.object_regions||[]);objectDraft=[];objectSelected=objectRegions.length-1;renderObjectControls();
  const effect={...state.defaults.animation,...data.animation};
  for(const [id,key] of Object.entries({animationMode:'mode',animationEngine:'engine',animationNt:'nt',animationEdge:'long_edge',animationPingpong:'pingpong',animationEasing:'easing',animationFps:'preview_fps',zoomStart:'zoom_start',zoomEnd:'zoom_end',anchorX:'anchor_x',anchorY:'anchor_y',animationDevice:'device'})){if($(id).type==='checkbox')$(id).checked=effect[key];else $(id).value=effect[key];}
  $('morphPoints').value=JSON.stringify(effect.points||[]);$('flipWeights').value=(effect.weights||[]).join(', ');pendingMorph=null;
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
  $('viewSuggestion').textContent=suggestion?`Kanal başına en az 2 raster piksel ile başlangıç: ${suggestion} kanal. Bu bir baskı garantisi değildir; gerçek kanal ayrımı ölçülür. Sayıyı değiştirebilirsin.`:'Kanal başına 2 piksel bırakan bir başlangıç yok; PPI / LPI ve fiziksel şerit testini kontrol et.';
  $('useViewSuggestion').disabled=!suggestion;
  $('detailStatus').textContent=value('detail_enabled')?(detailPixels?'Yerel AI ayrıntısı etkin. Güç değişimi Derinlik sekmesinde görünür; 3D için görünüşleri yeniden oluştur.':'Ayrıntı henüz hesaplanmadı; şu an temel harita gösterilir. Yalnız derinlik haritasını oluştur düğmesine bas.'):'Ayrıntı kapalı; temel derinlik kullanılır. Açıldığında 9 genel ve 8 yakın bölge AI ile analiz edilir. Yüzey kabartısı ayrıca açılırsa ışık/gölgeden tahmini ayrıntı eklenir.';
  updateEditorHelp();
  const ratio=value('ppi')/value('effective_lpi');
  const axisMM=value(value('axis')==='vertical'?'width_mm':'height_mm'),lenses=axisMM*value('effective_lpi')/25.4;
  $('samplingInfo').textContent=`Lens başına ${ratio.toFixed(2)} piksel · kanal başına ${(ratio/value('ne')).toFixed(2)} piksel · hareket yönünde ${lenses.toFixed(0)} lens. Çeyrek kanal kayması: ${(25.4/(4*value('ne')*axisMM)).toFixed(4)} LPI hata.`+(ratio<value('ne')?' Kanal sayısı raster örneklerini aşıyor.':'');
  const balanced=value('depth_curve')==='balanced';$('balancedBudget').hidden=!balanced;
  for(const id of ['effect_strength','front_strength','back_strength'])$(id).disabled=balanced;
  const job=selectedJob();const saved={...state?.defaults.render,...job?.render};
  const sameReference=JSON.stringify(referencePoint)===JSON.stringify(saved.reference_point||null);
  // A pinned reference is sampled from full-precision depth by the renderer;
  // the rounded slider display is not an independent render setting.
  const stale=job?.render_folder&&(!sameReference||renderFields.some(id=>!(id==='zero_reference'&&referencePoint)&&value(id)!==saved[id])||JSON.stringify(strokes)!==JSON.stringify(saved.depth_strokes||[])||JSON.stringify(objectRegions)!==JSON.stringify(saved.object_regions||[]));
  $('renderStale').hidden=!stale;$('renderStale').textContent='Görünüş ayarları değişti. Ekrandaki görüntü seçili eski çalışmaya ait; yeni etkiyi görmek için Görünüşleri oluştur veya Fotoğraftan baskıya hazırla düğmesini kullan.';
  if(job?.animation){let current;try{current=animationSettings();}catch{current=null;}const changed=!current||Object.keys(current).some(k=>k!=='preview_fps'&&JSON.stringify(current[k])!==JSON.stringify(job.animation[k]));$('renderStale').hidden=!changed;$('renderStale').textContent='Animasyon ayarları değişti. Gösterilen kareler seçili eski çalışmaya ait; yeni animasyon oluştur.';}
}
function objectMask(region,width,height){
  const xs=region.points.map(p=>Math.round(p[0]*(width-1))),ys=region.points.map(p=>Math.round(p[1]*(height-1)));
  const x0=Math.min(...xs),y0=Math.min(...ys),w=Math.max(...xs)-x0+1,h=Math.max(...ys)-y0+1;
  const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;const ctx=canvas.getContext('2d');
  ctx.beginPath();xs.forEach((x,i)=>i?ctx.lineTo(x-x0,ys[i]-y0):ctx.moveTo(x-x0,ys[i]-y0));ctx.closePath();ctx.fill();
  const data=ctx.getImageData(0,0,w,h).data,indices=[];
  for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(data[(y*w+x)*4+3]>=128)indices.push((y+y0)*width+x+x0);
  return indices;
}
function applyObjectPreview(vals,width,height){
  for(const region of objectRegions){
    const indices=objectMask(region,width,height);if(!indices.length)continue;
    const values=indices.map(i=>vals[i]).sort((a,b)=>a-b),middle=Math.floor(values.length/2);
    const pivot=values.length%2?values[middle]:(values[middle-1]+values[middle])/2,center=Math.max(0,Math.min(1,pivot+region.offset));
    const below=pivot-values[0],above=values[values.length-1]-pivot;
    const gain=Math.min(region.relief,below>0?center/below:Infinity,above>0?(1-center)/above:Infinity);
    for(const i of indices)vals[i]=center+gain*(vals[i]-pivot);
  }
}
function drawObjectBorders(ctx,c){
  [...objectRegions.map(r=>r.points),...(objectDraft.length?[objectDraft]:[])].forEach((points,index)=>{
    ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p[0]*c.width,p[1]*c.height):ctx.moveTo(p[0]*c.width,p[1]*c.height));
    if(index<objectRegions.length)ctx.closePath();ctx.strokeStyle=index===objectSelected?'#f59c40':'#56dbba';ctx.lineWidth=Math.max(2,c.width/400);ctx.stroke();
    for(const point of points){ctx.beginPath();ctx.arc(point[0]*c.width,point[1]*c.height,Math.max(2,c.width/250),0,Math.PI*2);ctx.fillStyle=ctx.strokeStyle;ctx.fill();}
    if(points.length){ctx.fillStyle=ctx.strokeStyle;ctx.font=`${Math.max(12,c.width/50)}px sans-serif`;ctx.fillText(index<objectRegions.length?String(index+1):'Çizim',points[0][0]*c.width,points[0][1]*c.height);}
  });
}
function renderObjectControls(){
  const select=$('objectSelect');select.replaceChildren(new Option('Nesne seçilmedi',''));
  objectRegions.forEach((_,i)=>select.add(new Option(`Nesne ${i+1}`,String(i))));select.value=objectSelected>=0?String(objectSelected):'';
  const region=objectRegions[objectSelected];$('objectOffset').value=region?.offset??0;$('objectRelief').value=region?.relief??1;
  $('objectOffset').disabled=$('objectRelief').disabled=!region;
  $('objectOffsetValue').textContent=Number($('objectOffset').value).toFixed(2);$('objectReliefValue').textContent=Number($('objectRelief').value).toFixed(2)+'×';
  $('objectInfo').textContent=objectDraft.length?`${objectDraft.length} sınır noktası · en az 3 nokta ile tamamla.`:`${objectRegions.length} nesne bölgesi. Derinlik görünümü yaklaşık düzenleme önizlemesidir; tam hesap yeni görünüşte uygulanır.`;
}
function objectChanged(){referencePoint=null;drawEditor();renderObjectControls();updateLabels();}
function loadImage(url) { return new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(Error('Görüntü açılamadı.'));image.src=protectedUrl(url);}); }
async function loadAsset() {
  const selectedId=assetId,asset=state.assets[selectedId];if(!asset)return;
  const revision=++assetLoadRevision;
  $('assetInfo').textContent=`${asset.size[0]} × ${asset.size[1]} piksel · orijinal dosya korunur`;
  let changed=false;
  if(loadedAsset!==selectedId){const image=await loadImage(asset.photo_url);if(revision!==assetLoadRevision||assetId!==selectedId)return;originalImage=image;loadedAsset=selectedId;strokes=[];objectRegions=[];objectDraft=[];objectSelected=-1;renderObjectControls();referencePoint=null;depthImage=null;depthPixels=null;loadedDepth='';detailPixels=null;loadedDetail='';surfacePixels=null;loadedSurface='';changed=true;}
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
  applyObjectPreview(vals,width,height);
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
  drawObjectBorders(ctx,c);
  if(referencePoint){
    const x=referencePoint.x*c.width,y=referencePoint.y*c.height,r=Math.max(7,c.width*.015);
    ctx.lineWidth=Math.max(2,c.width/300);ctx.strokeStyle='#56dbba';ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.moveTo(x-r*1.5,y);ctx.lineTo(x+r*1.5,y);ctx.moveTo(x,y-r*1.5);ctx.lineTo(x,y+r*1.5);ctx.stroke();
  }
  updateEditorHelp();
  $('emptyStage').hidden=true;
}
function showAnalysis(){const url=selectedJob()?.files.analysis_image;$('viewImage').hidden=!url;$('emptyStage').hidden=Boolean(url);if(url){$('viewImage').src=protectedUrl(url);$('viewImage').alt='Solda fotoğraf, ortada derinlik, sağda kanallar arası hareket riski';}else $('emptyStage').textContent='Sahne analizi hazırlanıyor…';$('previewNote').textContent='Solda fotoğraf · ortada kullanılan derinlik · sağda kanallar arası hareket riski. Sabit referans korunur; fiziksel baskı ölçümü değildir.';}
function switchTab(next){tab=next;stopPlayback();document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
  const edit=['photo','depth'].includes(tab);$('editCanvas').hidden=!edit;$('viewImage').hidden=edit;$('editControls').hidden=!edit;$('viewControls').hidden=edit;
  if(tab==='analysis'){$('viewControls').hidden=true;showAnalysis();return;}
  if(tab==='detail'){$('viewControls').hidden=true;showDetail();return;}
  if(tab==='parallax'){
    $('viewControls').hidden=true;showParallax();return;
  }
  $('previewNote').textContent=edit?'Orijinal renkler korunur. Fırça derinliği değiştirir; Sabit nokta seçimi derinlik haritasını kullanır.':tab==='proof'?'Seçilen baskı kanallarının dijital önizlemesi. Gerçek lensin iki göze ayrı görüntü verdiğini veya baskıda 3D oluştuğunu doğrulamaz.':selectedJob()?.animation?'Üretilen zaman kareleri. Baskıda görülecek kanal sayısı Ne ve fiziksel lens ayrımı farklı olabilir.':'Blender görünüşleri; hareket, fiziksel 3D kanıtı değildir. Yüz ayrıntısını ve kenarları ayrıca kontrol et.';
  edit?drawEditor():showView(0);
}
function showDetail(){const url=selectedJob()?.files.detail_depth;$('viewImage').hidden=!url;$('emptyStage').hidden=Boolean(url);if(url)$('viewImage').src=protectedUrl(url);else $('emptyStage').textContent='Ayrıntı seçeneğini açıp Yalnız derinlik haritasını oluştur düğmesine bas.';$('previewNote').textContent='Seçili çalışmada hesaplanan ayrıntılı harita. Güncel kaydırıcıları Derinlik sekmesinde gör; burası kaydedilmiş sonucu gösterir.';}
function suggestedViews(){const ppi=value('ppi'),lpi=value('effective_lpi');if(!Number.isFinite(ppi)||!Number.isFinite(lpi)||lpi<=0)return 0;const n=Math.floor(ppi/lpi/2);return n>=2?Math.min(64,n):0;}
function applyViewSuggestion(renderToo=false){const n=suggestedViews();if(!n){notify('En az iki kanal için çözünürlük / LPI oranını artır.');return;}if(matrix&&matrix.length!==n){notify(`Öneri ${n}; yüklü lens ölçümü ${matrix.length} kanal için. Ölçümü kaldır veya uygun matris yükle.`);return;}$('ne').value=n;if(renderToo)$('nr').value=n;updateLabels();}
function showParallax(){const url=selectedJob()?.files.parallax;$('viewImage').hidden=!url;$('emptyStage').hidden=Boolean(url);if(url)$('viewImage').src=protectedUrl(url);else $('emptyStage').textContent='Yeni bir görünüş çalışmasından sonra paralaks haritası oluşur.';$('previewNote').textContent='Mercan: baskının önü · mavi: arkası · siyah: sabit düzlem. Parlaklık uç görünüş farkını gösterir; gerçek optik derinlik ölçümü değildir.';}
function selectedJob(){return state?.jobs[jobId];}
function sourceForViews(){const j=selectedJob();if(!j)return null;if(tab==='proof'&&j.files.proof){const base=j.files.proof.replace('/lens-proof.png','/proof');return {base,count:j.print.ne};}if(tab==='views'&&j.view_base)return {base:j.view_base,count:j.view_count};return null;}
function showView(index){const source=sourceForViews();if(!source){$('viewImage').hidden=true;$('emptyStage').hidden=false;$('emptyStage').textContent=tab==='proof'?'Baskı hazırlanınca lens simülasyonu burada görünür.':'Önce görünüşleri oluştur.';return;}
  view=Math.max(0,Math.min(index,source.count-1));$('viewImage').hidden=false;$('emptyStage').hidden=true;$('viewImage').alt=tab==='proof'?'Baskı kanalı önizlemesi':selectedJob()?.animation?'Animasyon zaman karesi':'Blender görünüşü';$('viewImage').src=protectedUrl(`${source.base}/view_${String(view).padStart(4,'0')}.png`);$('viewSlider').max=source.count-1;$('viewSlider').value=view;$('viewLabel').textContent=`${view+1} / ${source.count}`;
}
function stopPlayback(){clearInterval(timer);timer=null;$('play').textContent='▶ Oynat';}
function play(){if(timer){stopPlayback();return;}if(!sourceForViews())return;$('play').textContent='Ⅱ Durdur';timer=setInterval(()=>{const source=sourceForViews();if(!source){stopPlayback();return;}if(selectedJob()?.animation){showView((view+1)%source.count);}else{if(view===source.count-1)direction=-1;if(view===0)direction=1;showView(view+direction)}},selectedJob()?.animation&&tab==='views'?1000/value('animationFps'):Number($('speed').value));}
function displayJob(){const job=selectedJob();$('downloads').replaceChildren();$('warnings').replaceChildren();$('analysisSummary').hidden=!job?.analysis;$('applyAnalysis').hidden=!job?.analysis;if(job?.analysis){const a=job.analysis;$('analysisSummary').textContent=`Analiz: ${a.parallax.effective_angle_deg.toFixed(3)}° uygulanan açı; kanal başına ${a.sampling_budget.pixels_per_channel.toFixed(2)} piksel. ${a.warnings.length} kontrol notu. Sabit referans korunmuştur. Rapor ve görsel aşağıdaki çıktılarda.`;}if(!job){$('qualitySummary').replaceChildren();$('qualitySummary').hidden=true;$('jobBadge').textContent='Hazır';$('jobBadge').classList.remove('draft');return;}
  $('jobBadge').textContent={complete:'Tamamlandı',failed:'Hata',running:'Çalışıyor',queued:'Sırada',cancelled:'Durduruldu',interrupted:'Kesildi',cancel_requested:'Durduruluyor'}[job.status]||job.status;
  const draft=job.status==='complete'&&job.files.interlaced;
  $('jobBadge').classList.toggle('draft',Boolean(draft));if(draft)$('jobBadge').textContent='Kalibrasyon taslağı';
  if(job.status==='complete'){
    const labels={scene:'Blender sahnesi',preview:'Hareketli önizleme',interlaced:'Lenticular TIFF · fiziksel test gerekli',white:'Beyaz mürekkep maskesi',pitch:'Pitch testi',registration:'Hizalama işaretleri',report:'Baskı raporu',project:'Çalışma ayarları',proof:'Dijital kanal önizlemesi',response:'Kanal yanıt testi',matrix_template:'Lens ölçüm şablonu'};
    Object.assign(labels,{depth:'Kullanılan derinlik',detail_depth:'Ayrıntılı derinlik haritası',base_depth:'Temel derinlik haritası',quality:'Görünüş kalite raporu',comparison:'Ghosting karşılaştırması',handoff:'Baskı teslim notları'});
    Object.assign(labels,{frameset:'Zaman kareleri kaydı',channel_plan:'Baskı kanal eşlemesi',sampling_risk:'Derinlik / netlik risk haritası'});
    Object.assign(labels,{analysis:'Sahne analizi · ayrıntılı kayıt',analysis_notes:'Sahne analizi · okunabilir rapor',analysis_image:'Sahne analizi · fotoğraf / derinlik / risk'});
    for(const [key,label]of Object.entries(labels))if(job.files[key]){const a=document.createElement('a');a.textContent=label;a.href=protectedUrl(job.files[key]);a.target='_blank';a.rel='noreferrer';$('downloads').append(a);}
    for(const message of job.warnings || []){const p=document.createElement('p');p.className='warning';p.textContent=message;$('warnings').append(p);}
  }
  if(['views','proof'].includes(tab))showView(view);
  if(tab==='parallax')showParallax();
  if(tab==='detail')showDetail();
  if(tab==='analysis')showAnalysis();
  const rows=[],q=job.quality,p=job.print_quality;
  if(q?.render_size)rows.push(`${q.render_size.join(' × ')} piksel · ${q.source_resolution_render?'Kaynak boyutunda görünüş':'Küçültülmüş çalışma görünüşü'}`);
  if(q?.restoration)rows.push(q.restoration.layers.some(l=>l.matting)?'İnce kenar ayrımı ve ortak arka plan katmanları uygulandı.':'Katmanlı arka plan uygulandı.');
  if(job.animation){rows.push(`${job.nt||job.animation.nt} zaman karesi · ${job.animation_quality?.method||job.animation.engine} · Ne=${job.print.ne}`);if(job.animation_quality?.uncertain_fraction!=null)rows.push(`Hareket eşleşmesinde belirsiz alan: %${(job.animation_quality.uncertain_fraction*100).toFixed(1)}`);}
  if(q?.parallax){const v=q.parallax;rows.push(`Uygulanan açı ${v.effective_angle_deg.toFixed(2)}° · uç fark %${v.max_parallax_percent.toFixed(2)} · adım ${v.adjacent_view_step_px.toFixed(2)} px`);rows.push(`Derinlik kırpılması %${(q.edits.clipped_fraction*100).toFixed(2)} · boş alan %${((q.max_nonopaque_fraction||0)*100).toFixed(2)}`);}
  if(p){rows.push(`Lens başına ${p.pixels_per_lens.toFixed(2)} piksel · kaynak ayrıntısı ${p.source_native_ppi.toFixed(0)} PPI`);rows.push(`Telafisi azaltılan alan %${(p.compensation_limited_fraction*100).toFixed(1)} · renk kırpılması %${(p.compensation_clipped_fraction*100).toFixed(2)}`);const e=p.simulation_error;if(e?.before_mse>1e-10)rows.push(`Lens modelindeki hata değişimi: %${((e.after_mse/e.before_mse-1)*100).toFixed(1)} (fiziksel baskı ölçümü değil)`);}
  if(q?.parallax?.reference_region_relief_px!=null)rows.push(`Sabit nokta çevresinde iç hacim farkı: ${q.parallax.reference_region_relief_px.toFixed(2)} kaynak piksel · nokta kayması ${q.parallax.reference_endpoint_disparity_px.toFixed(4)} px`);
  if(p){rows.push(`Şerit başına ${(p.pixels_per_channel??p.pixels_per_lens/job.print.ne).toFixed(2)} raster piksel · fiziksel 3D henüz doğrulanmadı`);if(p.raster_integrity?.sampled_pixels_verified)rows.push('Kaydedilen TIFF kanal örnekleri doğrulandı; bu fiziksel lens testi değildir.');}
  if(p?.depth_sampling){const d=p.depth_sampling;rows.push(`Baskı kanalları arasında adım: ${d.adjacent_step_lenticules_p95.toFixed(2)} lens (p95); 1 lensi aşan alan %${(100*d.over_one_lenticule_fraction).toFixed(1)}. Bu geometrik risk göstergesidir.`);for(const [key,label] of [['front','Ön'],['back','Arka']]){const s=d.sides[key];rows.push(`${label}: uç kayma ${s.max_endpoint_mm.toFixed(2)} mm · bölge içi fark ${s.internal_relief_p10_p90_mm.toFixed(2)} mm (p10–p90).`);}}
  $('qualitySummary').replaceChildren(...rows.map(t=>{const p=document.createElement('p');p.textContent=t;return p}));$('qualitySummary').hidden=!rows.length;
}
async function refresh(){
  state=await api('/api/state');
  if(!assetId || !state.assets[assetId]){const ids=Object.keys(state.assets);assetId=ids.filter(id=>id!=='wedding').at(-1)||ids[0]||'';}
  if(assetId)sessionStorage.setItem('studioAssetId',assetId);
  fillSelect($('assetSelect'),Object.values(state.assets).map(asset=>[asset.id,asset.name]),assetId);
  fillSelect($('animationSource'),Object.values(state.assets).filter(a=>a.kind!=='sequence').map(a=>[a.id,a.name]),$('animationSource').value||Object.values(state.assets).find(a=>a.kind!=='sequence')?.id);
  const jobs=Object.values(state.jobs).filter(j=>j.asset_id===assetId).sort((a,b)=>b.created.localeCompare(a.created));
  if(!jobId||!jobs.some(j=>j.id===jobId))jobId=jobs[0]?.id||'';
  const stageNames={analyze:'Sahne analizi',depth:'Derinlik',render:'Görünüş',full:'Tüm akış',print:'Baskı',pitch:'Pitch testi'}, statusNames={complete:'Tamamlandı',running:'Çalışıyor',queued:'Sırada',failed:'Hata',cancelled:'Durduruldu',interrupted:'Kesildi'};
  Object.assign(stageNames,{animation:'Animasyon',animation_full:'Animasyon + baskı',animation_print:'Animasyon baskısı'});
  fillSelect($('jobSelect'),jobs.map(j=>[j.id,`${new Date(j.created).toLocaleString('tr-TR',{timeZone:'Europe/Istanbul',dateStyle:'short',timeStyle:'short'})} · ${j.animation?(j.nt||j.animation.nt)+' zaman karesi':j.stage==='analyze'?'Analiz':j.stage==='depth'?'Harita':j.render.nr+' görünüş'} · ${stageNames[j.stage]||j.stage} · ${statusNames[j.status]||j.status}`]),jobId);
  const profile=$('profileSelect');fillSelect(profile,[['','Kayıtlı profil seç'],...Object.keys(state.profiles).map(name=>[name,name])],profile.value);
  const busy=Object.values(state.jobs).filter(j=>['queued','running','cancel_requested'].includes(j.status));
  activeJob=busy.find(j=>j.status==='running')?.id || busy[0]?.id || '';
  const current=state.jobs[activeJob]||selectedJob();
  $('progress').value=current?.progress || 0;$('progressText').textContent=current?.message || 'Fotoğrafını seçip ayarları düzenleyebilirsin.';$('cancel').hidden=!activeJob;
  $('messages').textContent=current?.status==='failed'?'Ayarları düzelterek yeni bir çalışma başlatabilirsin. Önceki çıktılar korunur.':busy.length>1?`${busy.length} işlem sırada`:current?.animation?'Animasyon yerelde çalışır; aynı kareler yeni baskı ayarlarıyla tekrar kullanılabilir.':'Derinlik dosyası tekrar kullanılır; model yeniden indirilmez.';
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
  const result=await api('/api/jobs',{asset_id:assetId,stage,...data,render_job:chosen?.id});jobId=result.id;view=0;await refresh();if(stage!=='pitch')switchTab(stage==='analyze'?'analysis':stage==='print'?'proof':stage==='depth'?'depth':'views');
}
function safe(action){return async(...args)=>{try{await action(...args)}catch(error){notify(error.message)}};}
function invalidatePrintEvidence(id){
  const pitch=['ppi','printer_dpi','nominal_lpi','effective_lpi','axis','tilt_deg','mirror','phase','width_mm','height_mm','bleed_mm','viewing_distance_mm','icc_path','color_mode','white_underbase','stripe_sampling'];
  let changed=false;
  for(const [flag,fields] of [['pitch_verified',pitch],['raster_ppi_verified',['ppi','printer_dpi','axis','tilt_deg','icc_path','color_mode','white_underbase']],['lens_angle_verified',['nominal_lpi','lens_view_angle_deg']]])if(fields.includes(id)&&$(flag).checked){$(flag).checked=false;changed=true;}
  if(matrix&&[...pitch,'ne','lens_view_angle_deg'].includes(id)){matrix=null;$('compensation').value=0;$('matrixInfo').textContent='Baskı koşulları değişti; uygun kanal ölçümünü yeniden yükle.';changed=true;}
  if(changed)notify('Baskı koşulu değişti; ilgili kalibrasyon onayı/ölçümü kaldırıldı. Yeni koşulu doğrula.');
}
for(const id of ['depth_black','depth_white','depth_gamma'])$(id).addEventListener('input',()=>{if(value('depth_white')-value('depth_black')<.01){if(id==='depth_black')$('depth_white').value=Math.min(1,value('depth_black')+.01);else $('depth_black').value=Math.max(0,value('depth_white')-.01);}referencePoint=null;switchTab('depth');updateLabels()});
$('resetDepthLevels').onclick=()=>{$('depth_black').value=0;$('depth_white').value=1;$('depth_gamma').value=1;referencePoint=null;switchTab('depth');updateLabels()};
for(const id of [...renderFields,...printFields])$(id).addEventListener('input',updateLabels);
for(const id of printFields)$(id).addEventListener('input',()=>{invalidatePrintEvidence(id);updateLabels();});
$('assetSelect').onchange=safe(async()=>{assetLoadRevision++;assetId=$('assetSelect').value;if(assetId)sessionStorage.setItem('studioAssetId',assetId);jobId='';loadedAsset='';originalImage=null;strokes=[];$('emptyStage').textContent='Fotoğraf yükleniyor…';$('emptyStage').hidden=false;await refresh();const asset=state.assets[assetId];$('workMode').value=asset?.kind==='sequence'?'animation':'photo';if(asset?.kind==='sequence'){animationSources=asset.source_ids.slice();if(selectedJob()?.animation)setSettings({render:selectedJob().render,print:selectedJob().print,animation:selectedJob().animation});renderAnimationSources();}updateAnimationMode();switchTab(asset?.kind==='sequence'?'views':'photo')});
$('jobSelect').onchange=()=>{jobId=$('jobSelect').value;view=0;displayJob();updateLabels()};
$('loadJobSettings').onclick=()=>{const job=selectedJob();if(job){setSettings({render:{...state.defaults.render,...job.render},print:{...state.defaults.print,...job.print},animation:job.animation});if(job.animation){animationSources=state.assets[job.asset_id].source_ids.slice();$('workMode').value='animation';renderAnimationSources();updateAnimationMode();}}};
$('axis').onchange=()=>{$('camera_axis').value=value('axis')==='vertical'?'x':'y'};
$('recommendChannels').onclick=()=>applyViewSuggestion(false);
$('useViewSuggestion').onclick=()=>applyViewSuggestion(true);
$('buildDepth').onclick=safe(()=>start('depth'));
$('analyzeScene').onclick=safe(()=>start('analyze'));
$('applyAnalysis').onclick=safe(()=>{
  const job=selectedJob();if(!job?.analysis||job.asset_id!==assetId)throw Error('Bu fotoğraf için tamamlanmış analizi seç.');
  const current=settings();
  for(const [part,fields] of [['render',renderFields],['print',printFields]])for(const id of fields){if(current[part][id]!==job[part][id])throw Error('Analizden sonra ayarlar değişmiş. Güncel ayarlarla yeniden analiz et.');}
  if(JSON.stringify(current.render.reference_point)!==JSON.stringify(job.render.reference_point)||JSON.stringify(current.render.depth_strokes)!==JSON.stringify(job.render.depth_strokes)||JSON.stringify(current.render.object_regions)!==JSON.stringify(job.render.object_regions)||JSON.stringify(current.print.crosstalk_matrix)!==JSON.stringify(job.print.crosstalk_matrix)||current.print.icc_path!==job.print.icc_path)throw Error('Referans, nesne veya baskı ölçümü değişmiş. Yeniden analiz et.');
  const rec=job.analysis.recommendations;let count=0;
  for(const part of ['render','print'])for(const [id,v]of Object.entries(rec[part])){$(id).value=v;if(part==='print')invalidatePrintEvidence(id);count++;}
  updateLabels();notify(count?'Öneriler ayarlara uygulandı. Yeni görünüş/baskı işinde kullanılacak.':'Değiştirilecek ayar önerisi yok; rapordaki kontrolleri incele.');
});
for(const id of ['detail_enabled','detail_strength','surface_strength'])$(id).addEventListener('input',()=>{referencePoint=null;switchTab('depth');updateLabels()});
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>switchTab(b.dataset.tab));
$('photoFile').onchange=safe(async()=>{const file=$('photoFile').files[0];if(!file)return;const result=await api('/api/upload?kind=photo',file,true,file.name);assetLoadRevision++;assetId=result.id;sessionStorage.setItem('studioAssetId',assetId);jobId='';loadedAsset='';originalImage=null;$('emptyStage').textContent='Fotoğraf yükleniyor…';$('emptyStage').hidden=false;await refresh();switchTab('photo');$('photoFile').value=''});
$('depthFile').onchange=safe(async()=>{const file=$('depthFile').files[0];if(!assetId)throw Error('Önce fotoğraf seç.');if(file){await api(`/api/upload?kind=depth&asset=${assetId}&convention=${value('depthConvention')}`,file,true,file.name);loadedDepth='';await refresh();switchTab('depth')}});
$('iccFile').onchange=safe(async()=>{const file=$('iccFile').files[0];if(file){const r=await api('/api/upload?kind=icc',file,true,file.name);if(iccPath!==r.path)invalidatePrintEvidence('icc_path');iccPath=r.path;$('iccInfo').textContent=r.name}});
$('matrixFile').onchange=safe(async()=>{const file=$('matrixFile').files[0];if(file){const r=await api('/api/upload?kind=matrix',file,true,file.name);matrix=r.matrix;$('ne').value=matrix.length;$('matrixInfo').textContent=`${r.name} · ${matrix.length} kanal`;updateLabels()}});
$('clearMatrix').onclick=()=>{matrix=null;$('matrixInfo').textContent='Ölçüm yok: komşu kanal modeli.'};
$('clearIcc').onclick=()=>{if(iccPath||value('color_mode')!=='RGB')invalidatePrintEvidence('icc_path');iccPath=null;$('color_mode').value='RGB';$('iccInfo').textContent='Varsayılan: sRGB.'};
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
$('editMode').add(new Option('Nesne sınırı','object'));
$('startObject').onclick=()=>{if(!originalImage){notify('Önce fotoğraf seç.');return;}objectDraft=[];switchTab('photo');$('editMode').value='object';$('objectEditor').open=true;objectChanged();$('editCanvas').focus();$('editCanvas').scrollIntoView({block:'center'});};
$('finishObject').onclick=()=>{if(objectDraft.length<3){notify('En az üç sınır noktası seç.');return;}if(objectRegions.length>=32){notify('En fazla 32 nesne kullanılabilir.');return;}objectRegions.push({points:objectDraft,offset:0,relief:1});objectDraft=[];objectSelected=objectRegions.length-1;$('editMode').value='view';objectChanged();};
$('undoObjectPoint').onclick=()=>{objectDraft.pop();objectChanged();};
$('cancelObject').onclick=()=>{objectDraft=[];$('editMode').value='view';objectChanged();};
$('objectSelect').onchange=()=>{objectSelected=$('objectSelect').value===''?-1:Number($('objectSelect').value);objectChanged();};
for(const [id,key]of [['objectOffset','offset'],['objectRelief','relief']])$(id).oninput=()=>{if(objectRegions[objectSelected])objectRegions[objectSelected][key]=Number($(id).value);objectChanged();};
$('removeObject').onclick=()=>{if(objectSelected>=0)objectRegions.splice(objectSelected,1);objectSelected=objectRegions.length-1;objectChanged();};
$('clearObjects').onclick=()=>{objectRegions=[];objectDraft=[];objectSelected=-1;objectChanged();};
for(const id of ['brushValue','brushRadius'])$(id).oninput=()=>{ $('brushCursor').hidden=true;updateEditorHelp() };
$('zero_reference').addEventListener('input',()=>{referencePoint=null;drawEditor()});
function updateEditorHelp(){
  const mode=value('editMode'),editing=['photo','depth'].includes(tab),brush=mode==='brush';
  $('brushValue').disabled=!brush;$('brushRadius').disabled=!brush;
  $('brushValueLabel').textContent=Number($('brushValue').value).toFixed(2)+' · 0 uzak / 1 yakın';
  $('brushRadiusLabel').textContent='Yarıçap %'+(Number($('brushRadius').value)*100).toFixed(1);
  if(mode==='object')$('previewNote').textContent='Nesnenin çevresine sırayla tıkla. Sınırı tamamla düğmesiyle kapat.';
  $('referenceInfo').textContent=referencePoint?`İşaretli noktadan referans alındı: ${Number($('zero_reference').value).toFixed(3)}. Aynı derinlikteki bölgeler sabit düzleme yakın kalır.`:`Referans ${Number($('zero_reference').value).toFixed(3)} · kişi otomatik seçilmez. Fotoğraftan bir nokta seçebilirsin.`;
  $('editCanvas').style.cursor=mode==='view'?'default':'crosshair';
  if(!brush||!editing)$('brushCursor').hidden=true;
  if(editing&&mode!=='object')$('previewNote').textContent=!depthPixels?'Önce Hızlı önizleme düğmesiyle derinliği hesaplat; ardından referans veya fırça kullan.':mode==='pin'?'Fotoğrafın içinde sabit kalmasını istediğin derinliğe tıkla. İşaret bir örnek noktasıdır; bütün kişiyi kilitlemez. Sonucu görmek için yeniden Hızlı önizleme oluştur.':brush?'Resmin üzerinde basılı tutarak boya. Daire fırça alanıdır. 0 uzak, 1 yakın; referansa eşit değer sabit düzleme yaklaştırır. Değişimi Derinlik sekmesinde izle.':'İncele modu düzenleme yapmaz. Referans için Sabit nokta seç, boyamak için Derinlik fırçası seç.';
}
function moveBrushCursor(event){
  const cursor=$('brushCursor'),c=$('editCanvas');
  if(value('editMode')!=='brush'||!depthPixels){cursor.hidden=true;return;}
  const rect=c.getBoundingClientRect(),stage=$('stage').getBoundingClientRect(),r=Number($('brushRadius').value)*Math.max(c.width,c.height);
  cursor.style.width=(2*r*rect.width/c.width)+'px';cursor.style.height=(2*r*rect.height/c.height)+'px';cursor.style.left=(event.clientX-stage.left)+'px';cursor.style.top=(event.clientY-stage.top)+'px';cursor.hidden=false;
}

function editAt(event){
  const c=$('editCanvas'),rect=c.getBoundingClientRect();const x=Math.min(1,Math.max(0,(event.clientX-rect.left)/rect.width)),y=Math.min(1,Math.max(0,(event.clientY-rect.top)/rect.height));
  if(value('editMode')==='object'){if(objectDraft.length>=128){notify('Bir sınır en fazla 128 nokta içerebilir.');return;}objectDraft.push([x,y]);drawEditor();renderObjectControls();return;}
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
$('editCanvas').tabIndex=0;$('editCanvas').setAttribute('aria-label','Fotoğraf düzenleme alanı');
$('editCanvas').onkeydown=event=>{if(value('editMode')!=='object')return;const step=event.shiftKey?.05:.01;if(event.key.startsWith('Arrow')){event.preventDefault();const k=['ArrowLeft','ArrowRight'].includes(event.key)?0:1;objectKeyboardPoint[k]=Math.max(0,Math.min(1,objectKeyboardPoint[k]+(['ArrowLeft','ArrowUp'].includes(event.key)?-step:step)));$('objectInfo').textContent=`Nokta: %${Math.round(objectKeyboardPoint[0]*100)}, %${Math.round(objectKeyboardPoint[1]*100)} · Enter ile ekle`;return;}if(event.key==='Enter'){event.preventDefault();if(objectDraft.length<128){objectDraft.push([...objectKeyboardPoint]);objectChanged();}}if(event.key==='Escape')$('cancelObject').click();};
$('editCanvas').onpointerdown=event=>{brushActive=true;event.target.setPointerCapture(event.pointerId);editAt(event)};
$('editCanvas').onpointerleave=()=>{$('brushCursor').hidden=true};
$('editCanvas').onpointermove=event=>{moveBrushCursor(event);if(brushActive&&value('editMode')==='brush')editAt(event)};
$('editCanvas').onpointerup=()=>{brushActive=false};$('editCanvas').onpointercancel=()=>{brushActive=false};
$('shutdown').onclick=safe(async()=>{stopPlayback();clearInterval(poll);await api('/api/shutdown',{ok:true});$('progressText').textContent='Uygulama kapatıldı. Yeniden açmak için Lenticular Studio dosyasını kullan.';document.querySelectorAll('button').forEach(b=>b.disabled=true)});
const poll=setInterval(()=>refresh().catch(error=>{$('messages').textContent='Uygulama bağlantısı bekleniyor.'}),2000);
function updateAnimationMode(){
  const active=value('workMode')==='animation';$('animationSection').hidden=!active;
  document.querySelector('.left-panel section:has(#nr)').hidden=active;
  $('print').hidden=active;$('full').hidden=active;
  $('morphEditor').hidden=!active||value('animationMode')!=='morph';
  $('animationEngine').disabled=value('animationMode')!=='motion';
  $('animationHint').textContent=value('animationMode')==='flip'?'Flip, kaynak görüntüleri seçilen bekleme paylarında değiştirir. Yeni hareket ara karesi üretmez.':value('animationMode')==='morph'?'A ve B üzerinde eşleşen noktaları seç. Nt yeni şekil dönüşüm kareleri üretilir.':value('animationMode')==='dissolve'?'Bu efekt lineer ışıkta yumuşak renk geçişidir. Hareket kestirimi yapmaz.':'İki fotoğraftan yeni ara kareler üretilir. Nt zaman kareleri ile Ne baskı kanalları ayrı ayarlardır.';
  if(value('animationMode')==='morph')safe(drawMorph)();
}
function renderAnimationSources(){
  $('animationSources').replaceChildren();
  animationSources.forEach((id,index)=>{const asset=state.assets[id];if(!asset)return;const li=document.createElement('li');const img=document.createElement('img');img.src=protectedUrl(asset.photo_url);img.alt=asset.name;li.append(img,document.createTextNode(`${index+1}. ${asset.name}`));
    for(const [label,action]of [['↑',()=>{if(index){[animationSources[index-1],animationSources[index]]=[animationSources[index],animationSources[index-1]];}}],['↓',()=>{if(index<animationSources.length-1){[animationSources[index+1],animationSources[index]]=[animationSources[index],animationSources[index+1]];}}],['×',()=>animationSources.splice(index,1)]]){const b=document.createElement('button');b.type='button';b.textContent=label;b.setAttribute('aria-label',label==='×'?'Fotoğrafı diziden çıkar':label==='↑'?'Fotoğrafı yukarı taşı':'Fotoğrafı aşağı taşı');b.onclick=()=>{action();$('morphPoints').value='[]';pendingMorph=null;renderAnimationSources();updateAnimationMode();};li.append(b);}$('animationSources').append(li);
  });
  if(value('animationMode')==='morph')safe(drawMorph)();
}
async function drawMorph(){
  const revision=++morphRevision;if(animationSources.length!==2)return;
  const assets=animationSources.map(id=>state.assets[id]);const images=await Promise.all(assets.map(a=>loadImage(a.photo_url)));if(revision!==morphRevision)return;
  const points=JSON.parse($('morphPoints').value||'[]');const w=320,h=Math.max(16,Math.round(w*assets[0].size[1]/assets[0].size[0]));
  ['morphA','morphB'].forEach((id,k)=>{const c=$(id);c.width=w;c.height=h;const ctx=c.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,w,h);const image=images[k],scale=Math.min(w/image.width,h/image.height);ctx.drawImage(image,(w-scale*image.width)/2,(h-scale*image.height)/2,scale*image.width,scale*image.height);ctx.fillStyle='#d72f57';ctx.strokeStyle='#d72f57';ctx.font='14px sans-serif';points.forEach((p,i)=>{const x=p[k*2]*w,y=p[k*2+1]*h;ctx.beginPath();ctx.arc(x,y,5,0,Math.PI*2);ctx.stroke();ctx.fillText(String(i+1),x+7,y-7);});if(k===0&&pendingMorph){ctx.beginPath();ctx.arc(pendingMorph[0]*w,pendingMorph[1]*h,6,0,Math.PI*2);ctx.stroke();}});
}
async function startAnimation(stage){
  if(stage!=='animation_print'){
    if(!animationSources.length)throw Error('Önce animasyon fotoğraflarını seç.');
    const result=await api('/api/sequence',{source_ids:animationSources,name:'Animasyon · '+animationSources.map(id=>state.assets[id].name).join(' → ')});assetId=result.id;sessionStorage.setItem('studioAssetId',assetId);jobId='';await refresh();
  }else if(!selectedJob()?.frames_folder)throw Error('Tamamlanmış bir animasyon işini seç.');
  await start(stage);
}
$('workMode').onchange=updateAnimationMode;
$('animationMode').onchange=()=>{updateAnimationMode();updateLabels();};
$('animationPhotos').onchange=safe(async()=>{const files=[...$('animationPhotos').files].sort((a,b)=>a.name.localeCompare(b.name,'tr',{numeric:true}));if(files.length+animationSources.length>256)throw Error('En fazla 256 kaynak seçilebilir.');for(const file of files){const asset=await api('/api/upload?kind=photo',file,true,file.name);animationSources.push(asset.id);}await refresh();$('animationPhotos').value='';renderAnimationSources();updateAnimationMode();});
$('addAnimationSource').onclick=()=>{const id=$('animationSource').value;if(id&&animationSources.length<256){animationSources.push(id);renderAnimationSources();}};
$('generateAnimation').onclick=safe(()=>startAnimation('animation'));
$('animationToPrint').onclick=safe(()=>startAnimation('animation_full'));
$('printAnimation').onclick=safe(()=>startAnimation('animation_print'));
$('clearMorphPoints').onclick=()=>{$('morphPoints').value='[]';pendingMorph=null;safe(drawMorph)();};
for(const [id,k]of [['morphA',0],['morphB',1]])$(id).onclick=safe(async event=>{if(animationSources.length!==2)throw Error('Morph için iki fotoğraf seç.');const rect=event.target.getBoundingClientRect();const p=[(event.clientX-rect.left)/rect.width,(event.clientY-rect.top)/rect.height];if(k===0)pendingMorph=p;else{if(!pendingMorph)throw Error('Önce A fotoğrafındaki noktayı seç.');const points=JSON.parse($('morphPoints').value||'[]');points.push([...pendingMorph,...p]);$('morphPoints').value=JSON.stringify(points);pendingMorph=null;}await drawMorph();updateLabels();});
for(const id of ['animationEngine','animationNt','animationEdge','animationPingpong','animationEasing','animationFps','animationDevice','zoomStart','zoomEnd','anchorX','anchorY','flipWeights','morphPoints'])$(id).addEventListener('change',safe(async()=>{updateLabels();if(id==='morphPoints')await drawMorph();}));
safe(async()=>{await refresh();const asset=state.assets[assetId];if(asset?.kind==='sequence'){animationSources=asset.source_ids.slice();$('workMode').value='animation';if(selectedJob()?.animation)setSettings({render:selectedJob().render,print:selectedJob().print,animation:selectedJob().animation});renderAnimationSources();}updateAnimationMode();updateLabels();if(asset?.kind==='sequence')switchTab('views')})();
