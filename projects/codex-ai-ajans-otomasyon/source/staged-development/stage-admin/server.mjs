import { createServer } from 'node:http';
import { createCipheriv, createHash, randomBytes, timingSafeEqual, pbkdf2Sync } from 'node:crypto';
import { DatabaseSync } from 'node:sqlite';
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const host = process.env.HOST || '0.0.0.0';
const port = Number(process.env.PORT || 5684);
const appRoot = path.resolve(process.env.APP_ROOT || '/app');
const workspaceRoot = path.resolve(process.env.WORKSPACE_ROOT || '/workspace');
const adminRoot = path.resolve(process.env.ADMIN_DATA_ROOT || path.join(workspaceRoot, 'data/admin'));
const operatorPasswordHash = process.env.OPERATOR_PASSWORD_HASH || '';
const encryptionSecret = process.env.ADMIN_ENCRYPTION_KEY || '';
if (!operatorPasswordHash || encryptionSecret.length < 32) throw new Error('admin_security_not_configured');

const publicRoot = path.join(appRoot, 'public');
const dbPath = path.join(adminRoot, 'ajans-kurucu.sqlite');
const appsRoot = path.join(adminRoot, 'apps');
mkdirSync(adminRoot, { recursive: true });
mkdirSync(appsRoot, { recursive: true });

const resources = [
  ['agent', 'analizci', 'Analizci', 'projects/agents/analizci.txt', 'Marka, veri ve performans yönünü çıkarır.'],
  ['agent', 'sosyal-medya-icerik-stratejisti', 'İçerik Stratejisti', 'projects/agents/sosyal-medya-icerik-stratejisti.txt', 'İçerik planı, metin, kanca ve CTA üretir.'],
  ['agent', 'gorsel-stratejist', 'Görsel Stratejist', 'projects/agents/gorsel-stratejist.txt', 'Görsel brief ve üretim yönü hazırlar.'],
  ['agent', 'kontrol-muhalefet-kurulu', 'Kontrol ve Muhalefet', 'projects/agents/kontrol-muhalefet-kurulu.txt', 'Cesur ve temkinli kontrolleri yürütür.'],
  ['agent', 'ana-ordinaryus', 'Ana Ordinaryüs', 'projects/agents/ana-ordinaryus.txt', 'Son iç kararı ve risk değerlendirmesini yapar.'],
  ['agent', 'operasyon-orkestratoru', 'Operasyon Orkestratörü', 'projects/agents/operasyon-orkestratoru.txt', 'Görev sırası, model, süre ve maliyeti yönetir.'],
  ['agent', 'guncellik-gozcusu', 'Güncellik Gözcüsü', 'projects/agents/guncellik-gozcusu.txt', 'Trend, platform ve model güncelliğini izler.'],
  ['agent', 'hafiza-ogrenme-yoneticisi', 'Hafıza Yöneticisi', 'projects/agents/hafiza-ogrenme-yoneticisi.txt', 'Kalıcı ve geçici öğrenmeyi ayırır.'],
  ['agent', 'yayin-arayuz-ajani', 'Yayın ve Arayüz', 'projects/agents/yayin-arayuz-ajani.txt', 'Kullanıcıya sade sonuç ve onay paketi sunar.'],
  ['agent', 'bagimsiz-denetci', 'Bağımsız Denetçi', 'projects/agents/bagimsiz-denetci.txt', 'Kritik kararı farklı bakışla denetler.'],
  ['agent', 'baslatma-saglik-kontrol-ajani', 'Başlatma ve Sağlık', 'projects/agents/baslatma-saglik-kontrol-ajani.txt', 'Başlangıç ve güvenli devam kontrolünü yapar.'],
  ['model', 'model-kutuphanesi', 'Model Kütüphanesi', 'projects/models/model-kutuphanesi.json', 'Kullanılabilecek model adayları ve durumları.'],
  ['model', 'model-secimi', 'Model Seçim Kuralları', 'projects/models/model-secimi.json', 'Göreve göre model seçimi.'],
  ['model', 'model-yonlendirme', 'Dinamik Model Yönlendirme', 'data/memory/model-yonlendirme.json', 'Katman, maliyet ve yükseltme kuralları.'],
  ['flow', 'durum-makinesi', 'Görev Durumları', 'data/memory/durum-makinesi.json', 'Bir görevin başlangıçtan öğrenmeye kadar akışı.'],
  ['flow', 'tartisma-politikasi', 'Tartışma Akışı', 'data/memory/tartisma-politikasi.json', 'Tur sınırları ve kapanış kararları.'],
  ['flow', 'yetki-matrisi', 'Yetki ve Onay Akışı', 'data/memory/yetki-matrisi.json', 'Sistem ve kullanıcı yetki sınırları.'],
  ['policy', 'baglam-derleme-politikasi', 'Token ve Bağlam', 'data/memory/baglam-derleme-politikasi.json', 'Gereksiz tokenı önleyen bağlam kuralları.'],
  ['policy', 'guvenlik-politikasi', 'Güvenlik', 'data/memory/guvenlik-politikasi.json', 'Saldırı, veri ve dış eylem korumaları.'],
  ['policy', 'hafiza-politikasi', 'Hafıza', 'data/memory/hafiza-politikasi.json', 'Hafızanın saklama ve temizleme düzeni.'],
  ['policy', 'kalite-politikasi', 'Kalite', 'data/memory/kalite-politikasi.json', 'Çıktı kalite eşikleri ve red kuralları.'],
  ['policy', 'gizlilik-ve-veri-saklama', 'Gizlilik ve Saklama', 'data/memory/gizlilik-ve-veri-saklama.json', 'Müşteri verisi ve saklama süreleri.'],
  ['policy', 'degisiklik-yonetimi', 'Değişiklik ve Geri Alma', 'data/memory/degisiklik-yonetimi.json', 'Sürümlü değişiklik ve geri dönüş düzeni.'],
  ['policy', 'musteri-baslangic-motoru', 'Müşteri Başlangıcı', 'data/memory/musteri-baslangic-motoru.json', 'Yeni ve eski hesap başlangıç değerlendirmesi.'],
  ['policy', 'zaman-yonetimi', 'Zaman Yönetimi', 'data/memory/zaman-yonetimi.json', 'Kapanma, toparlanma ve çalışma zamanları.'],
  ['policy', 'test-kabul-kriterleri', 'Test ve Kabul', 'data/memory/test-kabul-kriterleri.json', 'Bir sürümün hazır sayılma şartları.']
].map(([category, key, name, source, description]) => ({ category, key, name, source, description, format: source.endsWith('.json') ? 'json' : 'text' }));

const resourceMap = new Map(resources.map((item) => [`${item.category}:${item.key}`, item]));
const providers = [
  { id: 'google_gemini', name: 'Google Gemini', fields: ['api_key'] },
  { id: 'openai', name: 'OpenAI', fields: ['api_key'] },
  { id: 'cloudflare', name: 'Cloudflare AI', fields: ['account_id', 'api_token'] },
  { id: 'meta_instagram', name: 'Meta ve Instagram', fields: ['app_id', 'app_secret', 'access_token', 'page_id', 'instagram_account_id'] },
  { id: 'wix', name: 'Wix', fields: ['api_key', 'site_id'] },
  { id: 'ga4', name: 'Google Analytics 4', fields: ['property_id', 'service_account_json'] }
];
const providerMap = new Map(providers.map((item) => [item.id, item]));

const db = new DatabaseSync(dbPath);
db.exec(`
  PRAGMA journal_mode=WAL;
  PRAGMA synchronous=FULL;
  PRAGMA foreign_keys=ON;
  PRAGMA busy_timeout=5000;
  CREATE TABLE IF NOT EXISTS sessions(
    session_hash TEXT PRIMARY KEY, csrf_hash TEXT NOT NULL, created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL, revoked_at TEXT
  );
  CREATE TABLE IF NOT EXISTS resource_versions(
    version_id TEXT PRIMARY KEY, resource_key TEXT NOT NULL, category TEXT NOT NULL,
    version_no INTEGER NOT NULL, content TEXT NOT NULL, content_hash TEXT NOT NULL,
    source_hash TEXT NOT NULL, status TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL, UNIQUE(resource_key, category, version_no)
  );
  CREATE INDEX IF NOT EXISTS idx_resource_versions_lookup
    ON resource_versions(category, resource_key, status, version_no DESC);
  CREATE TABLE IF NOT EXISTS connections(
    provider TEXT PRIMARY KEY, label TEXT NOT NULL, metadata_json TEXT NOT NULL,
    ciphertext TEXT NOT NULL, iv TEXT NOT NULL, auth_tag TEXT NOT NULL,
    status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS app_instances(
    app_id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
    brand_name TEXT NOT NULL, status TEXT NOT NULL, config_json TEXT NOT NULL,
    generation_no INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS studio_settings(
    setting_key TEXT PRIMARY KEY, value_json TEXT NOT NULL, updated_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS audit_events(
    sequence INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL, object_id TEXT, payload_json TEXT NOT NULL,
    previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL, created_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS login_limits(
    key TEXT PRIMARY KEY, window_start TEXT NOT NULL, count INTEGER NOT NULL
  );
`);
db.exec('PRAGMA optimize;');

const now = () => new Date().toISOString();
const id = (prefix) => `${prefix}-${Date.now()}-${randomBytes(6).toString('hex')}`;
const sha256 = (value) => createHash('sha256').update(value).digest('hex');
const safeEqual = (left, right) => {
  const a = Buffer.from(String(left || '')); const b = Buffer.from(String(right || ''));
  return a.length === b.length && timingSafeEqual(a, b);
};
const json = (value, fallback = null) => { try { return JSON.parse(value); } catch { return fallback; } };
const safeSlug = (value, label = 'slug') => {
  const result = String(value || '').trim().toLowerCase();
  if (!/^[a-z0-9][a-z0-9-]{1,62}$/.test(result)) throw Object.assign(new Error(`invalid_${label}`), { status: 400 });
  return result;
};
const atomicWrite = (target, content) => {
  mkdirSync(path.dirname(target), { recursive: true });
  const temp = `${target}.${randomBytes(6).toString('hex')}.tmp`;
  writeFileSync(temp, content, { encoding: 'utf8', flag: 'wx' });
  renameSync(temp, target);
};
const audit = (eventType, objectId, payload = {}) => {
  const previous = db.prepare('SELECT event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1').get()?.event_hash || 'GENESIS';
  const eventId = id('audit'); const stamp = now(); const payloadJson = JSON.stringify(payload);
  const eventHash = sha256(`${previous}|${eventId}|${eventType}|${objectId || ''}|${payloadJson}|${stamp}`);
  db.prepare('INSERT INTO audit_events(event_id,event_type,object_id,payload_json,previous_hash,event_hash,created_at) VALUES(?,?,?,?,?,?,?)').run(eventId, eventType, objectId || null, payloadJson, previous, eventHash, stamp);
};
const verifyPassword = (password) => {
  const parts = operatorPasswordHash.split('$');
  if (parts.length !== 4 || parts[0] !== 'pbkdf2_sha256') return false;
  const expected = Buffer.from(parts[3], 'base64');
  const actual = pbkdf2Sync(password, Buffer.from(parts[2], 'base64'), Number(parts[1]), expected.length, 'sha256');
  return expected.length === actual.length && timingSafeEqual(expected, actual);
};
const encryptionKey = createHash('sha256').update(encryptionSecret).digest();
const encrypt = (value) => {
  const iv = randomBytes(12); const cipher = createCipheriv('aes-256-gcm', encryptionKey, iv);
  const encrypted = Buffer.concat([cipher.update(JSON.stringify(value), 'utf8'), cipher.final()]);
  return { ciphertext: encrypted.toString('base64'), iv: iv.toString('base64'), auth_tag: cipher.getAuthTag().toString('base64') };
};

const readBody = (req, max = 2 * 1024 * 1024) => new Promise((resolve, reject) => {
  const chunks = []; let size = 0;
  req.on('data', (chunk) => {
    size += chunk.length;
    if (size > max) { reject(Object.assign(new Error('body_too_large'), { status: 413 })); req.destroy(); return; }
    chunks.push(chunk);
  });
  req.on('end', () => { try { resolve(chunks.length ? JSON.parse(Buffer.concat(chunks).toString('utf8')) : {}); } catch { reject(Object.assign(new Error('invalid_json'), { status: 400 })); } });
  req.on('error', reject);
});
const cookies = (req) => Object.fromEntries(String(req.headers.cookie || '').split(';').map((item) => item.trim()).filter(Boolean).map((item) => { const i = item.indexOf('='); return [item.slice(0, i), decodeURIComponent(item.slice(i + 1))]; }));
const session = (req) => {
  const token = cookies(req).ajans_admin_session;
  if (!token) return null;
  const row = db.prepare('SELECT * FROM sessions WHERE session_hash=? AND revoked_at IS NULL AND expires_at>?').get(sha256(token), now());
  return row ? { row, token } : null;
};
const requireSession = (req, res, csrf = false) => {
  const active = session(req);
  if (!active) { sendJson(res, 401, { error: 'login_required' }); return null; }
  if (csrf && !safeEqual(active.row.csrf_hash, sha256(req.headers['x-csrf-token'] || ''))) { sendJson(res, 403, { error: 'csrf_invalid' }); return null; }
  return active;
};
const rateLimit = (key) => {
  const stamp = Date.now(); const current = db.prepare('SELECT * FROM login_limits WHERE key=?').get(key);
  if (!current || stamp - Date.parse(current.window_start) > 15 * 60 * 1000) { db.prepare('INSERT OR REPLACE INTO login_limits(key,window_start,count) VALUES(?,?,1)').run(key, now()); return true; }
  if (current.count >= 6) return false;
  db.prepare('UPDATE login_limits SET count=count+1 WHERE key=?').run(key); return true;
};
const sendJson = (res, status, value, extra = {}) => {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'no-referrer', ...extra });
  res.end(JSON.stringify(value));
};
const sourceContent = (resource) => {
  const target = path.resolve(workspaceRoot, resource.source);
  if (!target.startsWith(`${workspaceRoot}${path.sep}`) || !existsSync(target)) return '';
  return readFileSync(target, 'utf8');
};
const currentResource = (resource) => {
  const active = db.prepare("SELECT * FROM resource_versions WHERE category=? AND resource_key=? AND status='active' ORDER BY version_no DESC LIMIT 1").get(resource.category, resource.key);
  const baseline = sourceContent(resource);
  return active ? { content: active.content, version_id: active.version_id, version_no: active.version_no, status: 'active', content_hash: active.content_hash, source_hash: active.source_hash, created_at: active.created_at }
    : { content: baseline, version_id: null, version_no: 0, status: 'baseline', content_hash: sha256(baseline), source_hash: sha256(baseline), created_at: null };
};
const resourceSummary = (resource) => {
  const current = currentResource(resource);
  const versions = db.prepare('SELECT COUNT(*) count FROM resource_versions WHERE category=? AND resource_key=?').get(resource.category, resource.key).count;
  return { ...resource, current: { ...current, content: undefined }, version_count: versions, baseline_changed: current.source_hash !== sha256(sourceContent(resource)) };
};
const serviceHealth = async () => {
  const checks = [
    ['n8n', 'http://n8n:5678/healthz'],
    ['ajans_merkezi', 'http://ajans-merkezi:5680/api/health'],
    ['runtime', 'http://ajans-runtime:5681/health/live']
  ];
  const entries = await Promise.all(checks.map(async ([name, url]) => { try { const result = await fetch(url, { signal: AbortSignal.timeout(1800) }); return [name, result.ok ? 'healthy' : 'warning']; } catch { return [name, 'offline']; } }));
  return Object.fromEntries(entries);
};
const publicConfig = (app) => {
  const config = json(app.config_json, {});
  return { app_id: app.app_id, slug: app.slug, name: app.name, brand_name: app.brand_name, status: app.status, theme: config.theme || {}, features: config.features || [], generated_at: app.updated_at, no_ai_calls_from_admin: true };
};
const defaultStudioSettings = {
  model_assignments: {
    roles: [
      { role_id: 'analysis', name: 'Marka Analizi', mode: 'auto', provider: '', model: '' },
      { role_id: 'content', name: 'İçerik Üretimi', mode: 'auto', provider: '', model: '' },
      { role_id: 'visual', name: 'Görsel Üretimi', mode: 'auto', provider: '', model: '' },
      { role_id: 'debate', name: 'Kalite Kontrolü', mode: 'auto', provider: '', model: '' },
      { role_id: 'ordinaryus', name: 'Son Karar', mode: 'auto', provider: '', model: '' },
      { role_id: 'interface', name: 'Kullanıcı Asistanı', mode: 'auto', provider: '', model: '' }
    ],
    principle: 'Gerekli kaliteyi sağlayan en ucuz ve hızlı model.'
  },
  flow_design: {
    stages: [
      { id: 'analysis', name: 'Analiz', enabled: true },
      { id: 'content', name: 'İçerik', enabled: true },
      { id: 'visual', name: 'Görsel', enabled: true },
      { id: 'debate', name: 'Kalite kontrolü', enabled: true },
      { id: 'ordinaryus', name: 'Son karar', enabled: true },
      { id: 'approval', name: 'Kullanıcı onayı', enabled: true }
    ],
    normal_debate_rounds: 3,
    critical_debate_rounds: 4,
    final_publish_approval_required: true,
    external_publish_enabled: false
  }
};
const studioSettings = () => Object.fromEntries(Object.entries(defaultStudioSettings).map(([key, fallback]) => [key, json(db.prepare('SELECT value_json FROM studio_settings WHERE setting_key=?').get(key)?.value_json, fallback)]));

const mime = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8' };
const sendFile = (res, file) => {
  const body = readFileSync(file);
  res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-cache', 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'no-referrer', 'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'" });
  res.end(body);
};

const server = createServer(async (req, res) => {
  const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
  try {
    if (url.pathname === '/api/health' && req.method === 'GET') { sendJson(res, 200, { status: 'ok', ai_calls_enabled: false }); return; }
    if (url.pathname === '/api/login' && req.method === 'POST') {
      const ip = req.socket.remoteAddress || 'unknown';
      if (!rateLimit(`login:${ip}`)) { sendJson(res, 429, { error: 'too_many_attempts' }); return; }
      const body = await readBody(req);
      if (!verifyPassword(String(body.password || ''))) { audit('login_failed', null, { ip_hash: sha256(ip) }); sendJson(res, 401, { error: 'invalid_password' }); return; }
      const token = randomBytes(32).toString('base64url'); const csrf = randomBytes(32).toString('base64url'); const stamp = now(); const expires = new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString();
      db.prepare('INSERT INTO sessions(session_hash,csrf_hash,created_at,expires_at) VALUES(?,?,?,?)').run(sha256(token), sha256(csrf), stamp, expires);
      audit('login_success', 'admin');
      sendJson(res, 200, { status: 'authenticated', csrf_token: csrf, expires_at: expires }, { 'Set-Cookie': `ajans_admin_session=${encodeURIComponent(token)}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800` }); return;
    }
    if (url.pathname === '/api/logout' && req.method === 'POST') {
      const active = requireSession(req, res, true); if (!active) return;
      db.prepare('UPDATE sessions SET revoked_at=? WHERE session_hash=?').run(now(), active.row.session_hash); audit('logout', 'admin');
      sendJson(res, 200, { status: 'logged_out' }, { 'Set-Cookie': 'ajans_admin_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0' }); return;
    }
    if (url.pathname === '/api/state' && req.method === 'GET') {
      if (!requireSession(req, res)) return;
      const grouped = Object.fromEntries(['agent', 'model', 'flow', 'policy'].map((category) => [category, resources.filter((item) => item.category === category).map(resourceSummary)]));
      const connections = providers.map((provider) => { const row = db.prepare('SELECT provider,label,metadata_json,status,created_at,updated_at FROM connections WHERE provider=?').get(provider.id); return { ...provider, configured: Boolean(row), label: row?.label || provider.name, metadata: json(row?.metadata_json, {}), status: row?.status || 'not_configured', created_at: row?.created_at || null, updated_at: row?.updated_at || null }; });
      const apps = db.prepare('SELECT * FROM app_instances ORDER BY updated_at DESC').all().map(publicConfig);
      const drafts = db.prepare("SELECT COUNT(*) count FROM resource_versions WHERE status='draft'").get().count;
      const active = db.prepare("SELECT COUNT(*) count FROM resource_versions WHERE status='active'").get().count;
      const auditTail = db.prepare('SELECT sequence,event_type,object_id,created_at FROM audit_events ORDER BY sequence DESC LIMIT 20').all();
      sendJson(res, 200, { generated_at: now(), ai_calls_enabled: false, resources: grouped, settings: studioSettings(), connections, apps, stats: { agents: grouped.agent.length, active_revisions: active, drafts, apps: apps.length, configured_connections: connections.filter((item) => item.configured).length }, services: await serviceHealth(), audit: auditTail }); return;
    }
    const settingsRoute = url.pathname.match(/^\/api\/settings\/(model_assignments|flow_design)$/);
    if (settingsRoute && req.method === 'PUT') {
      if (!requireSession(req, res, true)) return;
      const body = await readBody(req); const key = settingsRoute[1]; let value;
      if (key === 'model_assignments') {
        const allowedRoles = new Map(defaultStudioSettings.model_assignments.roles.map((item) => [item.role_id, item.name]));
        const roles = Array.isArray(body.value?.roles) ? body.value.roles : [];
        if (roles.length !== allowedRoles.size || roles.some((item) => !allowedRoles.has(item.role_id) || !['auto', 'manual'].includes(item.mode) || (item.mode === 'manual' && (!String(item.provider || '').trim() || !String(item.model || '').trim())))) { sendJson(res, 400, { error: 'invalid_model_assignments' }); return; }
        value = { roles: roles.map((item) => ({ role_id: item.role_id, name: allowedRoles.get(item.role_id), mode: item.mode, provider: item.mode === 'manual' ? String(item.provider).trim().slice(0, 80) : '', model: item.mode === 'manual' ? String(item.model).trim().slice(0, 160) : '' })), principle: defaultStudioSettings.model_assignments.principle };
      } else {
        const allowedStages = new Map(defaultStudioSettings.flow_design.stages.map((item) => [item.id, item.name]));
        const stages = Array.isArray(body.value?.stages) ? body.value.stages : [];
        const normal = Number(body.value?.normal_debate_rounds); const critical = Number(body.value?.critical_debate_rounds);
        if (stages.length !== allowedStages.size || stages.some((item) => !allowedStages.has(item.id)) || !Number.isInteger(normal) || normal < 1 || normal > 6 || !Number.isInteger(critical) || critical < normal || critical > 8) { sendJson(res, 400, { error: 'invalid_flow_design' }); return; }
        value = { stages: stages.map((item) => ({ id: item.id, name: allowedStages.get(item.id), enabled: item.id === 'approval' ? true : item.enabled === true })), normal_debate_rounds: normal, critical_debate_rounds: critical, final_publish_approval_required: true, external_publish_enabled: false };
      }
      const stamp = now();
      db.prepare(`INSERT INTO studio_settings(setting_key,value_json,updated_at) VALUES(?,?,?) ON CONFLICT(setting_key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at`).run(key, JSON.stringify(value), stamp);
      audit('studio_setting_saved', key, { value_hash: sha256(JSON.stringify(value)), immutable_safety: key === 'flow_design' ? { final_publish_approval_required: true, external_publish_enabled: false } : undefined });
      sendJson(res, 200, { status: 'saved', key, value, updated_at: stamp }); return;
    }
    const resourceRoute = url.pathname.match(/^\/api\/resources\/(agent|model|flow|policy)\/([a-z0-9-]+)$/);
    if (resourceRoute && req.method === 'GET') {
      if (!requireSession(req, res)) return;
      const resource = resourceMap.get(`${resourceRoute[1]}:${resourceRoute[2]}`);
      if (!resource) { sendJson(res, 404, { error: 'resource_not_found' }); return; }
      const versions = db.prepare('SELECT version_id,version_no,status,note,content_hash,source_hash,created_at FROM resource_versions WHERE category=? AND resource_key=? ORDER BY version_no DESC LIMIT 50').all(resource.category, resource.key);
      sendJson(res, 200, { resource, current: currentResource(resource), versions, baseline: { content: sourceContent(resource), content_hash: sha256(sourceContent(resource)) } }); return;
    }
    if (resourceRoute && req.method === 'PUT') {
      if (!requireSession(req, res, true)) return;
      const resource = resourceMap.get(`${resourceRoute[1]}:${resourceRoute[2]}`);
      if (!resource) { sendJson(res, 404, { error: 'resource_not_found' }); return; }
      const body = await readBody(req); const content = String(body.content || '');
      if (!content.trim() || content.length > 250000) { sendJson(res, 400, { error: 'invalid_content' }); return; }
      if (resource.format === 'json' && json(content) === null) { sendJson(res, 400, { error: 'invalid_json' }); return; }
      const next = Number(db.prepare('SELECT COALESCE(MAX(version_no),0)+1 next FROM resource_versions WHERE category=? AND resource_key=?').get(resource.category, resource.key).next);
      const versionId = id('version'); const status = body.activate === true ? 'active' : 'draft'; const stamp = now();
      db.exec('BEGIN IMMEDIATE');
      try {
        if (status === 'active') db.prepare("UPDATE resource_versions SET status='archived' WHERE category=? AND resource_key=? AND status='active'").run(resource.category, resource.key);
        db.prepare('INSERT INTO resource_versions(version_id,resource_key,category,version_no,content,content_hash,source_hash,status,note,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)').run(versionId, resource.key, resource.category, next, content, sha256(content), sha256(sourceContent(resource)), status, String(body.note || '').slice(0, 500), stamp);
        audit('resource_version_saved', `${resource.category}:${resource.key}`, { version_id: versionId, version_no: next, status, content_hash: sha256(content) });
        db.exec('COMMIT');
      } catch (error) { db.exec('ROLLBACK'); throw error; }
      sendJson(res, 201, { status, version_id: versionId, version_no: next, content_hash: sha256(content) }); return;
    }
    const rollbackRoute = url.pathname.match(/^\/api\/resources\/(agent|model|flow|policy)\/([a-z0-9-]+)\/rollback$/);
    if (rollbackRoute && req.method === 'POST') {
      if (!requireSession(req, res, true)) return;
      const resource = resourceMap.get(`${rollbackRoute[1]}:${rollbackRoute[2]}`); const body = await readBody(req);
      const old = resource && db.prepare('SELECT * FROM resource_versions WHERE version_id=? AND category=? AND resource_key=?').get(String(body.version_id || ''), resource.category, resource.key);
      if (!old) { sendJson(res, 404, { error: 'version_not_found' }); return; }
      const next = Number(db.prepare('SELECT COALESCE(MAX(version_no),0)+1 next FROM resource_versions WHERE category=? AND resource_key=?').get(resource.category, resource.key).next); const versionId = id('version'); const stamp = now();
      db.exec('BEGIN IMMEDIATE');
      try {
        db.prepare("UPDATE resource_versions SET status='archived' WHERE category=? AND resource_key=? AND status='active'").run(resource.category, resource.key);
        db.prepare("INSERT INTO resource_versions(version_id,resource_key,category,version_no,content,content_hash,source_hash,status,note,created_at) VALUES(?,?,?,?,?,?,?,'active',?,?)").run(versionId, resource.key, resource.category, next, old.content, old.content_hash, sha256(sourceContent(resource)), `Geri dönüş: v${old.version_no}`, stamp);
        audit('resource_rollback', `${resource.category}:${resource.key}`, { from_version_id: old.version_id, new_version_id: versionId, new_version_no: next }); db.exec('COMMIT');
      } catch (error) { db.exec('ROLLBACK'); throw error; }
      sendJson(res, 200, { status: 'active', version_id: versionId, version_no: next }); return;
    }
    const connectionRoute = url.pathname.match(/^\/api\/connections\/([a-z0-9_-]+)$/);
    if (connectionRoute && req.method === 'PUT') {
      if (!requireSession(req, res, true)) return;
      const provider = providerMap.get(connectionRoute[1]); if (!provider) { sendJson(res, 404, { error: 'provider_not_found' }); return; }
      const body = await readBody(req); const secret = body.secret && typeof body.secret === 'object' ? body.secret : {};
      if (!Object.keys(secret).length || JSON.stringify(secret).length > 30000) { sendJson(res, 400, { error: 'secret_required' }); return; }
      const sealed = encrypt(secret); const stamp = now(); const metadata = body.metadata && typeof body.metadata === 'object' ? body.metadata : {};
      db.prepare(`INSERT INTO connections(provider,label,metadata_json,ciphertext,iv,auth_tag,status,created_at,updated_at) VALUES(?,?,?,?,?,?,'saved_unverified',?,?)
        ON CONFLICT(provider) DO UPDATE SET label=excluded.label,metadata_json=excluded.metadata_json,ciphertext=excluded.ciphertext,iv=excluded.iv,auth_tag=excluded.auth_tag,status='saved_unverified',updated_at=excluded.updated_at`).run(provider.id, String(body.label || provider.name).slice(0, 120), JSON.stringify(metadata), sealed.ciphertext, sealed.iv, sealed.auth_tag, stamp, stamp);
      audit('connection_saved', provider.id, { fields: Object.keys(secret).map((key) => sha256(key).slice(0, 10)), secret_returned: false });
      sendJson(res, 200, { provider: provider.id, configured: true, status: 'saved_unverified', secret_returned: false }); return;
    }
    if (url.pathname === '/api/apps' && req.method === 'POST') {
      if (!requireSession(req, res, true)) return;
      const body = await readBody(req); const slug = safeSlug(body.slug, 'app_slug'); const name = String(body.name || '').trim().slice(0, 120); const brandName = String(body.brand_name || '').trim().slice(0, 120);
      if (!name || !brandName) { sendJson(res, 400, { error: 'name_and_brand_required' }); return; }
      const existing = db.prepare('SELECT * FROM app_instances WHERE slug=?').get(slug); const stamp = now(); const appId = existing?.app_id || id('app'); const generationNo = Number(existing?.generation_no || 0) + 1;
      const activeResources = resources.map((resource) => { const current = currentResource(resource); return { category: resource.category, key: resource.key, version_id: current.version_id, version_no: current.version_no, content_hash: current.content_hash }; });
      const config = { schema_version: '1.0', app_id: appId, slug, name, brand_name: brandName, description: String(body.description || '').slice(0, 1000), theme: { accent: /^#[0-9a-f]{6}$/i.test(body.accent) ? body.accent : '#8b5cf6' }, features: Array.isArray(body.features) ? body.features.filter((item) => ['brand','content','visuals','workflow','approvals','calendar','connections','models'].includes(item)).slice(0, 12) : ['brand','content','visuals','workflow','approvals'], resources: activeResources, studio_settings: studioSettings(), connection_requirements: Array.isArray(body.connection_requirements) ? body.connection_requirements.filter((item) => providerMap.has(item)) : [], generation_no: generationNo, generated_at: stamp, proprietary_logic_visible_to_client: false, publish_requires_explicit_approval: true };
      db.prepare(`INSERT INTO app_instances(app_id,slug,name,brand_name,status,config_json,generation_no,created_at,updated_at) VALUES(?,?,?,?,'generated',?,?,?,?)
        ON CONFLICT(slug) DO UPDATE SET name=excluded.name,brand_name=excluded.brand_name,status='generated',config_json=excluded.config_json,generation_no=excluded.generation_no,updated_at=excluded.updated_at`).run(appId, slug, name, brandName, JSON.stringify(config), generationNo, existing?.created_at || stamp, stamp);
      const appDir = path.resolve(appsRoot, slug); if (!appDir.startsWith(`${appsRoot}${path.sep}`)) throw Object.assign(new Error('invalid_app_path'), { status: 400 });
      atomicWrite(path.join(appDir, 'manifest.json'), `${JSON.stringify({ ...config, resources: activeResources.map(({ content_hash, ...rest }) => ({ ...rest, integrity: content_hash })) }, null, 2)}\n`);
      audit('client_app_generated', appId, { slug, generation_no: generationNo, resource_count: activeResources.length });
      const row = db.prepare('SELECT * FROM app_instances WHERE app_id=?').get(appId); sendJson(res, existing ? 200 : 201, { app: publicConfig(row), preview_url: `/client/${encodeURIComponent(slug)}` }); return;
    }
    const clientConfigRoute = url.pathname.match(/^\/client-api\/([a-z0-9-]+)\/config$/);
    if (clientConfigRoute && req.method === 'GET') {
      const app = db.prepare("SELECT * FROM app_instances WHERE slug=? AND status='generated'").get(clientConfigRoute[1]);
      if (!app) { sendJson(res, 404, { error: 'app_not_found' }); return; }
      sendJson(res, 200, publicConfig(app)); return;
    }
    const clientRoute = url.pathname.match(/^\/client\/([a-z0-9-]+)$/);
    if (clientRoute && req.method === 'GET') {
      const app = db.prepare("SELECT app_id FROM app_instances WHERE slug=? AND status='generated'").get(clientRoute[1]);
      if (!app) { sendJson(res, 404, { error: 'app_not_found' }); return; }
      sendFile(res, path.join(publicRoot, 'client.html')); return;
    }
    if (req.method !== 'GET') { sendJson(res, 405, { error: 'unsupported_method' }); return; }
    const requested = url.pathname === '/' ? 'index.html' : url.pathname.slice(1); const target = path.resolve(publicRoot, path.normalize(requested).replace(/^(\.\.(\/|\\|$))+/, ''));
    if (!target.startsWith(`${publicRoot}${path.sep}`)) { sendJson(res, 403, { error: 'forbidden' }); return; }
    if (!existsSync(target)) { sendJson(res, 404, { error: 'not_found' }); return; }
    sendFile(res, target);
  } catch (error) {
    sendJson(res, Number(error.status || 500), { error: Number(error.status || 500) >= 500 ? 'internal_error' : error.message });
  }
});

server.listen(port, host, () => process.stdout.write(`Ajans Kurucu http://${host}:${port}\n`));
