import { createServer } from 'node:http';
import { createHash, createHmac, createCipheriv, randomBytes, timingSafeEqual, pbkdf2Sync } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { DatabaseSync } from 'node:sqlite';
import { copyFileSync, existsSync, lstatSync, readFileSync, realpathSync, renameSync, rmSync, writeFileSync, statfsSync, mkdirSync } from 'node:fs';
import path from 'node:path';

const host = process.env.HOST || '0.0.0.0';
const port = Number(process.env.PORT || 5681);
const dbPath = path.resolve(process.env.DB_PATH || '/runtime/ajans-runtime.sqlite');
const workspaceRoot = path.resolve(process.env.WORKSPACE_ROOT || '/workspace');
const runtimeApiKey = process.env.RUNTIME_API_KEY || '';
const scopedServiceKeys = {
  center: process.env.CENTER_API_KEY || '', scheduler: process.env.SCHEDULER_API_KEY || '', worker: process.env.WORKER_API_KEY || '', n8n: process.env.N8N_SERVICE_API_KEY || ''
};
const scopedServiceKeysConfigured = Object.values(scopedServiceKeys).every((value) => value.length >= 32);
const allowLegacyRuntimeKey = process.env.ALLOW_LEGACY_RUNTIME_KEY === 'true' || !scopedServiceKeysConfigured;
const approvalKey = process.env.APPROVAL_HMAC_KEY || '';
const operatorPasswordHash = process.env.OPERATOR_PASSWORD_HASH || '';
const credentialEncryptionSecret = process.env.CREDENTIAL_ENCRYPTION_KEY || '';
const allowSyntheticAccounts = process.env.ALLOW_SYNTHETIC_ACCOUNTS === 'true';
const allowSyntheticEvidence = process.env.ALLOW_SYNTHETIC_EVIDENCE === 'true';
const localDeliveryAccountId = '__local_file_only__';
const localDeliveryRoot = path.resolve(process.env.LOCAL_DELIVERY_ROOT || path.join(workspaceRoot, 'data/outputs/approved'));
const generatedImageRoot = path.resolve(process.env.GENERATED_IMAGE_ROOT || path.join(workspaceRoot, 'data/outputs/images'));
const brandDataRoot = path.resolve(process.env.BRAND_DATA_ROOT || path.join(workspaceRoot, 'data/brands'));
const maxBodyBytes = 1024 * 1024;
const leaseSeconds = Math.max(30, Number(process.env.LEASE_SECONDS || 180));
const minFreeBytes = Math.max(64 * 1024 * 1024, Number(process.env.MIN_FREE_BYTES || 512 * 1024 * 1024));

if (runtimeApiKey.length < 32 || approvalKey.length < 32 || credentialEncryptionSecret.length < 32) {
  throw new Error('Runtime sırları eksik veya yetersiz; servis güvenli biçimde başlatılmadı.');
}

mkdirSync(path.dirname(dbPath), { recursive: true });
mkdirSync(brandDataRoot, { recursive: true });
const db = new DatabaseSync(dbPath);
db.exec(`
  PRAGMA journal_mode=WAL;
  PRAGMA synchronous=FULL;
  PRAGMA foreign_keys=ON;
  PRAGMA busy_timeout=5000;
  PRAGMA trusted_schema=OFF;
  PRAGMA secure_delete=FAST;
  CREATE TABLE IF NOT EXISTS schema_migrations(
    version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, script_hash TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS runtime_meta(
    key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS tasks(
    task_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    brand_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    state TEXT NOT NULL DEFAULT 'queued',
    risk_level TEXT NOT NULL DEFAULT 'normal',
    agent_id TEXT,
    period_key TEXT,
    content_id TEXT,
    content_version TEXT,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    context_signature TEXT,
    pipeline_id TEXT,
    pipeline_stage TEXT,
    parent_task_id TEXT,
    result_json TEXT,
    result_hash TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 2,
    next_run_at TEXT,
    lease_owner TEXT,
    lease_token_hash TEXT,
    lease_expires_at TEXT,
    last_safe_state TEXT,
    row_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT
  );
  DROP INDEX IF EXISTS idx_tasks_logical_unique;
  CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_open_logical_unique
    ON tasks(brand_id, task_type, COALESCE(period_key,''), COALESCE(content_version,''))
    WHERE state IN ('queued','retry','running');
  CREATE INDEX IF NOT EXISTS idx_tasks_claim ON tasks(state, priority, next_run_at, created_at);
  CREATE TABLE IF NOT EXISTS pipeline_runs(
    pipeline_id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    goal TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    current_stage TEXT,
    debate_round INTEGER NOT NULL DEFAULT 0,
    max_debate_rounds INTEGER NOT NULL,
    max_model_calls INTEGER NOT NULL DEFAULT 12,
    max_input_tokens INTEGER NOT NULL DEFAULT 30000,
    max_output_tokens INTEGER NOT NULL DEFAULT 8000,
    max_cost_usd REAL NOT NULL DEFAULT 0.25,
    content_id TEXT NOT NULL,
    content_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT
  );
  CREATE TABLE IF NOT EXISTS pipeline_steps(
    pipeline_id TEXT NOT NULL REFERENCES pipeline_runs(pipeline_id),
    sequence INTEGER NOT NULL,
    task_id TEXT NOT NULL UNIQUE REFERENCES tasks(task_id),
    task_type TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    status TEXT NOT NULL,
    source_task_id TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    PRIMARY KEY(pipeline_id, sequence)
  );
  CREATE INDEX IF NOT EXISTS idx_pipeline_status ON pipeline_runs(status, updated_at);
  CREATE TABLE IF NOT EXISTS provider_circuits(
    provider TEXT PRIMARY KEY,
    state TEXT NOT NULL DEFAULT 'closed',
    failure_count INTEGER NOT NULL DEFAULT 0,
    open_until TEXT,
    last_error_type TEXT,
    updated_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS task_attempts(
    attempt_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    execution_id TEXT NOT NULL UNIQUE,
    provider TEXT, model TEXT, agent_id TEXT, state TEXT NOT NULL,
    input_tokens INTEGER, output_tokens INTEGER, estimated_cost REAL, currency TEXT,
    duration_ms INTEGER, retry_count INTEGER NOT NULL DEFAULT 0,
    quality_score REAL, brand_alignment REAL, schema_compliance REAL,
    user_acceptance TEXT NOT NULL DEFAULT 'unknown', error_type TEXT,
    request_fingerprint TEXT, cache_hit INTEGER, started_at TEXT NOT NULL, finished_at TEXT
  );
  CREATE TABLE IF NOT EXISTS validated_outputs(
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    task_type TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    validated_at TEXT NOT NULL,
    PRIMARY KEY(task_id, output_hash)
  );
  CREATE TABLE IF NOT EXISTS agent_output_provenance(
    provenance_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL UNIQUE REFERENCES tasks(task_id),
    brand_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    eligible_as_factual_evidence INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS checkpoints(
    checkpoint_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    sequence INTEGER NOT NULL,
    state TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    lease_owner TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(task_id, sequence)
  );
  CREATE TABLE IF NOT EXISTS dead_letters(
    dlq_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL UNIQUE REFERENCES tasks(task_id),
    error_fingerprint TEXT NOT NULL,
    attempts INTEGER NOT NULL,
    last_safe_state TEXT,
    redacted_error TEXT NOT NULL,
    human_action_required TEXT NOT NULL,
    created_at TEXT NOT NULL,
    resolved_at TEXT
  );
  CREATE TABLE IF NOT EXISTS approvals(
    approval_id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    account_binding_hash TEXT,
    content_id TEXT NOT NULL,
    content_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    preview_refs_json TEXT NOT NULL,
    nonce_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'waiting',
    consumed_at TEXT
  );
  CREATE TABLE IF NOT EXISTS approval_decisions(
    decision_id TEXT PRIMARY KEY,
    approval_id TEXT NOT NULL UNIQUE REFERENCES approvals(approval_id),
    decision TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    revision_note TEXT,
    decision_at TEXT NOT NULL,
    canonical_hash TEXT NOT NULL,
    signature_hmac TEXT NOT NULL,
    previous_decision_hash TEXT
  );
  CREATE TABLE IF NOT EXISTS local_approval_payloads(
    approval_id TEXT PRIMARY KEY REFERENCES approvals(approval_id),
    content_json TEXT NOT NULL,
    image_refs_json TEXT NOT NULL,
    created_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS local_delivery_receipts(
    approval_id TEXT PRIMARY KEY REFERENCES approvals(approval_id),
    delivery_id TEXT NOT NULL UNIQUE,
    output_dir TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    manifest_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS outbox_events(
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    delivered_at TEXT
  );
  CREATE TABLE IF NOT EXISTS publish_receipts(
    receipt_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE REFERENCES outbox_events(event_id),
    provider TEXT NOT NULL,
    provider_object_id TEXT,
    status TEXT NOT NULL,
    response_hash TEXT,
    created_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS audit_events(
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    brand_id TEXT,
    task_id TEXT,
    object_id TEXT,
    payload_hash TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL,
    occurred_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS cache_entries(
    request_fingerprint TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    role_version TEXT NOT NULL,
    task_type TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    source_hash_bundle TEXT NOT NULL,
    result_ref TEXT NOT NULL,
    result_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    schema_compliance REAL NOT NULL,
    quality_score REAL NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    last_hit_at TEXT,
    hit_count INTEGER NOT NULL DEFAULT 0
  );
  CREATE TABLE IF NOT EXISTS memory_records(
    memory_id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    task_scope TEXT NOT NULL,
    semantic_key TEXT NOT NULL,
    type TEXT NOT NULL,
    compact_content TEXT NOT NULL,
    confidence REAL NOT NULL,
    state TEXT NOT NULL DEFAULT 'candidate',
    sample_size INTEGER NOT NULL DEFAULT 0,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    supersedes TEXT,
    expires_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(brand_id, task_scope, semantic_key, version)
  );
  CREATE TABLE IF NOT EXISTS memory_evidence(
    evidence_id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL REFERENCES memory_records(memory_id),
    source_ref TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    source_date TEXT,
    evidence_kind TEXT NOT NULL,
    metric_window TEXT NOT NULL DEFAULT '',
    result_segment TEXT,
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(memory_id, source_hash)
  );
  CREATE TABLE IF NOT EXISTS verified_evidence(
    evidence_id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    claim TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    source_date TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    sample_size INTEGER NOT NULL DEFAULT 1,
    metric_window TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0.8,
    verified_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revoked_at TEXT
  );
  CREATE INDEX IF NOT EXISTS idx_verified_evidence_brand ON verified_evidence(brand_id, revoked_at);
  CREATE UNIQUE INDEX IF NOT EXISTS idx_verified_evidence_brand_source ON verified_evidence(brand_id, source_hash, claim);
  CREATE TABLE IF NOT EXISTS operator_sessions(
    session_hash TEXT PRIMARY KEY,
    csrf_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_used_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT
  );
  CREATE TABLE IF NOT EXISTS brand_profiles(
    brand_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    onboarding_state TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS brand_assets(
    asset_id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    original_name TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(brand_id, sha256)
  );
  CREATE INDEX IF NOT EXISTS idx_brand_assets_brand ON brand_assets(brand_id, created_at DESC);
  CREATE TABLE IF NOT EXISTS model_preferences(
    brand_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'auto',
    provider TEXT,
    model TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(brand_id, role_id)
  );
  CREATE TABLE IF NOT EXISTS encrypted_connections(
    brand_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    label TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    ciphertext TEXT NOT NULL,
    iv TEXT NOT NULL,
    auth_tag TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'saved_unverified',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(brand_id, provider)
  );
  CREATE TABLE IF NOT EXISTS security_quarantine(
    quarantine_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    reason_codes TEXT NOT NULL,
    redacted_excerpt TEXT,
    created_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS rate_limits(
    key TEXT PRIMARY KEY,
    window_start TEXT NOT NULL,
    count INTEGER NOT NULL
  );
  CREATE TABLE IF NOT EXISTS personal_data_records(
    record_id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    subject_key_hash TEXT NOT NULL,
    category TEXT NOT NULL,
    source_type TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    storage_ref TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    deleted_at TEXT
  );
  CREATE INDEX IF NOT EXISTS idx_personal_data_subject
    ON personal_data_records(brand_id, subject_key_hash, deleted_at);
  CREATE INDEX IF NOT EXISTS idx_personal_data_expiry
    ON personal_data_records(expires_at, deleted_at);
  CREATE TABLE IF NOT EXISTS privacy_requests(
    request_id TEXT PRIMARY KEY,
    brand_id TEXT NOT NULL,
    subject_key_hash TEXT NOT NULL,
    request_type TEXT NOT NULL,
    scope_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_operator',
    created_at TEXT NOT NULL,
    completed_at TEXT,
    report_json TEXT
  );
  CREATE INDEX IF NOT EXISTS idx_privacy_requests_status
    ON privacy_requests(status, created_at);
`);

const ensureColumn = (table, column, definition) => {
  const columns = new Set(db.prepare(`PRAGMA table_info(${table})`).all().map((item) => item.name));
  if (!columns.has(column)) db.exec(`ALTER TABLE ${table} ADD COLUMN ${column} ${definition}`);
};
ensureColumn('tasks', 'context_signature', 'TEXT');
ensureColumn('tasks', 'pipeline_id', 'TEXT');
ensureColumn('tasks', 'pipeline_stage', 'TEXT');
ensureColumn('tasks', 'parent_task_id', 'TEXT');
ensureColumn('pipeline_runs', 'max_model_calls', 'INTEGER NOT NULL DEFAULT 12');
ensureColumn('pipeline_runs', 'max_input_tokens', 'INTEGER NOT NULL DEFAULT 30000');
ensureColumn('pipeline_runs', 'max_output_tokens', 'INTEGER NOT NULL DEFAULT 8000');
ensureColumn('pipeline_runs', 'max_cost_usd', 'REAL NOT NULL DEFAULT 0.25');
ensureColumn('memory_evidence', 'metric_window', "TEXT NOT NULL DEFAULT ''");
ensureColumn('verified_evidence', 'sample_size', 'INTEGER NOT NULL DEFAULT 1');
ensureColumn('verified_evidence', 'metric_window', "TEXT NOT NULL DEFAULT ''");
ensureColumn('verified_evidence', 'confidence', 'REAL NOT NULL DEFAULT 0.8');
ensureColumn('approvals', 'account_binding_hash', 'TEXT');

const now = () => new Date().toISOString();
const id = (prefix) => `${prefix}-${Date.now()}-${randomBytes(8).toString('hex')}`;
const sha256 = (value) => createHash('sha256').update(String(value)).digest('hex');
const sha256Bytes = (value) => createHash('sha256').update(value).digest('hex');
const hmac = (value) => createHmac('sha256', approvalKey).update(String(value)).digest('hex');
const safeEqual = (a, b) => {
  const left = Buffer.from(String(a || ''));
  const right = Buffer.from(String(b || ''));
  return left.length === right.length && timingSafeEqual(left, right);
};
const stable = (value) => {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])]));
  return value;
};
const canonical = (value) => JSON.stringify(stable(value));
const parseJson = (value, fallback = null) => { try { return JSON.parse(value); } catch { return fallback; } };
const redact = (value) => String(value || '').replace(/(?:api[_-]?key|token|secret|password|authorization)\s*[:=]\s*[^\s,;]+/giu, '$1=[REDACTED]').slice(0, 1200);
const isInside = (root, candidate) => candidate === root || candidate.startsWith(`${root}${path.sep}`);
const safePathSegment = (value, label) => {
  const segment = String(value || '').trim();
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$/.test(segment) || segment === '.' || segment === '..') throw new Error(`invalid_${label}`);
  return segment;
};
if (!isInside(workspaceRoot, localDeliveryRoot) || !isInside(workspaceRoot, generatedImageRoot) || !isInside(workspaceRoot, brandDataRoot)) throw new Error('workspace_storage_root_invalid');

const credentialEncryptionKey = createHash('sha256').update(credentialEncryptionSecret).digest();
const encryptSecretJson = (value) => {
  const iv = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm', credentialEncryptionKey, iv);
  const encrypted = Buffer.concat([cipher.update(canonical(value), 'utf8'), cipher.final()]);
  return {
    ciphertext: encrypted.toString('base64'),
    iv: iv.toString('base64'),
    auth_tag: cipher.getAuthTag().toString('base64')
  };
};
const limitText = (value, max = 4000) => String(value || '').trim().slice(0, max);
const arrayText = (value, maxItems = 30, maxLength = 500) => Array.isArray(value)
  ? value.slice(0, maxItems).map((item) => limitText(item, maxLength)).filter(Boolean)
  : [];
const normalizeBrandProfile = (body = {}) => ({
  brand_id: safePathSegment(body.brand_id || 'trendybrander', 'brand_id').toLocaleLowerCase('tr-TR'),
  name: limitText(body.name, 120) || 'Markam',
  website: limitText(body.website, 500),
  description: limitText(body.description, 6000),
  target_audience: limitText(body.target_audience, 5000),
  products: limitText(body.products, 6000),
  tone: limitText(body.tone, 3000),
  goals: limitText(body.goals, 4000),
  forbidden_expressions: arrayText(body.forbidden_expressions, 80, 300),
  content_examples: arrayText(body.content_examples, 30, 1200)
});
const legacyBrandProfile = () => {
  const readProjectText = (name) => {
    const target = path.join(workspaceRoot, 'projects', name);
    return existsSync(target) ? readFileSync(target, 'utf8').trim().slice(0, 12000) : '';
  };
  return {
    brand_id: 'trendybrander',
    name: 'TrendyBrander',
    website: '',
    description: readProjectText('marka-kimligi.txt'),
    target_audience: readProjectText('hedef-kitle.txt'),
    products: readProjectText('urunler.txt'),
    tone: '',
    goals: '',
    forbidden_expressions: readProjectText('yasakli-ifadeler.txt').split(/\r?\n/).map((item) => item.replace(/^[-*]\s*/, '').trim()).filter(Boolean).slice(0, 80),
    content_examples: readProjectText('icerik-ornekleri.txt').split(/\r?\n\r?\n/).map((item) => item.trim()).filter(Boolean).slice(0, 30)
  };
};
const connectionProviders = new Set(['google_gemini', 'openai', 'cloudflare', 'meta_instagram']);
const modelRoles = new Set(['analysis', 'content', 'visual', 'debate', 'ordinaryus', 'interface']);
const assetRules = {
  document: { max: 25 * 1024 * 1024, extensions: new Set(['.txt', '.md', '.json', '.pdf', '.doc', '.docx']) },
  image: { max: 25 * 1024 * 1024, extensions: new Set(['.png', '.jpg', '.jpeg', '.webp']) },
  video: { max: 100 * 1024 * 1024, extensions: new Set(['.mp4', '.mov', '.webm']) }
};
const assetMime = {
  '.txt': 'text/plain', '.md': 'text/markdown', '.json': 'application/json', '.pdf': 'application/pdf',
  '.doc': 'application/msword', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.webm': 'video/webm'
};

const resolveGeneratedImage = (reference) => {
  const raw = typeof reference === 'string' ? reference : reference?.path || reference?.url || reference?.name || '';
  let relative = String(raw).trim().replaceAll('\\', '/');
  if (relative.startsWith('/media/generated/')) relative = relative.slice('/media/generated/'.length);
  else if (relative.startsWith('data/outputs/images/')) relative = relative.slice('data/outputs/images/'.length);
  else if (relative.startsWith('/workspace/data/outputs/images/')) relative = relative.slice('/workspace/data/outputs/images/'.length);
  try { relative = decodeURIComponent(relative); } catch { throw new Error('invalid_image_reference_encoding'); }
  if (!relative || relative !== path.posix.basename(relative) || !/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,179}\.(?:png|jpe?g|webp)$/i.test(relative)) throw new Error('invalid_image_reference');
  const candidate = path.resolve(generatedImageRoot, relative);
  if (!isInside(generatedImageRoot, candidate) || !existsSync(candidate)) throw new Error('generated_image_not_found');
  const info = lstatSync(candidate);
  if (!info.isFile() || info.isSymbolicLink()) throw new Error('generated_image_not_regular_file');
  const realRoot = realpathSync(generatedImageRoot);
  const realCandidate = realpathSync(candidate);
  if (!isInside(realRoot, realCandidate)) throw new Error('generated_image_outside_root');
  return { name: relative, path: realCandidate, extension: path.extname(relative).toLowerCase() };
};

const writeLocalDelivery = (approvalId) => {
  const existingReceipt = db.prepare("SELECT * FROM local_delivery_receipts WHERE approval_id=? AND status='saved'").get(approvalId);
  if (existingReceipt) return { delivery_id: existingReceipt.delivery_id, output_dir: existingReceipt.output_dir, manifest_hash: existingReceipt.manifest_hash, reused: true };
  const approval = db.prepare('SELECT * FROM approvals WHERE approval_id=?').get(approvalId);
  const decision = db.prepare('SELECT * FROM approval_decisions WHERE approval_id=?').get(approvalId);
  const payloadRow = db.prepare('SELECT * FROM local_approval_payloads WHERE approval_id=?').get(approvalId);
  if (!approval || !decision || !payloadRow || approval.account_id !== localDeliveryAccountId || decision.decision !== 'approve') throw new Error('local_delivery_not_authorized');
  const content = parseJson(payloadRow.content_json);
  const imageRefs = parseJson(payloadRow.image_refs_json, []);
  if (!content || typeof content !== 'object' || Array.isArray(content)) throw new Error('local_delivery_content_integrity_failed');
  if (typeof content.caption !== 'string' || !content.caption.trim() || content.caption.length > 5000) throw new Error('local_delivery_caption_invalid');
  if (!Array.isArray(imageRefs) || imageRefs.length < 1 || imageRefs.length > 4) throw new Error('local_delivery_images_invalid');
  const images = imageRefs.map((item) => {
    const resolved = resolveGeneratedImage(item.reference || item);
    const actualHash = sha256Bytes(readFileSync(resolved.path));
    if (!item.sha256 || !safeEqual(actualHash, item.sha256)) throw new Error('local_delivery_image_integrity_failed');
    return { ...resolved, sha256: actualHash };
  });
  const boundHash = sha256(canonical({ content_payload: content, image_bindings: imageRefs.map((item) => ({ name: item.name, sha256: item.sha256 })) }));
  if (!safeEqual(boundHash, approval.content_hash)) throw new Error('local_delivery_content_integrity_failed');
  const brand = safePathSegment(approval.brand_id, 'brand_id');
  const contentId = safePathSegment(approval.content_id, 'content_id');
  const version = safePathSegment(approval.content_version, 'content_version');
  const relativeOutputDir = path.posix.join('data/outputs/approved', brand, contentId, version);
  const finalDir = path.resolve(localDeliveryRoot, brand, contentId, version);
  if (!isInside(localDeliveryRoot, finalDir)) throw new Error('local_delivery_target_outside_root');
  mkdirSync(path.dirname(finalDir), { recursive: true });
  const deliveryId = `local-${approvalId}`;
  if (existsSync(finalDir)) {
    const existingApproval = parseJson(readFileSync(path.join(finalDir, 'approval.json'), 'utf8'));
    if (!existingApproval || existingApproval.approval_id !== approvalId || existingApproval.content_hash !== approval.content_hash) throw new Error('local_delivery_target_conflict');
    const existingManifest = readFileSync(path.join(finalDir, 'manifest.json'), 'utf8');
    const manifestHash = sha256(existingManifest);
    tx(() => {
      db.prepare('INSERT OR REPLACE INTO local_delivery_receipts(approval_id,delivery_id,output_dir,manifest_json,manifest_hash,status,created_at,updated_at) VALUES(?,?,?,?,?,?,COALESCE((SELECT created_at FROM local_delivery_receipts WHERE approval_id=?),?),?)').run(approvalId, deliveryId, relativeOutputDir, existingManifest, manifestHash, 'saved', approvalId, now(), now());
      db.prepare("UPDATE approvals SET status='approved_local_saved',consumed_at=? WHERE approval_id=?").run(now(), approvalId);
    });
    return { delivery_id: deliveryId, output_dir: relativeOutputDir, manifest_hash: manifestHash, reused: true };
  }
  const stagingParent = path.join(localDeliveryRoot, '.staging');
  mkdirSync(stagingParent, { recursive: true });
  const stagingDir = path.join(stagingParent, `${safePathSegment(approvalId, 'approval_id')}-${randomBytes(6).toString('hex')}`);
  mkdirSync(stagingDir, { recursive: false });
  try {
    const copiedImages = images.map((image, index) => {
      const fileName = `visual-${String(index + 1).padStart(2, '0')}${image.extension}`;
      const destination = path.join(stagingDir, fileName);
      copyFileSync(image.path, destination);
      return { source_name: image.name, file: fileName, sha256: sha256Bytes(readFileSync(destination)) };
    });
    const contentDocument = `${JSON.stringify(stable(content), null, 2)}\n`;
    writeFileSync(path.join(stagingDir, 'content.json'), contentDocument, { encoding: 'utf8', flag: 'wx' });
    writeFileSync(path.join(stagingDir, 'caption.txt'), `${content.caption.trim()}\n`, { encoding: 'utf8', flag: 'wx' });
    const approvalDocument = { approval_id: approvalId, decision: 'approve', approved_by: decision.approved_by, decision_at: decision.decision_at, content_hash: approval.content_hash, canonical_hash: decision.canonical_hash, signature_hmac: decision.signature_hmac, delivery_mode: 'local_file_only', publish_authorized: false };
    writeFileSync(path.join(stagingDir, 'approval.json'), `${JSON.stringify(approvalDocument, null, 2)}\n`, { encoding: 'utf8', flag: 'wx' });
    const manifest = { schema_version: '1.0', delivery_id: deliveryId, approval_id: approvalId, brand_id: brand, content_id: contentId, content_version: version, content_hash: approval.content_hash, created_at: now(), publish_authorized: false, files: [{ file: 'content.json', sha256: sha256(contentDocument) }, { file: 'caption.txt', sha256: sha256(`${content.caption.trim()}\n`) }, ...copiedImages] };
    const manifestJson = `${JSON.stringify(manifest, null, 2)}\n`;
    writeFileSync(path.join(stagingDir, 'manifest.json'), manifestJson, { encoding: 'utf8', flag: 'wx' });
    renameSync(stagingDir, finalDir);
    const manifestHash = sha256(manifestJson);
    tx(() => {
      const stamp = now();
      db.prepare('INSERT OR REPLACE INTO local_delivery_receipts(approval_id,delivery_id,output_dir,manifest_json,manifest_hash,status,created_at,updated_at) VALUES(?,?,?,?,?,?,COALESCE((SELECT created_at FROM local_delivery_receipts WHERE approval_id=?),?),?)').run(approvalId, deliveryId, relativeOutputDir, manifestJson, manifestHash, 'saved', approvalId, stamp, stamp);
      db.prepare("UPDATE approvals SET status='approved_local_saved',consumed_at=? WHERE approval_id=?").run(stamp, approvalId);
      audit({ eventType: 'local_delivery_saved', actor: 'runtime', brandId: approval.brand_id, objectId: deliveryId, payload: { approval_id: approvalId, content_hash: approval.content_hash, output_dir: relativeOutputDir, manifest_hash: manifestHash, publish_authorized: false } });
    });
    return { delivery_id: deliveryId, output_dir: relativeOutputDir, manifest_hash: manifestHash, reused: false };
  } catch (error) {
    if (existsSync(stagingDir)) rmSync(stagingDir, { recursive: true, force: true });
    throw error;
  }
};

for (const task of db.prepare('SELECT task_id,brand_id,task_type,payload_json,payload_hash FROM tasks WHERE context_signature IS NULL').all()) {
  const actualPayloadHash = sha256(task.payload_json);
  if (safeEqual(actualPayloadHash, task.payload_hash)) {
    const signature = hmac(canonical({ task_id: task.task_id, brand_id: task.brand_id, task_type: task.task_type, payload_hash: actualPayloadHash }));
    db.prepare('UPDATE tasks SET context_signature=? WHERE task_id=?').run(signature, task.task_id);
  }
}
db.prepare("UPDATE verified_evidence SET revoked_at=COALESCE(revoked_at,?) WHERE source_kind='validated_agent_output'").run(now());

const tx = (fn) => {
  db.exec('BEGIN IMMEDIATE');
  try { const result = fn(); db.exec('COMMIT'); return result; }
  catch (error) { db.exec('ROLLBACK'); throw error; }
};

const audit = ({ eventType, actor, brandId = null, taskId = null, objectId = null, payload = {} }) => {
  const previous = db.prepare('SELECT event_hash FROM audit_events ORDER BY seq DESC LIMIT 1').get()?.event_hash || 'GENESIS';
  const occurredAt = now();
  const payloadHash = sha256(canonical(payload));
  const eventId = id('audit');
  const eventHash = hmac(canonical({ eventId, eventType, actor, brandId, taskId, objectId, payloadHash, previous, occurredAt }));
  db.prepare(`INSERT INTO audit_events(event_id,event_type,actor,brand_id,task_id,object_id,payload_hash,previous_hash,event_hash,occurred_at)
    VALUES(?,?,?,?,?,?,?,?,?,?)`).run(eventId, eventType, actor, brandId, taskId, objectId, payloadHash, previous, eventHash, occurredAt);
  return eventHash;
};

const verifyAudit = () => {
  const rows = db.prepare('SELECT * FROM audit_events ORDER BY seq').all();
  let previous = 'GENESIS';
  for (const row of rows) {
    if (row.previous_hash !== previous) return { ok: false, seq: row.seq, reason: 'previous_hash_mismatch' };
    const expected = hmac(canonical({ eventId: row.event_id, eventType: row.event_type, actor: row.actor, brandId: row.brand_id, taskId: row.task_id, objectId: row.object_id, payloadHash: row.payload_hash, previous, occurredAt: row.occurred_at }));
    if (!safeEqual(expected, row.event_hash)) return { ok: false, seq: row.seq, reason: 'event_hash_mismatch' };
    previous = row.event_hash;
  }
  return { ok: true, count: rows.length, head: previous };
};

const recoverStaleLeases = (actor = 'startup_recovery') => tx(() => {
  const stamp = now();
  const stale = db.prepare("SELECT * FROM tasks WHERE state='running' AND lease_expires_at IS NOT NULL AND lease_expires_at<?").all(stamp);
  for (const task of stale) {
    if (task.retry_count < task.max_retries) {
      db.prepare("UPDATE tasks SET state='retry',retry_count=retry_count+1,lease_owner=NULL,lease_token_hash=NULL,lease_expires_at=NULL,next_run_at=?,row_version=row_version+1,updated_at=? WHERE task_id=?").run(stamp, stamp, task.task_id);
    } else {
      db.prepare("UPDATE tasks SET state='failed',lease_owner=NULL,lease_token_hash=NULL,lease_expires_at=NULL,row_version=row_version+1,updated_at=? WHERE task_id=?").run(stamp, task.task_id);
      db.prepare('INSERT OR IGNORE INTO dead_letters(dlq_id,task_id,error_fingerprint,attempts,last_safe_state,redacted_error,human_action_required,created_at) VALUES(?,?,?,?,?,?,?,?)').run(id('dlq'), task.task_id, sha256('stale_lease_retry_exhausted'), task.retry_count + 1, task.last_safe_state, 'stale lease retry exhausted', 'review', stamp);
    }
    audit({ eventType: 'stale_lease_recovered', actor, brandId: task.brand_id, taskId: task.task_id, objectId: task.task_id, payload: { previous_owner_hash: sha256(task.lease_owner || ''), next_state: task.retry_count < task.max_retries ? 'retry' : 'failed' } });
  }
  return stale.length;
});

const outputSchemas = JSON.parse(readFileSync(path.join(workspaceRoot, 'data/contracts/output-schemas.json'), 'utf8'));
const accountRegistryPath = path.join(workspaceRoot, 'data/memory/hesap-kayitlari.json');
const loadAccountRegistry = () => {
  const registry = JSON.parse(readFileSync(accountRegistryPath, 'utf8'));
  if (allowSyntheticAccounts) return registry;
  const signature = registry.signature;
  if (!signature?.payload_json || !signature?.payload_sha256 || !signature?.value || signature.algorithm !== 'HMAC-SHA256-DPAPI-local-user') throw new Error('account_registry_signature_missing');
  if (!safeEqual(sha256(signature.payload_json), signature.payload_sha256) || !safeEqual(hmac(signature.payload_json), signature.value)) throw new Error('account_registry_signature_invalid');
  const signed = JSON.parse(signature.payload_json);
  const expected = { schema_version: registry.schema_version, updated_at: registry.updated_at, status: registry.status, records: registry.records };
  if (!safeEqual(canonical(signed), canonical(expected))) throw new Error('account_registry_payload_mismatch');
  return registry;
};
const accountRegistry = loadAccountRegistry();
const accountBinding = (registry, brandId, accountId) => {
  const record = registry.records.find((entry) => entry.brand_id === brandId && entry.account_id === accountId && entry.status === 'verified');
  if (!record) return null;
  return { record, hash: sha256(canonical({ brand_id: record.brand_id, platform: record.platform, account_id: record.account_id, page_id: record.page_id || null, credential_ref: record.credential_ref, status: record.status, verified_at: record.verified_at })) };
};
const contextPolicy = JSON.parse(readFileSync(path.join(workspaceRoot, 'data/memory/baglam-derleme-politikasi.json'), 'utf8'));
const evidenceKinds = new Set(['operator_observation', 'official_source', 'performance_measurement', 'user_revision', 'manual_document', ...(allowSyntheticEvidence ? ['synthetic'] : [])]);
const evidenceConfidence = { operator_observation: 0.8, official_source: 0.9, performance_measurement: 0.9, user_revision: 0.95, manual_document: 0.75, synthetic: 0.9 };
const pipelineAgents = {
  classification: 'operasyon_orkestratoru', analysis: 'analizci', content_ideas: 'sosyal_medya_icerik_stratejisti',
  visual_brief: 'gorsel_stratejist', debate_turn: 'kontrol_muhalefet_kurulu', ordinaryus_decision: 'ana_ordinaryus',
  independent_audit: 'bagimsiz_denetci', interface_summary: 'yayin_arayuz_ajani'
};

const compilePipelineContext = ({ pipeline, taskType, taskId, source = null, round = 0 }) => {
  const safeName = `${pipeline.pipeline_id}-${taskType}-${round}`.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 180);
  const sourceRel = `data/runtime/context-sources/${safeName}.json`;
  const outputRel = `data/runtime/context-packs/${safeName}.json`;
  const sourcePath = path.join(workspaceRoot, sourceRel);
  mkdirSync(path.dirname(sourcePath), { recursive: true });
  writeFileSync(sourcePath, `${canonical(source || {})}\n`, 'utf8');
  const script = path.join(workspaceRoot, 'projects/runtime/build-context-pack.mjs');
  const args = [script, `--root=${workspaceRoot}`, `--task=${taskType}`, `--agent=${pipelineAgents[taskType]}`, `--source=${sourceRel}`, `--out=${outputRel}`, `--goal=${pipeline.goal}`, `--risk=${pipeline.risk_level}`, `--task_id=${taskId}`];
  const built = spawnSync(process.execPath, args, { encoding: 'utf8', timeout: 30000, env: { ...process.env, AJANS_RUNTIME_URL: '' } });
  if (built.status !== 0) throw new Error(`context_compile_failed:${redact(built.stderr || built.stdout)}`);
  const pack = JSON.parse(readFileSync(path.join(workspaceRoot, outputRel), 'utf8'));
  const budget = contextPolicy.task_budgets?.[taskType];
  if (!pack?.model_payload || !budget) throw new Error('context_pack_invalid');
  return {
    ...pack.model_payload,
    no_publish: true,
    compact_context_required: true,
    context_manifest: {
      pack_schema_version: pack.schema_version,
      task_id: taskId,
      brand_id: pipeline.brand_id,
      role: pack.runtime?.role,
      source_fingerprint: pack.runtime?.cache?.source_fingerprint,
      guards: pack.runtime?.guards,
      compiled_at: pack.generated_at
    },
    model_budget: { max_calls: 1, max_input_tokens: budget.max_input_tokens, max_output_tokens: budget.max_output_tokens, max_cost_usd: budget.max_cost_usd }
  };
};

const insertInternalTask = ({ taskId, idempotencyKey, brandId, taskType, agentId, payload, riskLevel, priority = 'normal', pipelineId = null, pipelineStage = null, parentTaskId = null, contentId = null, contentVersion = null }) => {
  const payloadJson = canonical(payload); const payloadHash = sha256(payloadJson); const stamp = now();
  const contextSignature = hmac(canonical({ task_id: taskId, brand_id: brandId, task_type: taskType, payload_hash: payloadHash }));
  db.prepare(`INSERT INTO tasks(task_id,idempotency_key,brand_id,task_type,priority,state,risk_level,agent_id,content_id,content_version,payload_json,payload_hash,context_signature,pipeline_id,pipeline_stage,parent_task_id,max_retries,next_run_at,last_safe_state,created_at,updated_at)
    VALUES(?,?,?,?,?,'queued',?,?,?,?,?,?,?,?,?,?,1,?,'queued',?,?)`).run(taskId,idempotencyKey,brandId,taskType,priority,riskLevel,agentId,contentId,contentVersion,payloadJson,payloadHash,contextSignature,pipelineId,pipelineStage,parentTaskId,stamp,stamp,stamp);
  audit({ eventType: 'task_created', actor: 'pipeline_orchestrator', brandId, taskId, objectId: taskId, payload: { task_type: taskType, payload_hash: payloadHash, pipeline_id: pipelineId, pipeline_stage: pipelineStage } });
  return db.prepare('SELECT * FROM tasks WHERE task_id=?').get(taskId);
};

const pipelineSourceFor = (pipelineId, nextType, latestOutput) => {
  const rows = db.prepare("SELECT task_type,result_json FROM tasks WHERE pipeline_id=? AND state='completed' ORDER BY created_at").all(pipelineId);
  const outputs = Object.fromEntries(rows.map((row) => [row.task_type, parseJson(row.result_json, {})?.output || {}]));
  if (nextType === 'content_ideas' || nextType === 'visual_brief') return latestOutput;
  if (nextType === 'debate_turn') return { content_version: db.prepare('SELECT content_version FROM pipeline_runs WHERE pipeline_id=?').get(pipelineId)?.content_version, ideas: outputs.content_ideas?.ideas || [], visual_briefs: outputs.visual_brief?.visual_briefs || [], previous_round_summary: outputs.debate_turn?.required_changes?.join(' ') || '', changed_fields: [], risk_flags: [] };
  if (nextType === 'ordinaryus_decision') return { content_version: db.prepare('SELECT content_version FROM pipeline_runs WHERE pipeline_id=?').get(pipelineId)?.content_version, candidates: outputs.content_ideas?.ideas || [], agent_summaries: { analysis: outputs.analysis?.main_finding || '', visual: outputs.visual_brief?.data_disclaimer || '' }, dissent_summary: outputs.debate_turn || {}, evidence: [...new Set(Object.values(outputs).flatMap((item) => collectEvidenceRefs(item)))].slice(0,5), risk_flags: outputs.debate_turn?.required_changes || [], budget: {}, approval_state: 'not_requested' };
  if (nextType === 'independent_audit') return { decision: outputs.ordinaryus_decision?.decision || null, decision_version: db.prepare('SELECT content_version FROM pipeline_runs WHERE pipeline_id=?').get(pipelineId)?.content_version, evidence_refs: outputs.ordinaryus_decision?.evidence_refs || [], score_summary: { confidence: outputs.ordinaryus_decision?.confidence ?? null }, risk_flags: outputs.ordinaryus_decision?.remaining_risks || [], data_gaps: [], approval_state: 'not_requested' };
  if (nextType === 'interface_summary') return { content_id: db.prepare('SELECT content_id FROM pipeline_runs WHERE pipeline_id=?').get(pipelineId)?.content_id, content_version: db.prepare('SELECT content_version FROM pipeline_runs WHERE pipeline_id=?').get(pipelineId)?.content_version, target_account: null, summary: outputs.ordinaryus_decision?.Operator_summary || 'Karar paketi hazır.', visual_ref: outputs.visual_brief?.visual_briefs?.[0]?.id || null, ordinaryus_decision: outputs.ordinaryus_decision?.decision || null, risks: outputs.ordinaryus_decision?.remaining_risks || [], approval_status: 'not_requested', independent_audit: outputs.independent_audit || null };
  return latestOutput || {};
};

const modelFamilyFor = (provider, model) => {
  const normalizedProvider = String(provider || '').trim().toLocaleLowerCase('en-US');
  const normalizedModel = String(model || '').trim().toLocaleLowerCase('en-US');
  if (!normalizedProvider || !normalizedModel) return null;
  const combined = `${normalizedProvider}/${normalizedModel}`;
  const families = [
    ['google-gemini', ['google', 'gemini']],
    ['openai-gpt', ['openai', 'gpt-', 'o1', 'o3', 'o4']],
    ['anthropic-claude', ['anthropic', 'claude']],
    ['xai-grok', ['xai', 'grok']],
    ['mistral', ['mistral', 'mixtral']],
    ['cohere-command', ['cohere', 'command']],
    ['meta-llama', ['meta', 'llama']],
    ['microsoft-phi', ['microsoft', 'phi-']],
    ['deepseek', ['deepseek']]
  ];
  for (const [family, markers] of families) if (markers.some((marker) => combined.includes(marker))) return family;
  return `provider:${normalizedProvider}`;
};

const actualIndependentAuditRoute = (pipelineId, auditTaskId) => {
  const ordinaryusTask = db.prepare("SELECT task_id FROM tasks WHERE pipeline_id=? AND task_type='ordinaryus_decision' AND state='completed' ORDER BY completed_at DESC LIMIT 1").get(pipelineId);
  const latestCompletedAttempt = (taskId) => taskId ? db.prepare("SELECT provider,model FROM task_attempts WHERE task_id=? AND state='completed' ORDER BY finished_at DESC, rowid DESC LIMIT 1").get(taskId) : null;
  const ordinaryusAttempt = latestCompletedAttempt(ordinaryusTask?.task_id);
  const auditAttempt = latestCompletedAttempt(auditTaskId);
  const ordinaryusFamily = modelFamilyFor(ordinaryusAttempt?.provider, ordinaryusAttempt?.model);
  const auditFamily = modelFamilyFor(auditAttempt?.provider, auditAttempt?.model);
  const ordinaryusProvider = String(ordinaryusAttempt?.provider || '').trim().toLocaleLowerCase('en-US');
  const auditProvider = String(auditAttempt?.provider || '').trim().toLocaleLowerCase('en-US');
  const independent = Boolean(ordinaryusProvider && auditProvider && ordinaryusFamily && auditFamily && ordinaryusProvider !== auditProvider && ordinaryusFamily !== auditFamily);
  return {
    independent,
    ordinaryus: ordinaryusAttempt ? { provider: ordinaryusAttempt.provider, model: ordinaryusAttempt.model, family: ordinaryusFamily } : null,
    audit: auditAttempt ? { provider: auditAttempt.provider, model: auditAttempt.model, family: auditFamily } : null
  };
};

const advancePipeline = (completedTaskId) => {
  const completedTask = db.prepare('SELECT * FROM tasks WHERE task_id=?').get(completedTaskId);
  if (!completedTask?.pipeline_id || completedTask.state !== 'completed') return { advanced: false, reason: 'not_pipeline_task' };
  const pipeline = db.prepare('SELECT * FROM pipeline_runs WHERE pipeline_id=?').get(completedTask.pipeline_id);
  if (!pipeline || pipeline.status !== 'active') return { advanced: false, reason: 'pipeline_not_active' };
  const step = db.prepare('SELECT * FROM pipeline_steps WHERE task_id=?').get(completedTaskId);
  if (!step) throw new Error('pipeline_step_missing');
  db.prepare("UPDATE pipeline_steps SET status='completed',completed_at=? WHERE task_id=?").run(now(), completedTaskId);
  const latestOutput = parseJson(completedTask.result_json, {})?.output || {};
  let nextType = null; let nextRound = pipeline.debate_round;
  if (completedTask.task_type === 'classification') nextType = 'analysis';
  else if (completedTask.task_type === 'analysis') nextType = 'content_ideas';
  else if (completedTask.task_type === 'content_ideas') nextType = 'visual_brief';
  else if (completedTask.task_type === 'visual_brief') { nextType = 'debate_turn'; nextRound = 1; }
  else if (completedTask.task_type === 'debate_turn') {
    if (latestOutput.another_round_required === true && pipeline.debate_round < pipeline.max_debate_rounds) { nextType = 'debate_turn'; nextRound = pipeline.debate_round + 1; }
    else nextType = 'ordinaryus_decision';
  } else if (completedTask.task_type === 'ordinaryus_decision') nextType = (pipeline.risk_level === 'critical' || Number(latestOutput.confidence || 0) < 0.8) ? 'independent_audit' : 'interface_summary';
  else if (completedTask.task_type === 'independent_audit') {
    const actualRoute = actualIndependentAuditRoute(pipeline.pipeline_id, completedTaskId);
    const auditAllowsProgress = latestOutput.decision === 'UPHOLD'
      && latestOutput.independence_unavailable === false
      && !['high','critical'].includes(latestOutput.risk)
      && Number(latestOutput.confidence || 0) >= 0.75
      && actualRoute.independent === true;
    if (!auditAllowsProgress) {
      const reason = latestOutput.decision === 'VETO'
        ? 'independent_audit_veto'
        : latestOutput.decision === 'HUMAN_REVIEW'
          ? 'independent_audit_human_review'
          : actualRoute.independent !== true || latestOutput.independence_unavailable !== false
            ? 'independent_audit_independence_unavailable'
            : 'independent_audit_human_review';
      db.prepare("UPDATE pipeline_runs SET status='blocked',current_stage=?,updated_at=? WHERE pipeline_id=?").run(reason,now(),pipeline.pipeline_id);
      audit({ eventType: 'pipeline_blocked_by_independent_audit', actor: 'pipeline_orchestrator', brandId: pipeline.brand_id, taskId: completedTaskId, objectId: pipeline.pipeline_id, payload: { reason, decision: latestOutput.decision || null, risk: latestOutput.risk || null, confidence: latestOutput.confidence ?? null, model_claimed_independence_unavailable: latestOutput.independence_unavailable !== false, actual_route_independent: actualRoute.independent, ordinaryus_route: actualRoute.ordinaryus, audit_route: actualRoute.audit } });
      return { advanced: true, status: 'blocked', reason };
    }
    nextType = 'interface_summary';
  }
  else if (completedTask.task_type === 'interface_summary') {
    db.prepare("UPDATE pipeline_runs SET status='awaiting_Operator_approval',current_stage='awaiting_Operator_approval',updated_at=? WHERE pipeline_id=?").run(now(), pipeline.pipeline_id);
    audit({ eventType: 'pipeline_awaiting_Operator_approval', actor: 'pipeline_orchestrator', brandId: pipeline.brand_id, objectId: pipeline.pipeline_id, payload: { content_id: pipeline.content_id, content_version: pipeline.content_version } });
    return { advanced: true, status: 'awaiting_Operator_approval' };
  }
  if (!nextType) throw new Error('pipeline_next_stage_undefined');
  const sequence = Number(db.prepare('SELECT COALESCE(MAX(sequence),0) max_sequence FROM pipeline_steps WHERE pipeline_id=?').get(pipeline.pipeline_id).max_sequence) + 1;
  const taskId = `${pipeline.pipeline_id}-${sequence}-${nextType}`.slice(0,180);
  const source = pipelineSourceFor(pipeline.pipeline_id, nextType, latestOutput);
  const refreshedPipeline = { ...pipeline, debate_round: nextRound };
  const payload = compilePipelineContext({ pipeline: refreshedPipeline, taskType: nextType, taskId, source, round: nextRound });
  tx(() => {
    insertInternalTask({ taskId, idempotencyKey: `${pipeline.pipeline_id}:${sequence}:${nextType}:${nextRound}`, brandId: pipeline.brand_id, taskType: nextType, agentId: pipelineAgents[nextType], payload, riskLevel: pipeline.risk_level, priority: pipeline.risk_level === 'critical' ? 'critical' : 'normal', pipelineId: pipeline.pipeline_id, pipelineStage: nextType, parentTaskId: completedTaskId, contentId: pipeline.content_id, contentVersion: pipeline.content_version });
    db.prepare('INSERT INTO pipeline_steps(pipeline_id,sequence,task_id,task_type,agent_id,status,source_task_id,created_at) VALUES(?,?,?,?,?,?,?,?)').run(pipeline.pipeline_id,sequence,taskId,nextType,pipelineAgents[nextType],'queued',completedTaskId,now());
    db.prepare('UPDATE pipeline_runs SET current_stage=?,debate_round=?,updated_at=? WHERE pipeline_id=?').run(nextType,nextRound,now(),pipeline.pipeline_id);
  });
  return { advanced: true, next_task_id: taskId, next_stage: nextType, debate_round: nextRound };
};
const riskyClaimPatterns = [
  /\b\d+(?:[.,]\d+)?\s*(?:saniye(?:de|da|lik|lık)?|dakika(?:da|de|lık|lik)?|saat(?:te|lik)?|gün(?:de|lük)?|derece|°c|tl|₺|%|adet|yıkama)\b/iu,
  /[%₺]\s*\d+(?:[.,]\d+)?/u,
  /\b(?:her|tüm)\s+(?:kumaş|ürün|tasarım)/iu,
  /\b(?:asla|garanti|garantili|kesin|daima|stokta|aynı gün|ertesi gün|para kazan)\b/iu,
  /\b(?:müşterilerimiz|kullanıcılarımız)\s+(?:diyor|seviyor|öneriyor)/iu
];
const injectionPatterns = [
  /önceki\s+talimat(?:ları|lari)\s+unut/iu,
  /system\s+prompt/iu,
  /(?:api|erişim|giriş)\s*(?:anahtar|şifre|sır)/iu,
  /(?:hemen|şimdi)\s+yayınla/iu,
  /kalıcı\s+hafızaya\s+(?:gerçek|doğru)\s+olarak\s+ekle/iu,
  /ignore\s+(?:all\s+)?previous\s+instructions/iu,
  /reveal\s+(?:your\s+)?secrets?/iu
];

const typeMatches = (value, type) => {
  const types = Array.isArray(type) ? type : [type];
  return types.some((item) => {
    if (item === 'null') return value === null;
    if (item === 'array') return Array.isArray(value);
    if (item === 'integer') return Number.isInteger(value);
    if (item === 'number') return typeof value === 'number' && Number.isFinite(value);
    if (item === 'object') return value && typeof value === 'object' && !Array.isArray(value);
    return typeof value === item;
  });
};

const validateNode = (value, spec, pathName, errors, depth = 0) => {
  if (depth > outputSchemas.common.max_depth) { errors.push(`${pathName}:max_depth`); return; }
  if (spec.type && !typeMatches(value, spec.type)) { errors.push(`${pathName}:type`); return; }
  if (typeof value === 'string') {
    const maxLength = spec.maxLength ?? outputSchemas.common.max_string_chars;
    if (value.length > maxLength) errors.push(`${pathName}:maxLength`);
    if (spec.enum && !spec.enum.includes(value)) errors.push(`${pathName}:enum`);
  }
  if (typeof value === 'number') {
    if (spec.minimum !== undefined && value < spec.minimum) errors.push(`${pathName}:minimum`);
    if (spec.maximum !== undefined && value > spec.maximum) errors.push(`${pathName}:maximum`);
  }
  if (Array.isArray(value)) {
    if (spec.minItems && value.length < spec.minItems) errors.push(`${pathName}:minItems`);
    const maxItems = spec.maxItems ?? outputSchemas.common.max_array_items;
    if (value.length > maxItems) errors.push(`${pathName}:maxItems`);
    if (spec.items) value.forEach((item, index) => validateNode(item, spec.items, `${pathName}[${index}]`, errors, depth + 1));
  }
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    if (Object.keys(value).length > (outputSchemas.common.max_object_keys || 24)) errors.push(`${pathName}:maxProperties`);
    for (const key of spec.required || []) if (!(key in value)) errors.push(`${pathName}.${key}:required`);
    if (spec.properties) {
      for (const key of Object.keys(value)) if (!(key in spec.properties)) errors.push(`${pathName}.${key}:unknown`);
      for (const [key, child] of Object.entries(spec.properties)) if (key in value) validateNode(value[key], child, `${pathName}.${key}`, errors, depth + 1);
    } else if (Object.keys(value).length) errors.push(`${pathName}:object_schema_missing`);
  }
};

const collectRuntimeOwnedPaths = (value, pathName = '$', output = []) => {
  if (Array.isArray(value)) value.forEach((item, index) => collectRuntimeOwnedPaths(item, `${pathName}[${index}]`, output));
  else if (value && typeof value === 'object') {
    for (const [key, item] of Object.entries(value)) {
      const nextPath = `${pathName}.${key}`;
      if (outputSchemas.runtime_owned_fields.includes(key)) output.push(nextPath);
      collectRuntimeOwnedPaths(item, nextPath, output);
    }
  }
  return output;
};

const validateGenericLimits = (value, pathName, errors, depth = 0) => {
  if (depth > outputSchemas.common.max_depth) { errors.push(`${pathName}:max_depth`); return; }
  if (typeof value === 'string' && value.length > outputSchemas.common.max_string_chars) errors.push(`${pathName}:common_maxLength`);
  if (Array.isArray(value)) {
    if (value.length > outputSchemas.common.max_array_items) errors.push(`${pathName}:common_maxItems`);
    value.forEach((item, index) => validateGenericLimits(item, `${pathName}[${index}]`, errors, depth + 1));
  } else if (value && typeof value === 'object') {
    if (Object.keys(value).length > (outputSchemas.common.max_object_keys || 24)) errors.push(`${pathName}:common_maxProperties`);
    for (const [key, item] of Object.entries(value)) validateGenericLimits(item, `${pathName}.${key}`, errors, depth + 1);
  }
};

const collectStrings = (value, output = []) => {
  if (typeof value === 'string') output.push(value);
  else if (Array.isArray(value)) value.forEach((item) => collectStrings(item, output));
  else if (value && typeof value === 'object') Object.values(value).forEach((item) => collectStrings(item, output));
  return output;
};

const collectEvidenceRefs = (value, output = []) => {
  if (Array.isArray(value)) value.forEach((item) => collectEvidenceRefs(item, output));
  else if (value && typeof value === 'object') {
    for (const [key, item] of Object.entries(value)) {
      if (key === 'evidence_refs' && Array.isArray(item)) output.push(...item.map(String));
      else collectEvidenceRefs(item, output);
    }
  }
  return output;
};

const resolveVerifiedEvidence = (output, brandId, suppliedRegistry = []) => {
  const refs = [...new Set(collectEvidenceRefs(output))];
  const rows = refs.length && brandId
    ? db.prepare(`SELECT evidence_id AS id, claim, source_hash, source_date, source_kind, 1 AS verified FROM verified_evidence WHERE revoked_at IS NULL AND brand_id=? AND evidence_id IN (${refs.map(() => '?').join(',')})`).all(brandId, ...refs)
    : [];
  if (!allowSyntheticEvidence) return rows;
  const synthetic = suppliedRegistry.filter((item) => item?.id && item?.verified === true && item?.source_hash && item?.source_date && (!item.brand_id || item.brand_id === brandId));
  return [...rows, ...synthetic];
};

const validateOutput = ({ task_id: taskId, brand_id: suppliedBrandId, task_type: taskType, output, evidence_registry: suppliedRegistry = [] }) => {
  const schema = outputSchemas.schemas[taskType];
  const errors = [];
  const blockedClaims = [];
  const task = taskId ? db.prepare('SELECT task_id,brand_id,task_type FROM tasks WHERE task_id=?').get(taskId) : null;
  if (taskId && !task) errors.push('validation_task_not_found');
  if (task && task.task_type !== taskType) errors.push('validation_task_type_mismatch');
  if (task && suppliedBrandId && suppliedBrandId !== task.brand_id) errors.push('validation_brand_mismatch');
  const effectiveBrandId = task?.brand_id || suppliedBrandId || null;
  if (!schema) return { valid: false, errors: ['unknown_task_type'], blocked_claims: [] };
  if (!output || typeof output !== 'object' || Array.isArray(output)) return { valid: false, errors: ['output:object_required'], blocked_claims: [] };
  for (const ownedPath of collectRuntimeOwnedPaths(output)) errors.push(`${ownedPath}:runtime_owned`);
  validateGenericLimits(output, '$', errors);
  validateNode(output, { type: 'object', required: schema.required, properties: schema.properties }, '$', errors);
  const evidenceRefs = collectEvidenceRefs(output);
  if (evidenceRefs.length && !effectiveBrandId) errors.push('evidence_task_or_brand_required');
  const verifiedEvidence = resolveVerifiedEvidence(output, effectiveBrandId, suppliedRegistry);
  const verifiedClaims = verifiedEvidence.map((item) => String(item.claim || '').toLocaleLowerCase('tr-TR'));
  const verifiedIds = new Set(verifiedEvidence.map((item) => String(item.id)));
  for (const ref of evidenceRefs) if (!verifiedIds.has(ref)) errors.push(`invalid_evidence_ref:${ref}`);
  if (output.grounding_status === 'grounded' && evidenceRefs.length === 0) errors.push('grounded_output_requires_evidence');
  if (taskType === 'research_update' && output.changed === true && evidenceRefs.length === 0) errors.push('research_change_requires_evidence');
  if (taskType === 'memory_update' && output.type === 'permanent' && evidenceRefs.length === 0) errors.push('permanent_memory_requires_evidence');
  if (['ordinaryus_decision','independent_audit'].includes(taskType) && Number(output.confidence) >= 0.8 && evidenceRefs.length === 0) errors.push('high_confidence_requires_evidence');
  for (const text of collectStrings(output)) {
    if (riskyClaimPatterns.some((pattern) => pattern.test(text))) {
      const normalized = text.toLocaleLowerCase('tr-TR');
      if (!verifiedClaims.some((claim) => normalized.includes(claim) || claim.includes(normalized))) blockedClaims.push(text.slice(0, 240));
    }
    if (injectionPatterns.some((pattern) => pattern.test(text))) errors.push('embedded_instruction_detected');
  }
  if (blockedClaims.length) errors.push('unverified_claim');
  return { valid: errors.length === 0, errors: [...new Set(errors)], blocked_claims: [...new Set(blockedClaims)], output_hash: sha256(canonical(output)), action: errors.length ? 'claim_blocked_or_needs_data' : 'accept' };
};

const response = (res, status, payload, headers = {}) => {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'no-referrer', ...headers });
  res.end(JSON.stringify(payload));
};
const readBody = (req) => new Promise((resolve, reject) => {
  let size = 0; const chunks = [];
  req.on('data', (chunk) => { size += chunk.length; if (size > maxBodyBytes) { reject(Object.assign(new Error('body_too_large'), { status: 413 })); req.destroy(); } else chunks.push(chunk); });
  req.on('end', () => { try { resolve(chunks.length ? JSON.parse(Buffer.concat(chunks).toString('utf8')) : {}); } catch { reject(Object.assign(new Error('invalid_json'), { status: 400 })); } });
  req.on('error', reject);
});
const readRawBody = (req, maxBytes) => new Promise((resolve, reject) => {
  let size = 0; const chunks = [];
  req.on('data', (chunk) => {
    size += chunk.length;
    if (size > maxBytes) { reject(Object.assign(new Error('asset_too_large'), { status: 413 })); req.destroy(); return; }
    chunks.push(chunk);
  });
  req.on('end', () => resolve(Buffer.concat(chunks)));
  req.on('error', reject);
});
const bearer = (req) => String(req.headers.authorization || '').replace(/^Bearer\s+/i, '');
const serviceIdentity = (req) => {
  const token = bearer(req);
  for (const [identity, key] of Object.entries(scopedServiceKeys)) if (key.length >= 32 && safeEqual(token, key)) return identity;
  if (allowLegacyRuntimeKey && safeEqual(token, runtimeApiKey)) return 'legacy_test';
  return null;
};
const parseCookies = (req) => Object.fromEntries(String(req.headers.cookie || '').split(';').map((item) => item.trim()).filter(Boolean).map((item) => { const index = item.indexOf('='); return [item.slice(0, index), decodeURIComponent(item.slice(index + 1))]; }));
const getSession = (req) => {
  const token = parseCookies(req).ajans_session;
  if (!token) return null;
  const row = db.prepare('SELECT * FROM operator_sessions WHERE session_hash=? AND revoked_at IS NULL AND expires_at>?').get(sha256(token), now());
  if (row) db.prepare('UPDATE operator_sessions SET last_used_at=? WHERE session_hash=?').run(now(), row.session_hash);
  return row ? { row, token } : null;
};
const requireService = (req, res, allowed = null) => {
  const identity = serviceIdentity(req);
  if (!identity || (Array.isArray(allowed) && identity !== 'legacy_test' && !allowed.includes(identity))) { response(res, 401, { error: 'service_auth_required' }); return false; }
  req.ajansService = identity; return true;
};
const requireOperator = (req, res, csrf = false) => {
  const session = getSession(req);
  if (!session) { response(res, 401, { error: 'operator_session_required' }); return null; }
  if (csrf && !safeEqual(session.row.csrf_hash, sha256(req.headers['x-csrf-token'] || ''))) { response(res, 403, { error: 'csrf_invalid' }); return null; }
  return session;
};
const rateLimit = (key, limit, seconds) => tx(() => {
  const stamp = Date.now(); const row = db.prepare('SELECT * FROM rate_limits WHERE key=?').get(key);
  if (!row || stamp - Date.parse(row.window_start) > seconds * 1000) { db.prepare('INSERT OR REPLACE INTO rate_limits(key,window_start,count) VALUES(?,?,1)').run(key, now()); return true; }
  if (row.count >= limit) return false;
  db.prepare('UPDATE rate_limits SET count=count+1 WHERE key=?').run(key); return true;
});
const verifyPassword = (password) => {
  const parts = operatorPasswordHash.split('$');
  if (parts.length !== 4 || parts[0] !== 'pbkdf2_sha256') return false;
  const expected = Buffer.from(parts[3], 'base64');
  const actual = pbkdf2Sync(password, Buffer.from(parts[2], 'base64'), Number(parts[1]), expected.length, 'sha256');
  return expected.length === actual.length && timingSafeEqual(expected, actual);
};

const server = createServer(async (req, res) => {
  const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
  try {
    if (req.method !== 'GET' && url.pathname.startsWith('/v1/') && url.pathname !== '/v1/audit/verify') {
      const disk = statfsSync(path.dirname(dbPath));
      const freeBytes = Number(disk.bavail) * Number(disk.bsize);
      if (freeBytes <= minFreeBytes) { response(res, 507, { error: 'insufficient_storage', disk_free_bytes: freeBytes, required_free_bytes: minFreeBytes }); return; }
    }
    if (url.pathname === '/health/live' && req.method === 'GET') { response(res, 200, { status: 'live' }); return; }
    if (url.pathname === '/health/ready' && req.method === 'GET') {
      const quick = db.prepare('PRAGMA quick_check').get();
      const auditState = verifyAudit();
      const disk = statfsSync(path.dirname(dbPath));
      const freeBytes = Number(disk.bavail) * Number(disk.bsize);
      const operatorConfigured = Boolean(operatorPasswordHash);
      const ready = Object.values(quick)[0] === 'ok' && auditState.ok && freeBytes > minFreeBytes && operatorConfigured;
      response(res, ready ? 200 : 503, { status: ready ? 'ready' : 'not_ready', database: Object.values(quick)[0], audit: auditState, disk_free_bytes: freeBytes, required_free_bytes: minFreeBytes, operator_password_configured: operatorConfigured }); return;
    }
    if (url.pathname === '/v1/operator/login' && req.method === 'POST') {
      const ip = req.socket.remoteAddress || 'unknown';
      if (!rateLimit(`login:${ip}`, 5, 900)) { response(res, 429, { error: 'login_rate_limited' }); return; }
      if (!operatorPasswordHash) { response(res, 503, { error: 'operator_password_not_configured' }); return; }
      const body = await readBody(req);
      if (!verifyPassword(String(body.password || ''))) { audit({ eventType: 'operator_login_failed', actor: 'anonymous', payload: { ip_hash: sha256(ip) } }); response(res, 401, { error: 'invalid_credentials' }); return; }
      const token = randomBytes(32).toString('base64url'); const csrf = randomBytes(32).toString('base64url');
      const expires = new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString();
      tx(() => { db.prepare('INSERT INTO operator_sessions(session_hash,csrf_hash,created_at,last_used_at,expires_at) VALUES(?,?,?,?,?)').run(sha256(token), sha256(csrf), now(), now(), expires); audit({ eventType: 'operator_login', actor: 'Operator' }); });
      response(res, 200, { status: 'authenticated', csrf_token: csrf, expires_at: expires }, { 'Set-Cookie': `ajans_session=${encodeURIComponent(token)}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800` }); return;
    }
    if (url.pathname === '/v1/operator/logout' && req.method === 'POST') {
      const session = requireOperator(req, res, true); if (!session) return;
      tx(() => { db.prepare('UPDATE operator_sessions SET revoked_at=? WHERE session_hash=?').run(now(), session.row.session_hash); audit({ eventType: 'operator_logout', actor: 'Operator' }); });
      response(res, 200, { status: 'logged_out' }, { 'Set-Cookie': 'ajans_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0' }); return;
    }
    if (url.pathname === '/v1/operator/app-state' && req.method === 'GET') {
      const session = requireOperator(req, res); if (!session) return;
      const requestedBrand = safePathSegment(url.searchParams.get('brand_id') || 'trendybrander', 'brand_id').toLocaleLowerCase('tr-TR');
      const storedProfile = db.prepare('SELECT * FROM brand_profiles WHERE brand_id=?').get(requestedBrand);
      const profile = storedProfile ? parseJson(storedProfile.profile_json, legacyBrandProfile()) : legacyBrandProfile();
      const assets = db.prepare('SELECT asset_id,brand_id,kind,original_name,stored_name,mime_type,size_bytes,sha256,created_at FROM brand_assets WHERE brand_id=? ORDER BY created_at DESC').all(requestedBrand).map((item) => ({
        ...item,
        url: `/media/brand/${encodeURIComponent(item.brand_id)}/${encodeURIComponent(item.kind)}/${encodeURIComponent(item.stored_name)}`
      }));
      const modelPreferences = db.prepare('SELECT brand_id,role_id,mode,provider,model,updated_at FROM model_preferences WHERE brand_id=? ORDER BY role_id').all(requestedBrand);
      const connections = db.prepare('SELECT brand_id,provider,label,metadata_json,status,created_at,updated_at FROM encrypted_connections WHERE brand_id=? ORDER BY provider').all(requestedBrand).map((item) => ({
        brand_id: item.brand_id, provider: item.provider, label: item.label, metadata: parseJson(item.metadata_json, {}), status: item.status, configured: true, created_at: item.created_at, updated_at: item.updated_at
      }));
      const pipelines = db.prepare('SELECT pipeline_id,brand_id,goal,risk_level,status,current_stage,debate_round,max_debate_rounds,content_id,content_version,created_at,updated_at,completed_at FROM pipeline_runs WHERE brand_id=? ORDER BY created_at DESC LIMIT 20').all(requestedBrand).map((item) => ({
        ...item,
        steps: db.prepare('SELECT sequence,task_type,agent_id,status,created_at,completed_at FROM pipeline_steps WHERE pipeline_id=? ORDER BY sequence').all(item.pipeline_id)
      }));
      response(res, 200, {
        generated_at: now(),
        profile,
        onboarding_state: storedProfile?.onboarding_state || (profile.description ? 'in_progress' : 'draft'),
        assets,
        model_preferences: modelPreferences,
        connections,
        pipelines,
        model_roles: [
          { id: 'analysis', name: 'Marka Analizi', description: 'Marka ve performans bilgisini yorumlar.' },
          { id: 'content', name: 'İçerik Üretimi', description: 'Fikir, metin, kanca ve CTA hazırlar.' },
          { id: 'visual', name: 'Görsel Üretimi', description: 'Görsel brief ve üretim modelini yönetir.' },
          { id: 'debate', name: 'Kalite Kontrolü', description: 'Fikirleri farklı bakışlarla sınar.' },
          { id: 'ordinaryus', name: 'Son Karar', description: 'Risk ve kaliteyi değerlendirir.' },
          { id: 'interface', name: 'Kullanıcı Asistanı', description: 'Sonucu sade biçimde sunar.' }
        ],
        providers: [
          { id: 'google_gemini', name: 'Google Gemini', kinds: ['text', 'image'] },
          { id: 'openai', name: 'OpenAI', kinds: ['text', 'image'] },
          { id: 'cloudflare', name: 'Cloudflare AI', kinds: ['text', 'image'] },
          { id: 'meta_instagram', name: 'Meta ve Instagram', kinds: ['social'] }
        ],
        safeguards: { publish_requires_operator_approval: true, external_publish_enabled: false, secrets_never_returned: true, proprietary_prompts_hidden: true }
      }); return;
    }
    if (url.pathname === '/v1/operator/brand-profile' && req.method === 'PUT') {
      const session = requireOperator(req, res, true); if (!session) return;
      const profile = normalizeBrandProfile(await readBody(req));
      const stamp = now();
      const profileJson = canonical(profile);
      const folder = path.resolve(brandDataRoot, profile.brand_id);
      if (!isInside(brandDataRoot, folder)) throw Object.assign(new Error('invalid_brand_path'), { status: 400 });
      mkdirSync(folder, { recursive: true });
      const target = path.join(folder, 'profile.json');
      const temporary = path.join(folder, `.profile-${randomBytes(8).toString('hex')}.tmp`);
      writeFileSync(temporary, `${JSON.stringify(profile, null, 2)}\n`, { encoding: 'utf8', flag: 'wx' });
      renameSync(temporary, target);
      tx(() => {
        db.prepare(`INSERT INTO brand_profiles(brand_id,name,profile_json,onboarding_state,created_at,updated_at) VALUES(?,?,?,'in_progress',?,?)
          ON CONFLICT(brand_id) DO UPDATE SET name=excluded.name,profile_json=excluded.profile_json,onboarding_state='in_progress',updated_at=excluded.updated_at`).run(profile.brand_id, profile.name, profileJson, stamp, stamp);
        audit({ eventType: 'brand_profile_saved', actor: 'Operator', brandId: profile.brand_id, objectId: profile.brand_id, payload: { profile_hash: sha256(profileJson) } });
      });
      response(res, 200, { status: 'saved', profile }); return;
    }
    const brandAssetsRoute = url.pathname.match(/^\/v1\/operator\/brands\/([^/]+)\/assets$/);
    if (brandAssetsRoute && req.method === 'POST') {
      const session = requireOperator(req, res, true); if (!session) return;
      const brandId = safePathSegment(decodeURIComponent(brandAssetsRoute[1]), 'brand_id').toLocaleLowerCase('tr-TR');
      const kind = String(url.searchParams.get('kind') || '');
      const rule = assetRules[kind];
      if (!rule) { response(res, 400, { error: 'unsupported_asset_kind' }); return; }
      const originalName = limitText(url.searchParams.get('filename'), 240);
      const extension = path.extname(originalName).toLocaleLowerCase('en-US');
      if (!originalName || !rule.extensions.has(extension)) { response(res, 400, { error: 'unsupported_asset_extension' }); return; }
      const bytes = await readRawBody(req, rule.max);
      if (!bytes.length) { response(res, 400, { error: 'empty_asset' }); return; }
      const digest = sha256Bytes(bytes);
      const existing = db.prepare('SELECT * FROM brand_assets WHERE brand_id=? AND sha256=?').get(brandId, digest);
      if (existing) { response(res, 200, { asset: { ...existing, url: `/media/brand/${encodeURIComponent(brandId)}/${encodeURIComponent(existing.kind)}/${encodeURIComponent(existing.stored_name)}` }, reused: true }); return; }
      const storedName = `${digest.slice(0, 24)}${extension}`;
      const folder = path.resolve(brandDataRoot, brandId, 'assets', kind);
      if (!isInside(brandDataRoot, folder)) throw Object.assign(new Error('invalid_asset_path'), { status: 400 });
      mkdirSync(folder, { recursive: true });
      const target = path.join(folder, storedName);
      const temporary = path.join(folder, `.${storedName}.${randomBytes(6).toString('hex')}.tmp`);
      writeFileSync(temporary, bytes, { flag: 'wx' });
      renameSync(temporary, target);
      const assetId = id('asset'); const stamp = now();
      const mimeType = assetMime[extension] || 'application/octet-stream';
      tx(() => {
        db.prepare('INSERT INTO brand_assets(asset_id,brand_id,kind,original_name,stored_name,relative_path,mime_type,size_bytes,sha256,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)').run(assetId, brandId, kind, originalName, storedName, path.posix.join('data/brands', brandId, 'assets', kind, storedName), mimeType, bytes.length, digest, stamp);
        audit({ eventType: 'brand_asset_uploaded', actor: 'Operator', brandId, objectId: assetId, payload: { kind, mime_type: mimeType, size_bytes: bytes.length, sha256: digest } });
      });
      response(res, 201, { asset: { asset_id: assetId, brand_id: brandId, kind, original_name: originalName, stored_name: storedName, mime_type: mimeType, size_bytes: bytes.length, sha256: digest, created_at: stamp, url: `/media/brand/${encodeURIComponent(brandId)}/${encodeURIComponent(kind)}/${encodeURIComponent(storedName)}` } }); return;
    }
    if (url.pathname === '/v1/operator/model-preferences' && req.method === 'PUT') {
      const session = requireOperator(req, res, true); if (!session) return;
      const body = await readBody(req); const brandId = safePathSegment(body.brand_id || 'trendybrander', 'brand_id').toLocaleLowerCase('tr-TR');
      const preferences = Array.isArray(body.preferences) ? body.preferences.slice(0, 20) : [];
      for (const preference of preferences) {
        if (!modelRoles.has(String(preference.role_id)) || !['auto', 'manual'].includes(String(preference.mode))) { response(res, 400, { error: 'invalid_model_preference' }); return; }
        if (preference.mode === 'manual' && (!limitText(preference.provider, 80) || !limitText(preference.model, 160))) { response(res, 400, { error: 'manual_model_required' }); return; }
      }
      const stamp = now();
      tx(() => {
        for (const preference of preferences) db.prepare(`INSERT INTO model_preferences(brand_id,role_id,mode,provider,model,updated_at) VALUES(?,?,?,?,?,?)
          ON CONFLICT(brand_id,role_id) DO UPDATE SET mode=excluded.mode,provider=excluded.provider,model=excluded.model,updated_at=excluded.updated_at`).run(brandId, preference.role_id, preference.mode, preference.mode === 'manual' ? limitText(preference.provider, 80) : null, preference.mode === 'manual' ? limitText(preference.model, 160) : null, stamp);
        audit({ eventType: 'model_preferences_saved', actor: 'Operator', brandId, objectId: brandId, payload: { roles: preferences.map((item) => item.role_id), automatic_default: true } });
      });
      response(res, 200, { status: 'saved', preferences: db.prepare('SELECT brand_id,role_id,mode,provider,model,updated_at FROM model_preferences WHERE brand_id=? ORDER BY role_id').all(brandId) }); return;
    }
    const connectionRoute = url.pathname.match(/^\/v1\/operator\/connections\/([^/]+)$/);
    if (connectionRoute && req.method === 'PUT') {
      const session = requireOperator(req, res, true); if (!session) return;
      const provider = safePathSegment(connectionRoute[1], 'provider');
      if (!connectionProviders.has(provider)) { response(res, 400, { error: 'unsupported_connection_provider' }); return; }
      const body = await readBody(req); const brandId = safePathSegment(body.brand_id || 'trendybrander', 'brand_id').toLocaleLowerCase('tr-TR');
      if (!body.secret || typeof body.secret !== 'object' || Array.isArray(body.secret) || Object.keys(body.secret).length === 0 || canonical(body.secret).length > 24000) { response(res, 400, { error: 'invalid_connection_secret' }); return; }
      const encrypted = encryptSecretJson(body.secret); const stamp = now(); const metadata = body.metadata && typeof body.metadata === 'object' && !Array.isArray(body.metadata) ? body.metadata : {};
      const safeMetadata = Object.fromEntries(Object.entries(metadata).slice(0, 30).map(([key, value]) => [limitText(key, 80), limitText(value, 500)]));
      tx(() => {
        db.prepare(`INSERT INTO encrypted_connections(brand_id,provider,label,metadata_json,ciphertext,iv,auth_tag,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,'saved_unverified',?,?)
          ON CONFLICT(brand_id,provider) DO UPDATE SET label=excluded.label,metadata_json=excluded.metadata_json,ciphertext=excluded.ciphertext,iv=excluded.iv,auth_tag=excluded.auth_tag,status='saved_unverified',updated_at=excluded.updated_at`).run(brandId, provider, limitText(body.label, 120) || provider, canonical(safeMetadata), encrypted.ciphertext, encrypted.iv, encrypted.auth_tag, stamp, stamp);
        audit({ eventType: 'encrypted_connection_saved', actor: 'Operator', brandId, objectId: provider, payload: { provider, secret_fields: Object.keys(body.secret).map((key) => sha256(key).slice(0, 12)), metadata_hash: sha256(canonical(safeMetadata)) } });
      });
      response(res, 200, { status: 'saved_unverified', provider, configured: true, metadata: safeMetadata, secret_returned: false }); return;
    }
    if (url.pathname === '/v1/operator/pipelines' && req.method === 'POST') {
      const session = requireOperator(req, res, true); if (!session) return;
      const body = await readBody(req);
      if (!body.brand_id || !body.goal || String(body.goal).length > 1000) { response(res, 400, { error: 'invalid_pipeline_request' }); return; }
      const riskLevel = ['low','normal','medium','high','critical'].includes(body.risk_level) ? body.risk_level : 'normal';
      const pipelineId = String(body.pipeline_id || id('pipeline')).slice(0,120);
      const existing = db.prepare('SELECT * FROM pipeline_runs WHERE pipeline_id=?').get(pipelineId);
      if (existing) { response(res, 200, { pipeline: existing, reused: true }); return; }
      const stamp = now(); const brandId = safePathSegment(body.brand_id, 'brand_id').toLocaleLowerCase('tr-TR'); const contentId = String(body.content_id || id('content')).slice(0,120); const contentVersion = String(body.content_version || 'v1').slice(0,80); const criticalBudget = riskLevel === 'critical';
      const pipeline = { pipeline_id: pipelineId, brand_id: brandId, goal: String(body.goal), risk_level: riskLevel, status: 'active', current_stage: 'classification', debate_round: 0, max_debate_rounds: criticalBudget ? 4 : 3, max_model_calls: criticalBudget ? 20 : 12, max_input_tokens: criticalBudget ? 50000 : 30000, max_output_tokens: criticalBudget ? 12000 : 8000, max_cost_usd: criticalBudget ? 0.5 : 0.25, content_id: contentId, content_version: contentVersion, created_at: stamp, updated_at: stamp };
      const taskId = `${pipelineId}-1-classification`.slice(0,180); let payload;
      try { payload = compilePipelineContext({ pipeline, taskType: 'classification', taskId, source: { request: pipeline.goal, platform: limitText(body.platform, 40), format: limitText(body.format, 40), model_mode: limitText(body.model_mode, 20) || 'auto' }, round: 0 }); }
      catch (error) { response(res, 422, { error: 'pipeline_context_compile_failed', detail: redact(error.message) }); return; }
      tx(() => {
        db.prepare('INSERT INTO pipeline_runs(pipeline_id,brand_id,goal,risk_level,status,current_stage,debate_round,max_debate_rounds,max_model_calls,max_input_tokens,max_output_tokens,max_cost_usd,content_id,content_version,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)').run(pipelineId,brandId,pipeline.goal,riskLevel,'active','classification',0,pipeline.max_debate_rounds,pipeline.max_model_calls,pipeline.max_input_tokens,pipeline.max_output_tokens,pipeline.max_cost_usd,contentId,contentVersion,stamp,stamp);
        insertInternalTask({ taskId, idempotencyKey: `${pipelineId}:1:classification`, brandId, taskType: 'classification', agentId: pipelineAgents.classification, payload, riskLevel, priority: riskLevel === 'critical' ? 'critical' : 'normal', pipelineId, pipelineStage: 'classification', contentId, contentVersion });
        db.prepare('INSERT INTO pipeline_steps(pipeline_id,sequence,task_id,task_type,agent_id,status,source_task_id,created_at) VALUES(?,?,?,?,?,?,NULL,?)').run(pipelineId,1,taskId,'classification',pipelineAgents.classification,'queued',stamp);
        audit({ eventType: 'operator_pipeline_created', actor: 'Operator', brandId, objectId: pipelineId, payload: { risk_level: riskLevel, content_id: contentId, content_version: contentVersion } });
      });
      response(res, 201, { pipeline: db.prepare('SELECT * FROM pipeline_runs WHERE pipeline_id=?').get(pipelineId), first_task_id: taskId }); return;
    }
    if (url.pathname === '/v1/evidence/verified' && req.method === 'POST') {
      const session = requireOperator(req, res, true); if (!session) return;
      const body = await readBody(req);
      const required = ['evidence_id','brand_id','claim','source_ref','source_hash','source_date','source_kind'];
      if (required.some((key) => !body[key])) { response(res, 400, { error: 'missing_evidence_fields' }); return; }
      if (!/^[a-f0-9]{64}$/i.test(String(body.source_hash)) || !Number.isFinite(Date.parse(body.source_date))) { response(res, 400, { error: 'invalid_evidence_provenance' }); return; }
      const sourceKind = String(body.source_kind);
      if (!evidenceKinds.has(sourceKind)) { response(res, 400, { error: 'unsupported_evidence_kind' }); return; }
      const sampleSize = sourceKind === 'performance_measurement' ? Number(body.sample_size) : 1;
      const metricWindow = sourceKind === 'performance_measurement' ? String(body.metric_window || '') : '';
      if (!Number.isInteger(sampleSize) || sampleSize < 1 || sampleSize > 1000000 || (sourceKind === 'performance_measurement' && (!metricWindow || metricWindow.length > 120))) { response(res, 400, { error: 'invalid_evidence_measurement_metadata' }); return; }
      const stamp = now();
      tx(() => {
        db.prepare('INSERT INTO verified_evidence(evidence_id,brand_id,claim,source_ref,source_hash,source_date,source_kind,sample_size,metric_window,confidence,verified_by,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)').run(String(body.evidence_id).slice(0,120), String(body.brand_id).slice(0,120), String(body.claim).slice(0,1200), String(body.source_ref).slice(0,500), String(body.source_hash), String(body.source_date).slice(0,40), sourceKind, sampleSize, metricWindow, evidenceConfidence[sourceKind], 'Operator', stamp);
        audit({ eventType: 'evidence_verified', actor: 'Operator', brandId: body.brand_id, objectId: body.evidence_id, payload: { source_hash: body.source_hash, source_date: body.source_date, source_kind: sourceKind, sample_size: sampleSize, metric_window: metricWindow } });
      });
      response(res, 201, { status: 'verified', evidence_id: body.evidence_id }); return;
    }
    if (url.pathname === '/v1/pipelines' && req.method === 'POST') {
      if (!requireService(req, res, ['center'])) return;
      const body = await readBody(req);
      if (!body.brand_id || !body.goal || String(body.goal).length > 1000) { response(res, 400, { error: 'invalid_pipeline_request' }); return; }
      const riskLevel = ['low','normal','medium','high','critical'].includes(body.risk_level) ? body.risk_level : 'normal';
      const pipelineId = String(body.pipeline_id || id('pipeline')).slice(0,120);
      const existing = db.prepare('SELECT * FROM pipeline_runs WHERE pipeline_id=?').get(pipelineId);
      if (existing) { response(res, 200, { pipeline: existing, reused: true }); return; }
      const stamp = now(); const contentId = String(body.content_id || id('content')).slice(0,120); const contentVersion = String(body.content_version || 'v1').slice(0,80);
      const criticalBudget = riskLevel === 'critical';
      const pipeline = { pipeline_id: pipelineId, brand_id: String(body.brand_id).slice(0,120), goal: String(body.goal), risk_level: riskLevel, status: 'active', current_stage: 'classification', debate_round: 0, max_debate_rounds: criticalBudget ? 4 : 3, max_model_calls: criticalBudget ? 20 : 12, max_input_tokens: criticalBudget ? 50000 : 30000, max_output_tokens: criticalBudget ? 12000 : 8000, max_cost_usd: criticalBudget ? 0.5 : 0.25, content_id: contentId, content_version: contentVersion, created_at: stamp, updated_at: stamp };
      const taskId = `${pipelineId}-1-classification`.slice(0,180);
      let payload;
      try { payload = compilePipelineContext({ pipeline, taskType: 'classification', taskId, source: { request: pipeline.goal }, round: 0 }); }
      catch (error) { response(res, 422, { error: 'pipeline_context_compile_failed', detail: redact(error.message) }); return; }
      tx(() => {
        db.prepare('INSERT INTO pipeline_runs(pipeline_id,brand_id,goal,risk_level,status,current_stage,debate_round,max_debate_rounds,max_model_calls,max_input_tokens,max_output_tokens,max_cost_usd,content_id,content_version,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)').run(pipelineId,pipeline.brand_id,pipeline.goal,riskLevel,'active','classification',0,pipeline.max_debate_rounds,pipeline.max_model_calls,pipeline.max_input_tokens,pipeline.max_output_tokens,pipeline.max_cost_usd,contentId,contentVersion,stamp,stamp);
        insertInternalTask({ taskId, idempotencyKey: `${pipelineId}:1:classification`, brandId: pipeline.brand_id, taskType: 'classification', agentId: pipelineAgents.classification, payload, riskLevel, priority: riskLevel === 'critical' ? 'critical' : 'normal', pipelineId, pipelineStage: 'classification', contentId, contentVersion });
        db.prepare('INSERT INTO pipeline_steps(pipeline_id,sequence,task_id,task_type,agent_id,status,source_task_id,created_at) VALUES(?,?,?,?,?,?,NULL,?)').run(pipelineId,1,taskId,'classification',pipelineAgents.classification,'queued',stamp);
        audit({ eventType: 'pipeline_created', actor: 'pipeline_orchestrator', brandId: pipeline.brand_id, objectId: pipelineId, payload: { risk_level: riskLevel, content_id: contentId, content_version: contentVersion } });
      });
      response(res, 201, { pipeline: db.prepare('SELECT * FROM pipeline_runs WHERE pipeline_id=?').get(pipelineId), first_task_id: taskId }); return;
    }
    const pipelineGet = url.pathname.match(/^\/v1\/pipelines\/([^/]+)$/);
    if (pipelineGet && req.method === 'GET') {
      if (!requireService(req, res, ['center'])) return;
      const pipeline = db.prepare('SELECT * FROM pipeline_runs WHERE pipeline_id=?').get(pipelineGet[1]);
      if (!pipeline) { response(res, 404, { error: 'pipeline_not_found' }); return; }
      const steps = db.prepare('SELECT * FROM pipeline_steps WHERE pipeline_id=? ORDER BY sequence').all(pipeline.pipeline_id);
      response(res, 200, { pipeline, steps }); return;
    }
    if (url.pathname === '/v1/tasks' && req.method === 'POST') {
      if (!requireService(req, res, ['center','scheduler'])) return; const body = await readBody(req);
      const required = ['task_id','idempotency_key','brand_id','task_type','payload'];
      if (required.some((key) => body[key] === undefined)) { response(res, 400, { error: 'missing_task_fields' }); return; }
      const payloadJson = canonical(body.payload); const payloadHash = sha256(payloadJson); const stamp = now();
      const contextSignature = hmac(canonical({ task_id: String(body.task_id), brand_id: String(body.brand_id), task_type: String(body.task_type), payload_hash: payloadHash }));
      const result = tx(() => {
        const existing = db.prepare('SELECT * FROM tasks WHERE idempotency_key=?').get(body.idempotency_key);
        if (existing) {
          if (existing.payload_hash !== payloadHash) return { conflict: true };
          return { existing: true, task: existing };
        }
        db.prepare(`INSERT INTO tasks(task_id,idempotency_key,brand_id,task_type,priority,state,risk_level,agent_id,period_key,content_id,content_version,payload_json,payload_hash,context_signature,max_retries,next_run_at,last_safe_state,created_at,updated_at)
          VALUES(?,?,?,?,?,'queued',?,?,?,?,?,?,?,?,?,?,?,?,?)`).run(body.task_id, body.idempotency_key, body.brand_id, body.task_type, body.priority || 'normal', body.risk_level || 'normal', body.agent_id || null, body.period_key || null, body.content_id || null, body.content_version || null, payloadJson, payloadHash, contextSignature, Math.min(Number(body.max_retries ?? 2), 4), body.next_run_at || stamp, 'queued', stamp, stamp);
        audit({ eventType: 'task_created', actor: 'orchestrator', brandId: body.brand_id, taskId: body.task_id, objectId: body.task_id, payload: { task_type: body.task_type, payload_hash: payloadHash } });
        return { existing: false, task: db.prepare('SELECT * FROM tasks WHERE task_id=?').get(body.task_id) };
      });
      if (result.conflict) { response(res, 409, { error: 'idempotency_conflict' }); return; }
      response(res, result.existing ? 200 : 201, { task: result.task, reused: result.existing }); return;
    }
    if (url.pathname === '/v1/tasks/recover-stale' && req.method === 'POST') {
      if (!requireService(req, res, ['scheduler'])) return;
      const recovered = recoverStaleLeases('scheduler_recovery');
      response(res, 200, { status: 'checked', recovered }); return;
    }
    if (url.pathname === '/v1/tasks/claim' && req.method === 'POST') {
      if (!requireService(req, res, ['worker'])) return; const body = await readBody(req); const worker = String(body.worker_id || '');
      if (!worker) { response(res, 400, { error: 'worker_id_required' }); return; }
      const taskTypes = Array.isArray(body.task_types) ? [...new Set(body.task_types.map((item) => String(item)).filter((item) => /^[a-z][a-z0-9_]{1,79}$/.test(item)))] : [];
      if (!taskTypes.length || taskTypes.length > 20) { response(res, 400, { error: 'valid_task_types_required' }); return; }
      const claimed = tx(() => {
        const current = now();
        const placeholders = taskTypes.map(() => '?').join(',');
        const task = db.prepare(`SELECT * FROM tasks WHERE state IN ('queued','retry') AND task_type IN (${placeholders}) AND (next_run_at IS NULL OR next_run_at<=?) AND (lease_expires_at IS NULL OR lease_expires_at<?)
          ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END, created_at LIMIT 1`).get(...taskTypes, current, current);
        if (!task) return null;
        const leaseToken = randomBytes(32).toString('base64url'); const expires = new Date(Date.now() + leaseSeconds * 1000).toISOString();
        const change = db.prepare(`UPDATE tasks SET state='running',lease_owner=?,lease_token_hash=?,lease_expires_at=?,row_version=row_version+1,updated_at=?
          WHERE task_id=? AND row_version=? AND (lease_expires_at IS NULL OR lease_expires_at<?)`).run(worker, sha256(leaseToken), expires, current, task.task_id, task.row_version, current);
        if (change.changes !== 1) return null;
        audit({ eventType: 'task_claimed', actor: worker, brandId: task.brand_id, taskId: task.task_id, objectId: task.task_id, payload: { lease_expires_at: expires } });
        return { task: db.prepare('SELECT * FROM tasks WHERE task_id=?').get(task.task_id), lease_token: leaseToken };
      });
      response(res, claimed ? 200 : 204, claimed || {}); return;
    }
    const taskContextVerify = url.pathname.match(/^\/v1\/tasks\/([^/]+)\/context\/verify$/);
    if (taskContextVerify && req.method === 'POST') {
      if (!requireService(req, res, ['worker'])) return;
      const task = db.prepare('SELECT * FROM tasks WHERE task_id=?').get(taskContextVerify[1]);
      if (!task) { response(res, 404, { error: 'task_not_found' }); return; }
      const payloadHash = sha256(task.payload_json);
      const expected = hmac(canonical({ task_id: task.task_id, brand_id: task.brand_id, task_type: task.task_type, payload_hash: payloadHash }));
      const valid = safeEqual(payloadHash, task.payload_hash) && safeEqual(expected, task.context_signature);
      audit({ eventType: valid ? 'task_context_verified' : 'task_context_rejected', actor: 'runtime_context_guard', brandId: task.brand_id, taskId: task.task_id, objectId: task.task_id, payload: { payload_hash: payloadHash } });
      response(res, valid ? 200 : 409, valid ? { valid: true, brand_id: task.brand_id, task_type: task.task_type, payload_hash: payloadHash } : { error: 'task_context_signature_invalid' }); return;
    }
    if (url.pathname === '/v1/budgets/preflight' && req.method === 'POST') {
      if (!requireService(req, res, ['worker'])) return; const body = await readBody(req);
      const task = db.prepare('SELECT * FROM tasks WHERE task_id=?').get(String(body.task_id || ''));
      if (!task) { response(res, 404, { error: 'task_not_found' }); return; }
      const taskBudget = contextPolicy.task_budgets?.[task.task_type];
      if (!taskBudget) { response(res, 422, { error: 'task_budget_missing' }); return; }
      const proposed = { calls: 1, input_tokens: Math.max(0,Number(body.max_input_tokens||0)), output_tokens: Math.max(0,Number(body.max_output_tokens||0)), cost_usd: Math.max(0,Number(body.max_cost_usd||0)) };
      if (proposed.input_tokens > taskBudget.max_input_tokens || proposed.output_tokens > taskBudget.max_output_tokens || proposed.cost_usd > taskBudget.max_cost_usd) { response(res, 422, { error: 'task_budget_preflight_rejected' }); return; }
      let limits = { max_model_calls: Number(taskBudget.max_model_calls || taskBudget.max_model_calls_per_agent_per_round || 1), max_input_tokens: taskBudget.max_input_tokens, max_output_tokens: taskBudget.max_output_tokens, max_cost_usd: taskBudget.max_cost_usd };
      let used = db.prepare('SELECT COUNT(*) calls,COALESCE(SUM(input_tokens),0) input_tokens,COALESCE(SUM(output_tokens),0) output_tokens,COALESCE(SUM(estimated_cost),0) cost_usd FROM task_attempts WHERE task_id=?').get(task.task_id);
      if (task.pipeline_id) {
        const pipeline = db.prepare('SELECT * FROM pipeline_runs WHERE pipeline_id=?').get(task.pipeline_id);
        limits = { max_model_calls: pipeline.max_model_calls, max_input_tokens: pipeline.max_input_tokens, max_output_tokens: pipeline.max_output_tokens, max_cost_usd: pipeline.max_cost_usd };
        used = db.prepare('SELECT COUNT(*) calls,COALESCE(SUM(a.input_tokens),0) input_tokens,COALESCE(SUM(a.output_tokens),0) output_tokens,COALESCE(SUM(a.estimated_cost),0) cost_usd FROM task_attempts a JOIN tasks t ON t.task_id=a.task_id WHERE t.pipeline_id=?').get(task.pipeline_id);
      }
      const remaining = { calls: limits.max_model_calls-used.calls, input_tokens: limits.max_input_tokens-used.input_tokens, output_tokens: limits.max_output_tokens-used.output_tokens, cost_usd: limits.max_cost_usd-used.cost_usd };
      const allowed = proposed.calls <= remaining.calls && proposed.input_tokens <= remaining.input_tokens && proposed.output_tokens <= remaining.output_tokens && proposed.cost_usd <= remaining.cost_usd + Number.EPSILON;
      audit({ eventType: allowed ? 'budget_preflight_passed' : 'budget_preflight_blocked', actor: 'runtime_budget_guard', brandId: task.brand_id, taskId: task.task_id, objectId: task.pipeline_id || task.task_id, payload: { proposed, remaining } });
      response(res, allowed ? 200 : 429, allowed ? { allowed: true, remaining } : { error: 'session_budget_exceeded', remaining }); return;
    }
    const providerCircuit = url.pathname.match(/^\/v1\/providers\/([^/]+)\/circuit$/);
    if (providerCircuit && req.method === 'GET') {
      if (!requireService(req, res, ['worker'])) return; const provider = providerCircuit[1].slice(0,80);
      const row = db.prepare('SELECT * FROM provider_circuits WHERE provider=?').get(provider);
      const isOpen = row?.state === 'open' && row.open_until && row.open_until > now();
      response(res, isOpen ? 503 : 200, { provider, state: isOpen ? 'open' : 'closed', failure_count: row?.failure_count || 0, open_until: isOpen ? row.open_until : null }); return;
    }
    if (providerCircuit && req.method === 'POST') {
      if (!requireService(req, res, ['worker'])) return; const provider = providerCircuit[1].slice(0,80); const body = await readBody(req); const stamp = now();
      const row = db.prepare('SELECT * FROM provider_circuits WHERE provider=?').get(provider); const previousFailures = Number(row?.failure_count || 0);
      if (body.success === true) db.prepare("INSERT INTO provider_circuits(provider,state,failure_count,open_until,last_error_type,updated_at) VALUES(?,'closed',0,NULL,NULL,?) ON CONFLICT(provider) DO UPDATE SET state='closed',failure_count=0,open_until=NULL,last_error_type=NULL,updated_at=excluded.updated_at").run(provider,stamp);
      else {
        const failures = previousFailures + 1; const open = failures >= 2; const openUntil = open ? new Date(Date.now()+60000).toISOString() : null;
        db.prepare("INSERT INTO provider_circuits(provider,state,failure_count,open_until,last_error_type,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(provider) DO UPDATE SET state=excluded.state,failure_count=excluded.failure_count,open_until=excluded.open_until,last_error_type=excluded.last_error_type,updated_at=excluded.updated_at").run(provider,open?'open':'closed',failures,openUntil,String(body.error_type||'provider_failure').slice(0,120),stamp);
      }
      const current = db.prepare('SELECT * FROM provider_circuits WHERE provider=?').get(provider); audit({ eventType: 'provider_circuit_updated', actor: 'model_worker', objectId: provider, payload: { state: current.state, failure_count: current.failure_count, open_until: current.open_until } }); response(res,200,current);return;
    }
    const taskAttempt = url.pathname.match(/^\/v1\/tasks\/([^/]+)\/attempts$/);
    if (taskAttempt && req.method === 'POST') {
      if (!requireService(req, res, ['worker'])) return; const taskId = taskAttempt[1]; const body = await readBody(req); const leaseHash = sha256(req.headers['x-lease-token'] || '');
      const task = db.prepare('SELECT * FROM tasks WHERE task_id=?').get(taskId);
      if (!task) { response(res, 404, { error: 'task_not_found' }); return; }
      if (!safeEqual(task.lease_token_hash, leaseHash) || task.lease_expires_at < now()) { response(res, 409, { error: 'lease_invalid' }); return; }
      if (!body.execution_id || !['completed','failed','rejected'].includes(body.state)) { response(res, 400, { error: 'invalid_attempt_fields' }); return; }
      const inputTokens = Number(body.input_tokens); const outputTokens = Number(body.output_tokens); const estimatedCost = Number(body.estimated_cost);
      if (!Number.isInteger(inputTokens) || inputTokens < 0 || !Number.isInteger(outputTokens) || outputTokens < 0 || !Number.isFinite(estimatedCost) || estimatedCost < 0) { response(res, 400, { error: 'verified_usage_accounting_required' }); return; }
      const existing = db.prepare('SELECT * FROM task_attempts WHERE execution_id=?').get(String(body.execution_id));
      if (existing) { response(res, existing.task_id === taskId ? 200 : 409, existing.task_id === taskId ? { status: 'reused' } : { error: 'execution_id_conflict' }); return; }
      const stamp = now();
      tx(() => {
        db.prepare(`INSERT INTO task_attempts(attempt_id,task_id,execution_id,provider,model,agent_id,state,input_tokens,output_tokens,estimated_cost,currency,duration_ms,retry_count,quality_score,brand_alignment,schema_compliance,user_acceptance,error_type,request_fingerprint,cache_hit,started_at,finished_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`).run(id('attempt'), taskId, String(body.execution_id).slice(0,180), body.provider || null, body.model || null, task.agent_id || null, body.state, inputTokens, outputTokens, estimatedCost, body.currency || 'USD', Math.max(0, Number(body.duration_ms || 0)), Math.max(0, Number(body.retry_count || 0)), body.quality_score == null ? null : Math.max(0, Math.min(1, Number(body.quality_score))), body.brand_alignment == null ? null : Math.max(0, Math.min(1, Number(body.brand_alignment))), body.schema_compliance == null ? null : Math.max(0, Math.min(1, Number(body.schema_compliance))), 'unknown', body.error_type ? String(body.error_type).slice(0,120) : null, body.request_fingerprint || task.payload_hash, body.cache_hit === true ? 1 : 0, body.started_at || stamp, stamp);
        audit({ eventType: 'model_attempt_recorded', actor: task.lease_owner, brandId: task.brand_id, taskId, objectId: body.execution_id, payload: { provider: body.provider || null, model: body.model || null, state: body.state, input_tokens: inputTokens, output_tokens: outputTokens, estimated_cost: estimatedCost } });
      });
      response(res, 201, { status: 'recorded' }); return;
    }
    const taskAction = url.pathname.match(/^\/v1\/tasks\/([^/]+)\/(heartbeat|checkpoint|complete|fail)$/);
    if (taskAction && req.method === 'POST') {
      if (!requireService(req, res, ['worker'])) return; const [, taskId, action] = taskAction; const body = await readBody(req); const leaseHash = sha256(req.headers['x-lease-token'] || ''); const expectedVersion = Number(req.headers['if-match']);
      const result = tx(() => {
        const task = db.prepare('SELECT * FROM tasks WHERE task_id=?').get(taskId);
        if (!task) return { status: 404, error: 'task_not_found' };
        if (!safeEqual(task.lease_token_hash, leaseHash) || task.lease_expires_at < now()) return { status: 409, error: 'lease_invalid' };
        if (!Number.isInteger(expectedVersion) || expectedVersion !== task.row_version) return { status: 409, error: 'row_version_conflict' };
        const stamp = now();
        if (action === 'heartbeat') {
          const expires = new Date(Date.now() + leaseSeconds * 1000).toISOString();
          db.prepare('UPDATE tasks SET lease_expires_at=?,row_version=row_version+1,updated_at=? WHERE task_id=?').run(expires, stamp, taskId);
        } else if (action === 'checkpoint') {
          const sequence = Number(body.sequence); if (!Number.isInteger(sequence) || sequence < 1) return { status: 400, error: 'invalid_checkpoint_sequence' };
          const payloadJson = canonical(body.payload || {});
          db.prepare('INSERT INTO checkpoints(checkpoint_id,task_id,sequence,state,payload_json,payload_hash,lease_owner,created_at) VALUES(?,?,?,?,?,?,?,?)').run(id('cp'), taskId, sequence, body.state || task.state, payloadJson, sha256(payloadJson), task.lease_owner, stamp);
          db.prepare('UPDATE tasks SET last_safe_state=?,row_version=row_version+1,updated_at=? WHERE task_id=?').run(body.state || task.state, stamp, taskId);
        } else if (action === 'complete') {
          let validatedOutputHash = null;
          if (outputSchemas.schemas[task.task_type]) {
            const output = body.result?.output;
            if (!output || typeof output !== 'object' || Array.isArray(output)) return { status: 409, error: 'validated_output_required' };
            validatedOutputHash = sha256(canonical(output));
            const validated = db.prepare('SELECT 1 FROM validated_outputs WHERE task_id=? AND task_type=? AND output_hash=?').get(taskId, task.task_type, validatedOutputHash);
            if (!validated) return { status: 409, error: 'output_not_validated_for_task' };
          }
          const resultJson = canonical(body.result || {});
          db.prepare(`UPDATE tasks SET state='completed',result_json=?,result_hash=?,completed_at=?,lease_owner=NULL,lease_token_hash=NULL,lease_expires_at=NULL,row_version=row_version+1,updated_at=? WHERE task_id=?`).run(resultJson, sha256(resultJson), stamp, stamp, taskId);
          if (validatedOutputHash) {
            db.prepare('INSERT OR REPLACE INTO agent_output_provenance(provenance_id,task_id,brand_id,task_type,output_hash,eligible_as_factual_evidence,created_at) VALUES(?,?,?,?,?,0,?)').run(`agent-output:${taskId}`, taskId, task.brand_id, task.task_type, validatedOutputHash, stamp);
          }
        } else {
          const retryable = body.retryable === true && task.retry_count < task.max_retries;
          const errorText = redact(body.error || 'unknown_error'); const errorFingerprint = sha256(errorText);
          if (retryable) {
            const delay = Math.min(300, 5 * (2 ** task.retry_count));
            db.prepare(`UPDATE tasks SET state='retry',retry_count=retry_count+1,next_run_at=?,lease_owner=NULL,lease_token_hash=NULL,lease_expires_at=NULL,row_version=row_version+1,updated_at=? WHERE task_id=?`).run(new Date(Date.now()+delay*1000).toISOString(), stamp, taskId);
          } else {
            db.prepare(`UPDATE tasks SET state='failed',lease_owner=NULL,lease_token_hash=NULL,lease_expires_at=NULL,row_version=row_version+1,updated_at=? WHERE task_id=?`).run(stamp, taskId);
            db.prepare('INSERT OR REPLACE INTO dead_letters(dlq_id,task_id,error_fingerprint,attempts,last_safe_state,redacted_error,human_action_required,created_at) VALUES(?,?,?,?,?,?,?,?)').run(id('dlq'), taskId, errorFingerprint, task.retry_count + 1, task.last_safe_state, errorText, body.human_action_required || 'review', stamp);
          }
        }
        audit({ eventType: `task_${action}`, actor: task.lease_owner, brandId: task.brand_id, taskId, objectId: taskId, payload: { state: body.state || null } });
        return { status: 200, task: db.prepare('SELECT * FROM tasks WHERE task_id=?').get(taskId) };
      });
      let advancement = null;
      if (!result.error && result.status === 200 && action === 'complete' && result.task?.pipeline_id) {
        try { advancement = advancePipeline(taskId); }
        catch (error) {
          tx(() => { db.prepare("UPDATE pipeline_runs SET status='blocked',updated_at=? WHERE pipeline_id=?").run(now(), result.task.pipeline_id); audit({ eventType: 'pipeline_advance_failed', actor: 'pipeline_orchestrator', brandId: result.task.brand_id, taskId, objectId: result.task.pipeline_id, payload: { error_hash: sha256(redact(error.message)) } }); });
          advancement = { advanced: false, error: 'pipeline_advance_failed' };
        }
      }
      response(res, result.status, result.error ? { error: result.error } : { task: result.task, advancement }); return;
    }
    if (url.pathname === '/v1/validate/output' && req.method === 'POST') {
      if (!requireService(req, res, ['worker'])) return; const body = await readBody(req); const result = validateOutput(body);
      if (body.task_id) {
        const task = db.prepare('SELECT task_id,task_type FROM tasks WHERE task_id=?').get(body.task_id);
        if (!task || task.task_type !== body.task_type) { response(res, 409, { error: 'validation_task_mismatch' }); return; }
        if (result.valid) db.prepare('INSERT OR REPLACE INTO validated_outputs(task_id,task_type,output_hash,validated_at) VALUES(?,?,?,?)').run(task.task_id, task.task_type, result.output_hash, now());
      }
      audit({ eventType: result.valid ? 'output_validated' : 'output_rejected', actor: 'runtime_validator', taskId: body.task_id || null, payload: { task_type: body.task_type, output_hash: result.output_hash, errors: result.errors, blocked_claim_hashes: result.blocked_claims.map(sha256) } });
      response(res, result.valid ? 200 : 422, result); return;
    }
    if (url.pathname === '/v1/security/scan-input' && req.method === 'POST') {
      if (!requireService(req, res, ['worker','center','scheduler'])) return; const body = await readBody(req); const raw = canonical(body.data || body.text || '');
      const reasons = injectionPatterns.map((pattern, index) => pattern.test(raw) ? `injection_pattern_${index+1}` : null).filter(Boolean);
      if (body.brand_id && body.expected_brand_id && body.brand_id !== body.expected_brand_id) reasons.push('cross_brand_data');
      const quarantined = reasons.length > 0;
      if (quarantined) tx(() => { const qid=id('quarantine'); db.prepare('INSERT INTO security_quarantine(quarantine_id,source_type,source_hash,reason_codes,redacted_excerpt,created_at) VALUES(?,?,?,?,?,?)').run(qid, body.source_type || 'external', sha256(raw), JSON.stringify(reasons), redact(raw).slice(0,300), now()); audit({ eventType: 'external_input_quarantined', actor: 'security_scanner', brandId: body.expected_brand_id || null, objectId: qid, payload: { reasons, source_hash: sha256(raw) } }); });
      response(res, quarantined ? 422 : 200, { safe: !quarantined, quarantined, reasons, external_content_is_instruction: false }); return;
    }
    if (url.pathname === '/v1/cache' && req.method === 'PUT') {
      if (!requireService(req, res, ['worker'])) return; const body = await readBody(req);
      if (Number(body.quality_score) < 0.8 || Number(body.schema_compliance) !== 1 || body.status !== 'completed') { response(res, 422, { error: 'cache_quality_gate_failed' }); return; }
      tx(() => { db.prepare(`INSERT OR REPLACE INTO cache_entries(request_fingerprint,brand_id,agent_id,role_version,task_type,provider,model,source_hash_bundle,result_ref,result_hash,status,schema_compliance,quality_score,created_at,expires_at,last_hit_at,hit_count)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,COALESCE((SELECT hit_count FROM cache_entries WHERE request_fingerprint=?),0))`).run(body.request_fingerprint, body.brand_id, body.agent_id, body.role_version, body.task_type, body.provider || null, body.model || null, canonical(body.source_hash_bundle), body.result_ref, body.result_hash, body.status, body.schema_compliance, body.quality_score, now(), body.expires_at || null, null, body.request_fingerprint); audit({ eventType: 'cache_written', actor: 'runtime', brandId: body.brand_id, objectId: body.request_fingerprint, payload: { quality_score: body.quality_score } }); });
      response(res, 201, { status: 'cached' }); return;
    }
    const cacheMatch = url.pathname.match(/^\/v1\/cache\/([A-Fa-f0-9]+)$/);
    if (cacheMatch && req.method === 'GET') {
      if (!requireService(req, res, ['worker'])) return; const row = db.prepare(`SELECT * FROM cache_entries WHERE request_fingerprint=? AND status='completed' AND quality_score>=0.8 AND schema_compliance=1 AND (expires_at IS NULL OR expires_at>?)`).get(cacheMatch[1], now());
      if (!row) { response(res, 404, { hit: false }); return; }
      const requestedSource = url.searchParams.get('source_hash_bundle');
      if (requestedSource && !safeEqual(sha256(row.source_hash_bundle), requestedSource)) { response(res, 404, { hit: false, reason: 'source_changed' }); return; }
      db.prepare('UPDATE cache_entries SET hit_count=hit_count+1,last_hit_at=? WHERE request_fingerprint=?').run(now(), row.request_fingerprint);
      response(res, 200, { hit: true, entry: row }); return;
    }
    if (url.pathname === '/v1/memory/candidates' && req.method === 'POST') {
      if (!requireService(req, res, ['center','scheduler'])) return; const body = await readBody(req); const stamp=now(); const memoryId=body.memory_id||id('mem');
      if (!body.brand_id || !body.task_scope || !body.semantic_key || !body.compact_content) { response(res,400,{error:'missing_memory_fields'});return; }
      tx(() => { db.prepare(`INSERT INTO memory_records(memory_id,brand_id,task_scope,semantic_key,type,compact_content,confidence,state,sample_size,evidence_count,created_at,updated_at,expires_at)
        VALUES(?,?,?,?,?,?,?,'candidate',0,0,?,?,?)`).run(memoryId,body.brand_id,body.task_scope,body.semantic_key,body.type||'hypothesis',String(body.compact_content).slice(0,700),Math.max(0,Math.min(1,Number(body.confidence||0))),stamp,stamp,body.expires_at||null); audit({eventType:'memory_candidate_created',actor:'memory_manager',brandId:body.brand_id,objectId:memoryId,payload:{semantic_key:body.semantic_key}}); });
      response(res,201,{memory_id:memoryId,state:'candidate'});return;
    }
    const memoryEvidence = url.pathname.match(/^\/v1\/memory\/([^/]+)\/evidence$/);
    if(memoryEvidence && req.method==='POST'){
      if(!requireService(req,res,['center','scheduler']))return;const body=await readBody(req);const memoryId=memoryEvidence[1];
      const record=db.prepare('SELECT * FROM memory_records WHERE memory_id=?').get(memoryId);if(!record){response(res,404,{error:'memory_not_found'});return;}
      if(!body.verified_evidence_id){response(res,400,{error:'verified_evidence_id_required'});return;}
      const authority=db.prepare('SELECT * FROM verified_evidence WHERE evidence_id=? AND brand_id=? AND revoked_at IS NULL').get(String(body.verified_evidence_id),record.brand_id);
      if(!authority){response(res,422,{error:'authoritative_evidence_not_found_for_brand'});return;}
      const existing=db.prepare('SELECT evidence_id FROM memory_evidence WHERE memory_id=? AND source_hash=? AND metric_window=?').get(memoryId,authority.source_hash,authority.metric_window||'');
      if(existing){response(res,200,{status:'evidence_reused',evidence_id:existing.evidence_id});return;}
      const evidenceId=id('evidence');
      tx(()=>{db.prepare('INSERT INTO memory_evidence(evidence_id,memory_id,source_ref,source_hash,source_date,evidence_kind,metric_window,result_segment,confidence,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)').run(evidenceId,memoryId,authority.source_ref,authority.source_hash,authority.source_date,authority.source_kind,authority.metric_window||'',body.result_segment?String(body.result_segment).slice(0,240):null,authority.confidence,now());db.prepare('UPDATE memory_records SET evidence_count=evidence_count+1,sample_size=sample_size+?,updated_at=? WHERE memory_id=?').run(authority.sample_size,now(),memoryId);audit({eventType:'memory_evidence_added',actor:'memory_manager',brandId:record.brand_id,objectId:memoryId,payload:{verified_evidence_id:authority.evidence_id,source_hash:authority.source_hash,metric_window:authority.metric_window||''}});});response(res,201,{status:'evidence_added',evidence_id:evidenceId});return;
    }
    const memoryPromote=url.pathname.match(/^\/v1\/memory\/([^/]+)\/promote$/);
    if(memoryPromote&&req.method==='POST'){
      if(!requireService(req,res,['center','scheduler']))return;const memoryId=memoryPromote[1];const body=await readBody(req);const record=db.prepare('SELECT * FROM memory_records WHERE memory_id=?').get(memoryId);if(!record){response(res,404,{error:'memory_not_found'});return;}
      const evidenceKinds=db.prepare('SELECT COUNT(DISTINCT evidence_kind) AS count FROM memory_evidence WHERE memory_id=?').get(memoryId).count;
      let target=body.target_state;let allowed=false;if(target==='temporary')allowed=record.sample_size>=10&&record.evidence_count>=2&&record.confidence>=0.7;if(target==='permanent')allowed=record.sample_size>=20&&record.evidence_count>=3&&evidenceKinds>=2&&record.confidence>=0.85;
      if(!allowed){response(res,422,{error:'memory_promotion_gate_failed',sample_size:record.sample_size,evidence_count:record.evidence_count,evidence_kinds:evidenceKinds,confidence:record.confidence});return;}
      tx(()=>{db.prepare('UPDATE memory_records SET state=?,updated_at=? WHERE memory_id=?').run(target,now(),memoryId);audit({eventType:'memory_promoted',actor:'memory_manager',brandId:record.brand_id,objectId:memoryId,payload:{target}});});response(res,200,{memory_id:memoryId,state:target});return;
    }
    if(url.pathname==='/v1/memory/select'&&req.method==='GET'){
      if(!requireService(req,res,['worker','center','scheduler']))return;const brand=url.searchParams.get('brand_id');const scope=url.searchParams.get('task_type')||'general';const limit=Math.min(5,Math.max(1,Number(url.searchParams.get('limit')||5)));const query=String(url.searchParams.get('q')||'').toLocaleLowerCase('tr-TR');
      const rows=db.prepare(`SELECT * FROM memory_records WHERE brand_id=? AND state IN ('temporary','permanent') AND (task_scope=? OR task_scope='general') AND (expires_at IS NULL OR expires_at>?)`).all(brand,scope,now());const terms=new Set(query.split(/\W+/u).filter((v)=>v.length>2));
      const ranked=rows.map((row)=>{const text=(row.semantic_key+' '+row.compact_content).toLocaleLowerCase('tr-TR');let match=0;for(const term of terms)if(text.includes(term))match+=1;return{...row,score:row.confidence+match*0.15+(row.state==='permanent'?0.1:0)}}).sort((a,b)=>b.score-a.score).slice(0,limit);
      response(res,200,{records:ranked});return;
    }
    if(url.pathname==='/v1/privacy/records'&&req.method==='POST'){
      if(!requireService(req,res,['center']))return;const body=await readBody(req);const required=['brand_id','subject_ref','category','source_type','payload_hash','expires_at'];
      if(required.some((key)=>!body[key])){response(res,400,{error:'missing_privacy_record_fields'});return;}
      if(!/^[A-Fa-f0-9]{64}$/.test(String(body.payload_hash))){response(res,400,{error:'invalid_payload_hash'});return;}
      const storageRef=String(body.storage_ref||`hash-only://${body.payload_hash}`);if(!storageRef.startsWith('hash-only://')){response(res,422,{error:'raw_personal_data_storage_not_enabled'});return;}
      const retentionDays={dm:90,comment:90,account_metadata:365,consent:730,analytics_identifier:180};const maxDays=retentionDays[body.category];
      if(!maxDays){response(res,400,{error:'unsupported_personal_data_category'});return;}
      const expiresAt=Date.parse(body.expires_at);if(!Number.isFinite(expiresAt)||expiresAt<=Date.now()||expiresAt>Date.now()+maxDays*86400000+60000){response(res,400,{error:'invalid_retention_expiry'});return;}
      const recordId=body.record_id||id('pdr');const subjectHash=sha256(String(body.subject_ref));
      tx(()=>{db.prepare('INSERT INTO personal_data_records(record_id,brand_id,subject_key_hash,category,source_type,payload_hash,storage_ref,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?,?)').run(recordId,body.brand_id,subjectHash,body.category,body.source_type,body.payload_hash,storageRef,now(),body.expires_at);audit({eventType:'personal_data_hash_registered',actor:'privacy_runtime',brandId:body.brand_id,objectId:recordId,payload:{category:body.category,subject_key_hash:subjectHash,payload_hash:body.payload_hash}});});
      response(res,201,{record_id:recordId,subject_key_hash:subjectHash,raw_payload_stored:false});return;
    }
    if(url.pathname==='/v1/privacy/requests'&&req.method==='POST'){
      if(!requireService(req,res,['center']))return;const body=await readBody(req);if(!body.brand_id||!body.subject_ref||!['access','erase','restrict'].includes(body.request_type)){response(res,400,{error:'invalid_privacy_request'});return;}
      const requestId=body.request_id||id('privacy');const subjectHash=sha256(String(body.subject_ref));const scope=Array.isArray(body.scope)?body.scope.slice(0,20):['all'];
      tx(()=>{db.prepare('INSERT INTO privacy_requests(request_id,brand_id,subject_key_hash,request_type,scope_json,status,created_at) VALUES(?,?,?,?,?,?,?)').run(requestId,body.brand_id,subjectHash,body.request_type,canonical(scope),'pending_operator',now());audit({eventType:'privacy_request_created',actor:'privacy_runtime',brandId:body.brand_id,objectId:requestId,payload:{request_type:body.request_type,subject_key_hash:subjectHash}});});
      response(res,201,{request_id:requestId,status:'pending_operator',subject_key_hash:subjectHash});return;
    }
    if(url.pathname==='/v1/privacy/requests/waiting'&&req.method==='GET'){
      const session=requireOperator(req,res);if(!session)return;const rows=db.prepare("SELECT request_id,brand_id,request_type,scope_json,status,created_at FROM privacy_requests WHERE status='pending_operator' ORDER BY created_at").all().map((row)=>({...row,scope:parseJson(row.scope_json,[]),scope_json:undefined}));response(res,200,{items:rows});return;
    }
    const privacyExecute=url.pathname.match(/^\/v1\/privacy\/requests\/([^/]+)\/execute$/);
    if(privacyExecute&&req.method==='POST'){
      const session=requireOperator(req,res,true);if(!session)return;const requestId=privacyExecute[1];const body=await readBody(req);const result=tx(()=>{const request=db.prepare('SELECT * FROM privacy_requests WHERE request_id=?').get(requestId);if(!request)return{status:404,error:'privacy_request_not_found'};if(request.status!=='pending_operator')return{status:409,error:'privacy_request_already_processed'};
        if(body.decision==='reject'){db.prepare("UPDATE privacy_requests SET status='rejected',completed_at=?,report_json=? WHERE request_id=?").run(now(),canonical({reason:String(body.reason||'operator_rejected').slice(0,300)}),requestId);audit({eventType:'privacy_request_rejected',actor:'Operator',brandId:request.brand_id,objectId:requestId});return{status:200,state:'rejected'};}
        if(body.decision!=='execute')return{status:400,error:'privacy_decision_invalid'};const changed=db.prepare('UPDATE personal_data_records SET deleted_at=? WHERE brand_id=? AND subject_key_hash=? AND deleted_at IS NULL').run(now(),request.brand_id,request.subject_key_hash).changes;const report={records_erased:changed,raw_payloads_stored_by_runtime:0,audit_events_preserved:true};db.prepare("UPDATE privacy_requests SET status='completed',completed_at=?,report_json=? WHERE request_id=?").run(now(),canonical(report),requestId);audit({eventType:'privacy_erasure_completed',actor:'Operator',brandId:request.brand_id,objectId:requestId,payload:{records_erased:changed,subject_key_hash:request.subject_key_hash}});return{status:200,state:'completed',report};});response(res,result.status,result.error?{error:result.error}:result);return;
    }
    if(url.pathname==='/v1/privacy/retention/run'&&req.method==='POST'){
      if(!requireService(req,res,['scheduler']))return;const stamp=now();const quarantineCutoff=new Date(Date.now()-30*86400000).toISOString();const sessionCutoff=new Date(Date.now()-7*86400000).toISOString();const rateCutoff=new Date(Date.now()-2*86400000).toISOString();const result=tx(()=>{const expiredPersonal=db.prepare('DELETE FROM personal_data_records WHERE expires_at<=?').run(stamp).changes;const expiredCache=db.prepare('DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at<=?').run(stamp).changes;const expiredSessions=db.prepare('DELETE FROM operator_sessions WHERE expires_at<=? OR (revoked_at IS NOT NULL AND revoked_at<=?)').run(stamp,sessionCutoff).changes;const expiredLimits=db.prepare('DELETE FROM rate_limits WHERE window_start<=?').run(rateCutoff).changes;const redactedQuarantine=db.prepare('UPDATE security_quarantine SET redacted_excerpt=NULL WHERE redacted_excerpt IS NOT NULL AND created_at<=?').run(quarantineCutoff).changes;const expiredApprovals=db.prepare("UPDATE approvals SET status='expired' WHERE status='waiting' AND expires_at<=?").run(stamp).changes;const expiredMemory=db.prepare("UPDATE memory_records SET state='expired',updated_at=? WHERE state IN ('candidate','temporary') AND expires_at IS NOT NULL AND expires_at<=?").run(stamp,stamp).changes;const counts={expired_personal_records:expiredPersonal,expired_cache_entries:expiredCache,expired_sessions:expiredSessions,expired_rate_limits:expiredLimits,redacted_quarantine_excerpts:redactedQuarantine,expired_approvals:expiredApprovals,expired_memory_records:expiredMemory};audit({eventType:'retention_maintenance_completed',actor:'privacy_runtime',payload:counts});return counts;});response(res,200,{status:'completed',counts:result,audit_preserved:true});return;
    }
    if(url.pathname==='/v1/local-approvals'&&req.method==='POST'){
      if(!requireService(req,res,['center','n8n']))return;
      const body=await readBody(req);
      const required=['brand_id','content_id','content_version','content_payload','idempotency_key','summary','preview_refs'];
      if(required.some((key)=>body[key]===undefined||body[key]===null||body[key]==='')){response(res,400,{error:'missing_local_approval_fields'});return;}
      if(!body.content_payload||typeof body.content_payload!=='object'||Array.isArray(body.content_payload)||typeof body.content_payload.caption!=='string'||!body.content_payload.caption.trim()||body.content_payload.caption.length>5000){response(res,400,{error:'invalid_local_content_payload'});return;}
      if(!Array.isArray(body.preview_refs)||body.preview_refs.length<1||body.preview_refs.length>4){response(res,400,{error:'invalid_local_preview_refs'});return;}
      let imageBindings;
      try { imageBindings=body.preview_refs.map((reference)=>{const image=resolveGeneratedImage(reference);return{reference,name:image.name,sha256:sha256Bytes(readFileSync(image.path))};}); }
      catch(error){response(res,422,{error:redact(error.message)});return;}
      const contentPayload=stable(body.content_payload);
      const derivedContentHash=sha256(canonical({content_payload:contentPayload,image_bindings:imageBindings.map(({name,sha256})=>({name,sha256}))}));
      if(body.content_hash&&!safeEqual(body.content_hash,derivedContentHash)){response(res,409,{error:'content_hash_mismatch'});return;}
      const existing=db.prepare('SELECT * FROM approvals WHERE idempotency_key=?').get(String(body.idempotency_key));
      if(existing){
        if(existing.account_id!==localDeliveryAccountId||!safeEqual(existing.content_hash,derivedContentHash)){response(res,409,{error:'local_approval_idempotency_conflict'});return;}
        response(res,200,{approval_id:existing.approval_id,nonce:hmac(`approval_nonce:${existing.approval_id}`),expires_at:existing.expires_at,reused:true,delivery_mode:'local_file_only',publish_authorized:false});return;
      }
      const approvalId=String(body.approval_id||id('approval')).slice(0,120);const nonce=hmac(`approval_nonce:${approvalId}`);const stamp=now();const expires=body.expires_at||new Date(Date.now()+24*60*60*1000).toISOString();
      if(Date.parse(expires)<=Date.now()||Date.parse(expires)>Date.now()+24*60*60*1000+60000){response(res,400,{error:'invalid_approval_expiry'});return;}
      const bindingHash=sha256(canonical({brand_id:body.brand_id,account_id:localDeliveryAccountId,delivery_mode:'local_file_only'}));
      tx(()=>{
        db.prepare('INSERT INTO approvals(approval_id,brand_id,account_id,account_binding_hash,content_id,content_version,content_hash,idempotency_key,summary,preview_refs_json,nonce_hash,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)').run(approvalId,String(body.brand_id).slice(0,120),localDeliveryAccountId,bindingHash,String(body.content_id).slice(0,120),String(body.content_version).slice(0,80),derivedContentHash,String(body.idempotency_key).slice(0,180),String(body.summary).slice(0,1200),canonical(body.preview_refs),sha256(nonce),stamp,expires);
        db.prepare('INSERT INTO local_approval_payloads(approval_id,content_json,image_refs_json,created_at) VALUES(?,?,?,?)').run(approvalId,canonical(contentPayload),canonical(imageBindings),stamp);
        audit({eventType:'local_approval_requested',actor:req.ajansService||'interface_agent',brandId:body.brand_id,objectId:approvalId,payload:{content_hash:derivedContentHash,content_version:body.content_version,delivery_mode:'local_file_only',publish_authorized:false,image_count:imageBindings.length}});
      });
      response(res,201,{approval_id:approvalId,nonce,expires_at:expires,delivery_mode:'local_file_only',publish_authorized:false});return;
    }
    if(url.pathname==='/v1/approvals'&&req.method==='POST'){
      if(!requireService(req,res,['center']))return;const body=await readBody(req);const required=['brand_id','account_id','content_id','content_version','content_payload','idempotency_key','summary'];if(required.some((key)=>body[key]===undefined||body[key]===null||body[key]==='')){response(res,400,{error:'missing_approval_fields'});return;}
      const binding=allowSyntheticAccounts?{hash:sha256(`synthetic:${body.brand_id}:${body.account_id}`)}:accountBinding(loadAccountRegistry(),body.brand_id,body.account_id);if(!binding){response(res,403,{error:'target_account_not_verified'});return;}
      const derivedContentHash=sha256(canonical(body.content_payload));if(body.content_hash&&!safeEqual(body.content_hash,derivedContentHash)){response(res,409,{error:'content_hash_mismatch'});return;}body.content_hash=derivedContentHash;
      const approvalId=body.approval_id||id('approval');const nonce=hmac(`approval_nonce:${approvalId}`);const stamp=now();const expires=body.expires_at||new Date(Date.now()+24*60*60*1000).toISOString();if(Date.parse(expires)<=Date.now()||Date.parse(expires)>Date.now()+24*60*60*1000+60000){response(res,400,{error:'invalid_approval_expiry'});return;}
      tx(()=>{db.prepare('INSERT INTO approvals(approval_id,brand_id,account_id,account_binding_hash,content_id,content_version,content_hash,idempotency_key,summary,preview_refs_json,nonce_hash,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)').run(approvalId,body.brand_id,body.account_id,binding.hash,body.content_id,body.content_version,body.content_hash,body.idempotency_key,String(body.summary).slice(0,1200),canonical(body.preview_refs||[]),sha256(nonce),stamp,expires);audit({eventType:'approval_requested',actor:'interface_agent',brandId:body.brand_id,objectId:approvalId,payload:{content_hash:body.content_hash,content_version:body.content_version,account_id:body.account_id,account_binding_hash:binding.hash}});});response(res,201,{approval_id:approvalId,nonce,expires_at:expires});return;
    }
    if(url.pathname==='/v1/approvals/waiting'&&req.method==='GET'){
      const session=requireOperator(req,res);if(!session)return;const rows=db.prepare("SELECT approval_id,brand_id,account_id,content_id,content_version,content_hash,summary,preview_refs_json,created_at,expires_at,status FROM approvals WHERE status='waiting' AND expires_at>? ORDER BY created_at").all(now()).map((row)=>{const local=row.account_id===localDeliveryAccountId;const payload=local?db.prepare('SELECT content_json FROM local_approval_payloads WHERE approval_id=?').get(row.approval_id):null;return{...row,nonce:hmac(`approval_nonce:${row.approval_id}`),preview_refs:parseJson(row.preview_refs_json,[]),preview_refs_json:undefined,delivery_mode:local?'local_file_only':'external_account',publish_authorized:false,content_payload:local?parseJson(payload?.content_json,{}):undefined};});response(res,200,{items:rows});return;
    }
    const approvalDecision=url.pathname.match(/^\/v1\/approvals\/([^/]+)\/decision$/);
    if(approvalDecision&&req.method==='POST'){
      const session=requireOperator(req,res,true);if(!session)return;const body=await readBody(req);const approvalId=approvalDecision[1];const decision=body.decision;if(!['approve','revise','reject'].includes(decision)){response(res,400,{error:'invalid_decision'});return;}
      const result=tx(()=>{const approval=db.prepare('SELECT * FROM approvals WHERE approval_id=?').get(approvalId);if(!approval)return{status:404,error:'approval_not_found'};if(approval.status!=='waiting')return{status:409,error:'approval_already_decided'};if(approval.expires_at<=now())return{status:409,error:'approval_expired'};if(!safeEqual(approval.nonce_hash,sha256(body.nonce||'')))return{status:403,error:'approval_nonce_invalid'};
        const decisionAt=now();const signed={approval_id:approvalId,brand_id:approval.brand_id,account_id:approval.account_id,account_binding_hash:approval.account_binding_hash,content_id:approval.content_id,content_version:approval.content_version,content_hash:approval.content_hash,idempotency_key:approval.idempotency_key,decision,approved_by:'Operator',decision_at:decisionAt,expires_at:approval.expires_at,nonce:body.nonce};const canonicalHash=sha256(canonical(signed));const signature=hmac(canonical(signed));const previous=db.prepare('SELECT canonical_hash FROM approval_decisions ORDER BY decision_at DESC LIMIT 1').get()?.canonical_hash||null;
        const local=approval.account_id===localDeliveryAccountId;db.prepare('INSERT INTO approval_decisions(decision_id,approval_id,decision,approved_by,revision_note,decision_at,canonical_hash,signature_hmac,previous_decision_hash) VALUES(?,?,?,?,?,?,?,?,?)').run(id('decision'),approvalId,decision,'Operator',decision==='revise'?String(body.revision_note||'').slice(0,1200):null,decisionAt,canonicalHash,signature,previous);db.prepare('UPDATE approvals SET status=? WHERE approval_id=?').run(decision==='approve'?(local?'approved_local_pending':'approved'):decision==='revise'?'revision_requested':'rejected',approvalId);audit({eventType:'approval_decided',actor:'Operator',brandId:approval.brand_id,objectId:approvalId,payload:{decision,canonical_hash:canonicalHash,delivery_mode:local?'local_file_only':'external_account'}});return{status:200,local,record:{...signed,canonical_hash:canonicalHash,signature_hmac:signature}};});
      if(result.error){response(res,result.status,{error:result.error});return;}
      if(result.local&&decision==='approve'){
        try{const delivery=writeLocalDelivery(approvalId);response(res,200,{...result,delivery});return;}
        catch(error){const message=redact(error.message);tx(()=>{const stamp=now();db.prepare("UPDATE approvals SET status='approved_local_delivery_failed' WHERE approval_id=?").run(approvalId);db.prepare("INSERT OR REPLACE INTO local_delivery_receipts(approval_id,delivery_id,output_dir,manifest_json,manifest_hash,status,created_at,updated_at) VALUES(?,?,?,?,?,?,COALESCE((SELECT created_at FROM local_delivery_receipts WHERE approval_id=?),?),?)").run(approvalId,`local-${approvalId}`,'',canonical({error:message}),sha256(message),'failed',approvalId,stamp,stamp);audit({eventType:'local_delivery_failed',actor:'runtime',objectId:approvalId,payload:{error_hash:sha256(message)}});});response(res,500,{error:'local_delivery_failed',detail:message,approval_recorded:true});return;}
      }
      response(res,result.status,result);return;
    }
    const localDeliveryRetry=url.pathname.match(/^\/v1\/local-deliveries\/([^/]+)\/retry$/);
    if(localDeliveryRetry&&req.method==='POST'){
      const session=requireOperator(req,res,true);if(!session)return;const approvalId=localDeliveryRetry[1];const approval=db.prepare('SELECT * FROM approvals WHERE approval_id=?').get(approvalId);if(!approval){response(res,404,{error:'approval_not_found'});return;}if(approval.account_id!==localDeliveryAccountId||!['approved_local_pending','approved_local_delivery_failed'].includes(approval.status)){response(res,409,{error:'local_delivery_retry_not_allowed'});return;}
      try{const delivery=writeLocalDelivery(approvalId);response(res,200,{delivery});return;}catch(error){response(res,500,{error:'local_delivery_failed',detail:redact(error.message)});return;}
    }
    if(url.pathname==='/v1/publish/authorize'&&req.method==='POST'){
      if(!requireService(req,res,['n8n']))return;const body=await readBody(req);if(!verifyAudit().ok){response(res,409,{error:'audit_chain_invalid'});return;}const result=tx(()=>{const approval=db.prepare('SELECT * FROM approvals WHERE approval_id=?').get(body.approval_id);const decision=db.prepare('SELECT * FROM approval_decisions WHERE approval_id=?').get(body.approval_id);if(!approval||!decision)return{status:404,error:'approval_not_found'};if(approval.account_id===localDeliveryAccountId)return{status:403,error:'local_delivery_never_publishable'};if(approval.consumed_at)return{status:409,error:'approval_already_consumed'};if(approval.status!=='approved'||decision.decision!=='approve')return{status:403,error:'approval_not_approved'};if(approval.expires_at<=now())return{status:409,error:'approval_expired'};for(const field of ['brand_id','account_id','content_id','content_version','content_hash','idempotency_key'])if(!safeEqual(approval[field],body[field]))return{status:409,error:`approval_${field}_mismatch`};const currentBinding=allowSyntheticAccounts?{hash:sha256(`synthetic:${approval.brand_id}:${approval.account_id}`)}:accountBinding(loadAccountRegistry(),approval.brand_id,approval.account_id);if(!currentBinding)return{status:409,error:'target_account_no_longer_verified'};if(!safeEqual(currentBinding.hash,approval.account_binding_hash))return{status:409,error:'target_account_binding_changed'};
        const signed={approval_id:approval.approval_id,brand_id:approval.brand_id,account_id:approval.account_id,account_binding_hash:approval.account_binding_hash,content_id:approval.content_id,content_version:approval.content_version,content_hash:approval.content_hash,idempotency_key:approval.idempotency_key,decision:decision.decision,approved_by:decision.approved_by,decision_at:decision.decision_at,expires_at:approval.expires_at,nonce:hmac(`approval_nonce:${approval.approval_id}`)};const canonicalHash=sha256(canonical(signed));const signature=hmac(canonical(signed));if(!safeEqual(canonicalHash,decision.canonical_hash)||!safeEqual(signature,decision.signature_hmac))return{status:409,error:'approval_signature_invalid'};
        const eventId=id('publish');const payload={approval_id:approval.approval_id,brand_id:approval.brand_id,account_id:approval.account_id,account_binding_hash:approval.account_binding_hash,content_id:approval.content_id,content_version:approval.content_version,content_hash:approval.content_hash,idempotency_key:approval.idempotency_key};const payloadJson=canonical(payload);db.prepare('INSERT INTO outbox_events(event_id,event_type,idempotency_key,payload_json,payload_hash,created_at) VALUES(?,\'publish_authorized\',?,?,?,?)').run(eventId,approval.idempotency_key,payloadJson,sha256(payloadJson),now());db.prepare('UPDATE approvals SET consumed_at=?,status=\'consumed\' WHERE approval_id=?').run(now(),approval.approval_id);audit({eventType:'publish_authorized',actor:'runtime',brandId:approval.brand_id,objectId:eventId,payload:{content_hash:approval.content_hash,account_id:approval.account_id,account_binding_hash:approval.account_binding_hash}});return{status:200,event_id:eventId,payload};});response(res,result.status,result.error?{error:result.error}:result);return;
    }
    if(url.pathname==='/v1/audit/verify'&&req.method==='POST'){
      if(!requireService(req,res,['center']))return;const result=verifyAudit();response(res,result.ok?200:409,result);return;
    }
    if(url.pathname==='/v1/metrics'&&req.method==='GET'){
      if(!requireService(req,res,['center']))return;const byState=db.prepare('SELECT state,COUNT(*) count FROM tasks GROUP BY state').all();const attempts=db.prepare('SELECT COUNT(*) calls,COALESCE(SUM(input_tokens),0) input_tokens,COALESCE(SUM(output_tokens),0) output_tokens,COALESCE(SUM(estimated_cost),0) estimated_cost_usd,COALESCE(AVG(quality_score),0) average_quality,COALESCE(AVG(schema_compliance),0) average_schema_compliance FROM task_attempts').get();const attemptsByModel=db.prepare('SELECT provider,model,COUNT(*) calls,COALESCE(SUM(input_tokens+output_tokens),0) total_tokens,COALESCE(SUM(estimated_cost),0) estimated_cost_usd,COALESCE(AVG(quality_score),0) average_quality FROM task_attempts GROUP BY provider,model ORDER BY calls DESC').all();const cache=db.prepare('SELECT COUNT(*) entries,COALESCE(SUM(hit_count),0) hits FROM cache_entries').get();const memory=db.prepare('SELECT state,COUNT(*) count FROM memory_records GROUP BY state').all();const approvals=db.prepare('SELECT status,COUNT(*) count FROM approvals GROUP BY status').all();const privacy=db.prepare('SELECT status,COUNT(*) count FROM privacy_requests GROUP BY status').all();const personalData=db.prepare('SELECT COUNT(*) count FROM personal_data_records WHERE deleted_at IS NULL').get().count;const dlq=db.prepare('SELECT COUNT(*) count FROM dead_letters WHERE resolved_at IS NULL').get().count;response(res,200,{generated_at:now(),tasks:byState,model_attempts:attempts,model_attempts_by_model:attemptsByModel,cache,memory,approvals,privacy_requests:privacy,active_personal_data_hash_records:personalData,open_dead_letters:dlq,audit:verifyAudit()});return;
    }
    response(res,404,{error:'not_found'});
  } catch(error){
    const status=Number(error.status||500);if(status>=500){try{tx(()=>audit({eventType:'runtime_error',actor:'runtime',payload:{message_hash:sha256(redact(error.message))}}));}catch{}}
    response(res,status,{error:status>=500?'internal_error':error.message});
  }
});

const recoveredLeases = recoverStaleLeases();
server.listen(port,host,()=>process.stdout.write(`Ajans Runtime listening on ${host}:${port}; recovered_leases=${recoveredLeases}\n`));
