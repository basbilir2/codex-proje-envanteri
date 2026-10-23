import { spawn } from 'node:child_process';
import { createHash, createHmac, pbkdf2Sync, randomBytes } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync, copyFileSync } from 'node:fs';
import path from 'node:path';

const workspace = '/runtime/account-binding-workspace';
const dbPath = '/runtime/account-binding-test.sqlite';
const reportPath = '/workspace/tests/results/account-binding-report.json';
for (const target of [workspace, dbPath, `${dbPath}-wal`, `${dbPath}-shm`]) {
  if (existsSync(target)) rmSync(target, { recursive: true, force: true });
}
mkdirSync(path.join(workspace, 'data/contracts'), { recursive: true });
mkdirSync(path.join(workspace, 'data/memory'), { recursive: true });
copyFileSync('/workspace/data/contracts/output-schemas.json', path.join(workspace, 'data/contracts/output-schemas.json'));
copyFileSync('/workspace/data/memory/baglam-derleme-politikasi.json', path.join(workspace, 'data/memory/baglam-derleme-politikasi.json'));
const approvalKey = `approval-${randomBytes(48).toString('hex')}`;
const canonical = (value) => value === null || typeof value !== 'object' ? JSON.stringify(value) : Array.isArray(value) ? `[${value.map(canonical).join(',')}]` : `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`;
const sha256 = (value) => createHash('sha256').update(value).digest('hex');

const originalAccount = {
  brand_id: 'trendybrander', platform: 'instagram', account_id: 'ig-account-123', page_id: 'page-123',
  credential_ref: 'n8n-credential-instagram-trendybrander', status: 'verified',
  verified_at: '2026-08-02T00:00:00.000Z', display_name: 'TrendyBrander'
};
const registryPath = path.join(workspace, 'data/memory/hesap-kayitlari.json');
const writeRegistry = (record) => {
  const registry = { schema_version: '1.0', updated_at: '2026-08-02', status: 'test', records: [record] };
  const payloadJson = JSON.stringify(registry);
  registry.signature = { algorithm: 'HMAC-SHA256-DPAPI-local-user', payload_json: payloadJson, payload_sha256: sha256(payloadJson), value: createHmac('sha256', approvalKey).update(payloadJson).digest('hex') };
  writeFileSync(registryPath, `${JSON.stringify(registry, null, 2)}\n`);
};
writeRegistry(originalAccount);

const port = 5714;
const base = `http://127.0.0.1:${port}`;
const centerKey = `center-${randomBytes(32).toString('hex')}`;
const n8nKey = `n8n-${randomBytes(32).toString('hex')}`;
const rootKey = `root-${randomBytes(32).toString('hex')}`;
const password = 'Synthetic-account-binding-password-2026!';
const salt = randomBytes(32); const iterations = 210000;
const passwordHash = `pbkdf2_sha256$${iterations}$${salt.toString('base64')}$${pbkdf2Sync(password, salt, iterations, 32, 'sha256').toString('base64')}`;
const hashFile = (file) => createHash('sha256').update(readFileSync(file)).digest('hex').toUpperCase();
const results = [];
const check = (name, passed, detail = null) => { if (!passed) throw new Error(`${name}:${JSON.stringify(detail)}`); results.push({ name, status: 'PASS', detail }); };
const serviceHeaders = (key) => ({ Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' });
const call = async (route, { method = 'GET', headers = {}, body } = {}) => {
  const response = await fetch(`${base}${route}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  const text = await response.text(); return { status: response.status, body: text ? JSON.parse(text) : {}, headers: response.headers };
};

let child;
try {
  child = spawn(process.execPath, ['/app/server.mjs'], { env: {
    ...process.env, HOST: '127.0.0.1', PORT: String(port), DB_PATH: dbPath, WORKSPACE_ROOT: workspace,
    LOCAL_DELIVERY_ROOT: path.join(workspace, 'data/outputs/approved'),
    GENERATED_IMAGE_ROOT: path.join(workspace, 'data/outputs/images'),
    RUNTIME_API_KEY: rootKey, CENTER_API_KEY: centerKey, N8N_SERVICE_API_KEY: n8nKey,
    SCHEDULER_API_KEY: `scheduler-${randomBytes(32).toString('hex')}`, WORKER_API_KEY: `worker-${randomBytes(32).toString('hex')}`,
    APPROVAL_HMAC_KEY: approvalKey, OPERATOR_PASSWORD_HASH: passwordHash
  }, stdio: ['ignore', 'ignore', 'pipe'] });
  let stderr = ''; child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
  let live = false; for (let index = 0; index < 100; index += 1) { try { if ((await fetch(`${base}/health/live`)).ok) { live = true; break; } } catch {} await new Promise((resolve) => setTimeout(resolve, 50)); }
  if (!live) throw new Error(`runtime_not_live:${stderr}`);

  const login = await call('/v1/operator/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: { password } });
  const cookie = login.headers.get('set-cookie')?.split(';')[0]; const csrf = login.body.csrf_token;
  check('operator-session-created', login.status === 200 && Boolean(cookie) && Boolean(csrf), login.body);

  const createAndApprove = async (suffix) => {
    const contentPayload = { caption: `Synthetic ${suffix}`, visual_ref: `synthetic://${suffix}` };
    const request = { brand_id: 'trendybrander', account_id: originalAccount.account_id, content_id: `content-${suffix}`, content_version: 'v1', content_payload: contentPayload, content_hash: sha256(canonical(contentPayload)), idempotency_key: `publish-${suffix}`, summary: `Synthetic ${suffix}` };
    const created = await call('/v1/approvals', { method: 'POST', headers: serviceHeaders(centerKey), body: request });
    check(`approval-created-${suffix}`, created.status === 201 && Boolean(created.body.nonce), created.body);
    const decision = await call(`/v1/approvals/${created.body.approval_id}/decision`, { method: 'POST', headers: { 'Content-Type': 'application/json', Cookie: cookie, 'X-CSRF-Token': csrf }, body: { decision: 'approve', nonce: created.body.nonce } });
    check(`approval-signed-${suffix}`, decision.status === 200 && Boolean(decision.body.record?.signature_hmac), decision.body);
    return { ...request, approval_id: created.body.approval_id };
  };

  const changedTarget = await createAndApprove('binding-changed');
  writeRegistry({ ...originalAccount, credential_ref: 'n8n-credential-unexpected' });
  let result = await call('/v1/publish/authorize', { method: 'POST', headers: serviceHeaders(n8nKey), body: changedTarget });
  check('changed-account-binding-invalidates-approval', result.status === 409 && result.body.error === 'target_account_binding_changed', result.body);

  writeRegistry(originalAccount);
  const disabledTarget = await createAndApprove('target-disabled');
  writeRegistry({ ...originalAccount, status: 'disabled' });
  result = await call('/v1/publish/authorize', { method: 'POST', headers: serviceHeaders(n8nKey), body: disabledTarget });
  check('disabled-account-invalidates-approval', result.status === 409 && result.body.error === 'target_account_no_longer_verified', result.body);

  result = await call('/v1/publish/authorize', { method: 'POST', headers: serviceHeaders(centerKey), body: disabledTarget });
  check('center-cannot-authorize-publish', result.status === 401, result.body);

  const report = { schema_version: '1.0', generated_at: new Date().toISOString(), status: 'PASS', tests: results.length, model_calls: 0, external_calls: 0, publish_actions: 0, provenance: { test_file: 'tests/account-binding.test.mjs', test_sha256: hashFile('/workspace/tests/account-binding.test.mjs'), runtime_file: 'ui/ajans-runtime/server.mjs', runtime_sha256: hashFile('/app/server.mjs') }, results };
  mkdirSync(path.dirname(reportPath), { recursive: true }); writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  process.stdout.write(JSON.stringify({ status: 'PASS', tests: results.length, report: reportPath }));
} catch (error) {
  mkdirSync(path.dirname(reportPath), { recursive: true }); writeFileSync(reportPath, `${JSON.stringify({ schema_version: '1.0', generated_at: new Date().toISOString(), status: 'FAIL', error: error.message, results }, null, 2)}\n`);
  console.error(error.stack); process.exitCode = 1;
} finally {
  if (child && child.exitCode === null) { child.kill('SIGTERM'); await new Promise((resolve) => child.once('exit', resolve)); }
  rmSync(workspace, { recursive: true, force: true });
}
