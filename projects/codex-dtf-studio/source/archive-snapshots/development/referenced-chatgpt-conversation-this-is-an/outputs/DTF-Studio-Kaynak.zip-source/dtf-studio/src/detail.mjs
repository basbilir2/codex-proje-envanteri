const clamp=(v,min=0,max=255)=>Math.max(min,Math.min(max,v));

// Non-generative finishing: sharpen the existing matte and bounded luminance.
// Transparent colour is excluded from the blur, preventing dark/white halos.
export function refineDetails(image,{amount=2.1}={}){
  const {width:w,height:h,data:source}=image,data=new Uint8ClampedArray(source),weights=[1,8,28,56,70,56,28,8,1];
  const horizontal=new Float32Array(w*h*4);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const k=(y*w+x)*4;
    for(let dx=-4;dx<=4;dx++){
      const q=(y*w+clamp(x+dx,0,w-1))*4,weight=weights[dx+4]/256,a=source[q+3]/255;
      horizontal[k+3]+=source[q+3]*weight;
      for(let c=0;c<3;c++)horizontal[k+c]+=source[q+c]*a*weight;
    }
  }
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const k=(y*w+x)*4,a=source[k+3];if(!a){data.fill(0,k,k+4);continue;}
    const blur=[0,0,0,0];
    for(let dy=-4;dy<=4;dy++){
      const q=(clamp(y+dy,0,h-1)*w+x)*4,weight=weights[dy+4]/256;
      for(let c=0;c<4;c++)blur[c]+=horizontal[q+c]*weight;
    }
    // Preserve the original support, including very faint isolated ink.
    data[k+3]=clamp(Math.round(a+clamp(amount*(a-blur[3]),-80,80)),Math.min(a,4),255);
    const luma=(r,g,b)=>.2126*r+.7152*g+.0722*b;
    const base=luma(source[k],source[k+1],source[k+2]),alpha=blur[3]/255;
    const mean=alpha>1e-5?luma(blur[0]/alpha,blur[1]/alpha,blur[2]/alpha):base;
    const delta=clamp((base-mean)*amount*.45,-12,12);
    for(let c=0;c<3;c++)data[k+c]=clamp(Math.round(source[k+c]+delta));
  }
  return {data,width:w,height:h};
}
