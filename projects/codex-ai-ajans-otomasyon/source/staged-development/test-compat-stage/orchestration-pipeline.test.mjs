import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { createHash, randomBytes, pbkdf2Sync } from 'node:crypto';
import { DatabaseSync } from 'node:sqlite';
import { existsSync, unlinkSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';

const dbPath = '/runtime/orchestration-pipeline-test.sqlite';
const reportPath = '/workspace/tests/results/orchestration-pipeline-report.json';
const statusPath = '/runtime/orchestration-worker-status.json';
for (const file of [dbPath, `${dbPath}-wal`, `${dbPath}-shm`, statusPath]) if (existsSync(file)) unlinkSync(file);
const apiKey = `orch-${randomBytes(32).toString('hex')}`;
const hmacKey = `orch-${randomBytes(48).toString('hex')}`;
const adapterKey = `orch-adapter-${randomBytes(32).toString('hex')}`;
const salt = randomBytes(32); const password = 'Synthetic-orchestration-password-2026!'; const iterations = 210000;
const passwordHash = `pbkdf2_sha256$${iterations}$${salt.toString('base64')}$${pbkdf2Sync(password, salt, iterations, 32, 'sha256').toString('base64')}`;
const children = []; const results = []; let adapterCalls = 0;
const check = (name, ok, detail = null) => { if (!ok) throw new Error(`${name}:${JSON.stringify(detail)}`); results.push({ name, status: 'PASS', detail }); };
const hashFile = (file) => createHash('sha256').update(readFileSync(file)).digest('hex').toUpperCase();
const outputs = {
  classification: { decision: 'analysis', risk_level: 'low', reason: 'Düşük riskli üretim testi.', required_agents: ['analizci'], model_layer: 1, budget: { max_input_tokens: 600, max_output_tokens: 140, max_calls: 1, max_retries: 0, max_cost_usd: 0 }, next_step: 'analysis' },
  analysis: { data_status: 'Yalnız marka verisi var.', grounding_status: 'hypothesis', evidence_refs: [], main_finding: 'Kolaylık mesajı test edilmelidir.', target_segment: 'Evde üretim isteyenler', strategic_direction: 'Düşük riskli içerik hipotezi üret.', priority_actions: ['Sade bir fikir hazırla.'], missing_data: ['Gerçek performans verisi'], risk_and_confidence: { risk: 'low', confidence: 0.5, reason: 'Gerçek sonuç yok.' } },
  content_ideas: { data_disclaimer: 'Gerçek performans verisi yok.', segment: 'Evde üretim isteyenler', ideas: [{ id: 'I1', format: 'post', hook: 'Fikrini ürüne dönüştür', message: 'Tasarımını hazırla ve uygulama talimatını izle.', cta: 'Tasarımını hazırla', visual_direction: 'Tek ürün ve sade arka plan' }], recommended_candidate: 'I1', selection_reason: 'Marka konumuna uygundur.' },
  visual_brief: { visual_briefs: [{ id: 'V1', format: 'post', composition: 'Tek ürün ve sade arka plan.', overlay_text: 'Fikrini ürüne dönüştür', generation_prompt: 'Sade ürün kompozisyonu üret.', negative_constraints: ['Fazla yazı kullanma.'], evidence_refs: [] }], generation_status: 'brief_only', data_disclaimer: 'Yalnız görsel brieftir.' },
  debate_turn: { bold_view: { position: 'Kancayı kısa tut.', concerns: [], proposal: 'Tek güçlü başlık kullan.', evidence_refs: [] }, cautious_view: { position: 'İddiayı ölçülü tut.', concerns: [], proposal: 'Performans iddiası ekleme.', evidence_refs: [] }, common_points: ['Sade anlatım'], required_changes: [], another_round_required: false, confidence: 0.6 },
  ordinaryus_decision: { decision: 'Operator_ONAYI', selected_candidate: 'I1', reason: 'Paket onaya sunulabilir.', required_revisions: [], remaining_risks: ['Gerçek performans verisi yok.'], confidence: 0.8, evidence_refs: ['evidence-test-001'], Operator_summary: 'Bir içerik ve görsel brief onaya hazır.' },
  independent_audit: { decision: 'UPHOLD', findings: ['Paket kullanıcı onayına sunulabilir.'], evidence_gaps: ['Yayın sonrası performans'], risk: 'medium', confidence: 0.79, evidence_refs: [], independence_unavailable: false, next_step: 'Onay özeti hazırla' },
  interface_summary: { summary: 'Bir içerik paketi onayınıza hazır.', attention_points: ['Gerçek performans verisi henüz yok.'], recommended_action: 'request_approval' }
};

const adapter = createServer(async (req, res) => {
  if (req.method !== 'POST' || req.headers.authorization !== `Bearer ${adapterKey}`) { res.writeHead(401); res.end('{}'); return; }
  let raw = ''; for await (const chunk of req) raw += chunk; const body = JSON.parse(raw || '{}'); adapterCalls += 1;
  let output = outputs[body.task_type];
  if (body.task_type === 'ordinaryus_decision' && body.task_id.startsWith('pipeline-same-provider-001')) output = { ...outputs.ordinaryus_decision, confidence: 0.7, evidence_refs: [] };
  if (body.task_type === 'independent_audit' && body.task_id.startsWith('pipeline-veto-001')) output = { ...outputs.independent_audit, decision: 'VETO', findings: ['Kritik risk giderilmedi.'], risk: 'high', confidence: 0.79, next_step: 'Akışı durdur' };
  if (body.task_type === 'independent_audit' && body.task_id.startsWith('pipeline-human-001')) output = { ...outputs.independent_audit, decision: 'HUMAN_REVIEW', independence_unavailable: true, confidence: 0.6, next_step: 'İnsan incelemesi bekle' };
  if (!output || !body.request_hash || !body.schema_hash || req.headers['x-ajans-request-hash'] !== body.request_hash) { res.writeHead(422); res.end('{}'); return; }
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ task_id: body.task_id, request_hash: body.request_hash, schema_hash: body.schema_hash, output, provider: 'google', model: 'models/gemini-3.1-flash-lite', usage: { input_tokens: 100, output_tokens: 30, total_tokens: 130 } }));
});

const waitFor = async (fn, label, attempts = 300) => { for (let index = 0; index < attempts; index += 1) { if (await fn()) return; await new Promise((resolve) => setTimeout(resolve, 100)); } throw new Error(`timeout:${label}`); };

try {
  await new Promise((resolve) => adapter.listen(5711, '127.0.0.1', resolve));
  const runtime = spawn(process.execPath, ['/app/server.mjs'], { env: { ...process.env, HOST: '127.0.0.1', PORT: '5710', DB_PATH: dbPath, WORKSPACE_ROOT: '/workspace', RUNTIME_API_KEY: apiKey, APPROVAL_HMAC_KEY: hmacKey, OPERATOR_PASSWORD_HASH: passwordHash, ALLOW_LEGACY_RUNTIME_KEY: 'true', ALLOW_SYNTHETIC_ACCOUNTS: 'true' }, stdio: ['ignore','ignore','pipe'] }); children.push(runtime);
  await waitFor(async () => { try { return (await fetch('http://127.0.0.1:5710/health/ready')).status === 200; } catch { return false; } }, 'runtime-ready');
  const evidenceDb = new DatabaseSync(dbPath);
  evidenceDb.prepare('INSERT INTO verified_evidence(evidence_id,brand_id,claim,source_ref,source_hash,source_date,source_kind,sample_size,metric_window,confidence,verified_by,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)').run('evidence-test-001','trendybrander','Paket sentetik kabul testinde şema ve marka sınırlarına uydu.','synthetic://orchestration-test','a'.repeat(64),new Date().toISOString(),'synthetic',1,'',0.9,'deterministic-test',new Date().toISOString());
  evidenceDb.close();
  const auth = { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' };
  let response = await fetch('http://127.0.0.1:5710/v1/pipelines', { method: 'POST', headers: auth, body: JSON.stringify({ pipeline_id: 'pipeline-e2e-001', brand_id: 'trendybrander', goal: 'Yayın yapmadan bir içerik paketi hazırla.', risk_level: 'normal', content_id: 'content-e2e-001', content_version: 'v1' }) });
  const created = await response.json(); check('pipeline-created-with-classification', response.status === 201 && created.first_task_id.endsWith('classification'), created);
  const worker = spawn(process.execPath, ['/workspace/ui/ajans-worker/worker.mjs'], { env: { ...process.env, HOST: '127.0.0.1', PORT: '5712', RUNTIME_URL: 'http://127.0.0.1:5710', RUNTIME_API_KEY: apiKey, MODEL_WORKER_ENABLED: 'true', MODEL_ACCEPTANCE_PROOF: 'verified', MODEL_PROVIDER: 'google', MODEL_NAME: 'models/gemini-3.1-flash-lite', MODEL_BILLING_MODE: 'free_tier', MODEL_INPUT_USD_PER_MILLION: '0', MODEL_OUTPUT_USD_PER_MILLION: '0', MODEL_PRICING_VERIFIED: 'true', MODEL_ADAPTER_URL: 'http://127.0.0.1:5711/execute', MODEL_ADAPTER_TOKEN: adapterKey, OUTPUT_SCHEMAS_PATH: '/workspace/data/contracts/output-schemas.json', CONTEXT_POLICY_PATH: '/workspace/data/memory/baglam-derleme-politikasi.json', STATUS_PATH: statusPath, WORKER_INTERVAL_MS: '250', WORKER_HEARTBEAT_MS: '250' }, stdio: ['ignore','ignore','pipe'] }); children.push(worker);
  await waitFor(async () => { try { return (await fetch('http://127.0.0.1:5712/health/ready')).status === 200; } catch { return false; } }, 'worker-ready');
  await waitFor(async () => { const result = await fetch('http://127.0.0.1:5710/v1/pipelines/pipeline-e2e-001', { headers: auth }); const body = await result.json(); return body.pipeline?.status === 'awaiting_Operator_approval'; }, 'pipeline-awaiting-approval');
  response = await fetch('http://127.0.0.1:5710/v1/pipelines/pipeline-e2e-001', { headers: auth }); const final = await response.json();
  const expected = ['classification','analysis','content_ideas','visual_brief','debate_turn','ordinaryus_decision','interface_summary'];
  check('full-agent-loop-completed', JSON.stringify(final.steps.map((item) => item.task_type)) === JSON.stringify(expected) && final.steps.every((item) => item.status === 'completed'), final.steps);
  check('verified-high-confidence-ordinaryus-does-not-require-independent-audit', !final.steps.some((item) => item.task_type === 'independent_audit'), final.steps);
  const db = new DatabaseSync(dbPath, { readOnly: true });
  const counts = { outbox: db.prepare('SELECT COUNT(*) count FROM outbox_events').get().count, approvals: db.prepare('SELECT COUNT(*) count FROM approvals').get().count, attempts: db.prepare('SELECT COUNT(*) count FROM task_attempts').get().count, evidence: db.prepare('SELECT COUNT(*) count FROM verified_evidence').get().count, provenance: db.prepare('SELECT COUNT(*) count FROM agent_output_provenance').get().count }; db.close();
  check('pipeline-stops-before-approval-and-publish', counts.outbox === 0 && counts.approvals === 0, counts);
  check('all-model-calls-accounted-with-verified-test-evidence', counts.attempts === expected.length && counts.provenance === expected.length && counts.evidence === 1 && adapterCalls === expected.length, { ...counts, adapterCalls });
  response = await fetch('http://127.0.0.1:5710/v1/pipelines', { method: 'POST', headers: auth, body: JSON.stringify({ pipeline_id: 'pipeline-same-provider-001', brand_id: 'trendybrander', goal: 'Aynı sağlayıcı bağımsızlık sahtekârlığı testi.', risk_level: 'normal', content_id: 'pipeline-same-provider-content', content_version: 'v1' }) });
  check('pipeline-same-provider-001-created', response.status === 201, await response.json());
  await waitFor(async () => { const result = await fetch('http://127.0.0.1:5710/v1/pipelines/pipeline-same-provider-001', { headers: auth }); const body = await result.json(); return body.pipeline?.status === 'blocked'; }, 'pipeline-same-provider-001-blocked');
  const sameProviderResult = await (await fetch('http://127.0.0.1:5710/v1/pipelines/pipeline-same-provider-001', { headers: auth })).json();
  check('same-provider-false-independence-claim-is-blocked', sameProviderResult.pipeline.current_stage === 'independent_audit_independence_unavailable' && sameProviderResult.steps.at(-1)?.task_type === 'independent_audit' && !sameProviderResult.steps.some((item) => item.task_type === 'interface_summary'), sameProviderResult);
  for (const blocked of [{ id: 'pipeline-veto-001', stage: 'independent_audit_veto' }, { id: 'pipeline-human-001', stage: 'independent_audit_human_review' }]) {
    response = await fetch('http://127.0.0.1:5710/v1/pipelines', { method: 'POST', headers: auth, body: JSON.stringify({ pipeline_id: blocked.id, brand_id: 'trendybrander', goal: 'Denetim kararı fail-closed testi.', risk_level: 'critical', content_id: `${blocked.id}-content`, content_version: 'v1' }) });
    check(`${blocked.id}-created`, response.status === 201, await response.json());
    await waitFor(async () => { const result = await fetch(`http://127.0.0.1:5710/v1/pipelines/${blocked.id}`, { headers: auth }); const body = await result.json(); return body.pipeline?.status === 'blocked'; }, `${blocked.id}-blocked`);
    const blockedResult = await (await fetch(`http://127.0.0.1:5710/v1/pipelines/${blocked.id}`, { headers: auth })).json();
    check(`${blocked.id}-audit-gate-stops-interface`, blockedResult.pipeline.current_stage === blocked.stage && blockedResult.steps.at(-1)?.task_type === 'independent_audit' && !blockedResult.steps.some((item) => item.task_type === 'interface_summary'), blockedResult);
  }
  const report = { schema_version: '1.0', generated_at: new Date().toISOString(), status: 'PASS', tests: results.length, deterministic_adapter_only: true, model_calls: adapterCalls, external_calls: 0, publish_actions: 0, provenance: { test_file: 'tests/orchestration-pipeline.test.mjs', test_sha256: hashFile('/workspace/tests/orchestration-pipeline.test.mjs'), runtime_file: 'ui/ajans-runtime/server.mjs', runtime_sha256: hashFile('/app/server.mjs'), worker_file: 'ui/ajans-worker/worker.mjs', worker_sha256: hashFile('/workspace/ui/ajans-worker/worker.mjs') }, results };
  mkdirSync(path.dirname(reportPath), { recursive: true }); writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`); process.stdout.write(JSON.stringify({ status: 'PASS', tests: results.length, stages: expected.length, report: reportPath }));
} catch (error) {
  mkdirSync(path.dirname(reportPath), { recursive: true }); writeFileSync(reportPath, `${JSON.stringify({ schema_version: '1.0', generated_at: new Date().toISOString(), status: 'FAIL', error: error.message, results }, null, 2)}\n`); console.error(error.stack); process.exitCode = 1;
} finally {
  for (const child of children.reverse()) if (child.exitCode === null) { child.kill('SIGTERM'); await new Promise((resolve) => child.once('exit', resolve)); }
  await new Promise((resolve) => adapter.close(resolve));
}
