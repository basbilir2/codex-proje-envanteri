import { createServer } from 'node:http';
import { readFile, readdir, stat } from 'node:fs/promises';
import path from 'node:path';

const port = Number(process.env.PORT || 5680);
const host = process.env.HOST || '0.0.0.0';
const appRoot = path.resolve(process.env.APP_ROOT || '/app');
const dataRoot = path.resolve(process.env.DATA_ROOT || '/data');
const referenceRoot = path.resolve(process.env.REFERENCE_ROOT || '/references');
const publicRoot = path.join(appRoot, 'public');
const generatedRoot = path.join(dataRoot, 'outputs', 'images');
const runtimeUrl = process.env.RUNTIME_URL || 'http://ajans-runtime:5681';
const runtimeApiKey = process.env.RUNTIME_API_KEY || '';

const json = async (file, fallback) => {
  try {
    return JSON.parse(await readFile(file, 'utf8'));
  } catch {
    return fallback;
  }
};

const text = async (file, fallback = '') => {
  try {
    return await readFile(file, 'utf8');
  } catch {
    return fallback;
  }
};

const imageTypes = new Set(['.png', '.jpg', '.jpeg', '.webp', '.gif']);
const listImages = async (folder, routePrefix) => {
  try {
    const entries = await readdir(folder, { withFileTypes: true });
    const results = [];
    for (const entry of entries) {
      if (!entry.isFile() || !imageTypes.has(path.extname(entry.name).toLowerCase())) continue;
      const info = await stat(path.join(folder, entry.name));
      results.push({
        name: entry.name,
        url: `${routePrefix}/${encodeURIComponent(entry.name)}`,
        size_bytes: info.size,
        modified_at: info.mtime.toISOString()
      });
    }
    return results.sort((a, b) => b.modified_at.localeCompare(a.modified_at));
  } catch {
    return [];
  }
};

const n8nHealth = async () => {
  try {
    const response = await fetch('http://n8n:5678/healthz', { signal: AbortSignal.timeout(2500) });
    return { status: response.ok ? 'healthy' : 'unhealthy', http_status: response.status };
  } catch {
    return { status: 'unreachable', http_status: null };
  }
};

const runtimeJson = async (route, authorized = false) => {
  try {
    const response = await fetch(`${runtimeUrl}${route}`, {
      headers: authorized ? { Authorization: `Bearer ${runtimeApiKey}` } : {},
      signal: AbortSignal.timeout(2500)
    });
    return { http_status: response.status, ...(await response.json()) };
  } catch {
    return { status: 'unreachable', http_status: null };
  }
};

const buildDashboard = async () => {
  const [
    analysis,
    content,
    conversations,
    sessions,
    performance,
    approvals,
    decisions,
    errors,
    activeContext,
    contextPack,
    modelRouting,
    generatedImages,
    referenceImages,
    guardianStatus,
    health,
    runtimeHealth,
    runtimeMetrics
  ] = await Promise.all([
    text(path.join(dataRoot, 'logs', 'analizci-son-cikti.txt')),
    json(path.join(dataRoot, 'logs', 'icerik-stratejisti-son-cikti.json'), null),
    json(path.join(dataRoot, 'logs', 'ajan-konusmalari.json'), { conversations: [], debates: [] }),
    json(path.join(dataRoot, 'logs', 'ajans-oturum-log.json'), { records: [] }),
    json(path.join(dataRoot, 'logs', 'model-performans-kaydi.json'), { records: [] }),
    json(path.join(dataRoot, 'approvals', 'onay-bekleyen.json'), { items: [] }),
    json(path.join(dataRoot, 'approvals', 'onay-kayitlari.json'), { records: [] }),
    json(path.join(dataRoot, 'logs', 'hata-kaydi.json'), { records: [] }),
    json(path.join(dataRoot, 'memory', 'aktif-baglam.json'), null),
    json(path.join(dataRoot, 'runtime', 'context-packs', 'gorsel-stratejist-current.json'), null),
    json(path.join(dataRoot, 'memory', 'model-yonlendirme.json'), null),
    listImages(generatedRoot, '/media/generated'),
    listImages(referenceRoot, '/media/reference'),
    json(path.join(dataRoot, 'health', 'current.json'), { overall: 'starting', services: {} }),
    n8nHealth(),
    runtimeJson('/health/ready'),
    runtimeJson('/v1/metrics', true)
  ]);

  const tokenRecords = Array.isArray(performance.records) ? performance.records : [];
  const tokenTotals = tokenRecords.reduce(
    (sum, item) => {
      sum.input += Number(item.input_tokens || 0);
      sum.output += Number(item.output_tokens || 0);
      sum.total += Number(item.input_tokens || 0) + Number(item.output_tokens || 0);
      sum.calls += 1;
      return sum;
    },
    { input: 0, output: 0, total: 0, calls: 0 }
  );

  return {
    generated_at: new Date().toISOString(),
    brand: { id: 'trendybrander', name: 'TrendyBrander' },
    system: {
      read_only_dashboard: true,
      write_exception: 'Only authenticated, CSRF-protected, server-signed approval decisions are accepted.',
      n8n: health,
      runtime: runtimeHealth,
      runtime_metrics: runtimeMetrics,
      guardian: guardianStatus,
      publish_adapter_enabled: false,
      final_publish_requires_Operator: true,
      active_state: activeContext?.state || 'unknown',
      active_agent: activeContext?.current_task?.agent_id || null,
      current_task: activeContext?.current_task || null,
      errors: Array.isArray(errors.records) ? errors.records.length : 0
    },
    context_efficiency: {
      mode: activeContext?.mode || 'unknown',
      full_agent_prompt_sent: contextPack?.agent?.full_prompt_sent ?? null,
      estimated_input_tokens: contextPack?.telemetry?.estimated_input_tokens ?? null,
      max_input_tokens: contextPack?.telemetry?.max_input_tokens ?? null,
      remaining_input_tokens: contextPack?.telemetry?.remaining_input_tokens ?? null,
      policy_active: modelRouting?.status === 'active_compact_context_policy'
    },
    conversations: conversations.conversations || [],
    debates: conversations.debates || [],
    sessions: sessions.records || [],
    outputs: {
      analysis: analysis
        ? {
            id: 'analizci-son-cikti',
            title: 'Analizci Raporu',
            type: 'analysis',
            status: 'completed',
            content: analysis
          }
        : null,
      content
    },
    visuals: {
      generated: generatedImages,
      briefs: content?.ideas || [],
      references: referenceImages
    },
    tokens: {
      totals: tokenTotals,
      records: tokenRecords
    },
    approvals: {
      waiting: approvals.items || [],
      decisions: decisions.records || []
    }
  };
};

const mimeTypes = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.gif': 'image/gif'
};

const send = (res, status, body, type, cache = 'no-store') => {
  res.writeHead(status, {
    'Content-Type': type,
    'Cache-Control': cache,
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
    'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
  });
  res.end(body);
};

const safeMediaPath = (root, encodedName) => {
  const name = path.basename(decodeURIComponent(encodedName));
  if (!imageTypes.has(path.extname(name).toLowerCase())) return null;
  const resolved = path.resolve(root, name);
  return resolved.startsWith(`${root}${path.sep}`) ? resolved : null;
};

const readRequestBody = (req) => new Promise((resolve, reject) => {
  const chunks = [];
  let size = 0;
  req.on('data', (chunk) => {
    size += chunk.length;
    if (size > 1024 * 1024) {
      reject(new Error('body_too_large'));
      req.destroy();
      return;
    }
    chunks.push(chunk);
  });
  req.on('end', () => resolve(Buffer.concat(chunks)));
  req.on('error', reject);
});

const proxyRuntime = async (req, res, route) => {
  try {
    const body = req.method === 'GET' ? undefined : await readRequestBody(req);
    const headers = { 'Content-Type': 'application/json' };
    if (req.headers.cookie) headers.Cookie = req.headers.cookie;
    if (req.headers['x-csrf-token']) headers['X-CSRF-Token'] = req.headers['x-csrf-token'];
    const upstream = await fetch(`${runtimeUrl}${route}`, { method: req.method, headers, body, signal: AbortSignal.timeout(5000) });
    const responseHeaders = {};
    const cookie = upstream.headers.get('set-cookie');
    if (cookie) responseHeaders['Set-Cookie'] = cookie;
    res.writeHead(upstream.status, {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'Referrer-Policy': 'no-referrer',
      ...responseHeaders
    });
    res.end(Buffer.from(await upstream.arrayBuffer()));
  } catch {
    send(res, 502, JSON.stringify({ error: 'runtime_unreachable' }), mimeTypes['.json']);
  }
};

const server = createServer(async (req, res) => {
  const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);

  const operatorRoutes = new Map([
    ['/api/operator/login', '/v1/operator/login'],
    ['/api/operator/logout', '/v1/operator/logout'],
    ['/api/approvals/waiting', '/v1/approvals/waiting']
  ]);
  if (operatorRoutes.has(url.pathname) && ['GET', 'POST'].includes(req.method)) {
    await proxyRuntime(req, res, operatorRoutes.get(url.pathname));
    return;
  }
  const decisionRoute = url.pathname.match(/^\/api\/approvals\/([^/]+)\/decision$/);
  if (decisionRoute && req.method === 'POST') {
    await proxyRuntime(req, res, `/v1/approvals/${encodeURIComponent(decisionRoute[1])}/decision`);
    return;
  }

  if (req.method !== 'GET') {
    send(res, 405, JSON.stringify({ error: 'unsupported_method' }), mimeTypes['.json']);
    return;
  }

  if (url.pathname === '/api/health') {
    send(res, 200, JSON.stringify({ status: 'ok', read_only: true }), mimeTypes['.json']);
    return;
  }

  if (url.pathname === '/api/dashboard') {
    try {
      send(res, 200, JSON.stringify(await buildDashboard()), mimeTypes['.json']);
    } catch (error) {
      send(res, 500, JSON.stringify({ error: 'dashboard_build_failed', detail: error.message }), mimeTypes['.json']);
    }
    return;
  }

  const mediaMatch = url.pathname.match(/^\/media\/(generated|reference)\/(.+)$/);
  if (mediaMatch) {
    const root = mediaMatch[1] === 'generated' ? generatedRoot : referenceRoot;
    const file = safeMediaPath(root, mediaMatch[2]);
    if (!file) {
      send(res, 404, 'Bulunamadı', 'text/plain; charset=utf-8');
      return;
    }
    try {
      const body = await readFile(file);
      send(res, 200, body, mimeTypes[path.extname(file).toLowerCase()], 'public, max-age=300');
    } catch {
      send(res, 404, 'Bulunamadı', 'text/plain; charset=utf-8');
    }
    return;
  }

  const requested = url.pathname === '/' ? 'index.html' : url.pathname.slice(1);
  const safe = path.normalize(requested).replace(/^(\.\.(\/|\\|$))+/, '');
  const file = path.resolve(publicRoot, safe);
  if (!file.startsWith(`${publicRoot}${path.sep}`) && file !== path.join(publicRoot, 'index.html')) {
    send(res, 403, 'Erişim reddedildi', 'text/plain; charset=utf-8');
    return;
  }

  try {
    const body = await readFile(file);
    send(res, 200, body, mimeTypes[path.extname(file).toLowerCase()] || 'application/octet-stream', 'no-cache');
  } catch {
    send(res, 404, 'Bulunamadı', 'text/plain; charset=utf-8');
  }
});

server.listen(port, host, () => {
  process.stdout.write(`Ajans Merkezi http://${host}:${port}\n`);
});
