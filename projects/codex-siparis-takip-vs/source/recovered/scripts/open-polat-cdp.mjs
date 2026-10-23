const targets = await fetch('http://127.0.0.1:9223/json').then((response) => response.json())
const target = targets.find((item) => item.type === 'page' && item.url.startsWith('https://web.whatsapp.com/'))
if (!target) throw new Error('WhatsApp CDP hedefi bulunamadı.')
const socket = new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, { once: true })
  socket.addEventListener('error', reject, { once: true })
})
let nextId = 0
const call = (method, params = {}) => new Promise((resolve, reject) => {
  const id = ++nextId
  const timer = setTimeout(() => reject(new Error(`${method} zaman aşımı`)), 10000)
  const listener = (event) => {
    const message = JSON.parse(event.data)
    if (message.id !== id) return
    socket.removeEventListener('message', listener)
    clearTimeout(timer)
    if (message.error) reject(new Error(message.error.message))
    else resolve(message.result)
  }
  socket.addEventListener('message', listener)
  socket.send(JSON.stringify({ id, method, params }))
})

const chatName = process.argv[2] || 'Polat'
const prepared = await call('Runtime.evaluate', { returnByValue: true, expression: `(() => {
  const title = [...document.querySelectorAll('[title]')].find((node) => node.getAttribute('title') === ${JSON.stringify(chatName)})
  if (!title) return { ok: false, reason: 'title-not-found' }
  let row = title
  for (let node = title; node && node !== document.body; node = node.parentElement) {
    const rect = node.getBoundingClientRect()
    if (rect.left < 620 && rect.width >= 400 && rect.height >= 60 && rect.height <= 100) { row = node; break }
  }
  let scrollable = row.parentElement
  while (scrollable && scrollable !== document.body && !(scrollable.scrollHeight > scrollable.clientHeight + 100 && /auto|scroll/.test(getComputedStyle(scrollable).overflowY))) scrollable = scrollable.parentElement
  if (scrollable && scrollable !== document.body) {
    const before = row.getBoundingClientRect()
    const viewport = scrollable.getBoundingClientRect()
    scrollable.scrollTop += before.top - viewport.top - 220
    scrollable.dispatchEvent(new Event('scroll', { bubbles: true }))
  }
  const rect = row.getBoundingClientRect()
  return { ok: true, x: rect.left + rect.width * 0.55, y: rect.top + rect.height / 2, rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }, scrollTop: scrollable?.scrollTop || 0 }
})()` })
const point = prepared.result.value
if (!point.ok) throw new Error(point.reason)
await new Promise((resolve) => setTimeout(resolve, 500))
await call('Input.dispatchMouseEvent', { type: 'mouseMoved', x: point.x, y: point.y })
await call('Input.dispatchMouseEvent', { type: 'mousePressed', x: point.x, y: point.y, button: 'left', clickCount: 1 })
await call('Input.dispatchMouseEvent', { type: 'mouseReleased', x: point.x, y: point.y, button: 'left', clickCount: 1 })
await new Promise((resolve) => setTimeout(resolve, 1500))
const checked = await call('Runtime.evaluate', { returnByValue: true, expression: `(() => ({ main: Boolean(document.querySelector('#main')), header: document.querySelector('#main header [title]')?.getAttribute('title') || document.querySelector('#main header')?.innerText?.slice(0, 100) || '' }))()` })
socket.close()
console.log(JSON.stringify({ point, result: checked.result.value }, null, 2))
