import json
import shutil
import urllib.request
from pathlib import Path
import tifffile

root=Path(__file__).resolve().parents[1]
req=json.loads((root/'.studio/relief-print-request.json').read_text(encoding='utf-8'))
info=json.loads((root/'.studio/server.json').read_text(encoding='utf-8'))
state=json.load(urllib.request.urlopen(info['url'].replace('/?','/api/state?')))
for n in (24,12):
    j=state['jobs'][req[f'job{n}']]
    if j['status']!='complete':
        print(json.dumps(dict(n=n,status=j['status'],message=j['message']),ensure_ascii=True))
        raise SystemExit(2)
out=root/'outputs/Ataturk_UV_60LPI_20cm_20261004_1707'
out.mkdir(exist_ok=True)
summary={}
for n in (24,12):
    j=state['jobs'][req[f'job{n}']]
    folder=Path(j['output'])/'print'
    r=json.loads((folder/'print-report.json').read_text(encoding='utf-8'))
    assert r['ne']==n and len(set(r['source_indices']))==n
    assert r['nonopaque_source_fraction']==0
    name=f'Ataturk_{n}Fotograf_60LPI_20x23.34cm_UV_1200PPI.tif'
    shutil.copyfile(folder/'interlaced.tif',out/name)
    assert (out/name).stat().st_size==(folder/'interlaced.tif').stat().st_size
    with tifffile.TiffFile(out/name) as t:
        p=t.pages[0]
        assert p.shape==(11028,9449,3)
        assert p.tags['XResolution'].value==(1200,1) and 34675 in p.tags
    shutil.copyfile(folder/'print-report.json',out/f'{n}Fotograf_BaskiRaporu.json')
    summary[n]=dict(file=name,source_indices=r['source_indices'],unique_source_count=n,
        rendered_count=r['nr'],encoded_count=r['ne'],physical_mm=r['physical_size_mm'],
        bytes=(out/name).stat().st_size)
folder=Path(state['jobs'][req['job24']]['output'])/'print'
shutil.copyfile(folder/'white-underbase.tif',out/'UV_Ortak_Beyaz_AltBaski_20x23.34cm_1200PPI.tif')
shutil.copyfile(folder/'pitch-test.tif',out/'60LPI_Pitch_Testi_1200PPI.tif')
(out/'DosyaBilgileri.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
notes='''ATATÜRK RÖLYEFİ — UV LENTICULAR BASKI

Ölçü: 20 × 23,34 cm. Raster: 9449 × 11028 piksel; 1200 PPI.
Yazıcı: 1200 DPI. Lens: 60 LPI, dikey çizgiler, sağ/sol 3D.
Renk: gömülü sRGB ICC profilli RGB. UV RIP'te uygun üretim profilini kullanın.
Aynalama kapalı. Arkadan baskıda yönü üretim yöntemiyle doğrulayın.

24Fotograf dosyası 24 ayrı Blender görünüşünü 24 kanala kodlar.
12Fotograf dosyası aynı görünüş setinden eşit açısal dağılımla seçilmiş
12 ayrı görünüşü 12 kanala kodlar. İki dosyanın kamera aralığı aynıdır.
1200 / 60 = lens başına 20 raster piksel/yazıcı noktası.
24 kanalda dilimler ayrı piksellere sığmaz; alan kapsama örneklemesi bazı
piksellerde komşu kanalları karıştırır. 24 bağımsız optik kanal çözüleceği
garanti değildir. İlk fiziksel karşılaştırmayı 12 sürümüyle yapın.
Kaynak ayrıntısı bu ölçüde yaklaşık 295 PPI'dır. 1200 PPI raster,
fazladan fotoğraf ayrıntısı oluşturmaz; lens dilimlerini örnekler.

Referans 0,20; güç 1,15; ön 1,05; arka 0,75; gri dengesi 1,10;
siyah 0; beyaz 1. İstenen açı 1,80°; uygulanan açı yaklaşık 0,93°.
Paralaks koruması: en büyük uç hareket farkı %1,5.

Beyaz maskesi iki renk dosyası için ortaktır. RIP'te ayrı White kanalı
olarak ata; RGB TIFF içinde spot beyaz yoktur. Maskenin tamamı opaktır.
%100 fiziksel boyutta bas. Sayfaya sığdırma veya interlace dosyasını
sonradan yeniden ölçekleme kullanma.
60 LPI etiket değeri kullanıldı; fiziksel pitch doğrulaması yapılmadı.
Pitch testini aynı lens, malzeme ve RIP koşullarında kontrol et.
Ölçülen etkin LPI farklıysa interlace yeniden hazırlanmalıdır.
'''
(out/'UV_Baski_Notlari.txt').write_text(notes,encoding='utf-8')
print(json.dumps(dict(output=str(out),files=summary),ensure_ascii=True))
