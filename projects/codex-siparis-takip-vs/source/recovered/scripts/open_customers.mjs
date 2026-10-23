const targets = await fetch('http://127.0.0.1:9223/json').then((response) => response.json())
const target = targets.find((item) => item.type === 'page' && /127\.0\.0\.1/.test(item.url))
if (!target) throw new Error('VS renderer target bulunamadı')
const socket = new WebSocket(target.webSocketDebuggerUrl)
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, { once: true })
  socket.addEventListener('error', reject, { once: true })
})
socket.send(JSON.stringify({
  id: 1,
  method: 'Runtime.evaluate',
  params: {
    expression: `(() => {
      const item = [...document.querySelectorAll('button, a')].find((node) => node.textContent.trim() === 'Müşteriler');
      if (!item) return false;
      item.click();
      return true;
    })()`,
    returnByValue: true,
  },
}))
const message = await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error('Müşteriler sayfası zaman aşımı')), 10000)
  socket.addEventListener('message', (event) => {
    const value = JSON.parse(event.data)
    if (value.id === 1) {
      clearTimeout(timer)
      resolve(value)
    }
  })
})
socket.close()
if (!message.result.result.value) throw new Error('Müşteriler düğmesi bulunamadı')
console.log('Müşteriler sayfası açıldı')
