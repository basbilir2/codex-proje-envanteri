import {cleanMatte,contractAlpha1px} from './matte.mjs';
export function cloneCanvas(source,width=source.width,height=source.height){const c=document.createElement('canvas');c.width=width;c.height=height;c.getContext('2d').drawImage(source,0,0,width,height);return c;}
const point=(e,c)=>{const r=c.getBoundingClientRect();return{x:Math.max(0,Math.min(c.width,(e.clientX-r.left)*c.width/r.width)),y:Math.max(0,Math.min(c.height,(e.clientY-r.top)*c.height/r.height))};};
export class AreaSelection{
  constructor(canvas,change){this.canvas=canvas;this.change=change;this.region=null;this.mode='rectangle';this.points=[];
    canvas.onpointerdown=e=>{if(this.locked||!this.image)return;e.preventDefault();
      if(this.mode==='quad'){
        if(this.points.length===4)this.points=[];
        const p=point(e,canvas);p.x=Math.min(canvas.width-1,p.x);p.y=Math.min(canvas.height-1,p.y);this.points.push(p);this.quad=this.points.length===4?this.points.map(p=>({...p})):null;
        const xs=this.points.map(p=>p.x),ys=this.points.map(p=>p.y);
        this.region=this.quad?{left:Math.floor(Math.min(...xs)),top:Math.floor(Math.min(...ys)),width:Math.ceil(Math.max(...xs))-Math.floor(Math.min(...xs))+1,height:Math.ceil(Math.max(...ys))-Math.floor(Math.min(...ys))+1}:null;
        this.draw();this.change(this.region);return;
      }
      this.start=point(e,canvas);canvas.setPointerCapture(e.pointerId);};
    canvas.onpointermove=e=>{if(this.start){this.select(this.start,point(e,canvas));this.draw();}};
    canvas.onpointerup=e=>{if(!this.start)return;this.select(this.start,point(e,canvas));this.start=null;if(this.region.width<16||this.region.height<16)this.region=null;this.draw();change(this.region);};
    canvas.onpointercancel=()=>{this.start=null;this.draw();};
  }
  load(image){this.image=image;this.canvas.width=image.naturalWidth||image.width;this.canvas.height=image.naturalHeight||image.height;this.all();}
  all(){this.region=null;this.quad=null;this.points=[];this.draw();this.change(null);}
  setMode(mode){this.mode=mode;this.all();}
  select(a,b){const left=Math.floor(Math.min(a.x,b.x)),top=Math.floor(Math.min(a.y,b.y));this.region={left,top,width:Math.ceil(Math.max(a.x,b.x))-left,height:Math.ceil(Math.max(a.y,b.y))-top};}
  draw(){if(!this.image)return;const c=this.canvas,ctx=c.getContext('2d'),host=c.parentElement,fit=Math.min((host.clientWidth-16)/c.width,(host.clientHeight-16)/c.height);c.style.width=c.width*fit+'px';c.style.height=c.height*fit+'px';ctx.clearRect(0,0,c.width,c.height);ctx.drawImage(this.image,0,0);const s=c.width/Math.max(1,c.getBoundingClientRect().width);
    if(this.mode==='quad'&&this.points.length){ctx.save();ctx.strokeStyle='#20bd91';ctx.fillStyle='#17584b';ctx.lineWidth=2*s;ctx.font=`${16*s}px system-ui`;ctx.beginPath();this.points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));if(this.quad)ctx.closePath();ctx.stroke();this.points.forEach((p,i)=>{ctx.beginPath();ctx.arc(p.x,p.y,5*s,0,Math.PI*2);ctx.fill();ctx.fillText(String(i+1),p.x+8*s,p.y+18*s);});ctx.restore();return;}
    if(!this.region)return;const r=this.region;ctx.save();ctx.fillStyle='#0007';ctx.beginPath();ctx.rect(0,0,c.width,c.height);ctx.rect(r.left,r.top,r.width,r.height);ctx.fill('evenodd');ctx.strokeStyle='#20bd91';ctx.lineWidth=2*s;ctx.setLineDash([6*s,4*s]);ctx.strokeRect(r.left,r.top,r.width,r.height);ctx.restore();}
}
export class ResultEditor{
  constructor(canvas,change){this.canvas=canvas;this.change=change;this.ready=false;this.history=[];this.tool='view';this.size=18;this.zoom=1;
    canvas.onpointerdown=e=>{if(!this.ready||this.locked||this.tool==='view')return;e.preventDefault();this.remember();this.stroke=point(e,canvas);canvas.setPointerCapture(e.pointerId);this.brush(this.stroke,this.stroke);};
    canvas.onpointermove=e=>{if(!this.stroke)return;const p=point(e,canvas);this.brush(this.stroke,p);this.stroke=p;};
    const end=()=>{if(this.stroke){this.stroke=null;change();}};canvas.onpointerup=end;canvas.onpointercancel=end;
  }
  remember(){if(!this.ready)return;this.history.push({canvas:cloneCanvas(this.canvas),recovery:cloneCanvas(this.recovery)});const bytes=()=>this.history.reduce((n,s)=>n+(s.canvas.width*s.canvas.height+s.recovery.width*s.recovery.height)*4,0);while(this.history.length>5||(this.history.length>1&&bytes()>64e6))this.history.shift();}
  set(source,{reset=false,recovery}={}){const copy=cloneCanvas(source);if(reset)this.history=[];else this.remember();this.canvas.width=copy.width;this.canvas.height=copy.height;this.canvas.getContext('2d').drawImage(copy,0,0);this.recovery=recovery?cloneCanvas(recovery,copy.width,copy.height):cloneCanvas(copy);this.ready=true;this.fit();}
  fit(){if(!this.ready)return;const s=Math.min(1,Math.max(100,this.canvas.parentElement.clientWidth-20)/this.canvas.width,480/this.canvas.height)*this.zoom;this.canvas.style.width=this.canvas.width*s+'px';this.canvas.style.height=this.canvas.height*s+'px';}
  brush(a,b){const c=this.canvas,ctx=c.getContext('2d'),r=this.size/2;
    if(this.tool==='erase'){ctx.save();ctx.globalCompositeOperation='destination-out';ctx.lineCap='round';ctx.lineWidth=this.size;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();ctx.beginPath();ctx.arc(b.x,b.y,r,0,Math.PI*2);ctx.fill();ctx.restore();}
    else if(this.tool==='restore'){const steps=Math.max(1,Math.ceil(Math.hypot(b.x-a.x,b.y-a.y)/Math.max(1,r/2)));for(let i=0;i<=steps;i++){const t=i/steps;ctx.save();ctx.beginPath();ctx.arc(a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t,r,0,Math.PI*2);ctx.clip();ctx.globalCompositeOperation='copy';ctx.drawImage(this.recovery,0,0);ctx.restore();}}
  }
  undo(){if(!this.history.length)return;const s=this.history.pop();this.canvas.width=s.canvas.width;this.canvas.height=s.canvas.height;this.canvas.getContext('2d').drawImage(s.canvas,0,0);this.recovery=s.recovery;this.fit();this.change();}
  edges(contract){const ctx=this.canvas.getContext('2d'),pixels=ctx.getImageData(0,0,this.canvas.width,this.canvas.height),clean=cleanMatte(pixels,1),out=contract?contractAlpha1px(clean):clean;this.remember();ctx.putImageData(new ImageData(out.data,out.width,out.height),0,0);this.change();}
  tones(brightness,contrast){this.remember();const copy=cloneCanvas(this.canvas),ctx=this.canvas.getContext('2d');ctx.clearRect(0,0,this.canvas.width,this.canvas.height);ctx.save();ctx.filter=`brightness(${brightness}%) contrast(${contrast}%)`;ctx.drawImage(copy,0,0);ctx.restore();this.change();}
  trim(){const c=this.canvas,w=c.width,h=c.height,data=c.getContext('2d').getImageData(0,0,w,h).data;let left=w,top=h,right=-1,bottom=-1;for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(data[(y*w+x)*4+3]>4){left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);}if(right<0)throw Error('Görsel tamamen silinmiş; Geri al ile geri getirebilirsin.');if(left===0&&top===0&&right===w-1&&bottom===h-1)return;const crop=s=>{const out=document.createElement('canvas');out.width=right-left+1;out.height=bottom-top+1;out.getContext('2d').drawImage(s,left,top,out.width,out.height,0,0,out.width,out.height);return out;};this.set(crop(c),{recovery:crop(this.recovery)});this.change();}
}
