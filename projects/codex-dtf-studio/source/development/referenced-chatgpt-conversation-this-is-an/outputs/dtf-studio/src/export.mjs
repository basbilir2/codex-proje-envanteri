import {px} from './engine.mjs';
function crc32(bytes){let crc=0xffffffff;for(const byte of bytes){crc^=byte;for(let k=0;k<8;k++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}
export function pngDpi(buffer,dpi){
  const source=new Uint8Array(buffer),ppm=Math.round(dpi/0.0254),chunk=new Uint8Array(21),view=new DataView(chunk.buffer);
  view.setUint32(0,9);chunk.set([112,72,89,115],4);view.setUint32(8,ppm);view.setUint32(12,ppm);chunk[16]=1;view.setUint32(17,crc32(chunk.subarray(4,17)));
  const parts=[source.subarray(0,8)];let pos=8,inserted=false;
  while(pos<source.length){const n=new DataView(source.buffer,source.byteOffset+pos,4).getUint32(0),type=String.fromCharCode(...source.subarray(pos+4,pos+8));if(type==='IDAT'&&!inserted){parts.push(chunk);inserted=true;}if(type!=='pHYs')parts.push(source.subarray(pos,pos+n+12));pos+=n+12;}
  return new Blob(parts,{type:'image/png'});
}
export function planPngPages(sheet){
  const dpi=sheet.settings.dpi,W=px(sheet.width,dpi),H=px(sheet.height,dpi);
  const limit=Math.min(16384,Math.floor(80e6/W));
  if(W>16384||limit<1)return null;
  if(H<=limit)return [sheet];
  const bands=[];
  for(const p of [...sheet.placed].sort((a,b)=>a.y-b.y)){
    const start=px(p.y,dpi),end=px(p.y+p.h,dpi),last=bands.at(-1);
    if(last&&start<last.end){last.end=Math.max(last.end,end);}else bands.push({start,end});
  }
  const pages=[];let from=0;
  while(from<H){
    let to=Math.min(H,from+limit);
    const crossing=bands.find(b=>b.start<to&&b.end>to);
    if(crossing)to=crossing.start;
    // A design/overlapping band must stay whole. Use the native PDF path if it cannot.
    if(to<=from)return null;
    const offset=from*25.4/dpi,height=to===H?sheet.height-offset:(to-from)*25.4/dpi;
    const placed=sheet.placed.filter(p=>px(p.y,dpi)>=from&&px(p.y+p.h,dpi)<=to).map(p=>({...p,y:p.y-offset}));
    pages.push({...sheet,height,placed,count:placed.length});from=to;
  }
  return pages;
}

export async function buildPdf(sheet,assets){
  const {PDFDocument,PDFName,PDFNumber,degrees,pushGraphicsState,popGraphicsState,concatTransformationMatrix}=await import('pdf-lib');
  const doc=await PDFDocument.create(),unit=Math.max(1,Math.ceil(Math.max(sheet.width,sheet.height)*72/25.4/14400)),pt=mm=>mm*72/25.4/unit;
  const page=doc.addPage([pt(sheet.width),pt(sheet.height)]);
  if(unit>1)page.node.set(PDFName.of('UserUnit'),PDFNumber.of(unit));
  const images=new Map();for(const [id,bytes] of assets)images.set(id,await doc.embedPng(bytes));
  page.pushOperators(pushGraphicsState());
  if(sheet.settings.mirror)page.pushOperators(concatTransformationMatrix(-1,0,0,1,pt(sheet.width),0));
  for(const p of sheet.placed){
    const image=images.get(p.id);if(!image)throw new Error('Baskı tasarımı bulunamadı.');
    page.drawImage(image,p.rotated?{x:pt(p.x),y:pt(sheet.height-p.y),width:pt(p.h),height:pt(p.w),rotate:degrees(-90)}:{x:pt(p.x),y:pt(sheet.height-p.y-p.h),width:pt(p.w),height:pt(p.h)});
  }
  page.pushOperators(popGraphicsState());doc.setTitle('DTF Studio — Baskı dosyası');doc.setProducer('DTF Studio');
  return new Blob([await doc.save()],{type:'application/pdf'});
}

export async function zipFiles(files){
  const parts=[],central=[],encoder=new TextEncoder();let offset=0;
  for(const file of files){
    const data=new Uint8Array(await file.blob.arrayBuffer()),name=encoder.encode(file.name),crc=crc32(data);
    if(offset+data.length>512*1024*1024)throw new Error('PNG paketi 512 MB sınırına ulaştı. Aynı dizgiyi PDF olarak hazırlayın.');
    const local=new Uint8Array(30+name.length),l=new DataView(local.buffer);
    l.setUint32(0,0x04034b50,true);l.setUint16(4,20,true);l.setUint16(6,0x800,true);l.setUint32(14,crc,true);l.setUint32(18,data.length,true);l.setUint32(22,data.length,true);l.setUint16(26,name.length,true);local.set(name,30);
    const entry=new Uint8Array(46+name.length),c=new DataView(entry.buffer);
    c.setUint32(0,0x02014b50,true);c.setUint16(4,20,true);c.setUint16(6,20,true);c.setUint16(8,0x800,true);c.setUint32(16,crc,true);c.setUint32(20,data.length,true);c.setUint32(24,data.length,true);c.setUint16(28,name.length,true);c.setUint32(42,offset,true);entry.set(name,46);
    parts.push(local,data);central.push(entry);offset+=local.length+data.length;
  }
  const size=central.reduce((n,a)=>n+a.length,0),end=new Uint8Array(22),v=new DataView(end.buffer);
  v.setUint32(0,0x06054b50,true);v.setUint16(8,files.length,true);v.setUint16(10,files.length,true);v.setUint32(12,size,true);v.setUint32(16,offset,true);
  return new Blob([...parts,...central,end],{type:'application/zip'});
}

async function renderPng(sheet,designs,progress){
  const dpi=sheet.settings.dpi,width=px(sheet.width,dpi),height=px(sheet.height,dpi);
  const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;
  const ctx=canvas.getContext('2d');if(!ctx)throw new Error('Baskı belleği ayrılamadı. Daha kısa bir film hazırlayın.');
  if(sheet.settings.mirror){ctx.translate(width,0);ctx.scale(-1,1);}
  ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';
  for(let i=0;i<sheet.placed.length;i++){
    const p=sheet.placed[i],d=designs.find(d=>d.id===p.id);
    const x=px(p.x,dpi),y=px(p.y,dpi),w=px(p.x+p.w,dpi)-x,h=px(p.y+p.h,dpi)-y;
    ctx.save();ctx.translate(x,y);if(p.rotated){ctx.translate(w,0);ctx.rotate(Math.PI/2);ctx.drawImage(d.canvas,0,0,h,w);}else ctx.drawImage(d.canvas,0,0,w,h);ctx.restore();
    if(i%25===0){progress(`Baskı dosyası işleniyor: ${i+1}/${sheet.count}`);await new Promise(r=>setTimeout(r,0));}
  }
  progress('Dosya kodlanıyor…');
  const png=await new Promise(r=>canvas.toBlob(r,'image/png'));canvas.width=canvas.height=1;
  if(!png)throw new Error('PNG oluşturulamadı. Daha kısa bir film deneyin.');
  const bytes=await png.arrayBuffer();
  return pngDpi(bytes,dpi);
}

export async function exportInBrowser(sheet,designs,format,progress=()=>{}){
  const pages=format==='png'?planPngPages(sheet):null;
  if(format==='pdf'||!pages){
    progress('Tasarımlar gerçek ölçülü PDF’ye yerleştiriliyor…');
    const used=new Set(sheet.placed.map(p=>p.id)),assets=new Map();
    for(const d of designs)if(used.has(d.id)){const png=await new Promise(r=>d.canvas.toBlob(r,'image/png'));if(!png)throw new Error('Tasarım kodlanamadı.');assets.set(d.id,new Uint8Array(await png.arrayBuffer()));}
    return {blob:await buildPdf(sheet,assets),extension:'pdf',pages:1,note:format==='png'?'Bu yerleşim PNG dosyalarına tasarımlar kesilmeden bölünemedi. Aynı ölçü ve dizgiyle PDF hazırlandı.':'Gerçek ölçülü PDF hazır. Tasarımlar kesilmedi.'};
  }
  if(pages.length===1)return {blob:await renderPng(sheet,designs,progress),extension:'png',pages:1,note:'Şeffaf PNG hazır.'};
  const files=[];for(let i=0;i<pages.length;i++){progress(`PNG parçası hazırlanıyor: ${i+1}/${pages.length}`);files.push({name:`DTF-${String(i+1).padStart(3,'0')}-${sheet.width/10}cm-${sheet.settings.dpi}dpi.png`,blob:await renderPng(pages[i],designs,s=>progress(`Parça ${i+1}/${pages.length} · ${s}`))});await new Promise(r=>setTimeout(r,0));}
  files.push({name:'OKU.txt',blob:new Blob([`DTF Studio\n${pages.length} PNG parçası, ${sheet.count} tasarım, ${sheet.width/10} cm film eni, ${sheet.settings.dpi} DPI.\nDosyaları numara sırasıyla %100 ölçekte basın. Sayfaya sığdırmayı kapatın. Tasarımlar kesilmedi; kaynak dizgi sırası ve ölçüleri korundu.\nParçalar arasında ek boşluk uygulamayın.\n`],{type:'text/plain'})});
  return {blob:await zipFiles(files),extension:'zip',pages:pages.length,note:`${pages.length} şeffaf PNG parçası ZIP içinde hazır. DPI ve tasarım ölçüleri korundu.`};
}
