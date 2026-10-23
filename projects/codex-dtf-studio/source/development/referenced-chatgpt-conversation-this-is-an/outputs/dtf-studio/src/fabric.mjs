const median=a=>{a.sort((x,y)=>x-y);return a[Math.floor(a.length/2)]||0;};
const basis=(x,y)=>[1,x,y,x*x,x*y,y*y];
function solve(a,b){
  const n=b.length,m=a.map((r,i)=>[...r,b[i]]);
  for(let k=0;k<n;k++){
    let p=k;for(let j=k+1;j<n;j++)if(Math.abs(m[j][k])>Math.abs(m[p][k]))p=j;
    [m[k],m[p]]=[m[p],m[k]];if(Math.abs(m[k][k])<1e-10)return null;
    const d=m[k][k];for(let j=k;j<=n;j++)m[k][j]/=d;
    for(let i=0;i<n;i++)if(i!==k){const d=m[i][k];for(let j=k;j<=n;j++)m[i][j]-=d*m[k][j];}
  }
  return m.map(r=>r[n]);
}
const predict=(fit,v)=>fit.map(c=>c.reduce((s,z,i)=>s+z*v[i],0));
function fit(samples,n){
  const a=Array.from({length:n},()=>Array(n).fill(0)),b=Array.from({length:3},()=>Array(n).fill(0));
  for(const p of samples)for(let i=0;i<n;i++){
    for(let j=0;j<n;j++)a[i][j]+=p.v[i]*p.v[j];
    for(let c=0;c<3;c++)b[c][i]+=p.v[i]*p.rgb[c];
  }
  for(let i=1;i<n;i++)a[i][i]+=samples.length*1e-7;
  const result=b.map(v=>solve(a,v));return result.every(Boolean)?result:null;
}
// Estimate from empty border cloth only. Select curvature on held-out samples;
// otherwise retain the simpler plane. No image detail is blurred or synthesized.
export function estimateFabric(border){
  const center=[0,1,2].map(c=>median(border.map(p=>p.rgb[c])));
  let samples=border.filter(p=>Math.hypot(...p.rgb.map((v,c)=>v-center[c]))<65);
  if(samples.length<18)samples=border;
  samples=samples.map(p=>({...p,v:basis(p.v[1],p.v[2])}));
  let plane;
  for(let pass=0;pass<3;pass++){
    plane=fit(samples,3);if(!plane)break;
    const errors=samples.map(p=>Math.hypot(...p.rgb.map((v,c)=>v-predict(plane,p.v)[c])));
    const m=median([...errors]),limit=Math.max(8,Math.min(40,m+3*1.4826*median(errors.map(e=>Math.abs(e-m)))));
    const next=samples.filter((_,i)=>errors[i]<=limit);if(next.length<18)break;samples=next;
  }
  plane=fit(samples,3)||center.map(v=>[v,0,0]);let selected=plane,curved=false;
  if(samples.length>=60){
    const train=samples.filter((_,i)=>i%5),validation=samples.filter((_,i)=>i%5===0),linear=fit(train,3),quadratic=fit(train,6);
    const error=model=>validation.reduce((s,p)=>s+p.rgb.reduce((z,v,c)=>z+(v-predict(model,p.v)[c])**2,0),0)/Math.max(1,validation.length*3);
    // Strong evidence and bounded curvature prevent border ink from creating
    // an unstable extrapolation through the unobserved centre of the print.
    if(linear&&quadratic&&error(quadratic)<error(linear)*.72&&quadratic.every(c=>c.slice(3).every(z=>Math.abs(z)<220))){selected=fit(samples,6)||plane;curved=true;}
  }
  const residuals=samples.map(p=>Math.hypot(...p.rgb.map((v,c)=>v-predict(selected,p.v)[c]))/Math.sqrt(3));
  const noise=median(residuals),at=(x,y)=>predict(selected,basis(x,y)).map(v=>Math.max(0,Math.min(255,v)));
  return {at,noise,curved};
}
