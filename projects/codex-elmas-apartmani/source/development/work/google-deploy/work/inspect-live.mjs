import {google} from 'googleapis';
import fs from 'node:fs';
const authJson=JSON.parse(fs.readFileSync('./.elmas-auth.json','utf8')).tokens.default;
const auth=new google.auth.OAuth2(authJson.client_id,authJson.client_secret);auth.setCredentials({refresh_token:authJson.refresh_token,access_token:authJson.access_token,expiry_date:authJson.expiry_date});
const sheets=google.sheets({version:'v4',auth});
const id='10V4oTIMWrR9AOsolDmF2586Uj0-mj8d_SFDj0qIOi8s';
for(const name of ['Daireler','Aidatlar','Odemeler','Dekontlar','GelirGider','KasaHareketleri']){const x=await sheets.spreadsheets.values.get({spreadsheetId:id,range:`${name}!A:Z`});const v=x.data.values||[];console.log(name,Math.max(0,v.length-1),v.length>1?v[1].slice(0,10):[])}

