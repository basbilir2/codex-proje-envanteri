const targets = await fetch('http://127.0.0.1:9223/json').then((response) => response.json())
const target = targets.find((item) => item.type === 'page' && item.url.startsWith('https://web.whatsapp.com/'))
if (!target) throw new Error('WhatsApp hedefi bulunamadı.')
const socket = new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, { once: true })
  socket.addEventListener('error', reject, { once: true })
})
const expression = `(() => {
  const visible = (node) => { const r=node.getBoundingClientRect(); return r.width>0&&r.height>0&&getComputedStyle(node).display!=='none' }
  const messages = [...document.querySelectorAll('#main [data-testid^="conv-msg-"], #main [id]')]
    .filter((node) => /^(conv-msg-|3[A-Z0-9]{8,})/.test((node.getAttribute('data-testid') || node.id || '')))
    .map((node) => ({
      id: node.id || '', testid: node.getAttribute('data-testid') || '', text: (node.innerText || '').replace(/\\s+/g,' ').trim().slice(0,300),
      html: node.outerHTML.slice(0,1200),
      controls: [...node.querySelectorAll('[title],[aria-label],[data-icon],[data-testid],[role="button"],a,img,video,canvas')].filter(visible).map((x)=>({tag:x.tagName,title:x.getAttribute('title')||'',aria:x.getAttribute('aria-label')||'',icon:x.getAttribute('data-icon')||'',testid:x.getAttribute('data-testid')||'',role:x.getAttribute('role')||'',src:(x.getAttribute('src')||'').slice(0,120)})).slice(0,80)
    }))
  return { mainText: document.querySelector('#main')?.innerText || '', messages }
})()`
const result = await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error('CDP zaman aşımı')), 10000)
  socket.addEventListener('message', (event) => {
    const value = JSON.parse(event.data)
    if (value.id !== 1) return
    clearTimeout(timer)
    resolve(value.result.result.value)
  })
  socket.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression,returnByValue:true}}))
})
socket.close()
console.log(JSON.stringify(result,null,2))
