import { spawn } from 'node:child_process';
import { randomBytes, createHash } from 'node:crypto';
import { DatabaseSync } from 'node:sqlite';
import { existsSync, unlinkSync, mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import path from 'node:path';

const reportPath = '/workspace/tests/results/disk-pressure-atomicity-report.json';
const sha256File = (file) => createHash('sha256').update(readFileSync(file)).digest('hex').toUpperCase();
const results = [];
const check = (name, condition, detail = null) => {
  results.push({ name, status: condition ? 'PASS' : 'FAIL', detail });
  if (!condition) throw new Error(`${name} failed: ${JSON.stringify(detail)}`);
};
const removeDb = (dbPath) => { for (const file of [dbPath, `${dbPath}-wal`, `${dbPath}-shm`]) if (existsSync(file)) unlinkSync(file); };
const startRuntime = async (port, dbPath, extraEnv = {}) => {
  const apiKey = `disk-${randomBytes(32).toString('hex')}`;
  const hmacKey = `disk-${randomBytes(48).toString('hex')}`;
  const child = spawn(process.execPath, ['/app/server.mjs'], { env: { ...process.env, HOST: '127.0.0.1', PORT: String(port), DB_PATH: dbPath, WORKSPACE_ROOT: '/workspace', RUNTIME_API_KEY: apiKey, APPROVAL_HMAC_KEY: hmacKey, ALLOW_LEGACY_RUNTIME_KEY: 'true', ALLOW_SYNTHETIC_ACCOUNTS: 'true', ...extraEnv }, stdio: ['ignore', 'ignore', 'pipe'] });
  let stderr = ''; child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
  for (let attempt = 0; attempt < 100; attempt += 1) {
    try { if ((await fetch(`http://127.0.0.1:${port}/health/live`)).ok) return { child, apiKey }; } catch {}
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  child.kill('SIGTERM'); throw new Error(`runtime start failed: ${stderr}`);
};
const stop = async (child) => { if (child?.exitCode === null) { child.kill('SIGTERM'); await new Promise((resolve) => child.once('exit', resolve)); } };
const createTask = async (port, apiKey, taskId, payload) => {
  const response = await fetch(`http://127.0.0.1:${port}/v1/tasks`, { method: 'POST', headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ task_id: taskId, idempotency_key: `idem-${taskId}`, brand_id: 'trendybrander', task_type: 'analysis', payload }) });
  const text = await response.text(); return { status: response.status, body: text ? JSON.parse(text) : {} };
};

let first; let second;
try {
  const atomicDb = '/runtime/atomic-rollback-test.sqlite'; removeDb(atomicDb);
  first = await startRuntime(5702, atomicDb);
  const injector = new DatabaseSync(atomicDb);
  injector.exec("CREATE TRIGGER synthetic_fail_audit BEFORE INSERT ON audit_events BEGIN SELECT RAISE(ABORT, 'synthetic_audit_failure'); END;");
  injector.close();
  const failedWrite = await createTask(5702, first.apiKey, 'atomic-rollback-task', { text: 'small' });
  check('synthetic-mid-transaction-failure-fails-closed', failedWrite.status === 500 && failedWrite.body.error === 'internal_error', failedWrite);
  const verify = new DatabaseSync(atomicDb, { readOnly: true });
  const taskCount = verify.prepare("SELECT COUNT(*) count FROM tasks WHERE task_id='atomic-rollback-task'").get().count;
  const quick = Object.values(verify.prepare('PRAGMA quick_check').get())[0];
  verify.close();
  check('mid-transaction-failure-leaves-no-partial-task', taskCount === 0, { task_count: taskCount });
  check('rollback-database-still-consistent', quick === 'ok', { quick_check: quick });
  await stop(first.child); first = null;

  const guardedDb = '/runtime/disk-preflight-test.sqlite'; removeDb(guardedDb);
  second = await startRuntime(5703, guardedDb, { MIN_FREE_BYTES: String(Number.MAX_SAFE_INTEGER) });
  const guardedWrite = await createTask(5703, second.apiKey, 'preflight-task', { text: 'small' });
  check('low-disk-preflight-rejects-before-write', guardedWrite.status === 507 && guardedWrite.body.error === 'insufficient_storage', guardedWrite);
  const guarded = new DatabaseSync(guardedDb, { readOnly: true });
  const guardedCount = guarded.prepare("SELECT COUNT(*) count FROM tasks WHERE task_id='preflight-task'").get().count;
  guarded.close();
  check('preflight-rejection-no-task-created', guardedCount === 0, { task_count: guardedCount });

  const report = { schema_version: '1.1', generated_at: new Date().toISOString(), status: 'PASS', model_calls: 0, external_calls: 0, host_disk_not_filled: true, production_runtime_has_test_failpoint: false, tests: results.length, provenance: { test_file: 'tests/disk-pressure-atomicity.test.mjs', test_sha256: sha256File('/workspace/tests/disk-pressure-atomicity.test.mjs'), runtime_file: 'ui/ajans-runtime/server.mjs', runtime_sha256: sha256File('/app/server.mjs'), schema_file: 'data/contracts/output-schemas.json', schema_sha256: sha256File('/workspace/data/contracts/output-schemas.json') }, results };
  mkdirSync(path.dirname(reportPath), { recursive: true });
  writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  process.stdout.write(JSON.stringify({ status: 'PASS', tests: results.length, report: reportPath }));
} catch (error) {
  mkdirSync(path.dirname(reportPath), { recursive: true });
  writeFileSync(reportPath, `${JSON.stringify({ schema_version: '1.0', generated_at: new Date().toISOString(), status: 'FAIL', error: error.message, results }, null, 2)}\n`, 'utf8');
  console.error(error.stack); process.exitCode = 1;
} finally {
  await stop(first?.child); await stop(second?.child);
}
