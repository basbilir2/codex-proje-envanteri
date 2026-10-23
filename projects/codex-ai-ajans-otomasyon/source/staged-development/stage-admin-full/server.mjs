import { createServer } from 'node:http';
import { createCipheriv, createHash, randomBytes, timingSafeEqual, pbkdf2Sync } from 'node:crypto';
import { DatabaseSync } from 'node:sqlite';
import { existsSync, mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync } from 'node:fs';
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
const workflowRoot = path.join(workspaceRoot, 'workflows');
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
  CREATE TABLE IF NOT EXISTS agent_definitions(
    agent_id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
    role TEXT NOT NULL, instructions TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0, token_profile TEXT NOT NULL DEFAULT 'medium',
    token_limit INTEGER NOT NULL DEFAULT 1800, model_mode TEXT NOT NULL DEFAULT 'auto',
    provider TEXT NOT NULL DEFAULT '', model TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_agent_definitions_order ON agent_definitions(enabled DESC, sort_order, name);
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

const credentialKey = /^(credentials?|api[_-]?keys?|access[_-]?tokens?|api[_-]?tokens?|app[_-]?secrets?|passwords?|client[_-]?secrets?|authorization)$/i;
const sanitizeWorkflowValue = (value, key = '') => {
  if (credentialKey.test(key)) return '__RUNTIME_CREDENTIAL__';
  if (Array.isArray(value)) return value.map((item) => sanitizeWorkflowValue(item));
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.entries(value).filter(([childKey]) => childKey !== 'credentials').map(([childKey, child]) => [childKey, sanitizeWorkflowValue(child, childKey)]));
};
const workflowBundle = () => {
  if (!existsSync(workflowRoot)) return [];
  return readdirSync(workflowRoot, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith('.json'))
    .sort((a, b) => a.name.localeCompare(b.name, 'tr'))
    .slice(0, 200)
    .map((entry) => {
      const source = readFileSync(path.join(workflowRoot, entry.name), 'utf8');
      if (source.length > 2 * 1024 * 1024) throw Object.assign(new Error('workflow_template_too_large'), { status: 500 });
      const parsed = json(source);
      if (!parsed || typeof parsed !== 'object' || !Array.isArray(parsed.nodes)) throw Object.assign(new Error('invalid_workflow_template'), { status: 500 });
      const workflow = sanitizeWorkflowValue(parsed);
      workflow.active = false;
      delete workflow.id;
      delete workflow.versionId;
      delete workflow.pinData;
      delete workflow.staticData;
      delete workflow.shared;
      workflow.nodes = workflow.nodes.map((node) => {
        const clean = { ...node };
        delete clean.credentials;
        delete clean.webhookId;
        return clean;
      });
      return {
        filename: entry.name,
        name: String(workflow.name || entry.name.replace(/\.json$/i, '')).slice(0, 180),
        source_sha256: sha256(source),
        active: false,
        activation_policy: 'signed_runtime_only',
        test_or_canary: /(?:test|canary)/i.test(entry.name) || /(?:TEST|CANARY)/i.test(String(workflow.name || '')),
        workflow
      };
    });
};

const seedAgentDefinitions = () => {
  const count = Number(db.prepare('SELECT COUNT(*) count FROM agent_definitions').get().count);
  if (count) return;
  const stamp = now();
  const insert = db.prepare('INSERT INTO agent_definitions(agent_id,slug,name,role,instructions,enabled,sort_order,token_profile,token_limit,model_mode,provider,model,created_at,updated_at) VALUES(?,?,?,?,?,1,?,?,?,?,?,?,?,?)');
  resources.filter((item) => item.category === 'agent').forEach((resource, index) => {
    insert.run(id('agent'), resource.key, resource.name, resource.description, sourceContent(resource), index + 1, index < 2 ? 'high' : 'medium', index < 2 ? 4000 : 1800, 'auto', '', '', stamp, stamp);
  });
};

const agentRows = () => db.prepare('SELECT agent_id,slug,name,role,instructions,enabled,sort_order,token_profile,token_limit,model_mode,provider,model,created_at,updated_at FROM agent_definitions ORDER BY enabled DESC,sort_order,name').all().map((row) => ({ ...row, enabled: Boolean(row.enabled) }));
const tokenProfiles = { low: 800, medium: 1800, high: 4000, custom: null };
const cleanAgent = (body, existing = {}) => {
  const name = String(body.name ?? existing.name ?? '').trim().slice(0, 120);
  const slug = safeSlug(body.slug ?? existing.slug ?? '', 'agent_slug');
  const role = String(body.role ?? existing.role ?? '').trim().slice(0, 1000);
  const instructions = String(body.instructions ?? existing.instructions ?? '').trim().slice(0, 120000);
  const tokenProfile = String(body.token_profile ?? existing.token_profile ?? 'medium');
  const modelMode = String(body.model_mode ?? existing.model_mode ?? 'auto');
  const tokenLimit = Number(body.token_limit ?? existing.token_limit ?? tokenProfiles[tokenProfile] ?? 1800);
  if (!name || !role || !instructions || !Object.hasOwn(tokenProfiles, tokenProfile) || !['auto', 'manual'].includes(modelMode) || !Number.isInteger(tokenLimit) || tokenLimit < 128 || tokenLimit > 32000) throw Object.assign(new Error('invalid_agent_definition'), { status: 400 });
  const provider = modelMode === 'manual' ? String(body.provider ?? existing.provider ?? '').trim().slice(0, 80) : '';
  const model = modelMode === 'manual' ? String(body.model ?? existing.model ?? '').trim().slice(0, 160) : '';
  if (modelMode === 'manual' && (!provider || !model)) throw Object.assign(new Error('manual_model_required'), { status: 400 });
  return { slug, name, role, instructions, enabled: body.enabled === undefined ? Boolean(existing.enabled ?? true) : body.enabled === true, sort_order: Math.max(0, Math.min(999, Number(body.sort_order ?? existing.sort_order ?? 0) || 0)), token_profile: tokenProfile, token_limit: tokenLimit, model_mode: modelMode, provider, model };
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
  return { app_id: app.app_id, slug: app.slug, name: app.name, brand_name: app.brand_name, status: app.status, description: config.description || '', theme: config.theme || {}, features: config.features || [], plan: config.plan ? { id: config.plan.id, name: config.plan.name, limits: config.plan.limits } : null, agent_names: Array.isArray(config.agents) ? config.agents.map((agent) => ({ slug: agent.slug, name: agent.name, template_name: agent.template_name || agent.name })) : [], connection_policy: config.connection_policy || {}, assistant_chat: config.assistant_chat || {}, operating_modes: config.operating_modes || {}, runtime_engine: config.runtime_engine ? { type: config.runtime_engine.type, bundled: config.runtime_engine.bundled, user_account_required: false, user_interface_exposed: false, workflow_editor_exposed: false } : null, generation_no: app.generation_no, generated_at: app.updated_at, no_ai_calls_from_admin: true };
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
  },
  token_policy: {
    profiles: { low: 800, medium: 1800, high: 4000 },
    default_profile: 'medium',
    per_task_limit: 18000,
    daily_limit: 120000,
    monthly_limit: 2500000,
    maximum_calls_per_task: 24,
    maximum_retries: 2,
    stop_when_limit_reached: true
  },
  flow_blueprints: {
    active_flow_id: 'default-flow',
    flows: [{ flow_id: 'default-flow', name: 'Varsayılan yaşayan ajans akışı', enabled: true, algorithm: 'sequential_debate', agent_slugs: resources.filter((item) => item.category === 'agent').map((item) => item.key), normal_rounds: 3, critical_rounds: 4 }]
  },
  plan_templates: {
    basic: { name: 'Basic', max_enabled_agents: 11, model_selection: 'automatic_only', api_control_default: 'locked', monthly_token_limit: 300000, debate_rounds: 1, custom_flows: false, advanced_memory: false },
    plus: { name: 'Plus', max_enabled_agents: 25, model_selection: 'guided', api_control_default: 'guided', monthly_token_limit: 1200000, debate_rounds: 2, custom_flows: true, advanced_memory: false },
    pro: { name: 'Pro', max_enabled_agents: 100, model_selection: 'full', api_control_default: 'open', monthly_token_limit: 5000000, debate_rounds: 4, custom_flows: true, advanced_memory: true }
  }
};
const studioSettings = () => Object.fromEntries(Object.entries(defaultStudioSettings).map(([key, fallback]) => [key, json(db.prepare('SELECT value_json FROM studio_settings WHERE setting_key=?').get(key)?.value_json, fallback)]));
seedAgentDefinitions();

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
      const agents = agentRows();
      const apps = db.prepare('SELECT * FROM app_instances ORDER BY updated_at DESC').all().map(publicConfig);
      const drafts = db.prepare("SELECT COUNT(*) count FROM resource_versions WHERE status='draft'").get().count;
      const active = db.prepare("SELECT COUNT(*) count FROM resource_versions WHERE status='active'").get().count;
      const auditTail = db.prepare('SELECT sequence,event_type,object_id,created_at FROM audit_events ORDER BY sequence DESC LIMIT 20').all();
      sendJson(res, 200, { generated_at: now(), ai_calls_enabled: false, offline_creator: true, resources: grouped, agent_library: agents, settings: studioSettings(), apps, stats: { agents: agents.length, enabled_agents: agents.filter((item) => item.enabled).length, active_revisions: active, drafts, apps: apps.length }, services: await serviceHealth(), audit: auditTail }); return;
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
    if (url.pathname === '/api/settings/token_policy' && req.method === 'PUT') {
      if (!requireSession(req, res, true)) return;
      const body = await readBody(req); const source = body.value || {};
      const value = {
        profiles: { low: 800, medium: 1800, high: 4000 },
        default_profile: ['low', 'medium', 'high'].includes(source.default_profile) ? source.default_profile : 'medium',
        per_task_limit: Number(source.per_task_limit), daily_limit: Number(source.daily_limit), monthly_limit: Number(source.monthly_limit),
        maximum_calls_per_task: Number(source.maximum_calls_per_task), maximum_retries: Number(source.maximum_retries), stop_when_limit_reached: true
      };
      if (![value.per_task_limit, value.daily_limit, value.monthly_limit, value.maximum_calls_per_task, value.maximum_retries].every(Number.isInteger) || value.per_task_limit < 1000 || value.daily_limit < value.per_task_limit || value.monthly_limit < value.daily_limit || value.maximum_calls_per_task < 1 || value.maximum_calls_per_task > 100 || value.maximum_retries < 0 || value.maximum_retries > 5) { sendJson(res, 400, { error: 'invalid_token_policy' }); return; }
      const stamp = now(); db.prepare(`INSERT INTO studio_settings(setting_key,value_json,updated_at) VALUES('token_policy',?,?) ON CONFLICT(setting_key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at`).run(JSON.stringify(value), stamp);
      audit('token_policy_saved', 'token_policy', { per_task_limit: value.per_task_limit, daily_limit: value.daily_limit, monthly_limit: value.monthly_limit });
      sendJson(res, 200, { status: 'saved', value, updated_at: stamp }); return;
    }
    if (url.pathname === '/api/settings/flow_blueprints' && req.method === 'PUT') {
      if (!requireSession(req, res, true)) return;
      const body = await readBody(req); const source = body.value || {}; const flows = Array.isArray(source.flows) ? source.flows : [];
      const knownAgents = new Set(agentRows().map((item) => item.slug));
      if (!flows.length || flows.length > 50) { sendJson(res, 400, { error: 'invalid_flow_blueprints' }); return; }
      const cleanFlows = flows.map((flow, index) => {
        const flowId = safeSlug(flow.flow_id || `flow-${index + 1}`, 'flow_id'); const name = String(flow.name || '').trim().slice(0, 120);
        const agentSlugs = [...new Set((Array.isArray(flow.agent_slugs) ? flow.agent_slugs : []).filter((slug) => knownAgents.has(slug)))].slice(0, 100);
        const normal = Number(flow.normal_rounds); const critical = Number(flow.critical_rounds);
        if (!name || !agentSlugs.length || !['sequential', 'sequential_debate', 'parallel_panel', 'custom'].includes(flow.algorithm) || !Number.isInteger(normal) || normal < 1 || normal > 6 || !Number.isInteger(critical) || critical < normal || critical > 8) throw Object.assign(new Error('invalid_flow_blueprints'), { status: 400 });
        return { flow_id: flowId, name, enabled: flow.enabled !== false, algorithm: flow.algorithm, agent_slugs: agentSlugs, normal_rounds: normal, critical_rounds: critical };
      });
      const activeFlowId = cleanFlows.some((flow) => flow.flow_id === source.active_flow_id) ? source.active_flow_id : cleanFlows[0].flow_id;
      const value = { active_flow_id: activeFlowId, flows: cleanFlows };
      const stamp = now(); db.prepare(`INSERT INTO studio_settings(setting_key,value_json,updated_at) VALUES('flow_blueprints',?,?) ON CONFLICT(setting_key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at`).run(JSON.stringify(value), stamp);
      audit('flow_blueprints_saved', activeFlowId, { flow_count: cleanFlows.length }); sendJson(res, 200, { status: 'saved', value, updated_at: stamp }); return;
    }
    if (url.pathname === '/api/agents' && req.method === 'POST') {
      if (!requireSession(req, res, true)) return;
      const body = await readBody(req); const agent = cleanAgent(body); const agentId = id('agent'); const stamp = now();
      db.prepare('INSERT INTO agent_definitions(agent_id,slug,name,role,instructions,enabled,sort_order,token_profile,token_limit,model_mode,provider,model,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)').run(agentId, agent.slug, agent.name, agent.role, agent.instructions, agent.enabled ? 1 : 0, agent.sort_order, agent.token_profile, agent.token_limit, agent.model_mode, agent.provider, agent.model, stamp, stamp);
      audit('agent_created', agentId, { slug: agent.slug, enabled: agent.enabled }); sendJson(res, 201, { ...agent, agent_id: agentId, created_at: stamp, updated_at: stamp }); return;
    }
    const agentRoute = url.pathname.match(/^\/api\/agents\/([a-zA-Z0-9_-]+)$/);
    if (agentRoute && req.method === 'PUT') {
      if (!requireSession(req, res, true)) return;
      const existing = db.prepare('SELECT * FROM agent_definitions WHERE agent_id=?').get(agentRoute[1]); if (!existing) { sendJson(res, 404, { error: 'agent_not_found' }); return; }
      const agent = cleanAgent(await readBody(req), { ...existing, enabled: Boolean(existing.enabled) }); const stamp = now();
      db.prepare('UPDATE agent_definitions SET slug=?,name=?,role=?,instructions=?,enabled=?,sort_order=?,token_profile=?,token_limit=?,model_mode=?,provider=?,model=?,updated_at=? WHERE agent_id=?').run(agent.slug, agent.name, agent.role, agent.instructions, agent.enabled ? 1 : 0, agent.sort_order, agent.token_profile, agent.token_limit, agent.model_mode, agent.provider, agent.model, stamp, existing.agent_id);
      audit('agent_updated', existing.agent_id, { slug: agent.slug, enabled: agent.enabled, token_limit: agent.token_limit }); sendJson(res, 200, { ...agent, agent_id: existing.agent_id, updated_at: stamp }); return;
    }
    const cloneAgentRoute = url.pathname.match(/^\/api\/agents\/([a-zA-Z0-9_-]+)\/clone$/);
    if (cloneAgentRoute && req.method === 'POST') {
      if (!requireSession(req, res, true)) return;
      const existing = db.prepare('SELECT * FROM agent_definitions WHERE agent_id=?').get(cloneAgentRoute[1]); if (!existing) { sendJson(res, 404, { error: 'agent_not_found' }); return; }
      const stamp = now(); const agentId = id('agent'); const suffix = randomBytes(3).toString('hex'); const slug = `${existing.slug.slice(0, 54)}-${suffix}`;
      db.prepare('INSERT INTO agent_definitions(agent_id,slug,name,role,instructions,enabled,sort_order,token_profile,token_limit,model_mode,provider,model,created_at,updated_at) VALUES(?,?,?,?,?,0,?,?,?,?,?,?,?,?)').run(agentId, slug, `${existing.name} Kopyası`.slice(0, 120), existing.role, existing.instructions, Number(existing.sort_order) + 1, existing.token_profile, existing.token_limit, existing.model_mode, existing.provider, existing.model, stamp, stamp);
      audit('agent_cloned', agentId, { source_agent_id: existing.agent_id, slug }); sendJson(res, 201, { agent_id: agentId, slug }); return;
    }
    if (url.pathname === '/api/project/export' && req.method === 'GET') {
      if (!requireSession(req, res)) return;
      const activeResources = resources.map((resource) => { const current = currentResource(resource); return { category: resource.category, key: resource.key, content: current.content, content_hash: current.content_hash }; });
      const apps = db.prepare('SELECT app_id,slug,name,brand_name,status,config_json,generation_no,created_at,updated_at FROM app_instances ORDER BY created_at').all().map((app) => ({ ...app, config: json(app.config_json, {}), config_json: undefined }));
      const bundle = { format: 'ajans-kurucu-portable', schema_version: 1, exported_at: now(), contains_credentials: false, agents: agentRows(), resources: activeResources, studio_settings: studioSettings(), apps };
      audit('portable_bundle_exported', 'ajans-kurucu', { agent_count: bundle.agents.length, app_count: apps.length, contains_credentials: false });
      sendJson(res, 200, bundle, { 'Content-Disposition': `attachment; filename="ajans-kurucu-${new Date().toISOString().slice(0, 10)}.ajanskurucu"` }); return;
    }
    if (url.pathname === '/api/project/import' && req.method === 'POST') {
      if (!requireSession(req, res, true)) return;
      const bundle = await readBody(req, 8 * 1024 * 1024);
      if (bundle?.format !== 'ajans-kurucu-portable' || Number(bundle.schema_version) !== 1 || bundle.contains_credentials !== false || !Array.isArray(bundle.agents) || !Array.isArray(bundle.resources)) { sendJson(res, 400, { error: 'invalid_portable_bundle' }); return; }
      const forbidden = new Set(['api_key', 'access_token', 'api_token', 'app_secret', 'password', 'ciphertext', 'auth_tag', 'service_account_json']);
      const hasForbidden = (value) => value && typeof value === 'object' && Object.entries(value).some(([key, child]) => forbidden.has(key) || hasForbidden(child));
      if (hasForbidden(bundle)) { sendJson(res, 400, { error: 'portable_bundle_contains_secret' }); return; }
      const cleanAgents = bundle.agents.slice(0, 2000).map((agent) => cleanAgent(agent, agent)); const stamp = now();
      db.exec('BEGIN IMMEDIATE');
      try {
        for (const agent of cleanAgents) {
          const agentId = String(bundle.agents.find((item) => item.slug === agent.slug)?.agent_id || id('agent')).slice(0, 120);
          db.prepare(`INSERT INTO agent_definitions(agent_id,slug,name,role,instructions,enabled,sort_order,token_profile,token_limit,model_mode,provider,model,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(slug) DO UPDATE SET name=excluded.name,role=excluded.role,instructions=excluded.instructions,enabled=excluded.enabled,sort_order=excluded.sort_order,token_profile=excluded.token_profile,token_limit=excluded.token_limit,model_mode=excluded.model_mode,provider=excluded.provider,model=excluded.model,updated_at=excluded.updated_at`).run(agentId, agent.slug, agent.name, agent.role, agent.instructions, agent.enabled ? 1 : 0, agent.sort_order, agent.token_profile, agent.token_limit, agent.model_mode, agent.provider, agent.model, stamp, stamp);
        }
        for (const [key, value] of Object.entries(bundle.studio_settings || {})) {
          if (!Object.hasOwn(defaultStudioSettings, key)) continue;
          db.prepare('INSERT INTO studio_settings(setting_key,value_json,updated_at) VALUES(?,?,?) ON CONFLICT(setting_key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at').run(key, JSON.stringify(value), stamp);
        }
        for (const imported of bundle.resources.slice(0, resources.length)) {
          const resource = resourceMap.get(`${imported.category}:${imported.key}`); const content = String(imported.content || ''); if (!resource || !content.trim() || content.length > 250000 || (resource.format === 'json' && json(content) === null)) continue;
          const next = Number(db.prepare('SELECT COALESCE(MAX(version_no),0)+1 next FROM resource_versions WHERE category=? AND resource_key=?').get(resource.category, resource.key).next); const versionId = id('version');
          db.prepare("UPDATE resource_versions SET status='archived' WHERE category=? AND resource_key=? AND status='active'").run(resource.category, resource.key);
          db.prepare("INSERT INTO resource_versions(version_id,resource_key,category,version_no,content,content_hash,source_hash,status,note,created_at) VALUES(?,?,?,?,?,?,?,'active','Taşınabilir paketten içe aktarıldı',?)").run(versionId, resource.key, resource.category, next, content, sha256(content), sha256(sourceContent(resource)), stamp);
        }
        for (const app of (Array.isArray(bundle.apps) ? bundle.apps.slice(0, 500) : [])) {
          const slug = safeSlug(app.slug, 'app_slug'); const config = app.config && typeof app.config === 'object' ? app.config : {}; const appId = String(app.app_id || id('app')).slice(0, 120);
          db.prepare(`INSERT INTO app_instances(app_id,slug,name,brand_name,status,config_json,generation_no,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(slug) DO UPDATE SET name=excluded.name,brand_name=excluded.brand_name,status=excluded.status,config_json=excluded.config_json,generation_no=excluded.generation_no,updated_at=excluded.updated_at`).run(appId, slug, String(app.name || slug).slice(0, 120), String(app.brand_name || '').slice(0, 120), 'generated', JSON.stringify(config), Math.max(1, Number(app.generation_no) || 1), app.created_at || stamp, stamp);
          atomicWrite(path.join(appsRoot, slug, 'manifest.json'), `${JSON.stringify(config, null, 2)}\n`);
        }
        audit('portable_bundle_imported', 'ajans-kurucu', { agent_count: cleanAgents.length, app_count: Array.isArray(bundle.apps) ? bundle.apps.length : 0, contains_credentials: false }); db.exec('COMMIT');
      } catch (error) { db.exec('ROLLBACK'); throw error; }
      sendJson(res, 200, { status: 'imported', agents: cleanAgents.length, apps: Array.isArray(bundle.apps) ? bundle.apps.length : 0 }); return;
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
      sendJson(res, 410, { error: 'connections_belong_to_generated_app' }); return;
    }
    if (url.pathname === '/api/apps' && req.method === 'POST') {
      if (!requireSession(req, res, true)) return;
      const body = await readBody(req); const slug = safeSlug(body.slug, 'app_slug'); const name = String(body.name || '').trim().slice(0, 120); const brandName = String(body.brand_name || '').trim().slice(0, 120);
      if (!name || !brandName) { sendJson(res, 400, { error: 'name_and_brand_required' }); return; }
      const existing = db.prepare('SELECT * FROM app_instances WHERE slug=?').get(slug); const stamp = now(); const appId = existing?.app_id || id('app'); const generationNo = Number(existing?.generation_no || 0) + 1;
      const activeResources = resources.map((resource) => { const current = currentResource(resource); return { category: resource.category, key: resource.key, version_id: current.version_id, version_no: current.version_no, content_hash: current.content_hash }; });
      const settings = studioSettings(); const planId = ['basic', 'plus', 'pro'].includes(body.plan_id) ? body.plan_id : 'basic'; const basePlan = settings.plan_templates[planId];
      const requestedAgentLimit = Number(body.max_enabled_agents ?? basePlan.max_enabled_agents); const requestedTokenLimit = Number(body.monthly_token_limit ?? basePlan.monthly_token_limit); const requestedRounds = Number(body.debate_rounds ?? basePlan.debate_rounds);
      if (!Number.isInteger(requestedAgentLimit) || requestedAgentLimit < 1 || requestedAgentLimit > 1000 || !Number.isInteger(requestedTokenLimit) || requestedTokenLimit < 10000 || requestedTokenLimit > 100000000 || !Number.isInteger(requestedRounds) || requestedRounds < 0 || requestedRounds > 8) { sendJson(res, 400, { error: 'invalid_plan_limits' }); return; }
      const enabledAgents = agentRows().filter((agent) => agent.enabled).sort((a, b) => a.sort_order - b.sort_order);
      const coreSlugs = new Set(resources.filter((item) => item.category === 'agent').map((item) => item.key));
      const coreAgents = enabledAgents.filter((agent) => coreSlugs.has(agent.slug));
      const customAgents = enabledAgents.filter((agent) => !coreSlugs.has(agent.slug));
      if (requestedAgentLimit < coreAgents.length) { sendJson(res, 400, { error: 'core_agent_limit_too_low', required_core_roles: coreAgents.length }); return; }
      const plan = { id: planId, name: basePlan.name, limits: { ...basePlan, max_enabled_agents: requestedAgentLimit, monthly_token_limit: requestedTokenLimit, debate_rounds: requestedRounds, included_core_roles: coreAgents.length, custom_role_slots: Math.max(0, requestedAgentLimit - coreAgents.length) } };
      const agentNames = body.agent_names && typeof body.agent_names === 'object' && !Array.isArray(body.agent_names) ? body.agent_names : {};
      const selectedAgents = [...coreAgents, ...customAgents.slice(0, Math.max(0, requestedAgentLimit - coreAgents.length))].sort((a, b) => a.sort_order - b.sort_order).map((agent) => ({ agent_id: agent.agent_id, slug: agent.slug, name: String(agentNames[agent.slug] || agent.name).trim().slice(0, 120) || agent.name, template_name: agent.name, role: agent.role, instructions: agent.instructions, token_profile: agent.token_profile, token_limit: agent.token_limit, model_mode: agent.model_mode, provider: agent.provider, model: agent.model, sort_order: agent.sort_order }));
      const appFeatures = Array.isArray(body.features) ? body.features.filter((item) => ['brand','content','visuals','workflow','approvals','calendar','connections','models'].includes(item)).slice(0, 12) : ['brand','content','visuals','workflow','approvals','connections'];
      const apiControlMode = ['locked', 'guided', 'open'].includes(body.api_control_mode) ? body.api_control_mode : (basePlan.api_control_default || 'locked');
      const shortSetting = (value, max = 160) => String(value || '').trim().slice(0, max);
      const textProvider = shortSetting(body.text_provider || 'google_gemini', 80);
      const textModel = shortSetting(body.text_model || 'auto');
      const visualProvider = shortSetting(body.visual_provider || 'openai', 80);
      const visualModel = shortSetting(body.visual_model || 'auto');
      if (!textProvider || !textModel || (appFeatures.includes('visuals') && (!visualProvider || !visualModel))) { sendJson(res, 400, { error: 'default_provider_and_model_required' }); return; }
      const requestedProviders = Array.isArray(body.allowed_providers) ? body.allowed_providers : String(body.allowed_providers || '').split(',');
      const allowedProviders = [...new Set([...requestedProviders.map((item) => shortSetting(item, 80)).filter(Boolean), textProvider, ...(appFeatures.includes('visuals') ? [visualProvider] : [])])].slice(0, 30);
      const connectionPolicy = {
        initial_credential_entry_required: true,
        credentials_included: false,
        credentials_stored_in_encrypted_app_vault: true,
        api_control_mode: apiControlMode,
        provider_selection_editable: apiControlMode !== 'locked',
        model_selection_editable: apiControlMode !== 'locked',
        can_add_providers: apiControlMode === 'open',
        allowed_providers: apiControlMode === 'locked' ? [...new Set([textProvider, ...(appFeatures.includes('visuals') ? [visualProvider] : [])])] : allowedProviders,
        defaults: { text: { provider: textProvider, model: textModel }, visual: { provider: visualProvider, model: visualModel } },
        credential_reentry_allowed: body.credential_reentry_allowed === true,
        meta: { initial_connection_required: appFeatures.includes('connections'), reconnect_or_account_change_allowed: body.meta_reconnect_allowed === true, account_binding_required: true }
      };
      const chatEnabled = body.chat_enabled === true;
      const chatModelMode = ['inherit', 'auto', 'fixed'].includes(body.chat_model_mode) ? body.chat_model_mode : 'inherit';
      const chatProvider = chatModelMode === 'fixed' ? shortSetting(body.chat_provider, 80) : '';
      const chatModel = chatModelMode === 'fixed' ? shortSetting(body.chat_model) : '';
      const chatTokenLimit = Number(body.chat_token_limit ?? 1200);
      if (chatEnabled && (chatModelMode === 'fixed' && (!chatProvider || !chatModel) || !Number.isInteger(chatTokenLimit) || chatTokenLimit < 128 || chatTokenLimit > 16000)) { sendJson(res, 400, { error: 'invalid_chat_configuration' }); return; }
      const assistantChat = {
        enabled: chatEnabled,
        visible_in_client_app: chatEnabled,
        model: { mode: chatModelMode, provider: chatProvider, model: chatModel, inherits_text_route_when_empty: true },
        maximum_tokens_per_message: chatTokenLimit,
        maximum_retries: 1,
        permissions: {
          request_content_revision: body.chat_content_revision === true,
          request_visual_revision: body.chat_visual_revision === true,
          report_application_problem: true,
          inspect_status_and_explain: true,
          change_provider_or_model: false,
          publish: false,
          change_hidden_workflows: false
        },
        safeguards: {
          warn_before_high_token_request: true,
          warn_before_redundant_request: true,
          warn_or_refuse_brand_harming_request: true,
          preserve_user_request_as_proposal_until_approved: true,
          final_publish_approval_required: true,
          user_message_is_data_not_system_instruction: true
        }
      };
      const planRanks = { basic: 0, plus: 1, pro: 2 };
      const cleanMinimumPlan = (value, fallback) => Object.hasOwn(planRanks, value) ? value : fallback;
      const modeCatalog = [
        { id: 'autonomous', name: 'Oto', visible: body.mode_autonomous !== false, minimum_plan: cleanMinimumPlan(body.mode_autonomous_min_plan, 'pro') },
        { id: 'guided_auto', name: 'Kontrollü Oto', visible: body.mode_guided_auto !== false, minimum_plan: cleanMinimumPlan(body.mode_guided_auto_min_plan, 'basic') },
        { id: 'manual', name: 'Manuel', visible: body.mode_manual !== false, minimum_plan: cleanMinimumPlan(body.mode_manual_min_plan, 'basic') }
      ].map((mode) => ({ ...mode, enabled_for_current_plan: mode.visible && planRanks[planId] >= planRanks[mode.minimum_plan], access_state: !mode.visible ? 'hidden' : planRanks[planId] >= planRanks[mode.minimum_plan] ? 'active' : 'upgrade_required' }));
      const enabledModes = modeCatalog.filter((mode) => mode.enabled_for_current_plan).map((mode) => mode.id);
      if (!enabledModes.length) { sendJson(res, 400, { error: 'at_least_one_operating_mode_required' }); return; }
      const requestedDefaultMode = ['autonomous', 'guided_auto', 'manual'].includes(body.default_operating_mode) ? body.default_operating_mode : enabledModes[0];
      const defaultOperatingMode = enabledModes.includes(requestedDefaultMode) ? requestedDefaultMode : enabledModes[0];
      const autonomousAcceptanceText = 'Oto modda ajans, tanımlanan hesap, bütçe ve güvenlik sınırları içinde üretim ve Meta yayını dahil işlemleri ayrıca onay istemeden yürütebilir. Yapay zekâ çıktılarında hata oluşabileceğini, sonuçları ve bağlı hesapları izleme sorumluluğunun kullanıcıda olduğunu kabul ediyorum.';
      const operatingModes = {
        catalog: modeCatalog,
        available: enabledModes,
        default: defaultOperatingMode,
        autonomous: {
          requires_explicit_risk_acceptance: true,
          acceptance_is_versioned_and_audited: true,
          acceptance_version: 1,
          acceptance_text: autonomousAcceptanceText,
          acceptance_text_sha256: sha256(autonomousAcceptanceText),
          acceptance_bound_to_app_generation: generationNo,
          may_publish_without_per_item_approval_after_acceptance: true,
          requires_bound_meta_account_and_publish_permission: true,
          can_bypass_final_publish_approval: true,
          hard_limits_still_apply: ['account_scope', 'budget', 'brand_safety', 'legal_safety', 'emergency_stop', 'idempotency']
        },
        guided_auto: { description: 'Ajans üretimi otomatik yürütür; kritik seçimler ve son yayın kullanıcı onayı ister.', can_bypass_final_publish_approval: false },
        manual: { description: 'Görevleri kullanıcı başlatır ve seçimleri kullanıcı yapar.', can_bypass_final_publish_approval: false },
        publish_policy_by_mode: { autonomous: 'risk_acceptance_then_no_per_item_approval', guided_auto: 'explicit_final_approval', manual: 'explicit_user_action' }
      };
      const runtimeEngine = {
        type: 'embedded_managed_n8n',
        bundled: true,
        lifecycle_managed_by_app: true,
        user_account_required: false,
        user_interface_exposed: false,
        workflow_editor_exposed: false,
        external_port_exposed: false,
        internal_network_only: true,
        workflow_activation: 'signed_runtime_only',
        credentials_injected_from_app_vault: true,
        runtime_image: 'n8nio/n8n:2.31.6@sha256:3c07c723326dd72e46a6969181c66a75260b7a204b9b77ba1ece6d594489c684'
      };
      const config = { schema_version: '2.3', app_id: appId, slug, name, brand_name: brandName, description: String(body.description || '').slice(0, 1000), theme: { accent: /^#[0-9a-f]{6}$/i.test(body.accent) ? body.accent : '#8b5cf6' }, features: appFeatures, plan, agents: selectedAgents, resources: activeResources, studio_settings: { token_policy: settings.token_policy, flow_blueprints: settings.flow_blueprints, model_assignments: settings.model_assignments, flow_design: settings.flow_design }, connection_policy: connectionPolicy, assistant_chat: assistantChat, operating_modes: operatingModes, runtime_engine: runtimeEngine, runtime_setup: { configured_in_generated_app: true, required_sections: ['brand_profile', 'ai_provider', 'meta_instagram', 'operating_mode'], credentials_included: false, customer_files_managed_by_app: true, n8n_account_required: false }, installer: { package_type: 'ajansapp', requires_user_file_management: false, first_run_wizard: true, local_data_isolation: true, hidden_runtime_installed_with_app: true }, generation_no: generationNo, generated_at: stamp, proprietary_logic_visible_to_client: false, publish_approval_policy: operatingModes.publish_policy_by_mode };
      db.prepare(`INSERT INTO app_instances(app_id,slug,name,brand_name,status,config_json,generation_no,created_at,updated_at) VALUES(?,?,?,?,'generated',?,?,?,?)
        ON CONFLICT(slug) DO UPDATE SET name=excluded.name,brand_name=excluded.brand_name,status='generated',config_json=excluded.config_json,generation_no=excluded.generation_no,updated_at=excluded.updated_at`).run(appId, slug, name, brandName, JSON.stringify(config), generationNo, existing?.created_at || stamp, stamp);
      const appDir = path.resolve(appsRoot, slug); if (!appDir.startsWith(`${appsRoot}${path.sep}`)) throw Object.assign(new Error('invalid_app_path'), { status: 400 });
      atomicWrite(path.join(appDir, 'manifest.json'), `${JSON.stringify({ ...config, resources: activeResources.map(({ content_hash, ...rest }) => ({ ...rest, integrity: content_hash })) }, null, 2)}\n`);
      audit('client_app_generated', appId, { slug, generation_no: generationNo, resource_count: activeResources.length });
      const row = db.prepare('SELECT * FROM app_instances WHERE app_id=?').get(appId); sendJson(res, existing ? 200 : 201, { app: publicConfig(row), preview_url: `/client/${encodeURIComponent(slug)}` }); return;
    }
    const appPackageRoute = url.pathname.match(/^\/api\/apps\/([a-zA-Z0-9_-]+)\/package$/);
    if (appPackageRoute && req.method === 'GET') {
      if (!requireSession(req, res)) return;
      const app = db.prepare("SELECT * FROM app_instances WHERE app_id=? AND status='generated'").get(appPackageRoute[1]);
      if (!app) { sendJson(res, 404, { error: 'app_not_found' }); return; }
      const config = json(app.config_json, {});
      const runtimeResources = resources.map((resource) => {
        const current = currentResource(resource);
        return { category: resource.category, key: resource.key, version_no: current.version_no, content: current.content, content_hash: current.content_hash };
      });
      const runtimeWorkflows = workflowBundle();
      const runtimeBlueprint = {
        visibility: 'installer_and_runtime_only',
        storage: 'encrypted_local_runtime_vault',
        user_interface_exposes_instructions: false,
        user_interface_exposes_n8n: false,
        architecture: 'TrendyBrander living agency core',
        engine: config.runtime_engine,
        resources: runtimeResources,
        workflows: runtimeWorkflows
      };
      const payload = {
        package_type: 'ajansapp',
        package_version: '1.1',
        exported_at: now(),
        credentials_included: false,
        creator_requires_internet: false,
        app: config,
        runtime_blueprint: runtimeBlueprint,
        integrity: {
          config_sha256: sha256(JSON.stringify(config)),
          runtime_blueprint_sha256: sha256(JSON.stringify(runtimeBlueprint)),
          workflow_count: runtimeWorkflows.length,
          approval_policy: 'mode_dependent',
          autonomous_requires_versioned_risk_acceptance: true,
          controlled_auto_requires_final_approval: true
        }
      };
      audit('client_app_package_exported', app.app_id, { slug: app.slug, generation_no: app.generation_no, credentials_included: false, workflow_count: runtimeWorkflows.length, hidden_runtime: true });
      sendJson(res, 200, payload, { 'Content-Disposition': `attachment; filename="${app.slug}-v${app.generation_no}.ajansapp"` }); return;
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
