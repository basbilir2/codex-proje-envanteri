const targets = await fetch('http://127.0.0.1:9223/json').then((response) => response.json())
const target = targets.find((item) => item.type === 'page' && /127\.0\.0\.1/.test(item.url))
if (!target) throw new Error('VS renderer target bulunamadı')

const socket = new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, { once: true })
  socket.addEventListener('error', reject, { once: true })
})

const id = 1
socket.send(JSON.stringify({
  id,
  method: 'Runtime.evaluate',
  params: {
    expression: `JSON.stringify({text: document.body.innerText, title: document.title})`,
    returnByValue: true,
  },
}))

const message = await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error('CDP yanıt zaman aşımı')), 10000)
  socket.addEventListener('message', (event) => {
    const value = JSON.parse(event.data)
    if (value.id === id) {
      clearTimeout(timer)
      resolve(value)
    }
  })
})
socket.close()
const payload = JSON.parse(message.result.result.value)
const result = {
  title: payload.title,
  hasConfiguredPersonAjans: payload.text.includes('AnonPerson_0012'),
  emptyCustomerMessage: payload.text.includes('Müşteri bulunamadı'),
  hasUploadActions: payload.text.includes('Excel / CSV yükle') && payload.text.includes('Müşteri yükle'),
}
console.log(JSON.stringify(result, null, 2))
if (!result.hasConfiguredPersonAjans || result.emptyCustomerMessage) process.exitCode = 2
