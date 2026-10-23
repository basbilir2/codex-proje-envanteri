export const MM_PER_INCH = 25.4;
export const px = (mm, dpi) => Math.round(mm * dpi / MM_PER_INCH);
export const effectiveDpi = (pixels, cm) => pixels * 2.54 / cm;
export function finite(value, min, max, label) {
  const n = Number(value);
  if (!Number.isFinite(n) || n < min || n > max) throw new Error(`${label}: ${min}–${max} aralığında olmalı.`);
  return n;
}
export function normalizeSettings(s) {
  const out = {
    film: finite(s.film, 100, 1600, 'Film eni (mm)'),
    gap: finite(s.gap, 0, 50, 'Boşluk (mm)'),
    margin: finite(s.margin, 0, 50, 'Kenar payı (mm)'),
    dpi: finite(s.dpi, 72, 600, 'Çıktı DPI'),
    mode: s.mode === 'metres' ? 'metres' : 'quantity',
    metres: finite(s.metres ?? 1, 0.1, 20, 'Film uzunluğu (m)'),
    rotate: s.rotate === true,
    mirror: s.mirror === true,
  };
  if (![150, 300, 600].includes(out.dpi)) throw new Error('DPI 150, 300 veya 600 olmalı.');
  if (out.film <= 2*out.margin) throw new Error('Kenar payı film eninden büyük.');
  return out;
}
function intersects(a,b) { return a.x < b.x+b.w-1e-6 && a.x+a.w > b.x+1e-6 && a.y < b.y+b.h-1e-6 && a.y+a.h > b.y+1e-6; }
function contains(a,b) {return b.x>=a.x-1e-6 && b.y>=a.y-1e-6 && b.x+b.w<=a.x+a.w+1e-6 && b.y+b.h<=a.y+a.h+1e-6;}
function pack(items, width, height, rotate, gap, method) {
  let free = [{x:0,y:0,w:width+gap,h:height+gap}];
  const placed=[];
  for (const item of items) {
    let best;
    for (const rect of free) for (const rotated of rotate ? [false,true] : [false]) {
      const w=(rotated?item.h:item.w)+gap, h=(rotated?item.w:item.h)+gap;
      if(w>rect.w+1e-6 || h>rect.h+1e-6) continue;
      const score=method==='bottom' ? [rect.y+h,rect.x,Math.min(rect.w-w,rect.h-h)] : [Math.min(rect.w-w,rect.h-h),Math.max(rect.w-w,rect.h-h),rect.y];
      if(!best || score.some((v,i)=>v<best.score[i] && score.slice(0,i).every((x,j)=>x===best.score[j]))) best={x:rect.x,y:rect.y,w,h,rotated,score};
    }
    if(!best) return null;
    const next=[];
    for(const r of free) {
      if(!intersects(r,best)){next.push(r);continue;}
      if(best.x>r.x)next.push({x:r.x,y:r.y,w:best.x-r.x,h:r.h});
      if(best.x+best.w<r.x+r.w)next.push({x:best.x+best.w,y:r.y,w:r.x+r.w-best.x-best.w,h:r.h});
      if(best.y>r.y)next.push({x:r.x,y:r.y,w:r.w,h:best.y-r.y});
      if(best.y+best.h<r.y+r.h)next.push({x:r.x,y:best.y+best.h,w:r.w,h:r.y+r.h-best.y-best.h});
    }
    free=next.filter((r,i)=>r.w>1e-6&&r.h>1e-6&&!next.some((other,j)=>j!==i&&contains(other,r)&&(j<i||!contains(r,other))));
    placed.push({...item,x:best.x,y:best.y,w:best.w-gap,h:best.h-gap,rotated:best.rotated});
  }
  return placed;
}
function quantityLayout(items,s) {
  const width=s.film-2*s.margin;
  for(const i of items) if(i.w>width && (!s.rotate || i.h>width))throw new Error('Bir tasarım film enine sığmıyor. Ölçüyü veya film enini değiştirin.');
  const area=items.reduce((a,i)=>a+(i.w+s.gap)*(i.h+s.gap),0);
  const orders=[ [...items].sort((a,b)=>b.w*b.h-a.w*a.h), [...items].sort((a,b)=>Math.max(b.w,b.h)-Math.max(a.w,a.h)) ];
  let winner;
  for(const order of orders) for(const method of ['short','bottom']) {
    let low=Math.max(0,area/(width+s.gap)-s.gap), high=items.reduce((a,i)=>a+(s.rotate&&i.w<=width?Math.min(i.h,i.w):i.h)+s.gap,0);
    // A conservative shelf upper bound remains feasible when rotation is allowed.
    high=items.reduce((a,i)=>a+(i.w<=width?i.h:i.w)+s.gap,0);
    let result=pack(order,width,high,s.rotate,s.gap,method);
    if(!result)continue;
    for(let n=0;n<17;n++) {
      const mid=(low+high)/2, p=pack(order,width,mid,s.rotate,s.gap,method);
      if(p){high=mid;result=p;}else low=mid;
    }
    const used=Math.max(...result.map(i=>i.y+i.h));
    if(!winner||used<winner.used)winner={used,placed:result};
  }
  if(!winner)throw new Error('Dizgi oluşturulamadı.');
  return {height:winner.used+2*s.margin,placed:winner.placed.map(i=>({...i,x:i.x+s.margin,y:i.y+s.margin}))};
}
export function layout(designs,settings) {
  const s=normalizeSettings(settings);
  if(!Array.isArray(designs)||!designs.length||designs.length>30)throw new Error('1–30 tasarım yükleyin.');
  const items=[];
  for(const d of designs) {
    const w=finite(d.widthCm,0.1,160,'Genişlik (cm)')*10, h=finite(d.heightCm,0.1,200,'Yükseklik (cm)')*10;
    const count=finite(d.quantity,1,500,'Adet');
    if(!Number.isInteger(count))throw new Error('Adet tam sayı olmalı.');
    for(let i=0;i<count;i++)items.push({id:d.id,w,h});
  }
  if(items.length>500)throw new Error('Bir dizgide en fazla 500 parça kullanılabilir.');
  let result;
  if(s.mode==='quantity')result=quantityLayout(items,s);
  else {
    if(designs.length!==1)throw new Error('Metre modunda tek tasarım kullanın; karışık işler için adet modunu seçin.');
    const d=items[0], W=s.film-2*s.margin,H=s.metres*1000-2*s.margin;
    let best;
    for(const rotated of s.rotate?[false,true]:[false]){
      const w=rotated?d.h:d.w,h=rotated?d.w:d.h;
      const cols=Math.floor((W+s.gap)/(w+s.gap)), rows=Math.floor((H+s.gap)/(h+s.gap));
      if(!best||cols*rows>best.count)best={count:cols*rows,cols,rows,w,h,rotated};
    }
    if(!best.count)throw new Error('Tasarım seçilen film alanına sığmıyor.');
    if(best.count>500)throw new Error('Bu metre/ölçü kombinasyonu 500 parça sınırını aşıyor.');
    const placed=[];
    for(let row=0;row<best.rows;row++)for(let col=0;col<best.cols;col++)placed.push({id:d.id,x:s.margin+col*(best.w+s.gap),y:s.margin+row*(best.h+s.gap),w:best.w,h:best.h,rotated:best.rotated});
    result={height:s.metres*1000,placed};
  }
  if(result.height>20000)throw new Error('Dizgi 20 metre sınırını aşıyor.');
  const area=result.placed.reduce((a,i)=>a+i.w*i.h,0);
  return {...result,width:s.film,settings:s,count:result.placed.length,utilization:area/(s.film*result.height)*100};
}
