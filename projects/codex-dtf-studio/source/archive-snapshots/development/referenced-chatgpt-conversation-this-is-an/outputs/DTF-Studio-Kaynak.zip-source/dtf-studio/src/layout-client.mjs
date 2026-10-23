import workerCode from './layout-worker-code.mjs';
import {layout} from './engine.mjs';
export function createLayoutCalculator(){
  let cancel;
  const calculate=(designs,settings)=>{
    cancel?.();
    return new Promise((resolve,reject)=>{
      let worker,url,ended=false;
      const stop=()=>{worker?.terminate();if(url)URL.revokeObjectURL(url);};
      cancel=()=>{if(ended)return;ended=true;stop();reject(new DOMException('Dizgi yenilendi.','AbortError'));};
      try{
        url=URL.createObjectURL(new Blob([workerCode],{type:'text/javascript'}));worker=new Worker(url);
        worker.onmessage=e=>{if(ended)return;ended=true;stop();e.data.error?reject(new Error(e.data.error)):resolve(e.data.result);};
        worker.onerror=()=>{if(ended)return;ended=true;stop();try{resolve(layout(designs,settings));}catch(e){reject(e);}};
        worker.postMessage({designs,settings});
      }catch{
        stop();setTimeout(()=>{if(ended)return;ended=true;try{resolve(layout(designs,settings));}catch(e){reject(e);}},0);
      }
    });
  };
  calculate.cancel=()=>cancel?.();return calculate;
}
