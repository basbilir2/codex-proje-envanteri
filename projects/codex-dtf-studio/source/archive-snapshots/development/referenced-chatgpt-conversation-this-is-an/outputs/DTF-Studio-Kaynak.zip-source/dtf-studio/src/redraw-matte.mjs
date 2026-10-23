const clamp=v=>Math.max(0,Math.min(1,v));
const median=values=>{values.sort((a,b)=>a-b);return values[Math.floor(values.length/2)];};
// Remove only the deliberately generated magenta backdrop, undoing its colour
// contribution at antialiased edges. This is separate from photo/fabric matting.
export function removeRedrawBackdrop({data:src,width:w,height:h},{contract=false}={}){
  const samples=[[],[],[]],n=w*h;
  for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(x<3||y<3||x>=w-3||y>=h-3){const p=(y*w+x)*4;if(src[p]>180&&src[p+1]<80&&src[p+2]>90)for(let c=0;c<3;c++)samples[c].push(src[p+c]);}
  if(samples[0].length<12)throw new Error('AI fon rengi güvenilir bulunamadı. Genel AI arka plan kaldırmayı kullanın.');
  const bg=samples.map(median),excess=Math.min(bg[0],bg[2])-bg[1];
  if(excess<70)throw new Error('AI fon rengi ayırt edilemiyor.');
  const data=new Uint8ClampedArray(src.length);
  for(let k=0;k<n;k++){
    const p=k*4;let a=clamp(1-(Math.min(src[p],src[p+2])-src[p+1])/excess);if(a<.12)a=0;else if(a>.98)a=1;
    data[p+3]=Math.round(a*src[p+3]);
    if(a)for(let c=0;c<3;c++)data[p+c]=Math.max(0,Math.min(255,Math.round((src[p+c]-(1-a)*bg[c])/a)));
  }
  // VAE backdrop fluctuations produce a faint veil. Keep soft coverage only
  // within two pixels of confident ink; isolated lettering dots remain seeds.
  const distance=new Uint8Array(n).fill(255),front=new Int32Array(n);let head=0,tail=0;
  for(let k=0;k<n;k++)if(data[k*4+3]>=180){distance[k]=0;front[tail++]=k;}
  while(head<tail){const k=front[head++],x=k%w,y=Math.floor(k/w);if(distance[k]>=2)continue;
    for(const q of [x?k-1:-1,x<w-1?k+1:-1,y?k-w:-1,y<h-1?k+w:-1])if(q>=0&&distance[q]===255){distance[q]=distance[k]+1;front[tail++]=q;}
  }
  const unmixed=new Uint8ClampedArray(data);
  for(let k=0;k<n;k++){
    const p=k*4;if(distance[k]===255){data.fill(0,p,p+4);continue;}
    if(!data[p+3]||data[p+3]>=245)continue;
    // Estimate edge colour from the nearest opaque ink, never the keyed pink.
    const x=k%w,y=Math.floor(k/w);let best=-1,d=100;
    for(let yy=Math.max(0,y-3);yy<=Math.min(h-1,y+3);yy++)for(let xx=Math.max(0,x-3);xx<=Math.min(w-1,x+3);xx++){
      const q=yy*w+xx,dd=(xx-x)**2+(yy-y)**2;if(unmixed[q*4+3]>=245&&dd<d){best=q;d=dd;}
    }
    if(best>=0)for(let c=0;c<3;c++)data[p+c]=unmixed[best*4+c];
  }
  // Generation/VAE border specks cannot belong to the centred artwork; discard
  // only small connected remnants that touch an image edge, never internal dots.
  const seen=new Uint8Array(n),queue=new Int32Array(n);
  for(let start=0;start<n;start++)if(data[start*4+3]>4&&!seen[start]){
    let head=0,tail=1,edge=false;queue[0]=start;seen[start]=1;
    while(head<tail){const k=queue[head++],x=k%w,y=Math.floor(k/w);if(!x||!y||x===w-1||y===h-1)edge=true;
      for(const q of [x?k-1:-1,x<w-1?k+1:-1,y?k-w:-1,y<h-1?k+w:-1])if(q>=0&&!seen[q]&&data[q*4+3]>4){seen[q]=1;queue[tail++]=q;}
    }
    if(edge&&tail<n*.015)for(let i=0;i<tail;i++)data.fill(0,queue[i]*4,queue[i]*4+4);
  }
  if(contract){const old=new Uint8ClampedArray(data);for(let y=1;y<h-1;y++)for(let x=1;x<w-1;x++){const p=(y*w+x)*4;let a=old[p+3];for(let yy=y-1;yy<=y+1;yy++)for(let xx=x-1;xx<=x+1;xx++)a=Math.min(a,old[(yy*w+xx)*4+3]);data[p+3]=a;if(!a)data.fill(0,p,p+4);}}
  return {data,width:w,height:h,background:bg};
}
