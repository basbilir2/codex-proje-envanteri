import sharp from 'sharp';
import {PDFDocument} from 'pdf-lib';
import {layout,px} from '../src/engine.mjs';
export async function renderSheet(manifest,assets){
  const sheet=layout(manifest.designs,manifest.settings),dpi=sheet.settings.dpi;
  const width=px(sheet.width,dpi),height=px(sheet.height,dpi);
  if(width*height>120e6||width>30000||height>30000)throw new Error('Bu çıktı tek dosya sınırını aşıyor. Dizgiyi daha kısa işlere bölün veya DPI değerini düşürün.');
  if(sheet.height*72/25.4>14400)throw new Error('PDF için film uzunluğu 508 cm altında olmalı. İşi bölün.');
  if(!Array.isArray(assets)||assets.length!==manifest.designs.length)throw new Error('Görseller eksik.');
  const inputs=new Map();
  for(const a of assets){
    if(!manifest.designs.some(d=>d.id===a.id)||inputs.has(a.id)||typeof a.png!=='string'||a.png.length>36e6)throw new Error('Geçersiz görsel.');
    const buffer=Buffer.from(a.png,'base64');
    if(buffer.length>25*1024*1024)throw new Error('Görsel 25 MB sınırını aşıyor.');
    const metadata=await sharp(buffer,{limitInputPixels:50e6}).metadata();
    if(metadata.format!=='png'||metadata.pages>1)throw new Error('İşlenmiş görsel tek kare PNG olmalı.');
    inputs.set(a.id,buffer);
  }
  const cache=new Map(),composites=[];
  for(const p of sheet.placed){
    const left=px(p.x,dpi),top=px(p.y,dpi),w=Math.min(width-left,px(p.x+p.w,dpi)-left),h=Math.min(height-top,px(p.y+p.h,dpi)-top);
    const key=`${p.id}:${w}:${h}:${p.rotated}`;
    if(!cache.has(key)){
      let image=sharp(inputs.get(p.id),{limitInputPixels:50e6});
      if(p.rotated)image=image.rotate(90);
      cache.set(key,await image.resize(w,h,{fit:'fill',kernel:'lanczos3'}).ensureAlpha().png().toBuffer());
    }
    composites.push({input:cache.get(key),left:px(p.x,dpi),top:px(p.y,dpi)});
  }
  let png=await sharp({create:{width,height,channels:4,background:{r:0,g:0,b:0,alpha:0}}}).composite(composites).png().toBuffer();
  let final=sharp(png);if(sheet.settings.mirror)final=final.flop();
  png=await final.withMetadata({density:dpi}).png().toBuffer();
  const pdf=await PDFDocument.create(),page=pdf.addPage([sheet.width*72/25.4,sheet.height*72/25.4]);
  const image=await pdf.embedPng(png);page.drawImage(image,{x:0,y:0,width:page.getWidth(),height:page.getHeight()});
  pdf.setTitle('DTF Studio — Baskı dosyası');pdf.setProducer('DTF Studio');
  return {png,pdf:Buffer.from(await pdf.save()),sheet,width,height};
}
