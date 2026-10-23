const $ = (id) => document.getElementById(id);
const escapeHtml = (value = '') => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
const fmtDate = (value) => value ? new Intl.DateTimeFormat('tr-TR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : '—';
const titles = { overview: 'Genel Bakış', agents: 'Rol Stüdyosu', models: 'Model ve Token Merkezi', flow: 'Akış Tasarımcısı', policies: 'Politikalar', factory: 'Uygulama Fabrikası', portfolio: 'Önceki Uygulamalarım', portable: 'Taşıma ve Kurulum', history: 'Sürüm Geçmişi', system: 'Sistem', guide: 'Kısa Kullanım Kılavuzu' };
const categoryNames = { agent: 'ROL', model: 'MODEL VE YÖNLENDİRME', flow: 'AKIŞ', policy: 'POLİTİKA' };
let state = null;
let csrf = sessionStorage.getItem('ajansAdminCsrf') || '';
let activeResource = null;
let activeAgent = null;
let activeFlowIndex = 0;

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

function renderAgentLibrary() {
  const agents = state.agent_library || [];
  $('agentLibrary').innerHTML = agents.length ? agents.map((agent) => `<article class="agent-card ${agent.enabled ? '' : 'agent-disabled'}">
    <div class="agent-card-head"><span class="badge ${agent.enabled ? 'active-badge' : ''}">${agent.enabled ? 'Açık' : 'Kapalı'}</span><span>Sıra ${agent.sort_order}</span></div>
    <h3>${escapeHtml(agent.name)}</h3><p>${escapeHtml(agent.role)}</p>
    <div class="agent-card-meta"><span>${agent.token_profile === 'low' ? 'Az' : agent.token_profile === 'high' ? 'Yüksek' : agent.token_profile === 'custom' ? 'Özel' : 'Orta'} · ${agent.token_limit.toLocaleString('tr-TR')} token</span><span>${agent.model_mode === 'auto' ? 'Otomatik model' : escapeHtml(agent.model)}</span></div>
    <footer><button class="secondary" data-edit-agent="${agent.agent_id}">Düzenle</button><button class="secondary" data-clone-agent="${agent.agent_id}">Kopyala</button></footer>
  </article>`).join('') : '<div class="empty-state"><strong>Henüz rol yok.</strong><span>İlk rolünü oluştur.</span></div>';
  document.querySelectorAll('[data-edit-agent]').forEach((button) => button.addEventListener('click', () => openAgent(button.dataset.editAgent)));
  document.querySelectorAll('[data-clone-agent]').forEach((button) => button.addEventListener('click', () => cloneAgent(button.dataset.cloneAgent)));
}

function openAgent(agentId = '') {
  activeAgent = (state.agent_library || []).find((agent) => agent.agent_id === agentId) || null;
  $('agentDialogTitle').textContent = activeAgent ? activeAgent.name : 'Yeni rol';
  $('agentId').value = activeAgent?.agent_id || ''; $('agentName').value = activeAgent?.name || ''; $('agentSlug').value = activeAgent?.slug || '';
  $('agentOrder').value = activeAgent?.sort_order ?? (state.agent_library?.length || 0) + 1; $('agentRole').value = activeAgent?.role || ''; $('agentInstructions').value = activeAgent?.instructions || '';
  $('agentEnabled').checked = activeAgent?.enabled ?? true; $('agentTokenProfile').value = activeAgent?.token_profile || 'medium'; $('agentTokenLimit').value = activeAgent?.token_limit || 1800;
  $('agentModelMode').value = activeAgent?.model_mode || 'auto'; $('agentProvider').value = activeAgent?.provider || ''; $('agentModel').value = activeAgent?.model || ''; toggleAgentModelFields(); $('agentDialog').showModal();
}

function toggleAgentModelFields() { const manual = $('agentModelMode').value === 'manual'; $('agentProvider').disabled = !manual; $('agentModel').disabled = !manual; }

async function saveAgent(event) {
  event.preventDefault();
  const payload = { name: $('agentName').value, slug: $('agentSlug').value, sort_order: Number($('agentOrder').value), role: $('agentRole').value, instructions: $('agentInstructions').value, enabled: $('agentEnabled').checked, token_profile: $('agentTokenProfile').value, token_limit: Number($('agentTokenLimit').value), model_mode: $('agentModelMode').value, provider: $('agentProvider').value, model: $('agentModel').value };
  try { await api(activeAgent ? `/api/agents/${activeAgent.agent_id}` : '/api/agents', { method: activeAgent ? 'PUT' : 'POST', body: JSON.stringify(payload) }); $('agentDialog').close(); notify(activeAgent ? 'Rol güncellendi.' : 'Yeni rol oluşturuldu.'); await load(); }
  catch (error) { const messages = { invalid_agent_definition: 'Rol bilgilerini ve token sınırını kontrol et.', manual_model_required: 'Sabit model için sağlayıcı ve model adı gerekir.', invalid_agent_slug: 'Kısa ad küçük harf, rakam ve tireden oluşmalı.' }; notify(messages[error.message] || error.message, 'error'); }
}

async function cloneAgent(agentId) { try { await api(`/api/agents/${agentId}/clone`, { method: 'POST', body: '{}' }); notify('Rol kapalı bir kopya olarak oluşturuldu.'); await load(); } catch (error) { notify(error.message, 'error'); } }

function renderStudioSettings() {
  const modelSettings = state.settings.model_assignments;
  $('modelAssignmentRows').innerHTML = modelSettings.roles.map((role) => `<div class="setting-row" data-model-role="${role.role_id}"><div><strong>${escapeHtml(role.name)}</strong><small>${role.mode === 'auto' ? 'Sistem uygun modeli seçer' : 'Sabit model kullanılır'}</small></div><select data-field="mode"><option value="auto" ${role.mode === 'auto' ? 'selected' : ''}>Otomatik</option><option value="manual" ${role.mode === 'manual' ? 'selected' : ''}>Manuel</option></select><input data-field="provider" placeholder="Sağlayıcı" value="${escapeHtml(role.provider || '')}" ${role.mode === 'auto' ? 'disabled' : ''}><input data-field="model" placeholder="Model adı" value="${escapeHtml(role.model || '')}" ${role.mode === 'auto' ? 'disabled' : ''}></div>`).join('');
  const flow = state.settings.flow_design;
  $('flowStageRows').innerHTML = flow.stages.map((stage) => `<label class="stage-toggle"><input type="checkbox" data-stage="${stage.id}" ${stage.enabled ? 'checked' : ''} ${stage.id === 'approval' ? 'disabled' : ''}><span>${escapeHtml(stage.name)}</span><small>${stage.id === 'approval' ? 'Zorunlu' : stage.enabled ? 'Açık' : 'Kapalı'}</small></label>`).join('');
  $('normalRounds').value = flow.normal_debate_rounds; $('criticalRounds').value = flow.critical_debate_rounds;
  document.querySelectorAll('[data-model-role] select[data-field="mode"]').forEach((select) => select.addEventListener('change', () => {
    const row = select.closest('[data-model-role]'); const manual = select.value === 'manual'; row.querySelector('[data-field="provider"]').disabled = !manual; row.querySelector('[data-field="model"]').disabled = !manual; row.querySelector('small').textContent = manual ? 'Sabit model kullanılır' : 'Sistem uygun modeli seçer';
  }));
  const token = state.settings.token_policy;
  $('defaultTokenProfile').value = token.default_profile; $('perTaskTokenLimit').value = token.per_task_limit; $('dailyTokenLimit').value = token.daily_limit; $('monthlyTokenLimit').value = token.monthly_limit; $('maxCallsPerTask').value = token.maximum_calls_per_task; $('maximumRetries').value = token.maximum_retries;
  renderFlowBlueprints(); renderPlanFields(); renderAppAgentNames();
}

async function saveTokenPolicy(event) {
  event.preventDefault(); const value = { default_profile: $('defaultTokenProfile').value, per_task_limit: Number($('perTaskTokenLimit').value), daily_limit: Number($('dailyTokenLimit').value), monthly_limit: Number($('monthlyTokenLimit').value), maximum_calls_per_task: Number($('maxCallsPerTask').value), maximum_retries: Number($('maximumRetries').value) };
  try { await api('/api/settings/token_policy', { method: 'PUT', body: JSON.stringify({ value }) }); notify('Token sınırları kaydedildi.'); await load(); } catch (error) { notify(error.message === 'invalid_token_policy' ? 'Token sınırlarını kontrol et; günlük sınır görevden, aylık sınır günlükten düşük olamaz.' : error.message, 'error'); }
}

function renderFlowBlueprints() {
  const settings = state.settings.flow_blueprints; const flows = settings.flows || [];
  activeFlowIndex = Math.min(activeFlowIndex, Math.max(0, flows.length - 1));
  $('flowBlueprintSelect').innerHTML = flows.map((flow, index) => `<option value="${index}" ${index === activeFlowIndex ? 'selected' : ''}>${escapeHtml(flow.name)}</option>`).join('');
  const flow = flows[activeFlowIndex]; if (!flow) return;
  $('flowBlueprintName').value = flow.name; $('flowAlgorithm').value = flow.algorithm; $('blueprintNormalRounds').value = flow.normal_rounds; $('blueprintCriticalRounds').value = flow.critical_rounds;
  const selected = new Set(flow.agent_slugs || []); const ordered = [...(flow.agent_slugs || []).map((slug) => state.agent_library.find((agent) => agent.slug === slug)).filter(Boolean), ...state.agent_library.filter((agent) => !selected.has(agent.slug))];
  $('flowAgentOrder').innerHTML = ordered.map((agent, index) => `<div class="flow-agent-row" data-flow-agent="${escapeHtml(agent.slug)}"><input type="checkbox" ${selected.has(agent.slug) ? 'checked' : ''}><span><strong>${escapeHtml(agent.name)}</strong><small>${agent.enabled ? 'Rol açık' : 'Rol kapalı'}</small></span><button type="button" class="text-button" data-move="up" ${index === 0 ? 'disabled' : ''}>Yukarı</button><button type="button" class="text-button" data-move="down" ${index === ordered.length - 1 ? 'disabled' : ''}>Aşağı</button></div>`).join('');
  $('flowAgentOrder').querySelectorAll('[data-move]').forEach((button) => button.addEventListener('click', () => { const row = button.closest('[data-flow-agent]'); const sibling = button.dataset.move === 'up' ? row.previousElementSibling : row.nextElementSibling; if (sibling) row.parentElement.insertBefore(button.dataset.move === 'up' ? row : sibling, button.dataset.move === 'up' ? sibling : row); }));
}

async function saveFlowBlueprints(event) {
  event.preventDefault(); const settings = structuredClone(state.settings.flow_blueprints); const current = settings.flows[activeFlowIndex];
  current.name = $('flowBlueprintName').value.trim(); current.algorithm = $('flowAlgorithm').value; current.normal_rounds = Number($('blueprintNormalRounds').value); current.critical_rounds = Number($('blueprintCriticalRounds').value); current.agent_slugs = [...document.querySelectorAll('[data-flow-agent]')].filter((row) => row.querySelector('input').checked).map((row) => row.dataset.flowAgent); settings.active_flow_id = current.flow_id;
  try { await api('/api/settings/flow_blueprints', { method: 'PUT', body: JSON.stringify({ value: settings }) }); notify('Çalışma düzeni kaydedildi.'); await load(); } catch (error) { notify(error.message === 'invalid_flow_blueprints' ? 'Akışta en az bir rol olmalı ve tur sınırları geçerli olmalı.' : error.message, 'error'); }
}

function newFlowBlueprint() {
  const settings = state.settings.flow_blueprints; const stamp = Date.now().toString(36); settings.flows.push({ flow_id: `duzen-${stamp}`, name: 'Yeni çalışma düzeni', enabled: true, algorithm: 'sequential_debate', agent_slugs: state.agent_library.filter((agent) => agent.enabled).map((agent) => agent.slug), normal_rounds: 3, critical_rounds: 4 }); activeFlowIndex = settings.flows.length - 1; renderFlowBlueprints();
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
    <article><span>Toplam rol</span><strong>${s.agents}</strong><small>${s.enabled_agents} rol açık</small></article>
    <article><span>Aktif düzenleme</span><strong>${s.active_revisions}</strong><small>müşteri şablonunda</small></article>
    <article><span>Çalışma modu</span><strong>Yerel</strong><small>API ve internet gerekmez</small></article>
    <article><span>Kullanıcı uygulaması</span><strong>${s.apps}</strong><small>oluşturulmuş</small></article>`;
  $('auditList').innerHTML = state.audit.length ? state.audit.map((item) => `<div><span class="activity-dot"></span><p><strong>${escapeHtml(item.event_type.replaceAll('_', ' '))}</strong><small>${escapeHtml(item.object_id || 'sistem')} · ${fmtDate(item.created_at)}</small></p></div>`).join('') : '<p class="empty-line">Henüz yönetici işlemi yok.</p>';
}

function renderPlanFields(force = false) {
  const planId = $('planId').value || 'basic'; const plan = state.settings.plan_templates[planId]; if (!plan) return;
  if (force || !$('editingAppId').value) { $('planAgentLimit').value = plan.max_enabled_agents; $('planTokenLimit').value = plan.monthly_token_limit; $('planDebateRounds').value = plan.debate_rounds; $('apiControlMode').value = plan.api_control_default || 'locked'; }
  $('planDescription').textContent = `${plan.name}: model seçimi ${plan.model_selection}, özel akış ${plan.custom_flows ? 'açık' : 'kapalı'}, gelişmiş hafıza ${plan.advanced_memory ? 'açık' : 'kapalı'}. Değerleri bu uygulama için değiştirebilirsin.`;
  renderAppAgentNames(); toggleApiControlFields();
}

function toggleApiControlFields() {
  const locked = $('apiControlMode').value === 'locked';
  $('allowedProviders').disabled = locked;
  $('allowedProviders').closest('label').classList.toggle('muted-field', locked);
}

function toggleChatFields() {
  const enabled = $('chatEnabled').checked; const fixed = enabled && $('chatModelMode').value === 'fixed';
  $('chatSettings').classList.toggle('disabled-settings', !enabled);
  $('chatModelMode').disabled = !enabled; $('chatTokenLimit').disabled = !enabled;
  $('chatProvider').disabled = !fixed; $('chatModel').disabled = !fixed;
  $('chatContentRevision').disabled = !enabled; $('chatVisualRevision').disabled = !enabled;
}

function renderAppAgentNames(overrides = {}) {
  const limit = Number($('planAgentLimit').value || 1); const enabled = (state.agent_library || []).filter((agent) => agent.enabled).sort((a, b) => a.sort_order - b.sort_order); const coreSlugs = new Set((state.resources?.agent || []).map((item) => item.key)); const core = enabled.filter((agent) => coreSlugs.has(agent.slug)); const custom = enabled.filter((agent) => !coreSlugs.has(agent.slug)); const agents = [...core, ...custom.slice(0, Math.max(0, limit - core.length))].sort((a, b) => a.sort_order - b.sort_order);
  const existing = Object.fromEntries([...document.querySelectorAll('[data-app-agent-name]')].map((input) => [input.dataset.appAgentName, input.value]));
  $('appAgentNames').innerHTML = agents.map((agent) => `<label><span>${escapeHtml(agent.name)}</span><input data-app-agent-name="${escapeHtml(agent.slug)}" value="${escapeHtml(overrides[agent.slug] || existing[agent.slug] || agent.name)}" maxlength="120"></label>`).join('') || '<p class="empty-line">Önce en az bir rolü aç.</p>';
}

function resetFactory() {
  $('factoryForm').reset(); $('editingAppId').value = ''; $('factoryFormTitle').textContent = 'Yeni uygulama'; $('factorySubmit').textContent = 'Uygulamayı oluştur'; $('resetFactory').classList.add('hidden'); $('factoryForm').elements.slug.disabled = false; $('planId').value = 'basic'; renderPlanFields(true); renderAppAgentNames(); toggleChatFields();
}

function editApp(appId) {
  const app = state.apps.find((item) => item.app_id === appId); if (!app) return;
  const form = $('factoryForm'); $('editingAppId').value = app.app_id; form.elements.name.value = app.name; form.elements.slug.value = app.slug; form.elements.slug.disabled = true; form.elements.brand_name.value = app.brand_name; form.elements.description.value = app.description || ''; form.elements.accent.value = app.theme?.accent || '#8b5cf6';
  form.querySelectorAll('input[name="features"]').forEach((input) => { input.checked = app.features.includes(input.value); }); $('planId').value = app.plan?.id || 'basic'; $('planAgentLimit').value = app.plan?.limits?.max_enabled_agents || 11; $('planTokenLimit').value = app.plan?.limits?.monthly_token_limit || 300000; $('planDebateRounds').value = app.plan?.limits?.debate_rounds ?? 1;
  const modeCatalog = Object.fromEntries((app.operating_modes?.catalog || []).map((mode) => [mode.id, mode])); $('modeAutonomous').checked = modeCatalog.autonomous?.visible !== false; $('modeGuidedAuto').checked = modeCatalog.guided_auto?.visible !== false; $('modeManual').checked = modeCatalog.manual?.visible !== false; $('modeAutonomousMinPlan').value = modeCatalog.autonomous?.minimum_plan || 'pro'; $('modeGuidedAutoMinPlan').value = modeCatalog.guided_auto?.minimum_plan || 'basic'; $('modeManualMinPlan').value = modeCatalog.manual?.minimum_plan || 'basic'; $('defaultOperatingMode').value = app.operating_modes?.default || 'guided_auto';
  const policy = app.connection_policy || {}; $('apiControlMode').value = policy.api_control_mode || 'locked'; $('allowedProviders').value = (policy.allowed_providers || []).join(', '); $('textProvider').value = policy.defaults?.text?.provider || 'google_gemini'; $('textModel').value = policy.defaults?.text?.model || 'auto'; $('visualProvider').value = policy.defaults?.visual?.provider || 'openai'; $('visualModel').value = policy.defaults?.visual?.model || 'auto'; $('credentialReentryAllowed').checked = policy.credential_reentry_allowed === true; $('metaReconnectAllowed').checked = policy.meta?.reconnect_or_account_change_allowed === true;
  const chat = app.assistant_chat || {}; $('chatEnabled').checked = chat.enabled === true; $('chatModelMode').value = chat.model?.mode || 'inherit'; $('chatProvider').value = chat.model?.provider || ''; $('chatModel').value = chat.model?.model || ''; $('chatTokenLimit').value = chat.maximum_tokens_per_message || 1200; $('chatContentRevision').checked = chat.permissions?.request_content_revision !== false; $('chatVisualRevision').checked = chat.permissions?.request_visual_revision !== false;
  $('factoryFormTitle').textContent = `${app.name} güncelleniyor`; $('factorySubmit').textContent = 'Yeni sürümü oluştur'; $('resetFactory').classList.remove('hidden'); renderPlanFields(false); toggleApiControlFields(); toggleChatFields(); renderAppAgentNames(Object.fromEntries((app.agent_names || []).map((agent) => [agent.slug, agent.name]))); switchView('factory');
}

function renderApps() {
  $('appList').innerHTML = state.apps.length ? state.apps.map((item) => `<article class="generated-app portfolio-app"><div class="app-symbol" style="background:${escapeHtml(item.theme?.accent || '#8b5cf6')}">${escapeHtml(item.brand_name.slice(0, 2).toUpperCase())}</div><div><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.brand_name)} · ${escapeHtml(item.plan?.name || 'Basic')} · v${item.generation_no}</p><span>${item.agent_names?.length || 0} rol · Son güncelleme: ${fmtDate(item.generated_at)}</span></div><div class="app-actions"><button class="secondary" data-edit-app="${item.app_id}">Düzenle</button><a href="/client/${encodeURIComponent(item.slug)}" target="_blank" rel="noopener">Önizle</a><button class="secondary" data-package-app="${item.app_id}">Kurulum paketi</button></div></article>`).join('') : '<div class="empty-state"><strong>Henüz uygulama oluşturulmadı.</strong><span>Uygulama Fabrikası’ndan ilk yaşayan ajansını oluştur.</span></div>';
  document.querySelectorAll('[data-edit-app]').forEach((button) => button.addEventListener('click', () => editApp(button.dataset.editApp)));
  document.querySelectorAll('[data-package-app]').forEach((button) => button.addEventListener('click', () => downloadAppPackage(button.dataset.packageApp)));
}

async function downloadAppPackage(appId) {
  try {
    const response = await fetch(`/api/apps/${encodeURIComponent(appId)}/package`, { credentials: 'same-origin', cache: 'no-store' });
    if (!response.ok) throw new Error((await response.json().catch(() => ({}))).error || 'Paket hazırlanamadı.');
    const disposition = response.headers.get('content-disposition') || ''; const match = disposition.match(/filename="([^"]+)"/i);
    const blob = await response.blob(); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = match?.[1] || 'yasayan-ajans.ajansapp'; document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(link.href); notify('Kurulum paketi indirildi. Paket şifre veya API anahtarı içermez.');
  } catch (error) { notify(error.message, 'error'); }
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
  renderOverview(); renderResources(); renderAgentLibrary(); renderStudioSettings(); renderApps(); renderHistory(); renderSystem(); renderPlanFields(false); toggleChatFields();
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

async function createApp(event) {
  event.preventDefault(); const form = new FormData(event.currentTarget); const features = form.getAll('features');
  const agentNames = Object.fromEntries([...document.querySelectorAll('[data-app-agent-name]')].map((input) => [input.dataset.appAgentName, input.value.trim()]));
  const payload = { name: form.get('name'), slug: event.currentTarget.elements.slug.value, brand_name: form.get('brand_name'), description: form.get('description'), accent: form.get('accent'), features, plan_id: $('planId').value, max_enabled_agents: Number($('planAgentLimit').value), monthly_token_limit: Number($('planTokenLimit').value), debate_rounds: Number($('planDebateRounds').value), agent_names: agentNames, mode_autonomous: $('modeAutonomous').checked, mode_guided_auto: $('modeGuidedAuto').checked, mode_manual: $('modeManual').checked, mode_autonomous_min_plan: $('modeAutonomousMinPlan').value, mode_guided_auto_min_plan: $('modeGuidedAutoMinPlan').value, mode_manual_min_plan: $('modeManualMinPlan').value, default_operating_mode: $('defaultOperatingMode').value, api_control_mode: $('apiControlMode').value, allowed_providers: $('allowedProviders').value, text_provider: $('textProvider').value, text_model: $('textModel').value, visual_provider: $('visualProvider').value, visual_model: $('visualModel').value, credential_reentry_allowed: $('credentialReentryAllowed').checked, meta_reconnect_allowed: $('metaReconnectAllowed').checked, chat_enabled: $('chatEnabled').checked, chat_model_mode: $('chatModelMode').value, chat_provider: $('chatProvider').value, chat_model: $('chatModel').value, chat_token_limit: Number($('chatTokenLimit').value || 1200), chat_content_revision: $('chatContentRevision').checked, chat_visual_revision: $('chatVisualRevision').checked };
  try { const result = await api('/api/apps', { method: 'POST', body: JSON.stringify(payload) }); notify($('editingAppId').value ? 'Uygulamanın yeni sürümü oluşturuldu.' : 'Yaşayan ajans uygulaması oluşturuldu.'); await load(); resetFactory(); switchView('portfolio'); window.open(result.preview_url, '_blank', 'noopener'); }
  catch (error) { notify(error.message === 'core_agent_limit_too_low' ? 'Rol sınırı açık çekirdek rollerin tamamını kapsamalı. Basic varsayılanı çekirdeği eksiltmez.' : error.message === 'invalid_chat_configuration' ? 'Sohbet modeli veya token sınırı geçerli değil.' : error.message === 'default_provider_and_model_required' ? 'Metin ve görsel için varsayılan sağlayıcı/model zorunlu.' : error.message === 'at_least_one_operating_mode_required' ? 'Seçilen planda en az bir çalışma modu açık olmalı.' : error.message, 'error'); }
}

async function exportProject() {
  try { const bundle = await api('/api/project/export'); const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `ajans-kurucu-${new Date().toISOString().slice(0, 10)}.ajanskurucu`; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 1000); notify('Taşıma paketi indirildi. Paket hesap şifresi içermez.'); } catch (error) { notify(error.message, 'error'); }
}

async function importProject() {
  const file = $('importProjectFile').files[0]; if (!file) { notify('Önce .ajanskurucu dosyasını seç.', 'error'); return; }
  try { const bundle = JSON.parse(await file.text()); await api('/api/project/import', { method: 'POST', body: JSON.stringify(bundle) }); notify('Taşıma paketi içe aktarıldı.'); $('importProjectFile').value = ''; await load(); } catch (error) { const messages = { invalid_portable_bundle: 'Seçilen dosya geçerli bir Ajans Kurucu paketi değil.', portable_bundle_contains_secret: 'Güvenlik nedeniyle hesap bilgisi içeren paket reddedildi.' }; notify(messages[error.message] || error.message, 'error'); }
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
$('factoryForm').addEventListener('submit', createApp);
$('modelAssignmentForm').addEventListener('submit', saveModelAssignments); $('flowDesignForm').addEventListener('submit', saveFlowDesign);
$('tokenPolicyForm').addEventListener('submit', saveTokenPolicy); $('flowBlueprintForm').addEventListener('submit', saveFlowBlueprints);
$('newFlow').addEventListener('click', newFlowBlueprint); $('flowBlueprintSelect').addEventListener('change', (event) => { activeFlowIndex = Number(event.target.value); renderFlowBlueprints(); });
$('newAgent').addEventListener('click', () => openAgent()); $('closeAgent').addEventListener('click', () => $('agentDialog').close()); $('agentForm').addEventListener('submit', saveAgent); $('agentModelMode').addEventListener('change', toggleAgentModelFields);
$('agentTokenProfile').addEventListener('change', () => { const values = { low: 800, medium: 1800, high: 4000 }; if (values[$('agentTokenProfile').value]) $('agentTokenLimit').value = values[$('agentTokenProfile').value]; });
$('planId').addEventListener('change', () => renderPlanFields(true)); $('planAgentLimit').addEventListener('change', () => renderAppAgentNames()); $('resetFactory').addEventListener('click', resetFactory);
$('apiControlMode').addEventListener('change', toggleApiControlFields); $('chatEnabled').addEventListener('change', toggleChatFields); $('chatModelMode').addEventListener('change', toggleChatFields);
$('exportProject').addEventListener('click', exportProject); $('importProject').addEventListener('click', importProject);
load();
