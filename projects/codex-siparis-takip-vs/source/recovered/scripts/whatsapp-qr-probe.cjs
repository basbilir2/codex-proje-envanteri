const { app, BrowserWindow } = require('electron')
const fs = require('fs')
const os = require('os')
const path = require('path')

if (process.argv.includes('--production-window')) {
  app.setName('İzmirde Reklam Sipariş Takip VS')
  app.setAppUserModelId('com.izmirde.reklam.siparistakip.vs')
  app.commandLine.appendSwitch('disable-backgrounding-occluded-windows')
  app.commandLine.appendSwitch('disable-renderer-backgrounding')
  app.commandLine.appendSwitch('disable-background-timer-throttling')
}

const isolatedData = fs.mkdtempSync(path.join(os.tmpdir(), 'siparis-vs-whatsapp-qr-'))
app.setPath('userData', isolatedData)

app.whenReady().then(async () => {
  if (process.argv.includes('--with-main')) {
    const main = new BrowserWindow({ show: false, webPreferences: { partition: 'persist:izmirde-siparis-takip-vs' } })
    main.webContents.setUserAgent(`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${process.versions.chrome} Safari/537.36`)
    await main.loadURL('https://siparis-takip-vs-4f72.firebaseapp.com/?desktop=1000')
  }
  const productionMode = process.argv.includes('--production-window')
  const window = new BrowserWindow({ show: false, webPreferences: productionMode ? {
    preload: path.join(__dirname, '..', 'whatsapp-preload.cjs'),
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: false,
    backgroundThrottling: false,
    partition: 'persist:izmirde-whatsapp-vs',
  } : { backgroundThrottling: false } })
  const userAgent = `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${process.versions.chrome} Safari/537.36`
  window.webContents.session.setUserAgent(userAgent)
  window.webContents.setUserAgent(userAgent)
  if (productionMode) window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }))
  const errors = []
  window.webContents.on('console-message', (_event, level, message) => {
    if (level >= 2 && errors.length < 8) errors.push(String(message).slice(0, 180))
  })
  window.webContents.on('did-fail-load', (_event, code, description, url) => {
    errors.push(`${code} ${description} ${new URL(url).hostname}`)
  })
  try {
    await window.loadURL('https://web.whatsapp.com/')
    await new Promise((resolve) => setTimeout(resolve, 15000))
    const page = await window.webContents.executeJavaScript(`(() => ({
      body: (document.body?.innerText || '').slice(0, 450),
      canvasCount: document.querySelectorAll('canvas').length,
      qrElements: document.querySelectorAll('[data-testid*="qr" i], img[alt*="QR" i]').length,
      chatList: Boolean(document.querySelector('#side, #pane-side, [data-testid="chat-list"]')),
    }))()`)
    process.stdout.write(JSON.stringify({ chrome: process.versions.chrome, page, errors, isolatedData }) + '\n')
  } catch (error) {
    process.stdout.write(JSON.stringify({ error: error.message, errors, isolatedData }) + '\n')
  }
  app.quit()
})
