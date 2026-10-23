const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
// Local, non-generative deconvolution of the existing print alpha. No OCR,
// font replacement or letter invention. The untouched design remains byte-identical.
export function strengthenFineText(image,selection){
  const {width:w,height:h,data:src}=image;
  const x0=clamp(Math.floor(selection.x),0,w-1),y0=clamp(Math.floor(selection.y),0,h-1),x1=clamp(Math.ceil(selection.x+selection.width),x0+1,w),y1=clamp(Math.ceil(selection.y+selection.height),y0+1,h);
  const width=x1-x0,height=y1-y0,n=width*height;
  if(width<3||height<3)throw new Error('Yazının tamamını içine alan biraz daha geniş bir alan seçin.');
  if(n>2e6)throw new Error('Yalnız küçük yazının çevresini seçin; alan en fazla 2 megapiksel olabilir.');
  const observed=new Float32Array(n),estimate=new Float32Array(n);let soft=0,peak=0;
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const k=y*width+x,a=src[((y+y0)*w+x+x0)*4+3]/255;
    observed[k]=estimate[k]=a;peak=Math.max(peak,a);if(a>.02&&a<.96)soft++;
  }
  if(soft<3||peak<.04)throw new Error('Bu alanda güçlendirilecek yumuşak yazı kenarı yok. Önce arka planı ayırın.');
  const temp=new Float32Array(n),blurred=new Float32Array(n),ratio=new Float32Array(n),correction=new Float32Array(n),weights=[.0625,.25,.375,.25,.0625];
  const blur=(input,output)=>{
    for(let y=0;y<height;y++)for(let x=0;x<width;x++){
      let s=0;for(let d=-2;d<=2;d++)s+=input[y*width+clamp(x+d,0,width-1)]*weights[d+2];temp[y*width+x]=s;
    }
    for(let y=0;y<height;y++)for(let x=0;x<width;x++){
      let s=0;for(let d=-2;d<=2;d++)s+=temp[clamp(y+d,0,height-1)*width+x]*weights[d+2];output[y*width+x]=s;
    }
  };
  for(let iteration=0;iteration<7;iteration++){
    blur(estimate,blurred);
    for(let k=0;k<n;k++)ratio[k]=observed[k]/Math.max(.02,blurred[k]);
    blur(ratio,correction);
    for(let k=0;k<n;k++)estimate[k]=observed[k]?clamp(estimate[k]*correction[k],Math.max(1/255,observed[k]-.32),Math.min(1,observed[k]+.38)):0;
  }
  const data=new Uint8ClampedArray(src);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const k=y*width+x,p=((y+y0)*w+x+x0)*4;
    // Feather the selection boundary; support and RGB stay strictly unchanged.
    const blend=clamp(Math.min(x,y,width-1-x,height-1-y)/3,0,1);
    data[p+3]=Math.round(255*(observed[k]*(1-blend)+estimate[k]*blend));
  }
  return {data,width:w,height:h};
}
