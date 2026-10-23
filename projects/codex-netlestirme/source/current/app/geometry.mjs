import sharp from 'sharp';

// Coordinates refer to the EXIF-oriented original, not a resized preview.
export function validateQuad(points,width,height){
  if(!Array.isArray(points)||points.length!==4||points.some(p=>!p||!Number.isFinite(p.x)||!Number.isFinite(p.y)||p.x<0||p.y<0||p.x>width-1||p.y>height-1))throw Error('Dört köşe görsel sınırlarında olmalı.');
  let sign=0,area=0;
  for(let i=0;i<4;i++){
    const a=points[i],b=points[(i+1)%4],c=points[(i+2)%4];
    const cross=(b.x-a.x)*(c.y-b.y)-(b.y-a.y)*(c.x-b.x);
    if(Math.abs(cross)<1||sign&&Math.sign(cross)!==sign)throw Error('Köşeleri kesişmeden sırayla seçin: sol üst, sağ üst, sağ alt, sol alt.');
    sign=Math.sign(cross);area+=a.x*b.y-b.x*a.y;
  }
  if(sign<0||area/2<256)throw Error('Köşe sırası veya alan boyutu geçersiz.');
  return points.map(p=>({x:p.x,y:p.y}));
}
function solve(rows){
  const n=rows.length;
  for(let col=0;col<n;col++){
    let pivot=col;for(let r=col+1;r<n;r++)if(Math.abs(rows[r][col])>Math.abs(rows[pivot][col]))pivot=r;
    [rows[col],rows[pivot]]=[rows[pivot],rows[col]];
    const v=rows[col][col];if(Math.abs(v)<1e-10)throw Error('Perspektif çözülemedi.');
    for(let j=col;j<=n;j++)rows[col][j]/=v;
    for(let r=0;r<n;r++)if(r!==col){const f=rows[r][col];for(let j=col;j<=n;j++)rows[r][j]-=f*rows[col][j];}
  }
  return rows.map(r=>r[n]);
}
export async function rectify(image,points){
  const {data,info}=await sharp(image).flatten({background:'#fff'}).removeAlpha().raw().toBuffer({resolveWithObject:true});
  const p=validateQuad(points,info.width,info.height),dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
  const width=Math.max(16,Math.round(Math.max(dist(p[0],p[1]),dist(p[3],p[2])))),height=Math.max(16,Math.round(Math.max(dist(p[0],p[3]),dist(p[1],p[2]))));
  if(width*height>16e6)throw Error('Düzeltilen perspektif en fazla 16 megapiksel olabilir.');
  const dst=[[0,0],[width-1,0],[width-1,height-1],[0,height-1]],rows=[];
  for(let i=0;i<4;i++){const [x,y]=dst[i],{x:u,y:v}=p[i];rows.push([x,y,1,0,0,0,-u*x,-u*y,u],[0,0,0,x,y,1,-v*x,-v*y,v]);}
  const h=solve(rows),out=Buffer.alloc(width*height*3,255);
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const d=h[6]*x+h[7]*y+1;
    const u=(h[0]*x+h[1]*y+h[2])/d,v=(h[3]*x+h[4]*y+h[5])/d;
    if(!Number.isFinite(u+v)||u<-.001||v<-.001||u>info.width-1+.001||v>info.height-1+.001)continue;
    const sx=Math.max(0,Math.min(info.width-1,u)),sy=Math.max(0,Math.min(info.height-1,v));
    const x0=Math.floor(sx),y0=Math.floor(sy),x1=Math.min(x0+1,info.width-1),y1=Math.min(y0+1,info.height-1),fx=sx-x0,fy=sy-y0;
    for(let c=0;c<3;c++)out[(y*width+x)*3+c]=Math.round((1-fy)*((1-fx)*data[(y0*info.width+x0)*3+c]+fx*data[(y0*info.width+x1)*3+c])+fy*((1-fx)*data[(y1*info.width+x0)*3+c]+fx*data[(y1*info.width+x1)*3+c]));
  }
  return {buffer:await sharp(out,{raw:{width,height,channels:3}}).png().toBuffer(),width,height,points:p};
}
