const $ = (id) => document.getElementById(id);
const escapeHtml = (value = '') => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
const fmtDate = (value) => value ? new Intl.DateTimeFormat('tr-TR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : '—';
const titles = { overview: 'Genel Bakış', agents: 'Ajan Stüdyosu', models: 'Model Merkezi', flow: 'Akış Tasarımcısı', policies: 'Politikalar', connections: 'Hesaplar ve API', factory: 'Uygulama Fabrikası', history: 'Sürüm Geçmişi', system: 'Sistem', guide: 'Kısa Kullanım Kılavuzu' };
const categoryNames = { agent: 'AJAN', model: 'MODEL VE YÖNLENDİRME', flow: 'AKIŞ', policy: 'POLİTİKA' };
let state = null;
let csrf = sessionStorage.getItem('ajansAdminCsrf') || '';
let activeResource = null;
let activeConnection = null;

function notify(message, type = 'success') {
  const box = $(type === 'error' ? 'error' : 'success');
  box.textContent = message; box.classList.remove('hidden');
  setTimeout(() => box.classList.add('hidden'), 5000);
}

async function api(route, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (csrf && options.method && options.method !== 'GET') headers['X-CSRF-Token'] = csrf;
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  const response = await fetch(route, { credentials: 'same-origin', cache: 'no-store', ...options, headers });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) showLogin();
    throw new Error(result.error || `İşlem başarısız (${response.status})`);
  }
  return result;
}

function showLogin() { $('loginScreen').classList.remove('hidden'); $('app').classList.add('hidden'); }
function showApp() { $('loginScreen').classList.add('hidden'); $('app').classList.remove('hidden'); }

function switchView(view) {
  document.querySelectorAll('.nav').forEach((button) => button.classList.toggle('active', button.dataset.view === view));
  document.querySelectorAll('.view').forEach((item) => item.classList.toggle('active', item.id === `view-${view}`));
  $('pageTitle').textContent = titles[view] || 'Ajans Kurucu';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function resourceCard(item) {
  const current = item.current || {};
  return `<button class="resource-card" data-resource="${item.category}:${item.key}">
    <div class="resource-top"><span class="badge ${current.status === 'active' ? 'active-badge' : ''}">${current.status === 'active' ? `Aktif v${current.version_no}` : 'Mevcut temel'}</span><span>${item.version_count} sürüm</span></div>
    <h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.description)}</p>
    <footer><span>Düzenle ve geçmişi gör</span><b>→</b></footer>
  </button>`;
}

function renderResources() {
  $('agentGrid').innerHTML = state.resources.agent.map(resourceCard).join('');
  $('modelGrid').innerHTML = state.resources.model.map(resourceCard).join('');
  $('flowGrid').innerHTML = state.resources.flow.map(resourceCard).join('');
  $('policyGrid').innerHTML = state.resources.policy.map(resourceCard).join('');
  document.querySelectorAll('[data-resource]').forEach((button) => button.addEventListener('click', () => openResource(button.dataset.resource)));
}

function renderStudioSettings() {
  const modelSettings = state.settings.model_assignments;
  $('modelAssignmentRows').innerHTML = modelSettings.roles.map((role) => `<div class="setting-row" data-model-role="${role.role_id}"><div><strong>${escapeHtml(role.name)}</strong><small>${role.mode === 'auto' ? 'Sistem uygun modeli seçer' : 'Sabit model kullanılır'}</small></div><select data-field="mode"><option value="auto" ${role.mode === 'auto' ? 'selected' : ''}>Otomatik</option><option value="manual" ${role.mode === 'manual' ? 'selected' : ''}>Manuel</option></select><input data-field="provider" placeholder="Sağlayıcı" value="${escapeHtml(role.provider || '')}" ${role.mode === 'auto' ? 'disabled' : ''}><input data-field="model" placeholder="Model adı" value="${escapeHtml(role.model || '')}" ${role.mode === 'auto' ? 'disabled' : ''}></div>`).join('');
  const flow = state.settings.flow_design;
  $('flowStageRows').innerHTML = flow.stages.map((stage) => `<label class="stage-toggle"><input type="checkbox" data-stage="${stage.id}" ${stage.enabled ? 'checked' : ''} ${stage.id === 'approval' ? 'disabled' : ''}><span>${escapeHtml(stage.name)}</span><small>${stage.id === 'approval' ? 'Zorunlu' : stage.enabled ? 'Açık' : 'Kapalı'}</small></label>`).join('');
  $('normalRounds').value = flow.normal_debate_rounds; $('criticalRounds').value = flow.critical_debate_rounds;
  document.querySelectorAll('[data-model-role] select[data-field="mode"]').forEach((select) => select.addEventListener('change', () => {
    const row = select.closest('[data-model-role]'); const manual = select.value === 'manual'; row.querySelector('[data-field="provider"]').disabled = !manual; row.querySelector('[data-field="model"]').disabled = !manual; row.querySelector('small').textContent = manual ? 'Sabit model kullanılır' : 'Sistem uygun modeli seçer';
  }));
}

async function saveModelAssignments(event) {
  event.preventDefault();
  const roles = [...document.querySelectorAll('[data-model-role]')].map((row) => ({ role_id: row.dataset.modelRole, mode: row.querySelector('[data-field="mode"]').value, provider: row.querySelector('[data-field="provider"]').value, model: row.querySelector('[data-field="model"]').value }));
  try { await api('/api/settings/model_assignments', { method: 'PUT', body: JSON.stringify({ value: { roles } }) }); notify('Model görev dağılımı kaydedildi.'); await load(); }
  catch (error) { notify(error.message === 'invalid_model_assignments' ? 'Manuel seçilen görevlerde sağlayıcı ve model adı zorunlu.' : error.message, 'error'); }
}

async function saveFlowDesign(event) {
  event.preventDefault();
  const baseline = state.settings.flow_design;
  const stages = baseline.stages.map((stage) => ({ id: stage.id, enabled: stage.id === 'approval' ? true : Boolean(document.querySelector(`[data-stage="${stage.id}"]`)?.checked) }));
  const value = { stages, normal_debate_rounds: Number($('normalRounds').value), critical_debate_rounds: Number($('criticalRounds').value) };
  try { await api('/api/settings/flow_design', { method: 'PUT', body: JSON.stringify({ value }) }); notify('Akış ayarları kaydedildi. Yayın onayı kilidi korundu.'); await load(); }
  catch (error) { notify(error.message === 'invalid_flow_design' ? 'Tur sınırlarını kontrol et. Kritik tur normal turdan düşük olamaz.' : error.message, 'error'); }
}

function renderOverview() {
  const s = state.stats;
  $('metrics').innerHTML = `
    <article><span>Ajan karakteri</span><strong>${s.agents}</strong><small>okunabilir ve sürümlü</small></article>
    <article><span>Aktif düzenleme</span><strong>${s.active_revisions}</strong><small>müşteri şablonunda</small></article>
    <article><span>Bağlantı</span><strong>${s.configured_connections}</strong><small>şifreli kasada</small></article>
    <article><span>Kullanıcı uygulaması</span><strong>${s.apps}</strong><small>oluşturulmuş</small></article>`;
  $('auditList').innerHTML = state.audit.length ? state.audit.map((item) => `<div><span class="activity-dot"></span><p><strong>${escapeHtml(item.event_type.replaceAll('_', ' '))}</strong><small>${escapeHtml(item.object_id || 'sistem')} · ${fmtDate(item.created_at)}</small></p></div>`).join('') : '<p class="empty-line">Henüz yönetici işlemi yok.</p>';
}

function renderConnections() {
  $('connectionGrid').innerHTML = state.connections.map((item) => `<article class="connection-card">
    <div class="connection-icon">${escapeHtml(item.name.slice(0, 1))}</div><div class="connection-copy"><div><h3>${escapeHtml(item.name)}</h3><span class="badge ${item.configured ? 'active-badge' : ''}">${item.configured ? 'Kaydedildi · doğrulama bekliyor' : 'Bağlı değil'}</span></div>
    <p>${item.configured ? `Son güncelleme: ${fmtDate(item.updated_at)}` : 'API veya hesap bilgilerini güvenli kasaya ekle.'}</p><button class="secondary" data-connection="${item.id}">${item.configured ? 'Bilgileri yenile' : 'Bağlantı ekle'}</button></div>
  </article>`).join('');
  document.querySelectorAll('[data-connection]').forEach((button) => button.addEventListener('click', () => openConnection(button.dataset.connection)));
}

function renderApps() {
  $('appList').innerHTML = state.apps.length ? state.apps.map((item) => `<article class="generated-app"><div class="app-symbol" style="background:${escapeHtml(item.theme?.accent || '#8b5cf6')}">${escapeHtml(item.brand_name.slice(0, 2).toUpperCase())}</div><div><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.brand_name)} · ${item.features.length} bölüm</p><span>Son üretim: ${fmtDate(item.generated_at)}</span></div><a href="/client/${encodeURIComponent(item.slug)}" target="_blank" rel="noopener">Önizle</a></article>`).join('') : '<div class="empty-state"><strong>Henüz uygulama oluşturulmadı.</strong><span>Soldaki ayarları doldurup ilk müşteri uygulamanı oluştur.</span></div>';
}

function renderHistory() {
  const all = Object.values(state.resources).flat().filter((item) => item.version_count > 0).sort((a, b) => b.version_count - a.version_count);
  $('historyList').innerHTML = all.length ? all.map((item) => `<button data-resource="${item.category}:${item.key}"><span class="badge">${categoryNames[item.category]}</span><div><strong>${escapeHtml(item.name)}</strong><small>${item.version_count} kayıtlı sürüm · ${item.current.status === 'active' ? `v${item.current.version_no} aktif` : 'temel sürüm aktif'}</small></div><b>Geçmişi aç →</b></button>`).join('') : '<div class="empty-state"><strong>Henüz yeni sürüm yok.</strong><span>Bir ajan veya kuralı düzenlediğinde burada görünecek.</span></div>';
  $('historyList').querySelectorAll('[data-resource]').forEach((button) => button.addEventListener('click', () => openResource(button.dataset.resource)));
}

function renderSystem() {
  const label = { healthy: 'Çalışıyor', warning: 'Kontrol gerekli', offline: 'Kapalı' };
  $('systemGrid').innerHTML = Object.entries(state.services).map(([name, status]) => `<article><span>${escapeHtml(name.replaceAll('_', ' '))}</span><strong class="service-${status}">${label[status] || status}</strong><small>yerel servis</small></article>`).join('') + `<article><span>Yönetim motoru</span><strong class="service-healthy">Çalışıyor</strong><small>AI çağrısı kapalı</small></article>`;
}

function render() {
  renderOverview(); renderResources(); renderStudioSettings(); renderConnections(); renderApps(); renderHistory(); renderSystem();
}

async function load() {
  try { state = await api('/api/state'); showApp(); render(); }
  catch (error) { if (error.message !== 'login_required') notify(error.message, 'error'); }
}

async function openResource(identity) {
  const [category, key] = identity.split(':');
  try {
    const result = await api(`/api/resources/${category}/${key}`); activeResource = result;
    $('editorCategory').textContent = categoryNames[category]; $('editorTitle').textContent = result.resource.name; $('editorDescription').textContent = result.resource.description;
    $('editorContent').value = result.current.content; $('editorNote').value = '';
    $('editorVersion').textContent = result.current.status === 'active' ? `Aktif v${result.current.version_no}` : 'Mevcut temel sürüm'; $('editorHash').textContent = `Özet: ${result.current.content_hash.slice(0, 12)}`;
    $('versionList').innerHTML = result.versions.length ? result.versions.map((version) => `<div><span><strong>v${version.version_no}</strong><small>${escapeHtml(version.note || 'Not yok')} · ${fmtDate(version.created_at)}</small></span><span class="badge ${version.status === 'active' ? 'active-badge' : ''}">${version.status === 'active' ? 'Aktif' : version.status === 'draft' ? 'Taslak' : 'Arşiv'}</span>${version.status === 'active' ? '' : `<button type="button" class="text-button" data-rollback="${version.version_id}">Bu sürüme dön</button>`}</div>`).join('') : '<p class="empty-line">Henüz yeni sürüm oluşturulmadı.</p>';
    $('versionList').querySelectorAll('[data-rollback]').forEach((button) => button.addEventListener('click', () => rollbackVersion(button.dataset.rollback)));
    $('editorDialog').showModal();
  } catch (error) { notify(error.message, 'error'); }
}

async function saveResource(activate) {
  if (!activeResource) return;
  const { category, key } = activeResource.resource;
  try {
    await api(`/api/resources/${category}/${key}`, { method: 'PUT', body: JSON.stringify({ content: $('editorContent').value, note: $('editorNote').value, activate }) });
    notify(activate ? 'Yeni sürüm aktif şablon yapıldı.' : 'Taslak sürüm kaydedildi.'); $('editorDialog').close(); await load();
  } catch (error) { notify(error.message === 'invalid_json' ? 'JSON yapısı geçerli değil; kaydedilmedi.' : error.message, 'error'); }
}

async function rollbackVersion(versionId) {
  if (!activeResource || !confirm('Seçilen sürümün yeni bir kopyası aktif şablon yapılsın mı?')) return;
  const { category, key } = activeResource.resource;
  try { await api(`/api/resources/${category}/${key}/rollback`, { method: 'POST', body: JSON.stringify({ version_id: versionId }) }); notify('Önceki sürüme güvenli dönüş yapıldı.'); $('editorDialog').close(); await load(); }
  catch (error) { notify(error.message, 'error'); }
}

function openConnection(providerId) {
  activeConnection = state.connections.find((item) => item.id === providerId);
  if (!activeConnection) return;
  $('connectionTitle').textContent = activeConnection.name; $('connectionLabel').value = activeConnection.label || activeConnection.name;
  $('connectionFields').innerHTML = activeConnection.fields.map((field) => `<label>${escapeHtml(field.replaceAll('_', ' '))}<input data-secret-field="${field}" type="${field.includes('secret') || field.includes('key') || field.includes('token') ? 'password' : 'text'}" autocomplete="off" required></label>`).join('');
  $('connectionDialog').showModal();
}

async function saveConnection(event) {
  event.preventDefault(); if (!activeConnection) return;
  const secret = Object.fromEntries([...document.querySelectorAll('[data-secret-field]')].map((input) => [input.dataset.secretField, input.value.trim()]));
  try { await api(`/api/connections/${activeConnection.id}`, { method: 'PUT', body: JSON.stringify({ label: $('connectionLabel').value, secret, metadata: {} }) }); $('connectionDialog').close(); notify('Bağlantı bilgileri şifreli kasaya kaydedildi. Henüz dış servise bağlanılmadı.'); await load(); }
  catch (error) { notify(error.message, 'error'); }
}

async function createApp(event) {
  event.preventDefault(); const form = new FormData(event.currentTarget); const features = form.getAll('features');
  const payload = { name: form.get('name'), slug: form.get('slug'), brand_name: form.get('brand_name'), description: form.get('description'), accent: form.get('accent'), features };
  try { const result = await api('/api/apps', { method: 'POST', body: JSON.stringify(payload) }); notify('Kullanıcı uygulaması oluşturuldu.'); await load(); window.open(result.preview_url, '_blank', 'noopener'); }
  catch (error) { notify(error.message, 'error'); }
}

$('loginForm').addEventListener('submit', async (event) => {
  event.preventDefault(); $('loginMessage').textContent = '';
  try { const result = await api('/api/login', { method: 'POST', body: JSON.stringify({ password: $('password').value }) }); csrf = result.csrf_token; sessionStorage.setItem('ajansAdminCsrf', csrf); $('password').value = ''; await load(); }
  catch (error) { $('loginMessage').textContent = error.message === 'invalid_password' ? 'Parola doğru değil.' : error.message; }
});
$('logout').addEventListener('click', async () => { try { await api('/api/logout', { method: 'POST', body: '{}' }); } catch {} csrf = ''; sessionStorage.removeItem('ajansAdminCsrf'); showLogin(); });
$('refresh').addEventListener('click', load);
$('nav').addEventListener('click', (event) => { const button = event.target.closest('[data-view]'); if (button) switchView(button.dataset.view); });
document.addEventListener('click', (event) => { const button = event.target.closest('[data-go]'); if (button) switchView(button.dataset.go); });
$('saveDraft').addEventListener('click', () => saveResource(false)); $('activateVersion').addEventListener('click', () => saveResource(true));
$('connectionForm').addEventListener('submit', saveConnection); $('closeConnection').addEventListener('click', () => $('connectionDialog').close());
$('factoryForm').addEventListener('submit', createApp);
$('modelAssignmentForm').addEventListener('submit', saveModelAssignments); $('flowDesignForm').addEventListener('submit', saveFlowDesign);
load();
