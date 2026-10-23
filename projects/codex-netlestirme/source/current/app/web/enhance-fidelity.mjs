const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
// Keep low-frequency colour faithful to the source, accepting neural detail
// around actual edges. Reference RGBA is the original high-quality 2x resize.
export function preserveEnhancement(reference,values){
  const {width:w,height:h}=reference,src=reference.data,data=new Uint8ClampedArray(src);
  if(values.length!==w*h*3)throw new Error('AI çıktısının boyutu kaynakla eşleşmedi.');
  const luma=(k)=>.2126*src[k]+.7152*src[k+1]+.0722*src[k+2];
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const k=y*w+x,p=k*4;if(!src[p+3]){data[p]=data[p+1]=data[p+2]=0;continue;}
    const centre=luma(p);let edge=0;
    for(let i=0;i<4;i++){const q=i===0?(x?k-1:k):i===1?(x<w-1?k+1:k):i===2?(y?k-w:k):(y<h-1?k+w:k);if(src[q*4+3]>32)edge=Math.max(edge,Math.abs(luma(q*4)-centre));}
    const limit=clamp(4+edge*.85,4,32),r=values[k*3]-src[p],g=values[k*3+1]-src[p+1],b=values[k*3+2]-src[p+2];
    if(!Number.isFinite(r+g+b))throw new Error('AI geçersiz piksel üretti. Görsel değiştirilmedi.');
    const dl=.2126*r+.7152*g+.0722*b,lum=clamp(dl,-limit,limit);
    data[p]=clamp(src[p]+lum+clamp(r-dl,-6,6),0,255);data[p+1]=clamp(src[p+1]+lum+clamp(g-dl,-6,6),0,255);data[p+2]=clamp(src[p+2]+lum+clamp(b-dl,-6,6),0,255);
  }
  return {data,width:w,height:h};
}
