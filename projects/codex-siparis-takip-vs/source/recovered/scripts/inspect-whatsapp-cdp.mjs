const targets = await fetch('http://127.0.0.1:9223/json').then((response) => response.json())
const target = targets.find((item) => item.type === 'page' && item.url.startsWith('https://web.whatsapp.com/'))
if (!target) throw new Error('WhatsApp CDP hedefi bulunamadı.')

const socket = new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, { once: true })
  socket.addEventListener('error', reject, { once: true })
})

const expression = `(() => {
  const visible = (node) => {
    const rect = node.getBoundingClientRect()
    const style = getComputedStyle(node)
    return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none'
  }
  const candidates = [...document.querySelectorAll('span,div,[title],[aria-label]')]
    .filter(visible)
    .filter((node) => /polat/i.test((node.getAttribute('title') || '') + ' ' + (node.getAttribute('aria-label') || '') + ' ' + (node.textContent || '')))
    .slice(0, 30)
    .map((node) => {
      const rect = node.getBoundingClientRect()
      return {
        tag: node.tagName,
        title: node.getAttribute('title') || '',
        aria: node.getAttribute('aria-label') || '',
        text: (node.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 180),
        cls: String(node.className || '').slice(0, 120),
        x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height),
      }
    })
  const polat = [...document.querySelectorAll('[title]')].find((node) => node.getAttribute('title') === 'Polat')
  const sourceMessage = [...document.querySelectorAll('[data-id]')].find((node) => (node.getAttribute('data-id') || '').endsWith('_3EB08EC6EE7ED0E5854C14'))
    || [...document.querySelectorAll('#main *')].find((node) => /5\.pdf/i.test(node.textContent || ''))?.closest('[data-id], [role="row"]')
  const messageNodes = sourceMessage ? [sourceMessage, ...sourceMessage.querySelectorAll('*')].filter((node) => {
    const attrs = ['title', 'aria-label', 'data-icon', 'data-testid', 'role'].map((name) => node.getAttribute?.(name) || '').join(' ')
    return attrs.trim() || /5\.pdf/i.test(node.textContent || '')
  }).slice(0, 100).map((node) => ({ tag: node.tagName, title: node.getAttribute?.('title') || '', aria: node.getAttribute?.('aria-label') || '', icon: node.getAttribute?.('data-icon') || '', testid: node.getAttribute?.('data-testid') || '', role: node.getAttribute?.('role') || '', text: (node.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 120) })) : []
  const pdfHits = [...document.querySelectorAll('#main *')].filter((node) => (node.textContent || '').trim() === '5.pdf').slice(0, 5).map((hit) => {
    const chain = []
    for (let node = hit; node && node !== document.querySelector('#main'); node = node.parentElement) chain.push({ tag: node.tagName, id: node.getAttribute?.('data-id') || '', role: node.getAttribute?.('role') || '', title: node.getAttribute?.('title') || '', aria: node.getAttribute?.('aria-label') || '', icon: node.getAttribute?.('data-icon') || '', testid: node.getAttribute?.('data-testid') || '', text: (node.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 90) })
    return chain.slice(0, 14)
  })
  const ancestors = []
  for (let node = polat; node && node !== document.body; node = node.parentElement) {
    const rect = node.getBoundingClientRect()
    ancestors.push({ tag: node.tagName, aria: node.getAttribute('aria-label') || '', x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height), clientHeight: node.clientHeight, scrollHeight: node.scrollHeight, scrollTop: node.scrollTop, overflowY: getComputedStyle(node).overflowY })
  }
  return {
    title: document.title,
    ready: document.readyState,
    bodyText: document.body?.innerText?.slice(0, 500) || '',
    side: Boolean(document.querySelector('#side')),
    paneSide: Boolean(document.querySelector('#pane-side')),
    main: Boolean(document.querySelector('#main')),
    mainText: document.querySelector('#main')?.innerText?.slice(0, 1200) || '',
    contentEditables: [...document.querySelectorAll('[contenteditable=true]')].filter(visible).length,
    headerNodes: [...document.querySelectorAll('#main header [title], #main header [aria-label], #main header [dir="auto"]')].slice(0, 20).map((node) => ({ tag: node.tagName, title: node.getAttribute('title') || '', aria: node.getAttribute('aria-label') || '', text: (node.textContent || '').trim().slice(0, 100) })),
    candidates, ancestors, sourceMessageFound: Boolean(sourceMessage), messageNodes, pdfHits,
  }
})()`

const result = await new Promise((resolve, reject) => {
  const id = 1
  const timer = setTimeout(() => reject(new Error('CDP yanıt vermedi.')), 10000)
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data)
    if (message.id !== id) return
    clearTimeout(timer)
    if (message.error) reject(new Error(message.error.message))
    else resolve(message.result.result.value)
  })
  socket.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression, returnByValue: true } }))
})

socket.close()
console.log(JSON.stringify(result, null, 2))
