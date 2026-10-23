import {createHmac,timingSafeEqual,createHash} from 'node:crypto';
export const hash=value=>createHash('sha256').update(typeof value==='string'?value:JSON.stringify(value)).digest('hex');
export function sign(data,secret){const payload=Buffer.from(JSON.stringify(data)).toString('base64url');return payload+'.'+createHmac('sha256',secret).update(payload).digest('base64url');}
export function verify(token,secret,kind){
  if(typeof token!=='string'||token.length>50000)throw new Error('Geçersiz yetki.');
  const [payload,signature,...rest]=token.split('.');
  const expected=createHmac('sha256',secret).update(payload).digest('base64url');
  if(rest.length||!signature||signature.length!==expected.length||!timingSafeEqual(Buffer.from(signature),Buffer.from(expected)))throw new Error('Geçersiz yetki.');
  const data=JSON.parse(Buffer.from(payload,'base64url').toString());
  if(data.kind!==kind||!Number.isFinite(data.exp)||data.exp<Date.now())throw new Error('İndirme/yükleme izni sona erdi. Tekrar deneyin.');
  return data;
}
