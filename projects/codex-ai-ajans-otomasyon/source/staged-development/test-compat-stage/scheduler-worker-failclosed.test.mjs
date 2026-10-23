import { spawn } from 'node:child_process';
import { createHash, randomBytes } from 'node:crypto';
import { DatabaseSync } from 'node:sqlite';
import { existsSync, unlinkSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';

const dbPath = '/runtime/scheduler-worker-failclosed.sqlite';
const reportPath = '/workspace/tests/results/scheduler-worker-failclosed-report.json';
const schedulerStatusPath = '/runtime/scheduler-failclosed.json';
const workerStatusPath = '/runtime/worker-failclosed.json';
for (const file of [dbPath, `${dbPath}-wal`, `${dbPath}-shm`, schedulerStatusPath, workerStatusPath]) if (existsSync(file)) unlinkSync(file);
const apiKey = `fc-${randomBytes(32).toString('hex')}`;
const hmacKey = `fc-${randomBytes(48).toString('hex')}`;
const adapterKey = `fc-${randomBytes(32).toString('hex')}`;
const children = [];
const results = [];
const check = (name, ok, detail = null) => { if (!ok) throw new Error(`${name}:${JSON.stringify(detail)}`); results.push({ name, status: 'PASS', detail }); };
const hashFile = (file) => createHash('sha256').update(readFileSync(file)).digest('hex').toUpperCase();
const start = (script, env) => { const child = spawn(process.execPath, [script], { env: { ...process.env, ...env }, stdio: ['ignore','ignore','pipe'] }); children.push(child); return child; };
const waitLive = async (url) => { for (let i = 0; i < 120; i += 1) { try { if ((await fetch(url)).ok) return; } catch {} await new Promise((resolve) => setTimeout(resolve, 50)); } throw new Error(`not_live:${url}`); };

try {
  start('/app/server.mjs', { HOST: '127.0.0.1', PORT: '5704', DB_PATH: dbPath, WORKSPACE_ROOT: '/workspace', RUNTIME_API_KEY: apiKey, APPROVAL_HMAC_KEY: hmacKey, ALLOW_LEGACY_RUNTIME_KEY: 'true', ALLOW_SYNTHETIC_ACCOUNTS: 'true' });
  await waitLive('http://127.0.0.1:5704/health/live');
  start('/workspace/ui/ajans-scheduler/scheduler.mjs', { HOST: '127.0.0.1', PORT: '5705', RUNTIME_URL: 'http://127.0.0.1:5704', RUNTIME_API_KEY: apiKey, AUTONOMOUS_TASKS_ENABLED: 'false', STATUS_PATH: schedulerStatusPath, SCHEDULER_INTERVAL_MS: '30000' });
  start('/workspace/ui/ajans-worker/worker.mjs', { HOST: '127.0.0.1', PORT: '5706', RUNTIME_URL: 'http://127.0.0.1:5704', RUNTIME_API_KEY: apiKey, MODEL_WORKER_ENABLED: 'false', MODEL_ADAPTER_URL: '', MODEL_ADAPTER_TOKEN: adapterKey, OUTPUT_SCHEMAS_PATH: '/workspace/data/contracts/output-schemas.json', CONTEXT_POLICY_PATH: '/workspace/data/memory/baglam-derleme-politikasi.json', STATUS_PATH: workerStatusPath, WORKER_INTERVAL_MS: '2000' });
  await Promise.all([waitLive('http://127.0.0.1:5705/health/live'), waitLive('http://127.0.0.1:5706/health/live')]);
  await new Promise((resolve) => setTimeout(resolve, 250));
  let response = await fetch('http://127.0.0.1:5705/health/ready'); let body = await response.json();
  check('scheduler-setup-required-before-credentials', response.status === 503 && body.readiness === 'setup_required', body);
  response = await fetch('http://127.0.0.1:5706/health/ready'); body = await response.json();
  check('worker-setup-required-before-adapter', response.status === 503 && body.readiness === 'setup_required', body);
  const db = new DatabaseSync(dbPath, { readOnly: true });
  const counts = { tasks: db.prepare('SELECT COUNT(*) count FROM tasks').get().count, outbox: db.prepare('SELECT COUNT(*) count FROM outbox_events').get().count, approvals: db.prepare('SELECT COUNT(*) count FROM approvals').get().count };
  db.close();
  check('disabled-execution-created-no-tasks', counts.tasks === 0, counts);
  check('disabled-execution-created-no-publish', counts.outbox === 0 && counts.approvals === 0, counts);
  const schedulerStatus = JSON.parse(readFileSync(schedulerStatusPath, 'utf8'));
  const workerStatus = JSON.parse(readFileSync(workerStatusPath, 'utf8'));
  check('health-files-report-zero-external-actions', schedulerStatus.model_calls === 0 && schedulerStatus.external_calls === 0 && schedulerStatus.publish_actions === 0 && workerStatus.publish_actions === 0, { schedulerStatus, workerStatus });
  const provenance = {
    test_file: 'tests/scheduler-worker-failclosed.test.mjs', test_sha256: hashFile('/workspace/tests/scheduler-worker-failclosed.test.mjs'),
    runtime_file: 'ui/ajans-runtime/server.mjs', runtime_sha256: hashFile('/app/server.mjs'),
    scheduler_file: 'ui/ajans-scheduler/scheduler.mjs', scheduler_sha256: hashFile('/workspace/ui/ajans-scheduler/scheduler.mjs'),
    worker_file: 'ui/ajans-worker/worker.mjs', worker_sha256: hashFile('/workspace/ui/ajans-worker/worker.mjs')
  };
  const report = { schema_version: '1.0', generated_at: new Date().toISOString(), status: 'PASS', tests: results.length, model_calls: 0, external_calls: 0, publish_actions: 0, provenance, results };
  mkdirSync(path.dirname(reportPath), { recursive: true }); writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  process.stdout.write(JSON.stringify({ status: 'PASS', tests: results.length, report: reportPath }));
} catch (error) {
  mkdirSync(path.dirname(reportPath), { recursive: true }); writeFileSync(reportPath, `${JSON.stringify({ schema_version: '1.0', status: 'FAIL', generated_at: new Date().toISOString(), error: error.message, results }, null, 2)}\n`); console.error(error.stack); process.exitCode = 1;
} finally {
  for (const child of children.reverse()) if (child.exitCode === null) { child.kill('SIGTERM'); await new Promise((resolve) => child.once('exit', resolve)); }
}
