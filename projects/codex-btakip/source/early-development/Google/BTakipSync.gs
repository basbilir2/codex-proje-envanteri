/**
 * BTakip Google Sheets senkron servisi.
 * Bu kod yalnızca yeni oluşturulacak BTakip Veri çalışma kitabına bağlanmalıdır.
 * Mevcut başka çalışma kitaplarını okumaz veya değiştirmez.
 */

const BTAKIP_SHEETS = {
  customers: {
    name: 'Müşteriler',
    fields: ['Id','Name','Company','Phone','Email','PriceGroupId','Notes','UpdatedAtUtc','Revision','DeviceId','Deleted'],
    labels: ['Kimlik','Ad','Firma','Telefon','E-posta','Fiyat Grubu Kimliği','Not','Son Değişiklik UTC','Sürüm','Cihaz','Silindi']
  },
  price_groups: {
    name: 'Fiyat Grupları',
    fields: ['Id','Code','Name','CostMultiplier','UpdatedAtUtc','Revision','DeviceId','Deleted'],
    labels: ['Kimlik','Kod','Ad','Maliyet Çarpanı','Son Değişiklik UTC','Sürüm','Cihaz','Silindi']
  },
  price_items: {
    name: 'Fiyatlar',
    fields: ['Id','Category','Name','Variant','Unit','Currency','UnitCost','SecondaryCost','SheetWidthCm','SheetHeightCm','ThicknessMm','BaseMaterialPriceItemId','IsPrintProduct','ServiceEnabled','ServiceName','ServiceFormula','ServiceUnitCost','Formula','Active','UpdatedAtUtc','Revision','DeviceId','Deleted','GroupProfitPercentOverrides','PriceGroupId','SpecialProfitPercent'],
    labels: ['Kimlik','Kategori','Ad','Varyant','Birim','Para Birimi','Birim Maliyet','İkincil Fiyat','Malzeme En cm','Malzeme Boy cm','Kalınlık mm','Kullanılan Malzeme Kimliği','Üründe Baskı','Hizmet Var','Hizmet Adı','Hizmet Hesabı','Hizmet Birim Maliyeti','Formül','Aktif','Son Değişiklik UTC','Sürüm','Cihaz','Silindi','Gruba Özel Kârlar JSON','Müşteri Fiyat Grubu','Eski Özel Kâr %']
  },
  orders: {
    name: 'Siparişler',
    fields: ['Id','Date','CustomerId','Description','WidthCm','HeightCm','AreaM2','LengthMeter','DurationMinutes','Quantity','ExchangeRate','CostTotalTl','SaleTotalTl','PriceGroupId','AlternativePercent','Lines','UpdatedAtUtc','Revision','DeviceId','Deleted'],
    labels: ['Kimlik','Tarih','Müşteri Kimliği','Açıklama','En cm','Boy cm','Alan m²','Uzunluk m','Süre dk','Adet','Kur','Maliyet TL','Satış TL','Fiyat Grubu','Alternatif %','Kalemler JSON','Son Değişiklik UTC','Sürüm','Cihaz','Silindi']
  },
  payments: {
    name: 'Tahsilatlar',
    fields: ['Id','Date','CustomerId','AmountTl','Description','PaymentType','UpdatedAtUtc','Revision','DeviceId','Deleted'],
    labels: ['Kimlik','Tarih','Müşteri Kimliği','Tutar TL','Açıklama','Ödeme Tipi','Son Değişiklik UTC','Sürüm','Cihaz','Silindi']
  }
};

// Yalnız yeni oluşturulan "BTakip Veri" çalışma kitabı.
const BTAKIP_SPREADSHEET_ID = '1-oT2r_qDlug83XMbGzqUJlOX7hxgCS_Ej--OBMHDv6A';

function setupBTakip(syncToken) {
  const token = syncToken && String(syncToken).length >= 16
    ? String(syncToken)
    : Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '');
  PropertiesService.getScriptProperties().setProperty('BTAKIP_TOKEN', token);
  PropertiesService.getScriptProperties().setProperty('CHANGE_TOKEN', String(Date.now()));
  const book = getBook_();
  Object.keys(BTAKIP_SHEETS).forEach(type => {
    const config = BTAKIP_SHEETS[type];
    let sheet = book.getSheetByName(config.name);
    if (!sheet) sheet = book.insertSheet(config.name);
    sheet.getRange(1, 1, 1, config.labels.length).setValues([config.labels]);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, config.labels.length)
      .setBackground('#143041').setFontColor('#ffffff').setFontWeight('bold');
    sheet.autoResizeColumns(1, config.labels.length);
    if (!sheet.getFilter()) sheet.getRange(1, 1, Math.max(2, sheet.getMaxRows()), config.labels.length).createFilter();
  });
  let info = book.getSheetByName('Ayarlar');
  if (!info) info = book.insertSheet('Ayarlar');
  info.getRange('A1:B6').setValues([
    ['BTakip Google Yedek', 'Bu çalışma kitabı yalnız BTakip için oluşturuldu.'],
    ['Senkron durumu', 'Hazır'],
    ['Değişiklik kontrolü', 'Uygulama açıkken ayarlanan saniye aralığında'],
    ['Yerel ana kayıt', 'PC içindeki btakip klasörü'],
    ['Satır silme', 'Silindi sütununu EVET/TRUE yapın; satırı fiziksel silmeyin'],
    ['Sürüm', '1.0']
  ]);
  info.getRange('A1:B1').setBackground('#143041').setFontColor('#ffffff').setFontWeight('bold');
  info.setFrozenRows(1);

  ScriptApp.getProjectTriggers()
    .filter(trigger => trigger.getHandlerFunction() === 'handleBTakipEdit')
    .forEach(trigger => ScriptApp.deleteTrigger(trigger));
  ScriptApp.newTrigger('handleBTakipEdit').forSpreadsheet(book).onEdit().create();
  console.log('BTAKIP_SYNC_TOKEN=' + token);
  return 'BTakip tabloları hazır. Senkron anahtarı yürütme günlüğüne yazıldı.';
}

function doGet(e) {
  try {
    assertToken_(e && e.parameter ? e.parameter.token : '');
    const action = (e.parameter.action || 'status').toLowerCase();
    const current = getChangeToken_();
    if (action === 'status') return json_({ ok: true, changeToken: current, serverTime: new Date().toISOString() });
    if (action !== 'pull') return json_({ ok: false, error: 'Bilinmeyen işlem.' });
    if (String(e.parameter.since || '') === current) return json_({ ok: true, changeToken: current, records: [] });
    const records = [];
    Object.keys(BTAKIP_SHEETS).forEach(type => readRecords_(type).forEach(data => records.push({ type: type, data: data })));
    return json_({ ok: true, changeToken: current, records: records });
  } catch (error) {
    return json_({ ok: false, error: String(error && error.message ? error.message : error) });
  }
}

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents || '{}');
    assertToken_(body.token || '');
    if (body.action !== 'push') return json_({ ok: false, error: 'Bilinmeyen işlem.' });
    const records = Array.isArray(body.records) ? body.records : [];
    const lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try {
      records.forEach(record => upsert_(record.type, record.data || {}));
      const token = bumpChangeToken_();
      return json_({ ok: true, changeToken: token, accepted: records.length });
    } finally {
      lock.releaseLock();
    }
  } catch (error) {
    return json_({ ok: false, error: String(error && error.message ? error.message : error) });
  }
}

function handleBTakipEdit(e) {
  if (!e || !e.range || e.range.getRow() <= 1) return;
  const sheet = e.range.getSheet();
  const type = Object.keys(BTAKIP_SHEETS).find(key => BTAKIP_SHEETS[key].name === sheet.getName());
  if (!type) return;
  const config = BTAKIP_SHEETS[type];
  const row = e.range.getRow();
  const values = sheet.getRange(row, 1, 1, config.fields.length).getValues()[0];
  const idIndex = config.fields.indexOf('Id');
  const updatedIndex = config.fields.indexOf('UpdatedAtUtc');
  const revisionIndex = config.fields.indexOf('Revision');
  const deviceIndex = config.fields.indexOf('DeviceId');
  const deletedIndex = config.fields.indexOf('Deleted');
  if (!values[idIndex]) values[idIndex] = Utilities.getUuid().replace(/-/g, '');
  values[updatedIndex] = new Date().toISOString();
  values[revisionIndex] = Number(values[revisionIndex] || 0) + 1;
  values[deviceIndex] = 'GOOGLE_SHEETS';
  if (values[deletedIndex] === '') values[deletedIndex] = false;
  sheet.getRange(row, 1, 1, config.fields.length).setValues([values]);
  bumpChangeToken_();
}

function upsert_(type, data) {
  const config = BTAKIP_SHEETS[type];
  if (!config) throw new Error('Bilinmeyen tablo: ' + type);
  if (!data.Id) throw new Error(type + ' kaydında Kimlik yok.');
  const sheet = getBook_().getSheetByName(config.name);
  if (!sheet) throw new Error(config.name + ' sayfası bulunamadı. setupBTakip çalıştırın.');
  let row = sheet.getLastRow() + 1;
  if (sheet.getLastRow() > 1) {
    const ids = sheet.getRange(2, 1, sheet.getLastRow() - 1, 1).getDisplayValues().flat();
    const index = ids.indexOf(String(data.Id));
    if (index >= 0) {
      row = index + 2;
      const existingRevision = Number(sheet.getRange(row, config.fields.indexOf('Revision') + 1).getValue() || 0);
      if (existingRevision > Number(data.Revision || 0)) return;
    }
  }
  const values = config.fields.map(field => {
    const value = data[field];
    if (field === 'Lines') return JSON.stringify(value || []);
    if (field === 'GroupProfitPercentOverrides') return JSON.stringify(value || {});
    if (field === 'UpdatedAtUtc' && !value) return new Date().toISOString();
    return value === undefined || value === null ? '' : value;
  });
  sheet.getRange(row, 1, 1, values.length).setValues([values]);
}

function readRecords_(type) {
  const config = BTAKIP_SHEETS[type];
  const sheet = getBook_().getSheetByName(config.name);
  if (!sheet || sheet.getLastRow() <= 1) return [];
  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, config.fields.length).getValues();
  return rows.filter(row => row.some(value => value !== '')).map(row => {
    const data = {};
    config.fields.forEach((field, index) => {
      let value = row[index];
      if (value instanceof Date) value = value.toISOString();
      if (field === 'Lines') {
        try { value = value ? JSON.parse(String(value)) : []; } catch (_) { value = []; }
      }
      if (field === 'GroupProfitPercentOverrides') {
        try { value = value ? JSON.parse(String(value)) : {}; } catch (_) { value = {}; }
      }
      if (['Revision'].includes(field)) value = Number(value || 0);
      if (['CostMultiplier','UnitCost','SecondaryCost','SheetWidthCm','SheetHeightCm','ThicknessMm','ServiceUnitCost','WidthCm','HeightCm','AreaM2','LengthMeter','DurationMinutes','Quantity','ExchangeRate','CostTotalTl','SaleTotalTl','AlternativePercent','AmountTl'].includes(field)) value = value === '' ? 0 : Number(value);
      if (field === 'SpecialProfitPercent') value = value === '' ? null : Number(value);
      if (['Deleted','Active','IsPrintProduct','ServiceEnabled'].includes(field)) value = value === true || String(value).toLowerCase() === 'true' || String(value).toLowerCase() === 'evet' || String(value) === '1';
      data[field] = value;
    });
    return data;
  });
}

function assertToken_(token) {
  const expected = PropertiesService.getScriptProperties().getProperty('BTAKIP_TOKEN');
  if (!expected) throw new Error('BTakip senkron anahtarı kurulmamış.');
  if (String(token) !== expected) throw new Error('Senkron anahtarı geçersiz.');
}

function getBook_() {
  return SpreadsheetApp.openById(BTAKIP_SPREADSHEET_ID);
}

function getChangeToken_() {
  return PropertiesService.getScriptProperties().getProperty('CHANGE_TOKEN') || '0';
}

function bumpChangeToken_() {
  const token = String(Date.now());
  PropertiesService.getScriptProperties().setProperty('CHANGE_TOKEN', token);
  return token;
}

function json_(value) {
  return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON);
}
