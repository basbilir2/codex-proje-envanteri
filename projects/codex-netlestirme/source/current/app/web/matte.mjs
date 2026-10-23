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

// Refine the uncertain band using nearby confident foreground/background colours.
// Work at native resolution, never filling holes or enlarging existing alpha.
export function refineMaskEdges(pixels,matte){
  const {width:w,height:h}=pixels,n=w*h,source=pixels.data,data=new Uint8ClampedArray(matte.data);
  // Fixed-memory tiles with the full search halo keep large source images from
  // requiring two full-resolution owner maps and queues at the same time.
  if(n>1000000){
    for(let y=0;y<h;y+=512)for(let x=0;x<w;x+=512){
      const x0=Math.max(0,x-12),y0=Math.max(0,y-12),x1=Math.min(w,x+524),y1=Math.min(h,y+524),tw=x1-x0,th=y1-y0;
      const src=new Uint8ClampedArray(tw*th*4),mask=new Uint8ClampedArray(src.length);
      for(let yy=0;yy<th;yy++){const start=((y0+yy)*w+x0)*4;src.set(source.subarray(start,start+tw*4),yy*tw*4);mask.set(matte.data.subarray(start,start+tw*4),yy*tw*4);}
      const tile=refineMaskEdges({data:src,width:tw,height:th},{data:mask,width:tw,height:th});
      for(let yy=y;yy<Math.min(y+512,h);yy++){const start=((yy-y0)*tw+x-x0)*4;data.set(tile.data.subarray(start,start+Math.min(512,w-x)*4),(yy*w+x)*4);}
    }
    return {data,width:w,height:h};
  }
  function nearest(foreground){
    const owner=new Int32Array(n).fill(-1),distance=new Uint8Array(n).fill(255),queue=new Int32Array(n);let head=0,tail=0;
    for(let k=0;k<n;k++)if(source[k*4+3]===255&&(foreground?matte.data[k*4+3]>=245:matte.data[k*4+3]<=5)){owner[k]=k;distance[k]=0;queue[tail++]=k;}
    while(head<tail){const k=queue[head++],x=k%w;if(distance[k]>=12)continue;
      for(const q of [x>0?k-1:-1,x<w-1?k+1:-1,k>=w?k-w:-1,k<n-w?k+w:-1])if(q>=0&&distance[q]===255){owner[q]=owner[k];distance[q]=distance[k]+1;queue[tail++]=q;}
    }
    return owner;
  }
  const fg=nearest(true),bg=nearest(false);
  for(let k=0;k<n;k++){
    const p=k*4,a=matte.data[p+3]/255;if(a<=.02||a>=.98||source[p+3]!==255||fg[k]<0||bg[k]<0)continue;
    const f=fg[k]*4,b=bg[k]*4;let energy=0,dot=0;
    for(let c=0;c<3;c++){const d=source[f+c]-source[b+c];energy+=d*d;dot+=(source[p+c]-source[b+c])*d;}
    if(energy<2700)continue;
    const projection=clamp(dot/energy);let residual=0;
    for(let c=0;c<3;c++)residual+=(source[p+c]-source[b+c]-projection*(source[f+c]-source[b+c]))**2;
    // Reject ambiguous texture/colour matches instead of changing the artwork.
    if(residual>3*22**2||Math.abs(projection-a)>.4)continue;
    const refined=.35*a+.65*projection;data[p+3]=Math.round(refined*255);
    for(let c=0;c<3;c++){
      const unmixed=source[b+c]+(source[p+c]-source[b+c])/Math.max(.08,refined);
      data[p+c]=Math.max(0,Math.min(255,source[p+c]+Math.max(-100,Math.min(100,unmixed-source[p+c]))));
    }
  }
  for(let p=0;p<data.length;p+=4)if(!data[p+3])data[p]=data[p+1]=data[p+2]=0;
  return {data,width:w,height:h};
}

// Bounded native-pixel edge finishing for isolated single-colour print.
// Keep every existing hole and faint isolated mark; only steepen soft transitions.
export function refineInkEdges(image){
  const {width:w,height:h,data:src}=image,data=new Uint8ClampedArray(src);
  const alpha=(x,y)=>src[(Math.max(0,Math.min(h-1,y))*w+Math.max(0,Math.min(w-1,x)))*4+3];
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const p=(y*w+x)*4,a=src[p+3];if(!a||a===255)continue;
    const mean=(a*4+alpha(x-1,y)*2+alpha(x+1,y)*2+alpha(x,y-1)*2+alpha(x,y+1)*2+alpha(x-1,y-1)+alpha(x+1,y-1)+alpha(x-1,y+1)+alpha(x+1,y+1))/16;
    data[p+3]=Math.max(Math.min(a,4),Math.min(255,Math.round(a+Math.max(-32,Math.min(32,(a-mean)*.9)))));
  }
  return {data,width:w,height:h};
}
