"""Extract educational knowledge from the specified job without assessing or modifying its output."""
from pathlib import Path
import hashlib
import json

SRC=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1\outputs\studio\20261006-105350-02b4bafc')
PACK=Path(r'C:\Users\USER\Documents\Codex\2026-10-10\referenced-chatgpt-conversation-this-is-an\outputs\len 2')
OUT=PACK/'egitim_icerigi'
OUT.mkdir(exist_ok=True)

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jsonl(name,rows):
    (OUT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')

names=['project.json','quality.json','render/job.json','render/render_result.json','render/repair.json','render/coverage.json','print/print-report.json','print/pitch-test.json','print/lens-response-template.json']
raw={name:json.loads((SRC/name).read_text(encoding='utf-8-sig')) for name in names}
before={name:digest(SRC/name) for name in names}
save('kaynak_kayitlari.json',{'source_folder':str(SRC),'interpretation':'Kullanıcının belirttiği genel lentiküler/yazılım eğitim kaynağı; çıktı düzeltme görevi değildir.','records':raw})
files=[]
for p in sorted(SRC.rglob('*')):
    if not p.is_file():continue
    rel=p.relative_to(SRC).as_posix()
    if rel.startswith('prepared/'): role='girdi_ve_derinlik_hazirligi'
    elif rel.startswith('render/'): role='sahne_katman_kamera_ve_gorunus'
    elif rel.startswith('print/'): role='baski_kodlama_kalibrasyon_ve_onizleme'
    else: role='is_ayarlari_ve_islem_raporu'
    files.append({'relative_path':rel,'bytes':p.stat().st_size,'role':role})
save('dosya_haritasi.json',{'source_folder':str(SRC),'files':files,'source_json_sha256':before})
project=raw['project.json'];job=raw['render/job.json'];quality=raw['quality.json'];report=raw['print/print-report.json']
topics=[
('İşlem zinciri','Bir işte girdi hazırlığı, render ve baskı aşamalarının dosyaları ayrı tutulur. Ana proje kaydı render ve baskı ayarlarını birlikte taşır.', ['project.json','render/job.json','print/print-report.json'],{'stages':['prepared','render','print'],'project_schema_version':project['schema_version']}),
('Görsel ve derinlik girdileri','Fotoğraf renk bilgisini, derinlik haritası sahne düzeni için kullanılan derinlik bilgisini taşır. PNG gösterimi ve sayısal NPY kaydı aynı iş içinde ayrı ürünlerdir.', ['render/job.json'],{'source_inputs':job['source_inputs'],'size':job['size'],'depth_convention':job['config']['depth_convention']}),
('Render ve baskı ayarlarının ayrılması','Kamera, derinlik, mesh ve katman ayarları render bölümündedir. Ölçü, PPI, yazıcı DPI, LPI ve kanal ayarları print bölümündedir. İki ayar grubu birbiri yerine kullanılmaz.', ['project.json'],{'render_fields':list(project['render']),'print_fields':list(project['print'])}),
('Sanal sahne ölçeği','near, far ve zero sahne kurulumunun derinlik değerleridir. Kaynak iş kaydı sahne uzunluklarının sanal birim olduğunu belirtir. Bunlar doğrudan basılı milimetreyle eşitlenmez.', ['render/job.json'],{k:job['config'][k] for k in ['near','far','zero','focal_mm','sensor_width_mm']}),
('Kamera görünüşleri','Nr render edilen bakış sayısını ifade eder. Konum dizisi, kamera ekseni ve kamera açıklığı birlikte kaydedilir. Her görünüşün dosyası ve gerçek kamera konumu izlenebilir.', ['render/job.json','render/render_result.json'],{'nr':job['config']['nr'],'positions':job['config']['positions'],'camera_axis':job['config']['camera_axis'],'camera_span':job['config']['camera_span']}),
('Projeksiyon kayıtları','Her kamera kaydı, gerçek ve beklenen görüntü koordinatlarını içeren projeksiyon kontrol alanları taşır. Bu yapı, bir render adımının nasıl kayıt altına alındığını öğretir.', ['render/render_result.json'],{'record_count':len(raw['render/render_result.json']),'example':raw['render/render_result.json'][0]}),
('Sabit derinlik ve etki ayarları','zero_reference, effect_strength ve depth_curve düzenlenmiş derinliğin kontrol alanlarıdır. Kamera açısı ayrıca kaydedilir. Buradaki değerler bu çalışmaya aittir; bütün işler için varsayılan değildir.', ['project.json','quality.json'],{'zero_reference':project['render']['zero_reference'],'effect_strength':project['render']['effect_strength'],'depth_curve':project['render']['depth_curve'],'angle_deg':project['render']['angle_deg']}),
('Katmanlı sahne yapısı','Sahne kaydı her derinlik katmanını bir mesh ve doku dosyasına bağlar. Ayrı maske dosyaları ve Blender sahnesi, renk, geometri ve görünürlük bilgisinin nasıl taşındığını gösterir.', ['render/job.json','render/repair.json'],{'surfaces':job['surfaces'],'layer_records':raw['render/repair.json']['layers']}),
('Gizli alan bilgisi','İş kaydı kullanılan onarım motorunu, dolgu sınırını ve tahmin edilen alan oranlarını saklar. Kaynak notu gizli rengin tahmin edildiğini açıklar; bu bilgi öğretim kaydında korunur.', ['render/repair.json','quality.json'],{'engine':raw['render/repair.json']['engine'],'padding_px':raw['render/repair.json']['padding_px'],'note':raw['render/repair.json']['note']}),
('İstenen ve uygulanan parametreler','İşlem raporu istenen kamera açısını, uygulanan açıyı, paralaks ölçülerini ve koruma alanlarını ayrı taşır. Bu, kullanıcı ayarı ile motorun kaydettiği sonuç değerini ayırmayı öğretir.', ['quality.json'],quality['parallax']),
('Kapsama raporu','Kapsama kaydı her görünüş için opak olmayan alan oranını içerir. Dosyadaki açıklama bunun bir yeniden oluşturma doğruluğu puanı olmadığını belirtir. Alanın anlamı kendi tanımıyla saklanır.', ['render/coverage.json'],raw['render/coverage.json']),
('Nr ve Ne eşlemesi','Nr kamera görünüşlerinin, Ne baskı kanallarının sayısıdır. source_indices dizisi kanalların hangi görünüşten alındığını kaydeder. Bu örnekte eşit olmaları iki kavramın aynı olduğu anlamına gelmez.', ['render/job.json','print/print-report.json'],{'nr':report['nr'],'ne':report['ne'],'source_indices':report['source_indices'],'sampling':report['sampling']}),
('Baskı ölçüsü ve çözünürlük','Fiziksel ölçü milimetre, raster çözünürlüğü PPI, yazıcı ayarı DPI, lens sıklığı LPI alanlarıyla ayrı saklanır. Raster boyutu ve dosyadan hesaplanan fiziksel boyut ayrıca raporlanır.', ['project.json','print/print-report.json'],{'settings':{k:project['print'][k] for k in ['width_mm','height_mm','ppi','printer_dpi','nominal_lpi','effective_lpi','ne']},'raster_size':report['raster_size'],'physical_size_mm':report['physical_size_mm'],'pixels_per_lens':report['pixels_per_lens']}),
('Lens yönü, faz, eğim ve aynalama','Baskı ayarlarında lens yönü, faz, eğim, görünüş sırası ve bütün görüntünün aynalanması ayrı alanlardır. Eğitim örneği, bu alanları kaynak adlarıyla eşleştirmeyi sağlar.', ['project.json'],{k:project['print'][k] for k in ['axis','phase','tilt_deg','reverse_views','mirror','fit','stripe_sampling']}),
('Pitch testi','Pitch test kaydı bir aday LPI dizisi ve PPI bilgisi içerir. Üretim notları testi aynı lens/yazıcı/RIP/malzeme ve bakış koşullarında, gerçek ölçekte kullanmayı tarif eder.', ['print/pitch-test.json','print/print-report.json'],{'candidate_lpi':raw['print/pitch-test.json']['candidate_lpi'],'ppi':raw['print/pitch-test.json']['ppi'],'printing_instructions':report['printing_instructions']}),
('Lens kanal yanıtı şeması','Yanıt şablonunda satır gözlenen bakış açısı, sütun basılan kanaldır. template_only alanı şablon verisini ölçüm verisinden ayırır. Bu yapı kalibrasyon bilgisinin dosyada nasıl temsil edildiğini öğretir.', ['print/lens-response-template.json'],{'template_only':raw['print/lens-response-template.json']['template_only'],'rows':raw['print/lens-response-template.json']['rows'],'columns':raw['print/lens-response-template.json']['columns']}),
('Renk ve beyaz alt baskı alanları','Renk modu, ICC profil yolu, renk profili hash kaydı ve beyaz alt baskı seçeneği ayrı taşınır. Beyaz çıktı kullanıldığında RIP bağlantısı, üretim notunda ayrı maske olarak tarif edilir.', ['project.json','print/print-report.json'],{'color_mode':project['print']['color_mode'],'icc_path':project['print']['icc_path'],'white_underbase':project['print']['white_underbase'],'color_profile_sha256':report['color_profile_sha256'],'white_ink_instructions':report['white_ink_instructions']}),
('Önizleme ve işlem durumu kayıtları','Önizleme dosyaları, benzetim ölçüleri ve üretim durumu ayrı kayıt türleridir. Bunları anlamları değişmeden okumak yazılım kullanım eğitiminin bir parçasıdır.', ['print/print-report.json'],{'status':report['status'],'simulation_error':report['simulation_error'],'ideal_print_depth_estimate':report['ideal_print_depth_estimate']}),
('Kaynak ve çıktı izlenebilirliği','Kaynak fotoğraf/derinlik hash değerleri, iş kaydı hash değeri ve üretilen TIFF hash değeri farklı aşamalar arasındaki bağı izlemek için saklanır.', ['project.json','render/job.json','print/print-report.json'],{'source_photo_sha256':project['source_sha256'],'source_job_sha256':report['source_job_sha256'],'interlaced_sha256':report['interlaced_sha256']}),
]
lessons=[]
for i,(title,content,refs,example) in enumerate(topics,1):
    lessons.append({'id':f'LEN2-LOCAL-{i:03}','topic':title,'educational_content':content,'source_files':refs,'source_sha256':{r:before[r] for r in refs},'example_values':example,'example_scope':'Bu dosyadaki örnek iş; evrensel varsayılan veya kalite kararı değildir.','purpose':'general_lenticular_and_software_education'})
jsonl('yerel_bilgi_kartlari.jsonl',lessons)
chunks=[json.loads(s) for s in (PACK/'rag/chunks.jsonl').read_text(encoding='utf-8').splitlines()]
manifest=[json.loads(s) for s in (PACK/'sources/manifest.jsonl').read_text(encoding='utf-8').splitlines()]
web_sources={s['source_id']:s for s in manifest if s['source_id'].startswith('web:')}
web=[]
for c in chunks:
    if c['source_id'] in web_sources:
        s=web_sources[c['source_id']]
        if c['source_id'] in {'web:peft-quantization','web:transformers-gguf'}:continue
        web.append({'source_id':s['source_id'],'title':s['title'],'url':s['url'],'accessed':s['accessed'],'educational_summary':c['text'],'full_text_copied':False})
jsonl('cevrimici_bilgi_kartlari.jsonl',web)
text=['# len 2 — Genel lentiküler ve yazılım eğitim içeriği','',
'Bu içerik kullanıcının gösterdiği çalışma klasöründen bilgi çıkarmak için hazırlanmıştır. Yazılım veya görsel çıktı düzeltme görevi değildir. Önceki dil modeli kurulum yorumu bu çalışma için geçerli değildir.','',
'Kaynak: `'+str(SRC)+'`','',
f'Klasördeki {len(files)} dosyanın görev haritası, dokuz JSON kaydının kaynak kopyası, {len(lessons)} yerel bilgi kartı ve {len(web)} lentiküler/görüntü işleme çevrim içi kaynak notu bu dizindedir. Kaynak dosyalar değiştirilmedi.','',
'## Dosyalar','',
'- `dosya_haritasi.json`: dosyaların hangi aşamaya ait olduğu ve seçilen kayıtların hash bilgileri.',
'- `kaynak_kayitlari.json`: kaynak JSON içerikleri; sayısal örnekler kendi bağlamında korunur.',
'- `yerel_bilgi_kartlari.jsonl`: açıklama, kaynak dosya ve örnek değerlerden oluşan eğitim içeriği.',
'- `cevrimici_bilgi_kartlari.jsonl`: daha önce araştırılmış birincil kaynakların özgün kısa özetleri; internetin tamamı değildir.','',
'## Bu klasörden çıkarılan bilgi','']
for x in lessons:
    text += ['### '+x['topic'],'',x['educational_content'],'','Kaynak: '+', '.join('`'+r+'`' for r in x['source_files'])+'.','']
text += ['## Çevrim içi kaynaklarla bağlantı','',
'Pitch ve üretim akışı için DP Lenticular ve Triaxes; renk profili için ICC; katmanlı derinlik için Shih ve arkadaşları; alfa/ön plan için PyMatting; ara kareler için RIFE; lens tasarımı araştırması için Disney Research notları birlikte kullanılabilir. Bu kaynakların kendi yöntemleri, bu eski işin motorunda kurulu özellikler gibi sunulmaz.','',
'Buradaki amaç alan bilgisini ve yazılım işleyişini kaynaklı biçimde derlemektir. Model adı, GPU veya ağırlık eğitimi bu içerik derleme aşamasının ön şartı değildir.','']
(OUT/'OKU.md').write_text('\n'.join(text),encoding='utf-8')
save('dogrulama.json',{'local_knowledge_cards':len(lessons),'web_knowledge_cards':len(web),'source_json_records':len(raw),'all_source_records_unchanged':all(digest(SRC/r)==before[r] for r in names),'software_modified':False,'print_outputs_modified':False,'visual_correction_performed':False})
# Correct the entry point without deleting the earlier deliverables.
entry=PACK/'len 2.md'
old=entry.read_text(encoding='utf-8')
marker='> **Kapsam düzeltmesi — 10 Ekim 2026:** Kullanıcının amacı bu klasördeki lentiküler/yazılım bilgisini genel eğitim içeriği olarak derlemektir. Güncel içerik [egitim_icerigi/OKU.md](egitim_icerigi/OKU.md) içindedir. Aşağıdaki dil modeli hazırlık planı önceki yanlış yorumdur; güncel görev planı olarak kullanılmamalıdır.\n\n'
if not old.startswith('> **Kapsam düzeltmesi'):entry.write_text(marker+old,encoding='utf-8')
job_path=PACK/'training/job_spec.json'
spec=json.loads(job_path.read_text(encoding='utf-8'))
spec['previous_status']=spec['status'];spec['status']='SUPERSEDED_BY_GENERAL_EDUCATIONAL_CONTENT_REQUEST'
spec['active_content']='egitim_icerigi/OKU.md'
job_path.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
package_files=[p for p in PACK.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='package_manifest.json']
(PACK/'checks/package_manifest.json').write_text(json.dumps([{'path':p.relative_to(PACK).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(package_files)],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'local_cards':len(lessons),'online_cards':len(web),'source_records_unchanged':all(digest(SRC/r)==before[r] for r in names),'entry':str(OUT/'OKU.md')},ensure_ascii=False))
