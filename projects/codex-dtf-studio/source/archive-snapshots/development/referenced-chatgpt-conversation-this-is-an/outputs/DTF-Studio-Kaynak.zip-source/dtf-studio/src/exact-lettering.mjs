const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
export function letteringSpec(image,selection,text,{style='serif'}={}){
  if(typeof text!=='string'||!text.trim()||text.length>80||/[\r\n\x00-\x1f]/.test(text))throw new Error('Tek satır doğru metni yazın (en fazla 80 karakter).');
  const {width:w,height:h,data}=image,x=clamp(Math.floor(selection.x),0,w-1),y=clamp(Math.floor(selection.y),0,h-1),width=clamp(Math.ceil(selection.x+selection.width),x+1,w)-x,height=clamp(Math.ceil(selection.y+selection.height),y+1,h)-y;
  if(![x,y,width,height].every(Number.isFinite)||width<12||height<8||width*height>1e6)throw new Error('Yalnız düzelteceğiniz yazının çevresini seçin.');
  const bins=new Map();let count=0,weight=0,mx=0,my=0,xx=0,xy=0,yy=0,transparent=0;
  for(let j=0;j<height;j++)for(let i=0;i<width;i++){
    const p=((y+j)*w+x+i)*4,a=data[p+3]/255;if(a<.1)transparent++;if(a<.7)continue;
    const key=[data[p]>>4,data[p+1]>>4,data[p+2]>>4].join(','),bin=bins.get(key)||{n:0,r:0,g:0,b:0};bin.n++;bin.r+=data[p];bin.g+=data[p+1];bin.b+=data[p+2];bins.set(key,bin);count++;weight+=a;mx+=i*a;my+=j*a;xx+=i*i*a;xy+=i*j*a;yy+=j*j*a;
  }
  if(!count)throw new Error('Seçili alanda yazı bulunamadı.');
  if(transparent<width*height*.08)throw new Error('Yazıyı yeniden oluşturmadan önce arka planı temizleyin.');
  const palette=[...bins.values()].sort((a,b)=>b.n-a.n),rgb=b=>[b.r,b.g,b.b].map(v=>Math.round(v/b.n)),ink=rgb(palette[0]);
  const other=palette.find(b=>b.n>count*.08&&Math.hypot(...rgb(b).map((v,i)=>v-ink[i]))>180);
  const vx=xx/weight-(mx/weight)**2,vy=yy/weight-(my/weight)**2,cov=xy/weight-mx*my/weight**2;
  const angle=width>height*1.5?clamp(.5*Math.atan2(2*cov,vx-vy),-.26,.26):0;
  return {x,y,width,height,text:text.trim(),font:style==='sans'?'Arial, sans-serif':'Times New Roman, serif',weight:style==='serif-regular'?'400':'700',ink,outline:other?rgb(other):null,angle};
}
export async function replaceExactLettering(canvas,selection,text,options={}){
  const ctx=canvas.getContext('2d'),spec=letteringSpec(ctx.getImageData(0,0,canvas.width,canvas.height),selection,text,options);
  // Only the selected rectangle changes. Text is typeset from the user's exact
  // string; no generative spelling or inference call is involved.
  const tile=document.createElement('canvas');tile.width=spec.width;tile.height=spec.height;const c=tile.getContext('2d'),pad=Math.max(1,Math.min(spec.height*.08,3));
  c.font=`${spec.weight} 100px ${spec.font}`;const m=c.measureText(spec.text),tw=Math.max(1,m.width),th=Math.max(1,m.actualBoundingBoxAscent+m.actualBoundingBoxDescent),co=Math.cos(spec.angle),si=Math.abs(Math.sin(spec.angle));
  const scale=Math.min((spec.width-2*pad)/(tw*co+th*si),(spec.height-2*pad)/(tw*si+th*co));
  c.translate(spec.width/2,spec.height/2);c.rotate(spec.angle);c.scale(scale,scale);c.textAlign='left';c.textBaseline='alphabetic';c.lineJoin='round';
  const tx=-tw/2,ty=(m.actualBoundingBoxAscent-m.actualBoundingBoxDescent)/2;
  if(spec.outline){c.strokeStyle=`rgb(${spec.outline.join(',')})`;c.lineWidth=Math.min(4,Math.max(1.5,.7/scale));c.strokeText(spec.text,tx,ty);}
  c.fillStyle=`rgb(${spec.ink.join(',')})`;c.fillText(spec.text,tx,ty);
  const out=document.createElement('canvas');out.width=canvas.width;out.height=canvas.height;const target=out.getContext('2d');target.drawImage(canvas,0,0);target.clearRect(spec.x,spec.y,spec.width,spec.height);target.drawImage(tile,spec.x,spec.y);
  return {canvas:out,spec};
}
