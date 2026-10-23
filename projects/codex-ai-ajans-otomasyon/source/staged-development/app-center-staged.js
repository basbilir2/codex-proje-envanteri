const $ = (id) => document.getElementById(id);
const escapeHtml = (value = '') => String(value)
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#039;');
const fmt = (value) => new Intl.NumberFormat('tr-TR').format(Number(value || 0));
const initials = (name = '') => name.split(/\s+/).map((part) => part[0]).join('').slice(0, 2).toUpperCase();
const isLocalTestReference = (image = {}) => String(image.name || '').startsWith('free-local-e2e-test-reference');
const titleMap = {
  overview: 'Genel Bakış', conversations: 'Ajan Konuşmaları', outputs: 'Çıktılar',
  visuals: 'Görseller', tokens: 'Token & Maliyet', approvals: 'Onay Bekleyenler', system: 'Sistem'
};
let dashboard = null;
let approvalCsrf = sessionStorage.getItem('approvalCsrf') || '';
let liveApprovals = [];

function switchView(view) {
  document.querySelectorAll('.view').forEach((item) => item.classList.toggle('active', item.id === `view-${view}`));
  document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === view));
  $('pageTitle').textContent = titleMap[view] || 'Ajans Merkezi';
}

function renderTimeline(messages = []) {
  if (!messages.length) return '<div class="empty"><strong>Henüz konuşma yok</strong>İlk ajan devri burada görünecek.</div>';
  return messages.slice(-4).map((message) => `
    <div class="timeline-item">
      <span class="avatar">${escapeHtml(initials(message.agent_name))}</span>
      <div><strong>${escapeHtml(message.agent_name)}</strong><p>${escapeHtml(message.text)}</p></div>
      <time>${escapeHtml(message.type)}</time>
    </div>`).join('');
}

function renderOverview(data) {
  const task = data.system.current_task;
  $('currentTaskTitle').textContent = task?.agent_id === 'yayin_arayuz_ajani'
    ? 'Ücretsiz yerel test tamamlandı — Operator onayı bekleniyor'
    : task
      ? `${task.agent_id || 'Ajan'} görevi hazır`
      : 'Bekleyen görev yok';
  $('currentTaskText').textContent = task?.goal || 'Sistem yeni görev bekliyor.';
  $('metricCalls').textContent = fmt(data.tokens.totals.calls);
  $('metricTokens').textContent = fmt(data.tokens.totals.total);
  $('metricIdeas').textContent = fmt(data.outputs.content?.ideas?.length || 0);
  $('metricImages').textContent = fmt(data.visuals.generated.filter((image) => !isLocalTestReference(image)).length);
  const latest = data.conversations.at(-1);
  $('recentConversation').innerHTML = renderTimeline(latest?.messages || []);

  const used = data.context_efficiency.estimated_input_tokens || 0;
  const limit = data.context_efficiency.max_input_tokens || 0;
  const remaining = data.context_efficiency.remaining_input_tokens || 0;
  const pct = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  $('contextTokens').textContent = fmt(used);
  $('contextLimit').textContent = `${fmt(limit)} token`;
  $('contextRemaining').textContent = `${fmt(remaining)} token`;
  $('budgetRing').style.setProperty('--pct', `${pct}%`);
  $('contextStatus').textContent = data.context_efficiency.full_agent_prompt_sent === false ? 'Tam prompt gönderilmedi' : 'Kontrol gerekli';
  $('contextStatus').className = `pill ${data.context_efficiency.full_agent_prompt_sent === false ? 'safe' : 'warning'}`;
}

function renderConversations(data) {
  $('conversationCount').textContent = `${data.conversations.length} kayıt`;
  $('conversationList').innerHTML = data.conversations.length ? data.conversations.map((conversation) => `
    <article class="conversation">
      <div class="conversation-head"><div><h3>${escapeHtml(conversation.title)}</h3><small>${escapeHtml(conversation.status)}</small></div><span class="pill">${conversation.messages.length} mesaj</span></div>
      ${conversation.messages.map((message) => `
        <div class="message">
          <span class="avatar">${escapeHtml(initials(message.agent_name))}</span>
          <div><div class="message-meta"><strong>${escapeHtml(message.agent_name)}</strong><span>${escapeHtml(message.type)}</span></div><p>${escapeHtml(message.text)}</p></div>
        </div>`).join('')}
    </article>`).join('') : '<div class="empty"><strong>Henüz konuşma yok</strong>Ajan mesajları kısa özet olarak burada tutulacak.</div>';

  $('debateList').innerHTML = data.debates.length ? data.debates.map((debate) => `
    <article class="card"><span class="pill warning">${escapeHtml(debate.status)}</span><h3>Tur ${debate.current_round} / ${debate.max_rounds}</h3><p>${escapeHtml(debate.note)}</p><small class="muted">${debate.participants.map(escapeHtml).join(' · ')}</small></article>`).join('') : '<div class="empty"><strong>Tartışma başlamadı</strong>Muhalif turları burada görünecek.</div>';
}

function renderOutputs(data) {
  const analysis = data.outputs.analysis;
  const content = data.outputs.content;
  const blocks = [];
  if (analysis) blocks.push(`
    <article class="output-card"><div class="output-head"><h3>Analizci Raporu</h3><span class="pill safe">Tamamlandı</span></div><div class="output-body"><pre>${escapeHtml(analysis.content)}</pre></div></article>`);
  if (content) blocks.push(`
    <article class="output-card"><div class="output-head"><h3>İçerik Stratejisti — 3 fikir</h3><span class="pill warning">${escapeHtml(content.status)}</span></div>
    <div class="output-body"><div class="idea-grid">${content.ideas.map((idea) => `
      <div class="idea"><b>${escapeHtml(idea.format)}</b><h4>${escapeHtml(idea.hook)}</h4><p>${escapeHtml(idea.message)}</p><p class="cta">${escapeHtml(idea.cta)}</p></div>`).join('')}</div>
      <p class="muted">${escapeHtml(content.data_disclaimer)}</p></div></article>`);
  $('outputList').innerHTML = blocks.join('') || '<div class="empty"><strong>Çıktı bulunamadı</strong>Üretilen raporlar burada görünecek.</div>';
}

function renderVisuals(data) {
  const briefs = data.visuals.briefs || [];
  const realGenerated = data.visuals.generated.filter((image) => !isLocalTestReference(image));
  const localTestReferences = data.visuals.generated.filter(isLocalTestReference);
  $('visualBriefs').innerHTML = briefs.length ? briefs.map((idea, index) => `
    <article class="visual-card"><div class="copy"><span class="pill">${index + 1}. ${escapeHtml(idea.format)}</span><h3>${escapeHtml(idea.hook)}</h3><p>${escapeHtml(idea.visual_brief)}</p><p class="muted">Gerçek görsel henüz üretilmedi.</p></div></article>`).join('') : '<div class="empty"><strong>Görsel brief yok</strong>İçerik fikirlerinden sonra oluşacak.</div>';
  $('generatedVisuals').innerHTML = data.visuals.generated.length ? data.visuals.generated.map((image) => `
    <article class="visual-card"><img src="${escapeHtml(image.url)}" alt="${escapeHtml(image.name)}"><div class="copy"><h3>${escapeHtml(image.name)}</h3><p>${isLocalTestReference(image) ? 'Yerel test referansı — AI üretimi değildir' : 'Üretilen görsel'}</p></div></article>`).join('') : '<div class="empty"><strong>Henüz gerçek görsel üretilmedi</strong>Görsel model bağlantısı hazır olduğunda burada görünecek.</div>';
  $('referenceVisuals').innerHTML = data.visuals.references.length ? data.visuals.references.map((image) => `
    <article class="visual-card"><img loading="lazy" src="${escapeHtml(image.url)}" alt="${escapeHtml(image.name)}"><div class="copy"><h3>${escapeHtml(image.name)}</h3><p>Marka görsel referansı</p></div></article>`).join('') : '<div class="empty"><strong>Referans bulunamadı</strong>Marka referans klasörü boş.</div>';
  $('visualStatus').textContent = `${briefs.length} brief · ${realGenerated.length} gerçek görsel · ${localTestReferences.length} test referansı`;
}

function renderTokens(data) {
  $('tokenInput').textContent = fmt(data.tokens.totals.input);
  $('tokenOutput').textContent = fmt(data.tokens.totals.output);
  $('tokenTotal').textContent = fmt(data.tokens.totals.total);
  $('tokenCalls').textContent = fmt(data.tokens.totals.calls);
  const max = Math.max(1, ...data.tokens.records.map((item) => Number(item.input_tokens || 0) + Number(item.output_tokens || 0)));
  $('tokenList').innerHTML = data.tokens.records.map((item) => {
    const total = Number(item.input_tokens || 0) + Number(item.output_tokens || 0);
    return `<article class="token-row"><div><h3>${escapeHtml(item.task_type)}</h3><small>${escapeHtml(item.provider)} · ${escapeHtml(item.model)}</small></div><div class="bar"><i style="width:${Math.round((total / max) * 100)}%"></i></div><div class="token-number">${fmt(total)}</div></article>`;
  }).join('') || '<div class="empty"><strong>Kullanım kaydı yok</strong>Model çağrıları burada ölçülecek.</div>';
}

function renderApprovalItems(items) {
  liveApprovals = items;
  const previewUrl = (reference) => {
    const raw = typeof reference === 'string' ? reference : reference?.url || reference?.path || reference?.name || '';
    if (raw.startsWith('/media/generated/')) return raw;
    const normalized = raw.replaceAll('\\', '/');
    const prefix = 'data/outputs/images/';
    if (normalized.startsWith(prefix)) return `/media/generated/${encodeURIComponent(normalized.slice(prefix.length))}`;
    if (/^[a-zA-Z0-9][a-zA-Z0-9._-]*\.(?:png|jpe?g|webp)$/i.test(normalized)) return `/media/generated/${encodeURIComponent(normalized)}`;
    return '';
  };
  $('approvalList').innerHTML = items.length ? items.map((item) => {
    const caption = item.content_payload?.caption || '';
    const images = (item.preview_refs || []).map(previewUrl).filter(Boolean);
    const localOnly = item.delivery_mode === 'local_file_only';
    return `
    <article class="card">
      <span class="pill warning">${localOnly ? 'Yerel dosyaya kaydetme onayı' : 'Onay bekliyor'}</span>
      <h3>${escapeHtml(item.summary)}</h3>
      <p>Sürüm: ${escapeHtml(item.content_version)} · Hedef: ${localOnly ? 'Yalnız yerel klasör — yayın yapılamaz' : escapeHtml(item.account_id)}</p>
      ${caption ? `<div class="output-body"><pre>${escapeHtml(caption)}</pre></div>` : ''}
      ${images.length ? `<div class="visual-grid">${images.map((url) => `<article class="visual-card"><img src="${escapeHtml(url)}" alt="Onay görseli"><div class="copy"><p>Onaylanacak görsel</p></div></article>`).join('')}</div>` : ''}
      <p class="muted">İçerik özeti: ${escapeHtml(item.content_hash.slice(0, 16))}…</p>
      <input class="approval-note" data-note-for="${escapeHtml(item.approval_id)}" placeholder="Yalnız revize istiyorsan not yaz">
      <div class="approval-actions">
        <button class="approve-button" data-approval="${escapeHtml(item.approval_id)}" data-decision="approve">Onayla</button>
        <button class="revise-button" data-approval="${escapeHtml(item.approval_id)}" data-decision="revise">Revize iste</button>
        <button class="reject-button" data-approval="${escapeHtml(item.approval_id)}" data-decision="reject">Reddet</button>
      </div>
    </article>`;
  }).join('') : '<div class="empty"><strong>Şu an onay bekleyen paket yok</strong>Görsel, muhalif kontrol ve Ordinaryüs kararı tamamlanınca paket burada görünecek.</div>';
}

async function loadLiveApprovals() {
  const response = await fetch('/api/approvals/waiting', { credentials: 'same-origin', cache: 'no-store' });
  if (response.status === 401) {
    $('approvalLogin').classList.remove('hidden');
    renderApprovalItems([]);
    return;
  }
  if (!response.ok) throw new Error(`Onay servisi ${response.status}`);
  $('approvalLogin').classList.add('hidden');
  renderApprovalItems((await response.json()).items || []);
}

async function approvalLogin() {
  const password = $('approvalPassword').value;
  const response = await fetch('/api/operator/login', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password }) });
  const result = await response.json();
  $('approvalPassword').value = '';
  if (!response.ok) { $('approvalLoginStatus').textContent = result.error === 'operator_password_not_configured' ? 'Onay parolası henüz ayarlanmadı.' : 'Giriş reddedildi.'; return; }
  approvalCsrf = result.csrf_token;
  sessionStorage.setItem('approvalCsrf', approvalCsrf);
  $('approvalLoginStatus').textContent = 'Giriş başarılı.';
  await loadLiveApprovals();
}

async function submitApproval(approvalId, decision) {
  const item = liveApprovals.find((entry) => entry.approval_id === approvalId);
  if (!item || !approvalCsrf) return;
  const note = document.querySelector(`[data-note-for="${CSS.escape(approvalId)}"]`)?.value || '';
  const response = await fetch(`/api/approvals/${encodeURIComponent(approvalId)}/decision`, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': approvalCsrf }, body: JSON.stringify({ decision, nonce: item.nonce, revision_note: note }) });
  if (!response.ok) { const result = await response.json(); alert(`Karar kaydedilemedi: ${result.error}`); return; }
  const result = await response.json();
  if (decision === 'approve' && result.delivery?.output_dir) alert(`Onaylandı ve yerel klasöre kaydedildi:\n${result.delivery.output_dir}\n\nSosyal medyada yayınlanmadı.`);
  await loadLiveApprovals();
}

function renderApprovals(data) {
  renderApprovalItems(data.approvals.waiting || []);
  loadLiveApprovals().catch((error) => { $('approvalLoginStatus').textContent = `Onay servisi hazır değil: ${error.message}`; });
}

function renderSystem(data) {
  const healthy = data.system.n8n.status === 'healthy';
  const runtimeReady = data.system.runtime?.status === 'ready';
  $('systemCards').innerHTML = `
    <article class="card"><span class="pill ${healthy ? 'safe' : 'warning'}">n8n</span><h3>${healthy ? 'Çalışıyor' : 'Kontrol gerekli'}</h3><p>Yerel otomasyon motoru: ${escapeHtml(data.system.n8n.status)}</p></article>
    <article class="card"><span class="pill safe">Yayın kilidi</span><h3>Kapalı</h3><p>Operator onayı ve etkin yayın adaptörü olmadan dış paylaşım yapılamaz.</p></article>
    <article class="card"><span class="pill ${runtimeReady ? 'safe' : 'warning'}">Runtime</span><h3>${runtimeReady ? 'Hazır' : 'Kurulum bekliyor'}</h3><p>Transactional görev, onay, audit, cache ve hafıza motoru: ${escapeHtml(data.system.runtime?.status || 'unreachable')}</p></article>
    <article class="card"><span class="pill ${data.context_efficiency.policy_active ? 'safe' : 'warning'}">Bağlam</span><h3>${data.context_efficiency.policy_active ? 'Kompakt v2 etkin' : 'Kontrol gerekli'}</h3><p>Tam geçmiş ve tam ajan promptu varsayılan model girdisine eklenmez.</p></article>
    <article class="card"><span class="pill">Aktif ajan</span><h3>${escapeHtml(data.system.active_agent || 'Yok')}</h3><p>Durum: ${escapeHtml(data.system.active_state)}</p></article>
    <article class="card"><span class="pill">Hata kaydı</span><h3>${fmt(data.system.errors)}</h3><p>Kayıtlı hata sayısı.</p></article>
    <article class="card"><span class="pill safe">Gizlilik</span><h3>Yerel ve salt okunur</h3><p>Bu merkez credential ve API anahtarlarını okuyamaz; veri değiştirme uç noktası içermez.</p></article>`;
}

function render(data) {
  dashboard = data;
  renderOverview(data);
  renderConversations(data);
  renderOutputs(data);
  renderVisuals(data);
  renderTokens(data);
  renderApprovals(data);
  renderSystem(data);
  const healthy = data.system.n8n.status === 'healthy';
  $('sideStatus').textContent = healthy ? 'Sistem çalışıyor' : 'Sistem kontrol edilmeli';
  $('sideStatusDot').classList.toggle('ok', healthy);
}

async function load() {
  $('loading').classList.remove('hidden');
  $('errorBox').classList.add('hidden');
  try {
    const response = await fetch('/api/dashboard', { cache: 'no-store' });
    if (!response.ok) throw new Error(`Sunucu yanıtı ${response.status}`);
    render(await response.json());
  } catch (error) {
    $('errorBox').textContent = `Ajans kayıtları yüklenemedi: ${error.message}`;
    $('errorBox').classList.remove('hidden');
  } finally {
    $('loading').classList.add('hidden');
  }
}

document.querySelectorAll('.nav-item').forEach((button) => button.addEventListener('click', () => switchView(button.dataset.view)));
document.querySelectorAll('[data-jump]').forEach((button) => button.addEventListener('click', () => switchView(button.dataset.jump)));
document.querySelectorAll('.subtab').forEach((button) => button.addEventListener('click', () => {
  document.querySelectorAll('.subtab').forEach((item) => item.classList.toggle('active', item === button));
  document.querySelectorAll('.visual-tab').forEach((item) => item.classList.toggle('active', item.id === `${button.dataset.visualTab}Visuals` || (button.dataset.visualTab === 'briefs' && item.id === 'visualBriefs')));
}));
$('refreshButton').addEventListener('click', load);
$('approvalLoginButton').addEventListener('click', approvalLogin);
$('approvalPassword').addEventListener('keydown', (event) => { if (event.key === 'Enter') approvalLogin(); });
$('approvalList').addEventListener('click', (event) => {
  const button = event.target.closest('button[data-approval]');
  if (button) submitApproval(button.dataset.approval, button.dataset.decision);
});
load();
setInterval(load, 15000);
