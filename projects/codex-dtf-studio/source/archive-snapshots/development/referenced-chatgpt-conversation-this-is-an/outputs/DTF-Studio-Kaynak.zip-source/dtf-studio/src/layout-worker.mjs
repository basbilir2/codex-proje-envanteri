import {layout} from './engine.mjs';
self.onmessage=e=>{try{self.postMessage({result:layout(e.data.designs,e.data.settings)});}catch(error){self.postMessage({error:error.message});}};
