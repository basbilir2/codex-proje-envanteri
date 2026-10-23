const targets = await fetch('http://127.0.0.1:9223/json').then((r) => r.json())
const target = targets.find((item) => item.type === 'page' && item.url.startsWith('https://web.whatsapp.com/'))
if (!target) throw new Error('WhatsApp penceresi bulunamadı.')
const socket = new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject })
let id = 0
const send = (method, params = {}) => new Promise((resolve, reject) => {
  const requestId = ++id
  const onMessage = (event) => {
    const response = JSON.parse(event.data)
    if (response.id !== requestId) return
    socket.removeEventListener('message', onMessage)
    if (response.error) reject(new Error(response.error.message))
    else resolve(response.result)
  }
  socket.addEventListener('message', onMessage)
  socket.send(JSON.stringify({ id: requestId, method, params }))
})
if (process.argv.includes('--search-kadir')) {
  await send('Runtime.evaluate', { expression: `document.querySelector('input[placeholder="Aratın veya yeni sohbet başlatın"]')?.focus()` })
  await send('Input.insertText', { text: 'Kadir' })
  await new Promise((resolve) => setTimeout(resolve, 1800))
}
const requestedChat = process.argv.includes('--open-kadir') ? 'Kadir' : process.argv.includes('--open-project-group') ? "İzmir'de Reklam" : ''
if (requestedChat) {
  const candidate = await send('Runtime.evaluate', { expression: `(() => { const node = [...document.querySelectorAll('#pane-side [role="row"]')].find((n) => (n.innerText || '').split('\\n')[0] === ${JSON.stringify(requestedChat)}); if (!node) return null; const r = node.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 } })()`, returnByValue: true })
  const point = candidate.result.value
  if (!point) throw new Error('Kadir sohbeti bulunamadı.')
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: point.x, y: point.y, button: 'left', clickCount: 1 })
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: point.x, y: point.y, button: 'left', clickCount: 1 })
  await new Promise((resolve) => setTimeout(resolve, 1800))
}
if (process.argv.includes('--rightclick-project')) {
  const candidate = await send('Runtime.evaluate', { expression: `(() => { const node = [...document.querySelectorAll('#main [title]')].find((n) => (n.getAttribute('title') || '').includes('afis_265x80cm_4K (1)-gigapixel-recover v1-2x.rar')); if (!node) return null; const r = node.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 } })()`, returnByValue: true })
  const point = candidate.result.value
  if (!point) throw new Error('Proje dosyası görünmüyor.')
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: point.x, y: point.y, button: 'right', clickCount: 1 })
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: point.x, y: point.y, button: 'right', clickCount: 1 })
  await new Promise((resolve) => setTimeout(resolve, 700))
}
const expression = `(() => {
  const main = document.querySelector('#main')
  const header = main?.querySelector('header')
  const nodes = [...(main?.querySelectorAll('[data-id], [data-testid^="conv-msg-"]') || [])]
  const unique = [...new Set(nodes.map((node) => node.closest('[data-id], [data-testid^="conv-msg-"]') || node))]
  return {
    chatOpen: Boolean(main),
    chat: header?.querySelector('span[title]')?.getAttribute('title') || '',
    headerTitles: [...(header?.querySelectorAll('[title]') || [])].map((x) => x.getAttribute('title')).filter(Boolean).slice(0, 8),
    visibleMessages: unique.length,
    attachments: unique.filter((node) => /\\.(pdf|jpg|jpeg|png|svg|cdr|ai|psd|tiff?|zip|rar)\\b/i.test(node.innerText || '') || node.querySelector('[data-testid*="document"], [data-testid*="image-thumb"], video')).slice(-20).map((node) => ({
      id: (node.getAttribute('data-id') || node.getAttribute('data-testid') || '').slice(-100),
      text: (node.innerText || '').slice(0, 160),
      title: [...node.querySelectorAll('[title]')].map((x) => x.getAttribute('title')).filter(Boolean).slice(0, 4),
      download: Boolean(node.querySelector('[download], [data-testid*="download"]')),
    })),
    chatRows: [...document.querySelectorAll('#pane-side [role="row"]')].slice(0, 10).map((node) => (node.innerText || '').slice(0, 100)),
    searchFields: [...document.querySelectorAll('input, [contenteditable="true"]')].slice(0, 10).map((node) => ({ tag: node.tagName, placeholder: node.getAttribute('placeholder'), label: node.getAttribute('aria-label'), dataTab: node.getAttribute('data-tab'), outer: node.outerHTML.slice(0, 280) })),
    kadirRow: [...document.querySelectorAll('#pane-side [role="row"]')].find((node) => (node.innerText || '').split('\\n')[0] === 'Kadir')?.outerHTML.slice(0, 650) || '',
    menu: [...document.querySelectorAll('[role="menuitem"]')].filter((node) => node.offsetParent !== null).map((node) => ({ id: node.id, label: node.getAttribute('aria-label') || node.innerText })).slice(0, 24),
    customActions: [...document.querySelectorAll('[id^="izmirde-reklam-whatsapp-"]')].map((node) => ({ id: node.id, label: node.getAttribute('aria-label'), disabled: node.disabled })),
    bodyTail: document.body.innerText.slice(-450),
    projectRects: [...document.querySelectorAll('#main [data-id]')].filter((n) => (n.innerText || '').includes('afis_265x80cm_4K (1)-gigapixel-recover v1-2x.rar')).map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), x: r.x, y: r.y, width: r.width, height: r.height } }).slice(-8),
    projectButtonRects: [...document.querySelectorAll('#main [title]')].filter((n) => (n.getAttribute('title') || '').includes('afis_265x80cm_4K')).map((n) => { const r = n.getBoundingClientRect(); return { title: n.getAttribute('title'), x: r.x, y: r.y, width: r.width, height: r.height } }).slice(-5),
  }
})()`
const result = await send('Runtime.evaluate', { expression, returnByValue: true })
console.log(JSON.stringify(result.result.value, null, 2))
socket.close()
