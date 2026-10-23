import fs from 'node:fs';
import path from 'node:path';

const auth = JSON.parse(fs.readFileSync('.elmas-auth.json', 'utf8')).tokens.default;
async function accessToken() {
  if (auth.access_token && Number(auth.expiry_date) > Date.now() + 60000) return auth.access_token;
  const body = new URLSearchParams({client_id:auth.client_id,client_secret:auth.client_secret,refresh_token:auth.refresh_token,grant_type:'refresh_token'});
  const response = await fetch('https://oauth2.googleapis.com/token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body});
  if (!response.ok) throw new Error('Google token yenileme başarısız: '+response.status);
  const data = await response.json();
  return data.access_token;
}
const token = await accessToken();
async function request(url, options={}) {
  const response = await fetch(url,{...options,headers:{Authorization:`Bearer ${token}`,...options.headers}});
  if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);
  return response.status===204?{}:response.json();
}
async function createFolder(name,parent){
  return request('https://www.googleapis.com/drive/v3/files?fields=id,name',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,mimeType:'application/vnd.google-apps.folder',...(parent?{parents:[parent]}:{})})});
}
const root={id:'1qG292zTKnn2IRve9fYxsaaubIr9mJ0IG'};
const bytes=fs.readFileSync(path.resolve('Elmas-Apartmani-Veri.xlsx'));
const boundary='elmas_'+Date.now();
const metadata=JSON.stringify({name:'Elmas Apartmanı • Yönetim',mimeType:'application/vnd.google-apps.spreadsheet',parents:[root.id]});
const body=Buffer.concat([
  Buffer.from(`--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${metadata}\r\n--${boundary}\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n`),
  bytes,Buffer.from(`\r\n--${boundary}--`)
]);
const sheet=await request('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink',{method:'POST',headers:{'Content-Type':`multipart/related; boundary=${boundary}`},body});
console.log(JSON.stringify({spreadsheetId:sheet.id,spreadsheetUrl:sheet.webViewLink,rootFolderId:root.id,rootFolderUrl:`https://drive.google.com/drive/folders/${root.id}`},null,2));
