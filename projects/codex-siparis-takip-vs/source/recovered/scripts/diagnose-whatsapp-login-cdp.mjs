const endpoint = 'http://127.0.0.1:9223/json'
const targets = () => fetch(endpoint).then((response) => response.json())

async function connect(url) {
  const socket = new WebSocket(url)
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true })
    socket.addEventListener('error', reject, { once: true })
  })
  let sequence = 0
  const pending = new Map()
  const events = []
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data)
    if (message.id) {
      const call = pending.get(message.id)
      if (!call) return
      pending.delete(message.id)
      if (message.error) call.reject(new Error(message.error.message))
      else call.resolve(message.result)
    } else events.push(message)
  })
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++sequence
    pending.set(id, { resolve, reject })
    socket.send(JSON.stringify({ id, method, params }))
  })
  return { socket, send, events }
}

const original = await targets()
const mainTarget = original.find((target) => target.type === 'page' && /^http:\/\/127\.0\.0\.1:\d+/.test(target.url))
if (!mainTarget) throw new Error('VS sayfası bulunamadı.')
const main = await connect(mainTarget.webSocketDebuggerUrl)
await main.send('Runtime.evaluate', {
  expression: 'window.siparisTakip.openWhatsApp()',
  awaitPromise: true,
  returnByValue: true,
})
main.socket.close()

let whatsappTarget
for (let index = 0; index < 40; index += 1) {
  whatsappTarget = (await targets()).find((target) => target.type === 'page' && target.url.startsWith('https://web.whatsapp.com/'))
  if (whatsappTarget) break
  await new Promise((resolve) => setTimeout(resolve, 250))
}
if (!whatsappTarget) throw new Error('WhatsApp penceresi açılmadı.')

const whatsapp = await connect(whatsappTarget.webSocketDebuggerUrl)
await whatsapp.send('Runtime.enable')
await whatsapp.send('Log.enable')
await whatsapp.send('Network.enable')
await whatsapp.send('Page.enable')
if (process.argv.includes('--clear-cache')) await whatsapp.send('Network.clearBrowserCache')
if (!process.argv.includes('--no-reload')) await whatsapp.send('Page.reload', { ignoreCache: true })
await new Promise((resolve) => setTimeout(resolve, 15000))

const expression = `(() => {
  const body = document.body?.innerText || ''
  const login = /Giriş yapmak için tara|Telefon numarası kullanarak giriş yapın|Scan to log in/i.test(body)
  return {
    title: document.title,
    url: location.href,
    readyState: document.readyState,
    login,
    loginText: body.slice(0, 550),
    hasChatList: Boolean(document.querySelector('#side, #pane-side, [data-testid="chat-list"]')),
    canvasCount: document.querySelectorAll('canvas').length,
    qrImageCount: document.querySelectorAll('img[alt*="QR" i], [data-testid*="qr" i]').length,
    userAgent: navigator.userAgent,
  }
})()`
const page = (await whatsapp.send('Runtime.evaluate', { expression, returnByValue: true })).result.value
const requests = new Map(whatsapp.events.filter((event) => event.method === 'Network.requestWillBeSent')
  .map((event) => [event.params.requestId, event.params.request.url]))
const safeResource = (url) => {
  if (!url || !/^https?:/i.test(url)) return ''
  const parsed = new URL(url)
  return `${parsed.hostname}${parsed.pathname}`.slice(0, 150)
}
const errors = whatsapp.events.filter(({ method, params }) =>
  method === 'Network.loadingFailed'
  || method === 'Runtime.exceptionThrown'
  || method === 'Log.entryAdded' && params.entry?.level === 'error'
  || method === 'Network.responseReceived' && params.response?.status >= 400)
  .slice(-30)
  .map(({ method, params }) => ({
    method,
    error: params.errorText || params.exceptionDetails?.text || params.entry?.text?.slice(0, 220) || '',
    status: params.response?.status || undefined,
    resource: safeResource(params.response?.url || requests.get(params.requestId) || params.entry?.url),
  }))

whatsapp.socket.close()
console.log(JSON.stringify({ page, errors }, null, 2))
