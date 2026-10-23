import {readdir,readFile,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
const root=fileURLToPath(new URL('..',import.meta.url)),sharp=createRequire(join(root,'app/package.json'))('sharp');
const jobs=[];
for(const name of await readdir(join(root,'app/jobs'))){try{const j=JSON.parse(await readFile(join(root,'app/jobs',name,'job.json'),'utf8'));if(j.mode==='quick'&&j.sourceWidth===192&&j.region?.width===97)jobs.push(j);}catch{}}
const job=jobs.sort((a,b)=>b.createdAt.localeCompare(a.createdAt))[0];if(!job)throw Error('Tarayıcı kontrol işi bulunamadı.');
const {data,info}=await sharp(join(root,'app/jobs',job.id,'edited.png')).ensureAlpha().raw().toBuffer({resolveWithObject:true});
let transparent=0;for(let i=3;i<data.length;i+=4)if(data[i]===0)transparent++;
const proof={job:job.id,width:info.width,height:info.height,centreAlpha:data[(Math.floor(info.height/2)*info.width+Math.floor(info.width/2))*4+3],transparent};
const path=join(root,'on-kontrol/editor-check.json');let previous=[];try{previous=JSON.parse(await readFile(path,'utf8'));}catch{}
previous.push({stage:process.argv[2],...proof});await writeFile(path,JSON.stringify(previous,null,2));console.log(JSON.stringify(proof));
