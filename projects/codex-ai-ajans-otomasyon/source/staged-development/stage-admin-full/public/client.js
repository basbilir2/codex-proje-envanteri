const featureNames = { brand: 'Markam', content: 'İçerik Üret', visuals: 'Görseller', workflow: 'Akış', approvals: 'Onaylar', calendar: 'Takvim', connections: 'Bağlantılar', models: 'Model Tercihi' };
const element = (tag, className, text) => { const node = document.createElement(tag); if (className) node.className = className; if (text !== undefined) node.textContent = text; return node; };

async function renderClientPreview() {
  const root = document.getElementById('clientApp');
  const slug = location.pathname.split('/').filter(Boolean).pop();
  const response = await fetch(`/client-api/${encodeURIComponent(slug)}/config`, { cache: 'no-store' });
  if (!response.ok) throw new Error('preview_unavailable');
  const config = await response.json();
  document.documentElement.style.setProperty('--accent', config.theme?.accent || '#8b5cf6');
  document.title = config.name;
  root.replaceChildren();

  const header = element('header');
  header.append(element('div', 'logo', (config.brand_name || 'A').slice(0, 2).toUpperCase()));
  const identity = element('div'); identity.append(element('strong', '', config.name), element('span', '', config.brand_name));
  header.append(identity, element('em', '', `${config.plan?.name || 'Basic'} · Önizleme`));

  const main = element('main');
  main.append(element('p', 'kicker', 'KURULABİLİR KULLANICI UYGULAMASI'), element('h1', '', `${config.name}`), element('p', '', 'İlk açılışta markanı tanıtacak, gerekli API ve sosyal medya hesaplarını bu uygulamanın içinde bağlayacaksın. Dosyaların uygulama tarafından yönetilecek; son yayın her zaman senin onayından geçecek.'));
  const cards = element('div', 'client-cards');
  for (const feature of config.features || []) {
    const card = element('article'); card.append(element('strong', '', featureNames[feature] || feature), element('span', '', 'Bu bölüm müşteri uygulamasında bulunacak.')); cards.append(card);
  }
  const roles = element('div', 'notice neutral', `${config.agent_names?.length || 0} rol bu uygulama için hazırlandı: ${(config.agent_names || []).map((agent) => agent.name).join(', ') || 'rol tanımı yok'}.`);
  const policy = config.connection_policy || {};
  const apiMode = { locked: 'Kilitli', guided: 'İzinli liste', open: 'Açık' }[policy.api_control_mode] || 'Kilitli';
  const policyGrid = element('div', 'client-policy-grid');
  const automation = element('div'); automation.append(element('strong', '', 'Gizli otomasyon motoru'), element('span', '', 'n8n uygulamanın içinde yönetilir. Kullanıcı hesabı, n8n ekranı veya iş akışı düzenleme gerekmez.'));
  const connections = element('div'); connections.append(element('strong', '', `API/model yetkisi: ${apiMode}`), element('span', '', `Kullanıcı ilk kurulumda gerekli API ve Meta izinlerini girer. Sonradan hesap değiştirme ${policy.meta?.reconnect_or_account_change_allowed ? 'açık' : 'kilitli'}.`));
  const modeBox = element('div'); const modeCatalog = config.operating_modes?.catalog || []; const modeNames = { autonomous: 'Oto', guided_auto: 'Kontrollü Oto', manual: 'Manuel' };
  modeBox.append(element('strong', '', 'Çalışma modları'), element('span', '', modeCatalog.filter((mode) => mode.visible).map((mode) => `${modeNames[mode.id] || mode.name}: ${mode.access_state === 'active' ? 'açık' : 'plan yükseltme gerekli'}`).join(' · ') || 'Mod tanımı yok'));
  policyGrid.append(automation, connections, modeBox);
  const notice = element('div', 'notice neutral', 'Bu önizleme Ajans Kurucu şablonundan oluşturuldu. Arka plandaki karakter talimatları, özel algoritma ve n8n iş akışları kullanıcıya gösterilmez. API ve hesap bilgileri bu önizlemeye veya Ana Uygulama’ya kaydedilmez.');
  main.append(cards, roles, policyGrid, notice);
  if ((config.operating_modes?.catalog || []).some((mode) => mode.id === 'autonomous' && mode.enabled_for_current_plan)) {
    main.append(element('div', 'notice neutral', 'Oto mod ilk kez açılırken kullanıcı sürümlü sorumluluk ve yapay zekâ hata riski metnini kabul eder. Kabulden sonra tanımlı sınırlar içinde son Meta yayını dahil ayrıca onay istemez; acil durdurma ve güvenlik duvarları korunur.'));
  }
  if (config.assistant_chat?.enabled) {
    const chat = element('section', 'client-chat'); const chatHead = element('header');
    chatHead.append(element('strong', '', 'Ajansla konuş'), element('span', 'badge', `${config.assistant_chat.maximum_tokens_per_message || 1200} token sınırı`));
    chat.append(chatHead, element('p', '', 'İçerik veya görsel revizesi isteyebilir, uygulama sorununu yazabilirsin. Riskli, tekrar eden veya gereksiz pahalı isteklerde ajans önce uyarır.'));
    const chatForm = element('div', 'client-chat-form'); const input = element('input'); input.placeholder = 'Ajansa isteğini yaz…'; input.disabled = true; const send = element('button', '', 'Gönder'); send.disabled = true; chatForm.append(input, send); chat.append(chatForm); main.append(chat);
  }
  root.append(header, main);
}

renderClientPreview().catch(() => { document.getElementById('clientApp').textContent = 'Önizleme yüklenemedi.'; });
