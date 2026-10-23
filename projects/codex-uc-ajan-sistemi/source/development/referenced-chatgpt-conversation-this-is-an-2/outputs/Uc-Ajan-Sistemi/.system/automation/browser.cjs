// Product-local browser worker. It never connects to the user's browser profile.
const {chromium}=require('playwright-core');
const fs=require('node:fs');
async function main(input){
 const url=new URL(input.url);
 if(!['127.0.0.1','localhost'].includes(url.hostname)||url.protocol!=='http:')throw Error('Yalnız yerel proje adresi kullanılabilir.');
 const browser=await chromium.launch({executablePath:input.browser,headless:true});
 try{
  const context=await browser.newContext({viewport:{width:Math.min(1920,Math.max(320,input.width||1280)),height:Math.min(1200,Math.max(320,input.height||800))},serviceWorkers:'block',acceptDownloads:false});
  const allowed=url.origin, errors=[],failed=[],assertions=[];
  await context.route('**/*',route=>{const target=new URL(route.request().url());return ['data:','blob:','about:'].includes(target.protocol)||target.origin===allowed?route.continue():route.abort('blockedbyclient');});
  const page=await context.newPage();
  page.on('pageerror',e=>errors.push(String(e.message).slice(0,1200)));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text().slice(0,1200));});
  page.on('response',r=>{if(r.status()>=400&&new URL(r.url()).origin===allowed&&!r.url().endsWith('/favicon.ico'))failed.push({url:r.url(),status:r.status()});});
  page.on('dialog',d=>d.dismiss());
  const response=await page.goto(input.url,{waitUntil:'domcontentloaded',timeout:25000});
  if(response&&response.status()>=400)errors.push('Sayfa HTTP '+response.status());
  const locator=s=>s.role?page.getByRole(s.role,{name:s.name,exact:s.exact!==false}):s.label?page.getByLabel(s.label,{exact:true}):s.text?page.getByText(s.text,{exact:s.exact!==false}):s.selector?page.locator(s.selector):null;
  for(const s of (input.steps||[]).slice(0,20)){
   try{
    const l=locator(s);
    switch(s.action){
     case 'click':if(!l)throw Error('Bir hedef belirt.');await l.click({timeout:7000});break;
     case 'fill':if(!l)throw Error('Bir hedef belirt.');await l.fill(String(s.value||''),{timeout:7000});break;
     case 'press':if(l)await l.press(s.key,{timeout:7000});else await page.keyboard.press(s.key);break;
     case 'hold':await page.keyboard.down(s.key);await page.waitForTimeout(Math.min(1500,Math.max(0,s.ms||300)));await page.keyboard.up(s.key);break;
     case 'wait':await page.waitForTimeout(Math.min(3000,Math.max(0,s.ms||250)));break;
     case 'expect_text':
      if(s.text)await page.getByText(s.text,{exact:s.exact===true}).first().waitFor({state:'visible',timeout:7000});
      else if(l)await l.waitFor({state:'visible',timeout:7000});
      else throw Error('expect_text için text veya role/name/selector hedefi gerekiyor.');
      break;
     case 'expect_visible':if(!l)throw Error('Bir hedef belirt.');await l.waitFor({state:'visible',timeout:7000});break;
     case 'expect_stable':case 'expect_motion':{
      if(!l)throw Error('Görsel kontrol için selector veya role/name belirt.');
      const before=await l.screenshot({timeout:7000});
      await page.waitForTimeout(Math.min(1500,Math.max(200,s.ms||650)));
      const after=await l.screenshot({timeout:7000});const changed=!before.equals(after);
      if(changed!==(s.action==='expect_motion'))throw Error(s.action==='expect_stable'?'Durması beklenen görüntü değişmeye devam ediyor.':'Hareket etmesi beklenen görüntü sabit kaldı.');
      break;
     }
     default:throw Error('Desteklenmeyen adım: '+s.action);
    }
    assertions.push({action:s.action,target:s.name||s.label||s.text||s.selector||s.key||'',passed:true});
   }catch(e){assertions.push({action:s.action,passed:false,error:String(e.message).slice(0,1500)});break;}
  }
  await page.waitForTimeout(450);
  const body=await page.locator('body').innerText({timeout:5000}).catch(()=>'');
  const snapshot=await page.locator('body').ariaSnapshot({timeout:5000}).catch(()=>'');
  await page.screenshot({path:input.screenshot,fullPage:false});
  return {passed:errors.length===0&&failed.length===0&&assertions.every(a=>a.passed),title:await page.title(),text:body.slice(0,5000),controls:snapshot.slice(0,9000),errors:[...new Set(errors)],failed_requests:failed.slice(0,20),assertions,screenshot:input.screenshot,external_network:'blocked',fresh_profile:true};
 }finally{await browser.close();}
}
let raw='';process.stdin.setEncoding('utf8');process.stdin.on('data',c=>raw+=c);process.stdin.on('end',()=>main(JSON.parse(raw)).then(r=>process.stdout.write(JSON.stringify(r))).catch(e=>{process.stdout.write(JSON.stringify({passed:false,errors:[String(e.message)],assertions:[]}));process.exitCode=1;}));
