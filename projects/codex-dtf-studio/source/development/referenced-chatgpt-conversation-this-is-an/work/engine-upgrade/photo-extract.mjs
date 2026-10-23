import {cleanMatte,contractAlpha1px} from './matte.mjs';
// Browser-local print isolation. Detection proposes a region; the user confirms it.
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const median=a=>{a.sort((x,y)=>x-y);return a[Math.floor(a.length/2)]||0;};
const skin=(r,g,b)=>r>g*1.12&&r>b*1.18&&r-g>12;

export function detectPrint({data,width:w,height:h}){
  const n=w*h,mask=new Uint8Array(n),radius=Math.max(5,Math.round(w*.025));
  const sums=[0,1,2].map(()=>new Float64Array((w+1)*(h+1)));
  for(let y=1;y<=h;y++){let row=[0,0,0];for(let x=1;x<=w;x++){const p=((y-1)*w+x-1)*4,k=y*(w+1)+x;for(let c=0;c<3;c++){row[c]+=data[p+c];sums[c][k]=sums[c][k-w-1]+row[c];}}}
  for(let y=radius;y<h-radius;y++)for(let x=radius;x<w-radius;x++){
    const p=(y*w+x)*4,r=data[p],g=data[p+1],b=data[p+2];
    if(data[p+3]<200||skin(r,g,b))continue;
    const x0=x-radius,y0=y-radius,x1=x+radius+1,y1=y+radius+1,area=(x1-x0)*(y1-y0);
    const mean=sums.map(s=>(s[y1*(w+1)+x1]-s[y0*(w+1)+x1]-s[y1*(w+1)+x0]+s[y0*(w+1)+x0])/area);
    const delta=Math.hypot(r-mean[0],g-mean[1],b-mean[2]);
    // Prefer bright ink over a locally smooth garment; broad silhouettes do not qualify.
    const lift=(r+g+b-mean[0]-mean[1]-mean[2])/3;
    if(delta>37&&lift>13)mask[y*w+x]=1;
  }
  // Group nearby strokes without joining distant subjects.
  const grow=Math.max(2,Math.round(w*.012)),dilated=new Uint8Array(n);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(mask[y*w+x])for(let yy=Math.max(0,y-grow);yy<=Math.min(h-1,y+grow);yy++)for(let xx=Math.max(0,x-grow);xx<=Math.min(w-1,x+grow);xx++)dilated[yy*w+xx]=1;
  const seen=new Uint8Array(n),queue=new Int32Array(n),candidates=[];
  for(let start=0;start<n;start++)if(dilated[start]&&!seen[start]){
    let head=0,tail=1,minX=w,minY=h,maxX=0,maxY=0,ink=0,colour=0;queue[0]=start;seen[start]=1;
    while(head<tail){const k=queue[head++],x=k%w,y=Math.floor(k/w);minX=Math.min(x,minX);maxX=Math.max(x,maxX);minY=Math.min(y,minY);maxY=Math.max(y,maxY);if(mask[k]){ink++;const p=k*4;colour+=Math.max(data[p],data[p+1],data[p+2])-Math.min(data[p],data[p+1],data[p+2]);}for(const next of [x>0?k-1:-1,x<w-1?k+1:-1,y>0?k-w:-1,y<h-1?k+w:-1])if(next>=0&&dilated[next]&&!seen[next]){seen[next]=1;queue[tail++]=next;}}
    const bw=maxX-minX+1,bh=maxY-minY+1,area=bw*bh,density=ink/area;
    if(bw<w*.06||bh<h*.018||bw>w*.82||bh>h*.45||area>n*.27||ink<18||density<.04)continue;
    const cx=(minX+maxX)/2/w,cy=(minY+maxY)/2/h;
    if(cx<.1||cx>.9||cy<.12||cy>.88||minX<w*.025||maxX>w*.975||maxY>h*.975)continue;
    const score=ink*(1+colour/Math.max(1,ink)/65)*(bw/bh>.65?1:.35)*(cy>.2?1:.6);
    candidates.push({x:minX,y:minY,width:bw,height:bh,score,density});
  }
  candidates.sort((a,b)=>b.score-a.score);
  const best=candidates[0];if(!best)return {region:null,confidence:'low',candidates:[]};
  const pad=Math.max(5,Math.round(Math.min(best.width,best.height)*.15));
  const x=clamp(best.x-pad,0,w-1),y=clamp(best.y-pad,0,h-1);
  return {region:{x,y,width:Math.min(w-x,best.width+2*pad),height:Math.min(h-y,best.height+2*pad)},confidence:candidates[1]&&best.score<candidates[1].score*1.5?'low':'candidate',candidates:candidates.slice(0,4)};
}

function solve3(a,b){
  const m=a.map((r,i)=>[...r,b[i]]);
  for(let k=0;k<3;k++){let p=k;for(let j=k+1;j<3;j++)if(Math.abs(m[j][k])>Math.abs(m[p][k]))p=j;[m[k],m[p]]=[m[p],m[k]];if(Math.abs(m[k][k])<1e-9)return [b[0]/Math.max(1,a[0][0]),0,0];const v=m[k][k];for(let j=k;j<4;j++)m[k][j]/=v;for(let i=0;i<3;i++)if(i!==k){const z=m[i][k];for(let j=k;j<4;j++)m[i][j]-=z*m[k][j];}}
  return m.map(r=>r[3]);
}

export function isolatePrint({data,width:w,height:h},region,tolerance=28,{contract=true,inkMode='auto'}={}){
  const x0=clamp(Math.floor(region.x),0,w-1),y0=clamp(Math.floor(region.y),0,h-1),cw=clamp(Math.ceil(region.width),1,w-x0),ch=clamp(Math.ceil(region.height),1,h-y0);
  const border=[],step=Math.max(1,Math.floor(Math.min(cw,ch)/90)),edge=Math.max(2,Math.round(Math.min(cw,ch)*.07));
  for(let y=0;y<ch;y+=step)for(let x=0;x<cw;x+=step)if(x<edge||y<edge||x>=cw-edge||y>=ch-edge){const k=((y+y0)*w+x+x0)*4;if(data[k+3]>200)border.push({v:[1,x/cw-.5,y/ch-.5],rgb:[data[k],data[k+1],data[k+2]]});}
  if(border.length<9)throw new Error('Kumaş zemini ölçülemedi. Baskının çevresinde biraz boş kumaş bırakın.');
  const mid=[0,1,2].map(c=>median(border.map(p=>p.rgb[c])));
  // Reject border contamination (ink, skin and seams), then fit the local illumination.
  let samples=border.filter(p=>Math.hypot(...p.rgb.map((v,c)=>v-mid[c]))<55);
  if(samples.length<9)samples=border;
  let planes;
  for(let pass=0;pass<3;pass++){
    const a=Array.from({length:3},()=>[0,0,0]),b=Array.from({length:3},()=>[0,0,0]);
    for(const p of samples)for(let i=0;i<3;i++){for(let j=0;j<3;j++)a[i][j]+=p.v[i]*p.v[j];for(let c=0;c<3;c++)b[c][i]+=p.v[i]*p.rgb[c];}
    planes=b.map(v=>solve3(a,v));
    const next=samples.filter(p=>Math.hypot(...p.rgb.map((v,c)=>v-planes[c].reduce((s,q,i)=>s+q*p.v[i],0)))<32);
    if(next.length<9)break;samples=next;
  }
  // For light single-colour ink, solve I = alpha*ink + (1-alpha)*fabric.
  // A contrast threshold alone turns anti-aliased white outlines into fabric-coloured fringes.
  const bright=[],sampleStep=Math.max(1,Math.ceil(Math.sqrt(cw*ch/60000)));let neutral=0;
  for(let y=0;y<ch;y+=sampleStep)for(let x=0;x<cw;x+=sampleStep){
    const p=((y+y0)*w+x+x0)*4,v=[1,x/cw-.5,y/ch-.5],bg=planes.map(c=>c.reduce((s,z,i)=>s+z*v[i],0)),rgb=[data[p],data[p+1],data[p+2]],lift=rgb.reduce((s,z,c)=>s+z-bg[c],0)/3;
    if(lift>40&&data[p+3]>200){bright.push(rgb);if(Math.max(...rgb)-Math.min(...rgb)<55)neutral++;}
  }
  const light=inkMode==='light'||(inkMode==='auto'&&bright.length>=20&&neutral/bright.length>.94);
  const ordered=bright.sort((a,b)=>b.reduce((s,v)=>s+v,0)-a.reduce((s,v)=>s+v,0)),top=ordered.slice(0,Math.max(3,Math.ceil(ordered.length*.06)));
  const ink=[0,1,2].map(c=>top.length?median(top.map(v=>v[c])):240);
  let output=new Uint8ClampedArray(cw*ch*4);const low=clamp(Number(tolerance)||28,8,100),high=low+23;let count=0,minX=cw,minY=ch,maxX=-1,maxY=-1;
  for(let y=0;y<ch;y++)for(let x=0;x<cw;x++){
    const p=((y+y0)*w+x+x0)*4,q=(y*cw+x)*4,v=[1,x/cw-.5,y/ch-.5],bg=planes.map(c=>clamp(c.reduce((s,z,i)=>s+z*v[i],0),0,255)),dist=Math.hypot(data[p]-bg[0],data[p+1]-bg[1],data[p+2]-bg[2]);
    let a;
    if(light){
      const direction=ink.map((z,c)=>z-bg[c]),energy=direction.reduce((s,z)=>s+z*z,0),projection=direction.reduce((s,z,c)=>s+z*(data[p+c]-bg[c]),0)/Math.max(1,energy),floor=(low*.22)/Math.max(20,Math.sqrt(energy/3));
      a=clamp((projection-floor)/(1-floor),0,1);
      const residual=Math.hypot(...direction.map((z,c)=>data[p+c]-bg[c]-projection*z));
      if(residual>30)a*=clamp(1-(residual-30)/45,0,1);
    }else{a=clamp((dist-low)/(high-low),0,1);a=a*a*(3-2*a);}
    a*=data[p+3]/255;
    if(a>.08){count++;minX=Math.min(x,minX);maxX=Math.max(x,maxX);minY=Math.min(y,minY);maxY=Math.max(y,maxY);}
    for(let c=0;c<3;c++)output[q+c]=a>0?(light?ink[c]:clamp(Math.round(bg[c]+(data[p+c]-bg[c])/Math.max(.2,a)),0,255)):0;
    output[q+3]=Math.round(a*255);
  }
  if(light){
    // Keep soft edge pixels close to real ink, not a translucent sheet of fabric
    // inside letters. Each detached dot/small character may seed its own edge.
    const distance=new Uint8Array(cw*ch).fill(255),queue=new Int32Array(cw*ch);let head=0,tail=0,peak=0;
    for(let k=0;k<cw*ch;k++)peak=Math.max(peak,output[k*4+3]);
    const seed=Math.min(76,peak*.6);
    for(let k=0;k<cw*ch;k++)if(output[k*4+3]>=seed){distance[k]=0;queue[tail++]=k;}
    while(head<tail){const k=queue[head++],x=k%cw,y=Math.floor(k/cw);if(distance[k]>=3)continue;
      for(let yy=Math.max(0,y-1);yy<=Math.min(ch-1,y+1);yy++)for(let xx=Math.max(0,x-1);xx<=Math.min(cw-1,x+1);xx++){const q=yy*cw+xx;if(distance[q]===255&&output[q*4+3]>5){distance[q]=distance[k]+1;queue[tail++]=q;}}
    }
    for(let k=0;k<cw*ch;k++)if(distance[k]===255)output.fill(0,k*4,k*4+4);
  }
  const cleaned=light?{data:output,width:cw,height:ch}:cleanMatte({data:output,width:cw,height:ch},1);
  output=(contract?contractAlpha1px(cleaned):cleaned).data;
  if(light&&contract){
    // Do not erase an opaque stroke or punctuation narrower than the contraction.
    const alpha=(x,y)=>x<0||y<0||x>=cw||y>=ch?0:cleaned.data[(y*cw+x)*4+3];
    for(let y=1;y<ch-1;y++)for(let x=1;x<cw-1;x++){
      const q=(y*cw+x)*4,a=cleaned.data[q+3];
      if(a>100&&output[q+3]<a&&((alpha(x-1,y)<a*.55&&alpha(x+1,y)<a*.55)||(alpha(x,y-1)<a*.55&&alpha(x,y+1)<a*.55)))output.set(cleaned.data.subarray(q,q+4),q);
    }
  }
  count=0;minX=cw;minY=ch;maxX=maxY=-1;
  for(let y=0;y<ch;y++)for(let x=0;x<cw;x++)if(output[(y*cw+x)*4+3]>20){count++;minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);}
  if(!count)throw new Error('Tasarım ayrılamadı. Alanı veya zemin temizleme seviyesini değiştirin.');
  return {data:output,width:cw,height:ch,method:light?'light-ink':'colour',bounds:{x:minX,y:minY,width:maxX-minX+1,height:maxY-minY+1},coverage:count/(cw*ch),source:{x:x0,y:y0,width:cw,height:ch}};
}
