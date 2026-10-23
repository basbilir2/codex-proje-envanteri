import sharp from 'sharp';
import {readFile,writeFile,rename} from 'node:fs/promises';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {rectify} from './geometry.mjs';

export const TASKS=['extract-design','repair-artwork','restore-image'];
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function atomicJSON(path,value){await writeFile(path+'.pending',JSON.stringify(value,null,2));await rename(path+'.pending',path);}
export function modelSize(width,height,maxEdge=512){
  if(!Number.isInteger(maxEdge)||maxEdge<128||maxEdge>1536)throw Error('Geçersiz motor boyutu.');
  const scale=Math.min(1,maxEdge/Math.max(width,height));
  const w=Math.max(128,Math.ceil(width*scale/16)*16),h=Math.max(128,Math.ceil(height*scale/16)*16);
  const ratio=Math.min(w/width,h/height),cw=Math.max(1,Math.round(width*ratio)),ch=Math.max(1,Math.round(height*ratio));
  return {width:w,height:h,contentWidth:cw,contentHeight:ch,left:Math.floor((w-cw)/2),top:Math.floor((h-ch)/2)};
}
export async function inspectSource(bytes){
  const meta=await sharp(bytes,{limitInputPixels:16e6,animated:false}).metadata();
  if(!['png','jpeg','webp'].includes(meta.format)||Math.min(meta.width,meta.height)<32)throw Error('En az 32 × 32 piksel PNG, JPEG veya WebP yükleyin.');
  const normalized=await sharp(bytes,{limitInputPixels:16e6}).rotate().toColourspace('srgb').png().toBuffer();
  const oriented=await sharp(normalized).metadata();
  return {normalized,source:{sha256:sha(bytes),format:meta.format,width:oriented.width,height:oriented.height,hasAlpha:meta.hasAlpha===true}};
}

// The model is an injected adapter. No filter fallback can masquerade as reconstruction.
export async function recover({dir,source,normalized,task='extract-design',region=null,quad=null,engine,maxEdge=512,signal,progress=()=>{}}){
  if(!TASKS.includes(task))throw Error('Geçersiz kurtarma görevi.');
  const report={schema:1,purpose:'Design Recovery / Artwork Reconstruction',task,source,steps:[],quality:{status:'unverified',printReady:false,reviewRequired:['Yazı ve rakamlar','Logo, desen ve geometri','Yüz kimliği varsa korunması','Yüzey dokusu, kıvrım, gölge ve parlama kalıntıları','Tasarım dolguları ve gerçek renkler','İnce kenarlar ve yeterli gerçek ayrıntı']},warnings:[]};
  let lastPercent=0;
  const stage=(name,percent)=>{signal?.throwIfAborted();lastPercent=Math.max(lastPercent,percent);progress({stage:name,done:lastPercent,total:100});};
  try{
    stage('Kaynak ve tasarım alanı hazırlanıyor',5);
    if(region&&quad)throw Error('Dikdörtgen alan veya dört köşe seçin; ikisi aynı anda kullanılamaz.');
    let selected=normalized;
    if(region){
      const {left,top,width,height}=region;
      if(![left,top,width,height].every(Number.isInteger)||left<0||top<0||width<16||height<16||left+width>source.width||top+height>source.height)throw Error('Tasarım alanı görsel sınırlarında ve en az 16 × 16 piksel olmalı.');
      selected=await sharp(selected).extract({left,top,width,height}).png().toBuffer();
    }
    if(quad){const warped=await rectify(selected,quad);selected=warped.buffer;report.steps.push({stage:'perspective',method:'four-point homography',points:warped.points,width:warped.width,height:warped.height});}
    else report.steps.push({stage:'perspective',status:'not-requested'});
    const prepared=await sharp(selected).metadata();
    report.selection={region,quad,width:prepared.width,height:prepared.height};
    await writeFile(join(dir,'prepared.png'),selected);
    // Use padding rather than stretching. Strip padding after inference.
    const size=modelSize(prepared.width,prepared.height,maxEdge);
    await sharp(selected).flatten({background:'#fff'}).resize(size.contentWidth,size.contentHeight).extend({left:size.left,top:size.top,right:size.width-size.contentWidth-size.left,bottom:size.height-size.contentHeight-size.top,background:'#fff'}).png().toFile(join(dir,'input.png'));
    report.modelInput={...size,sha256:sha(await readFile(join(dir,'input.png')))};
    report.steps.push({stage:'prepare',method:'sRGB, optional geometry, fit with padding',colourLock:false});
    if(!region&&!quad&&task==='extract-design')report.warnings.push('Tasarım alanı otomatik olarak doğrulanmadı; birden fazla tasarım veya örtüşen nesne modelin yanlış alanı seçmesine yol açabilir.');
    report.warnings.push('Gizlenmiş ayrıntı ve gerçek boya rengi tek fotoğraftan kesin olarak doğrulanamaz. Üretken model yazı veya geometriyi değiştirebilir.');
    stage('Tasarım üretken motorla kurtarılıyor',15);
    const result=await engine.run({dir,task,width:size.width,height:size.height,signal,progress:p=>{
      const fraction=p.total?Math.max(0,Math.min(1,p.done/p.total)):null;
      stage(p.stage,fraction===null?15:15+fraction*65);
    }});
    signal?.throwIfAborted();
    if(result?.kind!=='generative-reconstruction')throw Error('Adaptör gerçek yeniden oluşturma sonucu bildirmedi.');
    const raw=join(dir,'reconstructed.png'),meta=await sharp(raw,{limitInputPixels:24e6}).metadata();
    if(meta.format!=='png'||meta.width!==size.width||meta.height!==size.height)throw Error('Motorun PNG çıktısı veya boyutu doğrulanamadı.');
    const stats=await sharp(raw).stats();
    if(Math.max(...stats.channels.slice(0,3).map(c=>c.stdev))<.5)throw Error('Motor boş veya tek renk çıktı üretti.');
    report.reconstruction=result;report.steps.push({stage:'reconstruct',engine:result.model,kind:result.kind});
    stage('Çıktı ve işlem raporu doğrulanıyor',90);
    const aspect=prepared.width/prepared.height;
    const width=Math.max(1,Math.round(Math.min(size.contentWidth,size.contentHeight*aspect))),height=Math.max(1,Math.round(width/aspect));
    await sharp(raw).extract({left:size.left,top:size.top,width:size.contentWidth,height:size.contentHeight}).resize(width,height).withMetadata({density:300}).png().toFile(join(dir,'enhanced.pending.png'));
    report.output={file:'enhanced.png',width,height,sha256:sha(await readFile(join(dir,'enhanced.pending.png'))),colourspace:'sRGB',alpha:false,dpi:300,nativeModelWidth:size.width,nativeModelHeight:size.height};
    report.steps.push({stage:'technical-validation',png:true,dimensions:true,nonBlank:true,semanticFidelity:'not-verified',surfaceRemoval:'not-verified'});
    report.warnings.push('300 DPI etiketi ve büyük piksel boyutu, baskı kalitesi veya gerçek ayrıntı kazanımı kanıtı değildir.');
    if(Math.max(width,height)<2048)report.warnings.push('Ana çıktı düşük çözünürlüklü model üretimidir. Yüksek çözünürlüklü dışa aktarma ayrıca büyütür; eksik ayrıntıyı doğrulamaz.');
    signal?.throwIfAborted();
    await rename(join(dir,'enhanced.pending.png'),join(dir,'enhanced.png'));
    report.status='completed';await atomicJSON(join(dir,'recovery.json'),report);stage('Kurtarma çıktısı hazır · görsel kontrol gerekli',100);
    return report;
  }catch(e){report.status=signal?.aborted?'cancelled':'failed';report.error=e.message;await atomicJSON(join(dir,'recovery.json'),report);throw e;}
}

export async function exportPNG({dir,input='enhanced',longEdge=0,dpi=300}){
  if(!['enhanced','edited','transparent'].includes(input)||!Number.isInteger(longEdge)||longEdge!==0&&(longEdge<128||longEdge>8192)||!Number.isInteger(dpi)||dpi<72||dpi>1200)throw Error('Geçersiz PNG dışa aktarma ayarı.');
  const path=join(dir,input+'.png'),meta=await sharp(path,{limitInputPixels:24e6}).metadata();
  const scale=longEdge?longEdge/Math.max(meta.width,meta.height):1,width=Math.max(1,Math.round(meta.width*scale)),height=Math.max(1,Math.round(meta.height*scale));
  if(width*height>8192*8192)throw Error('Dışa aktarma en fazla 8192 × 8192 piksel olabilir.');
  await sharp(path).resize(width,height,{kernel:'lanczos3'}).withMetadata({density:dpi}).png().toFile(join(dir,'export.pending.png'));
  const out=await sharp(join(dir,'export.pending.png')).metadata(),stats=await sharp(join(dir,'export.pending.png')).stats();
  if(out.width!==width||out.height!==height||meta.hasAlpha&&!out.hasAlpha)throw Error('PNG dışa aktarma doğrulanamadı.');
  const report={schema:1,source:input+'.png',sourceSha256:sha(await readFile(path)),output:'export.png',width,height,dpi,alpha:out.hasAlpha===true,containsTransparency:out.hasAlpha===true&&!stats.isOpaque,resampling:scale===1?'none':'Lanczos3',realDetailVerified:false,printReady:false,reviewRequired:true,sha256:sha(await readFile(join(dir,'export.pending.png')))};
  await rename(join(dir,'export.pending.png'),join(dir,'export.png'));await atomicJSON(join(dir,'export.json'),report);return report;
}
