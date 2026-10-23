import { createHash, pbkdf2Sync, randomBytes } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { DatabaseSync } from 'node:sqlite';
import os from 'node:os';
import path from 'node:path';

const projectSource = process.env.AI_AJANS_ROOT || 'C:\\ai-ajans';
const runtimeFile = process.env.RUNTIME_FILE || path.join(projectSource, 'ui', 'ajans-runtime', 'server.mjs');
const testRoot = path.join(os.tmpdir(), `ai-ajans-local-delivery-${Date.now()}-${randomBytes(4).toString('hex')}`);
const projectRoot = path.join(testRoot, 'workspace');
const imageRoot = path.join(projectRoot, 'data', 'outputs', 'images');
const deliveryRoot = path.join(projectRoot, 'data', 'outputs', 'approved');
const dbPath = path.join(testRoot, 'runtime.sqlite');
const port = 5791;
mkdirSync(imageRoot, { recursive: true });
for (const relative of ['data/contracts/output-schemas.json', 'data/memory/hesap-kayitlari.json', 'data/memory/baglam-derleme-politikasi.json']) {
  const destination = path.join(projectRoot, relative);
  mkdirSync(path.dirname(destination), { recursive: true });
  copyFileSync(path.join(projectSource, relative), destination);
}
writeFileSync(path.join(imageRoot, 'candidate.png'), Buffer.from('89504e470d0a1a0a0000000d49484452', 'hex'));

const runtimeKey = `runtime-${randomBytes(32).toString('hex')}`;
const centerKey = `center-${randomBytes(32).toString('hex')}`;
const schedulerKey = `scheduler-${randomBytes(32).toString('hex')}`;
const workerKey = `worker-${randomBytes(32).toString('hex')}`;
const n8nKey = `n8n-${randomBytes(32).toString('hex')}`;
const approvalKey = `approval-${randomBytes(48).toString('hex')}`;
const password = 'Local-only-approval-test-2026!';
const salt = randomBytes(32);
const iterations = 210000;
const passwordHash = `pbkdf2_sha256$${iterations}$${salt.toString('base64')}$${pbkdf2Sync(password, salt, iterations, 32, 'sha256').toString('base64')}`;
const results = [];
const check = (name, ok, detail = null) => { if (!ok) throw new Error(`${name}:${JSON.stringify(detail)}`); results.push({ name, status: 'PASS' }); };
const call = async (route, { method = 'GET', token = centerKey, cookie = '', csrf = '', body } = {}) => {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (cookie) headers.Cookie = cookie;
  if (csrf) headers['X-CSRF-Token'] = csrf;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const response = await fetch(`http://127.0.0.1:${port}${route}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  return { status: response.status, headers: response.headers, body: await response.json() };
};
const waitFor = async () => { for (let i = 0; i < 100; i += 1) { try { if ((await fetch(`http://127.0.0.1:${port}/health/live`)).ok) return; } catch {} await new Promise((resolve) => setTimeout(resolve, 50)); } throw new Error('runtime_start_timeout'); };

let child;
let childError = '';
try {
  child = spawn(process.execPath, [runtimeFile], { env: { ...process.env, HOST: '127.0.0.1', PORT: String(port), DB_PATH: dbPath, WORKSPACE_ROOT: projectRoot, RUNTIME_API_KEY: runtimeKey, CENTER_API_KEY: centerKey, SCHEDULER_API_KEY: schedulerKey, WORKER_API_KEY: workerKey, N8N_SERVICE_API_KEY: n8nKey, APPROVAL_HMAC_KEY: approvalKey, OPERATOR_PASSWORD_HASH: passwordHash, LOCAL_DELIVERY_ROOT: deliveryRoot, GENERATED_IMAGE_ROOT: imageRoot, ALLOW_SYNTHETIC_ACCOUNTS: 'true' }, stdio: ['ignore', 'ignore', 'pipe'] });
  child.stderr.on('data', (chunk) => { childError += chunk.toString('utf8'); });
  try { await waitFor(); } catch (error) { throw new Error(`${error.message}:${childError.slice(0, 2000)}`); }

  const payload = { brand_id: 'trendybrander', content_id: 'local-test-content', content_version: 'v1', idempotency_key: 'local-test-content-v1', summary: 'Yerel teslim testi', content_payload: { caption: 'Tasarımını yükle. Ütüyle uygula. Kendi ürününü evde üret.', format: 'post' }, preview_refs: ['/media/generated/candidate.png'] };
  let response = await call('/v1/local-approvals', { method: 'POST', body: payload });
  check('local-approval-created-without-social-account', response.status === 201 && response.body.delivery_mode === 'local_file_only' && response.body.publish_authorized === false, response);
  const approval = response.body;
  response = await call('/v1/operator/login', { method: 'POST', token: '', body: { password } });
  check('operator-login', response.status === 200 && response.body.csrf_token, response);
  const csrf = response.body.csrf_token;
  const cookie = String(response.headers.get('set-cookie') || '').split(';')[0];
  response = await call('/v1/approvals/waiting', { token: '', cookie });
  check('waiting-package-includes-caption-and-local-mode', response.status === 200 && response.body.items[0]?.content_payload?.caption === payload.content_payload.caption && response.body.items[0]?.delivery_mode === 'local_file_only', response);
  response = await call(`/v1/approvals/${approval.approval_id}/decision`, { method: 'POST', token: '', cookie, csrf, body: { decision: 'approve', nonce: approval.nonce } });
  check('approval-saves-local-delivery', response.status === 200 && response.body.delivery?.output_dir && response.body.delivery?.reused === false, response);
  const outputDir = path.join(deliveryRoot, 'trendybrander', 'local-test-content', 'v1');
  check('caption-saved', readFileSync(path.join(outputDir, 'caption.txt'), 'utf8').trim() === payload.content_payload.caption);
  check('content-and-visual-saved', existsSync(path.join(outputDir, 'content.json')) && existsSync(path.join(outputDir, 'visual-01.png')) && existsSync(path.join(outputDir, 'approval.json')) && existsSync(path.join(outputDir, 'manifest.json')));
  const approvalFile = JSON.parse(readFileSync(path.join(outputDir, 'approval.json'), 'utf8'));
  check('saved-package-is-explicitly-nonpublishable', approvalFile.publish_authorized === false && approvalFile.delivery_mode === 'local_file_only', approvalFile);
  response = await call('/v1/publish/authorize', { method: 'POST', token: n8nKey, body: { ...payload, account_id: '__local_file_only__', approval_id: approval.approval_id, content_hash: approvalFile.content_hash } });
  check('local-delivery-cannot-be-publish-authorized', response.status === 403 && response.body.error === 'local_delivery_never_publishable', response);
  response = await call('/v1/local-approvals', { method: 'POST', body: payload });
  check('duplicate-local-request-is-idempotent', response.status === 200 && response.body.reused === true && response.body.approval_id === approval.approval_id, response);

  const invalid = { ...payload, content_id: 'invalid-path', content_version: 'v1', idempotency_key: 'invalid-path-v1', preview_refs: ['../candidate.png'] };
  response = await call('/v1/local-approvals', { method: 'POST', body: invalid });
  check('path-traversal-preview-rejected', response.status === 422 && response.body.error === 'invalid_image_reference', response);

  const rejectPayload = { ...payload, content_id: 'reject-content', idempotency_key: 'reject-content-v1' };
  response = await call('/v1/local-approvals', { method: 'POST', body: rejectPayload }); const rejected = response.body;
  response = await call(`/v1/approvals/${rejected.approval_id}/decision`, { method: 'POST', token: '', cookie, csrf, body: { decision: 'reject', nonce: rejected.nonce } });
  check('reject-does-not-save-delivery', response.status === 200 && !existsSync(path.join(deliveryRoot, 'trendybrander', 'reject-content')));

  const revisePayload = { ...payload, content_id: 'revise-content', idempotency_key: 'revise-content-v1' };
  response = await call('/v1/local-approvals', { method: 'POST', body: revisePayload }); const revised = response.body;
  response = await call(`/v1/approvals/${revised.approval_id}/decision`, { method: 'POST', token: '', cookie, csrf, body: { decision: 'revise', nonce: revised.nonce, revision_note: 'Başlığı kısalt.' } });
  check('revise-does-not-save-delivery', response.status === 200 && !existsSync(path.join(deliveryRoot, 'trendybrander', 'revise-content')));

  const db = new DatabaseSync(dbPath, { readOnly: true });
  const outbox = db.prepare('SELECT COUNT(*) count FROM outbox_events').get().count;
  const receipt = db.prepare("SELECT status,output_dir FROM local_delivery_receipts WHERE approval_id=?").get(approval.approval_id);
  db.close();
  check('no-publish-outbox-event-created', outbox === 0, { outbox });
  check('signed-local-delivery-receipt-recorded', receipt?.status === 'saved' && receipt.output_dir.includes('data/outputs/approved'), receipt);

  process.stdout.write(JSON.stringify({ status: 'PASS', tests: results.length, results }));
} catch (error) {
  console.error(error.stack);
  process.exitCode = 1;
} finally {
  if (child?.exitCode === null) { child.kill('SIGTERM'); await new Promise((resolve) => child.once('exit', resolve)); }
  rmSync(testRoot, { recursive: true, force: true });
}
