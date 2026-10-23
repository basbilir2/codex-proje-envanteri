const clamp=n=>Math.max(0,Math.min(1,n));
// Contract the foreground mask by one source-image pixel, after mask refinement.
export function contractAlpha1px(image){
  const {width:w,height:h}=image,source=image.data,data=new Uint8ClampedArray(source);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const k=(y*w+x)*4;let alpha=0;
    if(x>0&&y>0&&x<w-1&&y<h-1){
      alpha=255;
      for(let yy=y-1;yy<=y+1;yy++)for(let xx=x-1;xx<=x+1;xx++)alpha=Math.min(alpha,source[(yy*w+xx)*4+3]);
    }
    data[k+3]=alpha;
    if(!alpha)data[k]=data[k+1]=data[k+2]=0;
  }
  return {data,width:w,height:h};
}

export function cleanMatte(image,strength=1){
  const {width:w,height:h}=image,data=new Uint8ClampedArray(image.data),n=w*h;
  if(!strength)return {data,width:w,height:h};
  const low=6+strength*5,high=245-strength*5,seen=new Uint8Array(n),queue=new Int32Array(n);
  const maxDust=Math.min(12,Math.max(2,Math.floor(n/300000)));
  for(let start=0;start<n;start++)if(data[start*4+3]>low&&!seen[start]){
    let head=0,tail=1;queue[0]=start;seen[start]=1;
    while(head<tail){const k=queue[head++],x=k%w,y=Math.floor(k/w);for(const q of [x>0?k-1:-1,x<w-1?k+1:-1,y>0?k-w:-1,y<h-1?k+w:-1])if(q>=0&&!seen[q]&&data[q*4+3]>low){seen[q]=1;queue[tail++]=q;}}
    // Keep opaque punctuation and isolated fine ink; remove only small, faint remnants.
    let strongest=0;for(let i=0;i<tail;i++)strongest=Math.max(strongest,data[queue[i]*4+3]);
    if(tail<=maxDust&&strongest<200)for(let i=0;i<tail;i++)data[queue[i]*4+3]=0;
  }
  for(let i=3;i<data.length;i+=4){const t=clamp((data[i]-low)/(high-low));data[i]=Math.round(255*t);if(!data[i])data[i-3]=data[i-2]=data[i-1]=0;}
  return {data,width:w,height:h};
}

export function guidedAlpha(pixels,mask,guide){
  const {width:w,height:h,data}=pixels,mw=mask.width,mh=mask.height,channels=guide.channels||4;
  const out=new Uint8ClampedArray(data);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const k=(y*w+x)*4,lx=(x+.5)*mw/w-.5,ly=(y+.5)*mh/h-.5,cx=Math.max(0,Math.min(mw-1,Math.round(lx))),cy=Math.max(0,Math.min(mh-1,Math.round(ly)));
    let alpha=mask.data[cy*mw+cx];
    // Refine saturated mask boundaries too; otherwise a 512px hard edge becomes
    // a staircase at native resolution. Leave uniform interiors untouched.
    let boundary=alpha>1&&alpha<254;
    if(!boundary)for(let yy=Math.max(0,cy-1);yy<=Math.min(mh-1,cy+1);yy++)for(let xx=Math.max(0,cx-1);xx<=Math.min(mw-1,cx+1);xx++)if(mask.data[yy*mw+xx]!==alpha)boundary=true;
    if(boundary){
      let sum=0,weight=0;
      for(let yy=Math.max(0,cy-1);yy<=Math.min(mh-1,cy+1);yy++)for(let xx=Math.max(0,cx-1);xx<=Math.min(mw-1,cx+1);xx++){
        const q=(yy*mw+xx)*channels,dist=(data[k]-guide.data[q])**2+(data[k+1]-guide.data[q+1])**2+(data[k+2]-guide.data[q+2])**2;
        const a=Math.exp(-dist/(2*28*28)-((xx-lx)**2+(yy-ly)**2)/2);sum+=a*mask.data[yy*mw+xx];weight+=a;
      }
      if(weight>1e-8)alpha=sum/weight;
    }
    out[k+3]=Math.round(data[k+3]*alpha/255);
  }
  return {data:out,width:w,height:h};
}
