import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { createHash, randomBytes, pbkdf2Sync } from 'node:crypto';
import { DatabaseSync } from 'node:sqlite';
import { existsSync, unlinkSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';

const dbPath = '/runtime/worker-pipeline-test.sqlite';
const reportPath = '/workspace/tests/results/worker-pipeline-report.json';
const statusPath = '/runtime/worker-pipeline-status.json';
for (const file of [dbPath, `${dbPath}-wal`, `${dbPath}-shm`, statusPath]) if (existsSync(file)) unlinkSync(file);
const apiKey = `pipe-${randomBytes(32).toString('hex')}`;
const hmacKey = `pipe-${randomBytes(48).toString('hex')}`;
const adapterKey = `adapter-${randomBytes(32).toString('hex')}`;
const salt = randomBytes(32); const password = 'Synthetic-operator-only-2026!'; const iterations = 210000;
const passwordHash = `pbkdf2_sha256$${iterations}$${salt.toString('base64')}$${pbkdf2Sync(password, salt, iterations, 32, 'sha256').toString('base64')}`;
const results = []; const children = []; let adapterCalls = 0;
const check = (name, ok, detail = null) => { if (!ok) throw new Error(`${name}:${JSON.stringify(detail)}`); results.push({ name, status: 'PASS', detail }); };
const hashFile = (file) => createHash('sha256').update(readFileSync(file)).digest('hex').toUpperCase();
const waitFor = async (condition, label, attempts = 160) => { for (let i = 0; i < attempts; i += 1) { if (await condition()) return; await new Promise((resolve) => setTimeout(resolve, 50)); } throw new Error(`timeout:${label}`); };
const adapter = createServer(async (req, res) => {
  if (req.method !== 'POST' || req.headers.authorization !== `Bearer ${adapterKey}`) { res.writeHead(401); res.end('{}'); return; }
  let raw = ''; for await (const chunk of req) raw += chunk; const body = JSON.parse(raw || '{}'); adapterCalls += 1;
  if (body.task_type !== 'analysis' || !body.output_schema?.properties?.grounding_status || body.compact_context?.full_prompt || body.model_limits?.max_input_tokens !== 2600 || body.model_limits?.max_output_tokens !== 500 || !body.request_hash || !body.schema_hash || req.headers['x-ajans-request-hash'] !== body.request_hash) { res.writeHead(422); res.end('{}'); return; }
  await new Promise((resolve) => setTimeout(resolve, 600));
  const output = { data_status: 'Yalniz sentetik girdi var.', grounding_status: 'hypothesis', evidence_refs: [], main_finding: 'Bu bir boru hatti testidir.', target_segment: 'Sentetik hedef', strategic_direction: 'Yayin yapmadan dogrula.', priority_actions: ['Dogrulamayi tamamla.'], missing_data: ['Gercek performans'], risk_and_confidence: { risk: 'low', confidence: 0.5, reason: 'Sentetik veri.' } };
  let usage = { input_tokens: 120, output_tokens: 35, total_tokens: 155 };
  if (body.task_id === 'pipeline-missing-usage') usage = null;
  if (body.task_id === 'pipeline-negative-usage') usage = { input_tokens: -1, output_tokens: 35, total_tokens: 34 };
  if (body.task_id === 'pipeline-over-input-usage') usage = { input_tokens: 2601, output_tokens: 35, total_tokens: 2636 };
  const responseBody = { task_id: body.task_id, request_hash: body.request_hash, schema_hash: body.schema_hash, output, provider: 'google', model: 'models/gemini-3.1-flash-lite' };
  if (usage) responseBody.usage = usage;
  res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(responseBody));
});

try {
  await new Promise((resolve) => adapter.listen(5708, '127.0.0.1', resolve));
  const runtime = spawn(process.execPath, ['/app/server.mjs'], { env: { ...process.env, HOST: '127.0.0.1', PORT: '5707', DB_PATH: dbPath, WORKSPACE_ROOT: '/workspace', RUNTIME_API_KEY: apiKey, APPROVAL_HMAC_KEY: hmacKey, OPERATOR_PASSWORD_HASH: passwordHash, ALLOW_LEGACY_RUNTIME_KEY: 'true', ALLOW_SYNTHETIC_ACCOUNTS: 'true' }, stdio: ['ignore','ignore','pipe'] }); children.push(runtime);
  await waitFor(async () => { try { return (await fetch('http://127.0.0.1:5707/health/ready')).status === 200; } catch { return false; } }, 'runtime-ready');
  const auth = { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' };
  let response = await fetch('http://127.0.0.1:5707/v1/tasks', { method: 'POST', headers: auth, body: JSON.stringify({ task_id: 'pipeline-publish', idempotency_key: 'pipeline-publish-v1', brand_id: 'trendybrander', task_type: 'publish', agent_id: 'yayin_arayuz_ajani', payload: { no_publish: false }, max_retries: 0 }) });
  check('publish-task-enqueued-before-model-task', response.status === 201, await response.json());
  response = await fetch('http://127.0.0.1:5707/v1/tasks', { method: 'POST', headers: auth, body: JSON.stringify({ task_id: 'pipeline-good', idempotency_key: 'pipeline-good-v1', brand_id: 'trendybrander', task_type: 'analysis', agent_id: 'analizci', payload: { no_publish: true, compact_context_required: true, goal: 'Sentetik pipeline testi', model_budget: { max_calls: 1 } }, max_retries: 0 }) });
  check('valid-compact-task-enqueued', response.status === 201, await response.json());
  const worker = spawn(process.execPath, ['/workspace/ui/ajans-worker/worker.mjs'], { env: { ...process.env, HOST: '127.0.0.1', PORT: '5709', RUNTIME_URL: 'http://127.0.0.1:5707', RUNTIME_API_KEY: apiKey, MODEL_WORKER_ENABLED: 'true', MODEL_ACCEPTANCE_PROOF: 'verified', MODEL_PROVIDER: 'google', MODEL_NAME: 'models/gemini-3.1-flash-lite', MODEL_BILLING_MODE: 'free_tier', MODEL_INPUT_USD_PER_MILLION: '0', MODEL_OUTPUT_USD_PER_MILLION: '0', MODEL_PRICING_VERIFIED: 'true', MODEL_ADAPTER_URL: 'http://127.0.0.1:5708/execute', MODEL_ADAPTER_TOKEN: adapterKey, OUTPUT_SCHEMAS_PATH: '/workspace/data/contracts/output-schemas.json', CONTEXT_POLICY_PATH: '/workspace/data/memory/baglam-derleme-politikasi.json', STATUS_PATH: statusPath, WORKER_INTERVAL_MS: '2000', WORKER_HEARTBEAT_MS: '200' }, stdio: ['ignore','ignore','pipe'] }); children.push(worker);
  await waitFor(async () => { try { return (await fetch('http://127.0.0.1:5709/health/ready')).status === 200; } catch { return false; } }, 'worker-ready');
  await waitFor(() => { const db = new DatabaseSync(dbPath, { readOnly: true }); const state = db.prepare("SELECT state FROM tasks WHERE task_id='pipeline-good'").get()?.state; db.close(); return state === 'completed'; }, 'valid-task-complete');
  let db = new DatabaseSync(dbPath, { readOnly: true });
  const complete = db.prepare("SELECT state,result_hash FROM tasks WHERE task_id='pipeline-good'").get();
  const attempts = db.prepare("SELECT COUNT(*) count,SUM(input_tokens) input_tokens,SUM(output_tokens) output_tokens,MAX(quality_score) quality_score,MAX(schema_compliance) schema_compliance FROM task_attempts WHERE task_id='pipeline-good'").get();
  const provenanceCount = db.prepare("SELECT COUNT(*) count FROM agent_output_provenance WHERE task_id='pipeline-good' AND eligible_as_factual_evidence=0").get().count;
  const evidence = db.prepare("SELECT COUNT(*) count FROM verified_evidence WHERE source_kind='validated_agent_output'").get().count;
  const heartbeats = db.prepare("SELECT COUNT(*) count FROM audit_events WHERE event_type='task_heartbeat' AND task_id='pipeline-good'").get().count;
  const outbox = db.prepare('SELECT COUNT(*) count FROM outbox_events').get().count;
  const publishState = db.prepare("SELECT state FROM tasks WHERE task_id='pipeline-publish'").get()?.state; db.close();
  check('worker-validates-before-completion', complete.state === 'completed' && Boolean(complete.result_hash), complete);
  check('model-telemetry-separates-schema-from-quality', attempts.count === 1 && attempts.input_tokens === 120 && attempts.output_tokens === 35 && attempts.quality_score === null && attempts.schema_compliance === 1, attempts);
  check('validated-output-is-provenance-not-evidence', provenanceCount === 1 && evidence === 0, { provenanceCount, evidence });
  check('lease-heartbeat-during-adapter-call', heartbeats >= 2, { heartbeats });
  check('worker-never-publishes', outbox === 0, { outbox });
  check('model-worker-does-not-claim-publish-task', publishState === 'queued', { publishState });
  response = await fetch('http://127.0.0.1:5707/v1/tasks', { method: 'POST', headers: auth, body: JSON.stringify({ task_id: 'pipeline-forbidden', idempotency_key: 'pipeline-forbidden-v1', brand_id: 'trendybrander', task_type: 'analysis', agent_id: 'analizci', payload: { no_publish: true, full_prompt: 'forbidden' }, max_retries: 0 }) });
  check('forbidden-context-task-enqueued-for-failclosed-test', response.status === 201, await response.json());
  await waitFor(() => { const verify = new DatabaseSync(dbPath, { readOnly: true }); const state = verify.prepare("SELECT state FROM tasks WHERE task_id='pipeline-forbidden'").get()?.state; verify.close(); return state === 'failed'; }, 'forbidden-task-failed');
  check('forbidden-full-prompt-never-reached-adapter', adapterCalls === 1, { adapterCalls });
  response = await fetch('http://127.0.0.1:5707/v1/tasks', { method: 'POST', headers: auth, body: JSON.stringify({ task_id: 'pipeline-secret', idempotency_key: 'pipeline-secret-v1', brand_id: 'trendybrander', task_type: 'analysis', agent_id: 'analizci', payload: { no_publish: true, nested: { access_token: 'synthetic-forbidden' } }, max_retries: 0 }) });
  check('secret-context-task-enqueued-for-failclosed-test', response.status === 201, await response.json());
  await waitFor(() => { const verify = new DatabaseSync(dbPath, { readOnly: true }); const state = verify.prepare("SELECT state FROM tasks WHERE task_id='pipeline-secret'").get()?.state; verify.close(); return state === 'failed'; }, 'secret-task-failed');
  check('secret-context-never-reached-adapter', adapterCalls === 1, { adapterCalls });
  response = await fetch('http://127.0.0.1:5707/v1/tasks', { method: 'POST', headers: auth, body: JSON.stringify({ task_id: 'pipeline-overbudget', idempotency_key: 'pipeline-overbudget-v1', brand_id: 'trendybrander', task_type: 'analysis', agent_id: 'analizci', payload: { no_publish: true, goal: 'x'.repeat(9000) }, max_retries: 0 }) });
  check('overbudget-context-task-enqueued-for-failclosed-test', response.status === 201, await response.json());
  await waitFor(() => { const verify = new DatabaseSync(dbPath, { readOnly: true }); const state = verify.prepare("SELECT state FROM tasks WHERE task_id='pipeline-overbudget'").get()?.state; verify.close(); return state === 'failed'; }, 'overbudget-task-failed');
  check('hard-token-budget-blocks-adapter-call', adapterCalls === 1, { adapterCalls });
  for (const taskId of ['pipeline-missing-usage','pipeline-negative-usage','pipeline-over-input-usage']) {
    response = await fetch('http://127.0.0.1:5707/v1/tasks', { method: 'POST', headers: auth, body: JSON.stringify({ task_id: taskId, idempotency_key: `${taskId}-v1`, brand_id: 'trendybrander', task_type: 'analysis', agent_id: 'analizci', payload: { no_publish: true, goal: `Usage fail-closed test ${taskId}` }, max_retries: 0 }) });
    check(`${taskId}-enqueued`, response.status === 201, await response.json());
    await waitFor(() => { const verify = new DatabaseSync(dbPath, { readOnly: true }); const state = verify.prepare('SELECT state FROM tasks WHERE task_id=?').get(taskId)?.state; verify.close(); return state === 'failed'; }, `${taskId}-failed`);
  }
  db = new DatabaseSync(dbPath, { readOnly: true });
  const missingUsageAttempt = db.prepare("SELECT input_tokens,output_tokens,estimated_cost,error_type FROM task_attempts WHERE task_id='pipeline-missing-usage'").get();
  const negativeUsageAttempt = db.prepare("SELECT input_tokens,output_tokens,estimated_cost,error_type FROM task_attempts WHERE task_id='pipeline-negative-usage'").get();
  const overInputAttempt = db.prepare("SELECT input_tokens,output_tokens,estimated_cost,error_type FROM task_attempts WHERE task_id='pipeline-over-input-usage'").get(); db.close();
  check('missing-usage-reserves-full-budget-not-zero', missingUsageAttempt.input_tokens === 2600 && missingUsageAttempt.output_tokens === 500 && missingUsageAttempt.estimated_cost === 0.02 && missingUsageAttempt.error_type.includes('usage_unknown_budget_reserved'), missingUsageAttempt);
  check('negative-usage-reserves-full-budget-not-zero', negativeUsageAttempt.input_tokens === 2600 && negativeUsageAttempt.output_tokens === 500 && negativeUsageAttempt.estimated_cost === 0.02 && negativeUsageAttempt.error_type.includes('usage_unknown_budget_reserved'), negativeUsageAttempt);
  check('actual-input-token-overrun-fails-closed', overInputAttempt.input_tokens === 2601 && overInputAttempt.error_type === 'hard_input_token_budget_exceeded', overInputAttempt);
  const provenance = { test_file: 'tests/worker-pipeline.test.mjs', test_sha256: hashFile('/workspace/tests/worker-pipeline.test.mjs'), runtime_file: 'ui/ajans-runtime/server.mjs', runtime_sha256: hashFile('/app/server.mjs'), worker_file: 'ui/ajans-worker/worker.mjs', worker_sha256: hashFile('/workspace/ui/ajans-worker/worker.mjs'), schema_file: 'data/contracts/output-schemas.json', schema_sha256: hashFile('/workspace/data/contracts/output-schemas.json'), context_policy_file: 'data/memory/baglam-derleme-politikasi.json', context_policy_sha256: hashFile('/workspace/data/memory/baglam-derleme-politikasi.json') };
  const report = { schema_version: '1.0', generated_at: new Date().toISOString(), status: 'PASS', tests: results.length, deterministic_adapter_only: true, real_model_calls: 0, external_calls: 0, publish_actions: 0, provenance, results };
  mkdirSync(path.dirname(reportPath), { recursive: true }); writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`); process.stdout.write(JSON.stringify({ status: 'PASS', tests: results.length, report: reportPath }));
} catch (error) {
  mkdirSync(path.dirname(reportPath), { recursive: true }); writeFileSync(reportPath, `${JSON.stringify({ schema_version: '1.0', generated_at: new Date().toISOString(), status: 'FAIL', error: error.message, results }, null, 2)}\n`); console.error(error.stack); process.exitCode = 1;
} finally {
  for (const child of children.reverse()) if (child.exitCode === null) { child.kill('SIGTERM'); await new Promise((resolve) => child.once('exit', resolve)); }
  await new Promise((resolve) => adapter.close(resolve));
}
