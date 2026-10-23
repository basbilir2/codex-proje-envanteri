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
  header.append(identity, element('em', '', 'Önizleme'));

  const main = element('main');
  main.append(element('p', 'kicker', 'KULLANICI UYGULAMASI'), element('h1', '', `${config.brand_name} için yaşayan ajans`), element('p', '', 'Markanı tanıt, içerik akışını izle, görselleri ve metinleri kontrol et. Son yayın her zaman senin onayından geçer.'));
  const cards = element('div', 'client-cards');
  for (const feature of config.features || []) {
    const card = element('article'); card.append(element('strong', '', featureNames[feature] || feature), element('span', '', 'Bu bölüm müşteri uygulamasında bulunacak.')); cards.append(card);
  }
  const notice = element('div', 'notice neutral', 'Bu önizleme yönetici şablonundan oluşturuldu. Arka plandaki ajan karakterleri ve algoritma kullanıcıya gösterilmez.');
  main.append(cards, notice); root.append(header, main);
}

renderClientPreview().catch(() => { document.getElementById('clientApp').textContent = 'Önizleme yüklenemedi.'; });
