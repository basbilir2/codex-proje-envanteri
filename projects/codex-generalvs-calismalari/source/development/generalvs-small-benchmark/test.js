const fs = require('fs');
const { calculateTip } = require('./app.js');
let passed = 0;
function check(name, condition) {
  if (!condition) throw new Error(`Başarısız: ${name}`);
  passed += 1;
  console.log(`✓ ${name}`);
}
check('yüzde 10', JSON.stringify(calculateTip(100, 10)) === JSON.stringify({ tip: 10, total: 110 }));
check('ondalıklı oran', JSON.stringify(calculateTip(80, 12.5)) === JSON.stringify({ tip: 10, total: 90 }));
check('kuruş yuvarlama', JSON.stringify(calculateTip(19.99, 15)) === JSON.stringify({ tip: 3, total: 22.99 }));
check('sıfır tutar', JSON.stringify(calculateTip(0, 10)) === JSON.stringify({ tip: 0, total: 0 }));
check('sıfır oran', JSON.stringify(calculateTip(50, 0)) === JSON.stringify({ tip: 0, total: 50 }));
check('geçersiz tutar', calculateTip('x', 10) === null);
check('negatif tutar', calculateTip(-1, 10) === null);
check('negatif oran', calculateTip(10, -1) === null);
const html = fs.readFileSync('index.html', 'utf8');
check('erişilebilir canlı sonuç', html.includes('aria-live="polite"'));
check('harici bağımlılık yok', !/https?:\/\//.test(html));
console.log(`${passed}/10 doğrulama geçti.`);
