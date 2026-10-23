import fs from 'node:fs'
import path from 'node:path'

const userData = 'C:\\Users\\USER\\AppData\\Roaming\\İzmirde Reklam Sipariş Takip VS'
const databasePath = path.join(userData, 'vs-local-database.json')
const indexPath = path.join(userData, 'local-source-files.json')
const backups = path.join(userData, 'backups')
const orderId = '15IFHaAJZ6rutV1VynMO'
const messageId = '3A564FC8731F099FC2E8'
const indexKey = user_0017@example.invalid::${messageId}`
const actualFileName = 'WhatsApp Image 2026-09-18 at 22.46.13.jpeg'
const folder = 'C:\\Users\\USER\\Documents\\İzmirde Reklam Sipariş Takip VS\\Hızlı Siparişler\\Kadir'
const oldPath = path.join(folder, `Kadir - Kadir - ${actualFileName}`)
const newPath = path.join(folder, `Kadir - ${actualFileName}`)

if (!fs.existsSync(oldPath) && !fs.existsSync(newPath)) throw new Error('Kadir görseli bulunamadı.')
if (fs.existsSync(oldPath)) {
  if (fs.existsSync(newPath)) throw new Error('Hedef dosya zaten var; otomatik üzerine yazılmadı.')
  fs.renameSync(oldPath, newPath)
}
const bytes = fs.readFileSync(newPath)
if (bytes.length < 4 || bytes[0] !== 0xff || bytes[1] !== 0xd8 || bytes[2] !== 0xff) throw new Error('Kaydedilen dosya geçerli JPEG değil.')

fs.mkdirSync(backups, { recursive: true })
const stamp = new Date().toISOString().replace(/[:.]/g, '-')
fs.copyFileSync(databasePath, path.join(backups, `vs-local-database-before-kadir-fix-${stamp}.json`))
fs.copyFileSync(indexPath, path.join(backups, `local-source-files-before-kadir-fix-${stamp}.json`))

const database = JSON.parse(fs.readFileSync(databasePath, 'utf8'))
const index = JSON.parse(fs.readFileSync(indexPath, 'utf8'))
if (!database.docs?.[`orders/${orderId}`] || !database.docs?.[`orderPrivate/${orderId}`] || !index[indexKey]) throw new Error('Kadir kayıt bağlantıları bulunamadı.')
database.docs[`orders/${orderId}`].name = path.basename(actualFileName, path.extname(actualFileName))
database.docs[`orderPrivate/${orderId}`].sourceTitle = actualFileName
index[indexKey].path = newPath

for (const [target, value] of [[databasePath, database], [indexPath, index]]) {
  const temporary = `${target}.tmp`
  fs.writeFileSync(temporary, JSON.stringify(value, null, 2), 'utf8')
  fs.renameSync(temporary, target)
}

console.log(JSON.stringify({ ok: true, path: newPath, bytes: bytes.length, jpeg: true, orderId, messageId }))
