param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$sha256 = [System.Security.Cryptography.SHA256]::Create()
function Get-Sha256Hex([byte[]]$Bytes) { ([BitConverter]::ToString($sha256.ComputeHash($Bytes))).Replace('-', '') }
$basePath = Join-Path $Root 'BTakip_Dijital_Kopya_v1.5.30.json'
$outPath = Join-Path $Root 'BTakip_Dijital_Kopya_v1.5.32.json'
$base = Get-Content -Raw $basePath | ConvertFrom-Json
$old = $base.current_release_additions

$base.document.title = 'BTakip 1.5.32 — tek dosyalık ayrıntılı yazılım bağlamı ve kaynak kopyası'
$base.document.snapshot_date = '2026-09-09'
$base.document.generated_by = 'Codex kaynak incelemesi, sürüm 1.5.32 kaynak envanteri ve otomatik dosya kimliklendirmesi'
$base.identity.current_version = '1.5.32'
$base.identity.assembly_file_version = '1.5.32.0'

$newEmbeddedFiles = @(
    @('BTakip/CloudConfiguration.cs', 'firebase_google_client_configuration', 'C#'),
    @('BTakip/GoogleCloudSyncService.cs', 'account_scoped_firestore_sheets_drive_sync', 'C#'),
    @('firestore.rules', 'firestore_per_user_security_rules', 'Firebase Rules'),
    @('firebase.json', 'firebase_deployment_configuration', 'JSON')
)
foreach ($file in $newEmbeddedFiles) {
    if ($base.embedded_files.relative_path -contains $file[0]) { continue }
    $base.embedded_files += [pscustomobject][ordered]@{
        relative_path = $file[0]; role = $file[1]; language = $file[2]; encoding = 'utf-8-no-bom'
        newline = ''; bytes = 0; lines = 0; sha256 = ''; last_write_utc = ''; exact_content = ''
    }
}

foreach ($entry in $base.embedded_files) {
    $path = Join-Path $Root $entry.relative_path
    if (-not (Test-Path -LiteralPath $path)) { throw "Gömülü kaynak bulunamadı: $($entry.relative_path)" }
    $raw = [System.IO.File]::ReadAllBytes($path)
    $content = [System.IO.File]::ReadAllText($path)
    $entry.bytes = $raw.Length
    $entry.lines = if ($content.Length -eq 0) { 0 } else { ([regex]::Matches($content, "`r`n|`n|`r").Count + 1) }
    $entry.sha256 = Get-Sha256Hex $raw
    $entry.last_write_utc = (Get-Item -LiteralPath $path).LastWriteTimeUtc.ToString('o')
    $entry.exact_content = $content
    $entry.newline = if ($content.Contains("`r`n")) { 'CRLF' } elseif ($content.Contains("`n")) { 'LF' } elseif ($content.Contains("`r")) { 'CR' } else { 'none' }
}

$manifest = (($base.embedded_files | Sort-Object relative_path | ForEach-Object { "$($_.relative_path)`t$($_.sha256)" }) -join "`n") + "`n"
$base.snapshot_integrity.embedded_manifest_sha256 = Get-Sha256Hex ([System.Text.UTF8Encoding]::new($false).GetBytes($manifest))
$base.snapshot_integrity.embedded_file_count = @($base.embedded_files).Count
$base.generated_inventory.embedded_file_count = @($base.embedded_files).Count
$base.generated_inventory.embedded_total_bytes = [long](($base.embedded_files | Measure-Object bytes -Sum).Sum)

$releaseFiles = @(
    @($base.release_baseline.portable, (Join-Path $Root 'TestRuns\release-1.5.32\app\BTakip_Portable.exe'), 'TestRuns/release-1.5.32/app/BTakip_Portable.exe'),
    @($base.release_baseline.setup, (Join-Path $Root 'TestRuns\release-1.5.32\setup\BTakip_Setup.exe'), 'TestRuns/release-1.5.32/setup/BTakip_Setup.exe')
)
foreach ($release in $releaseFiles) {
    $entry = $release[0]; $path = $release[1]
    $entry.relative_path = $release[2]
    $entry.bytes = (Get-Item -LiteralPath $path).Length
    $entry.sha256 = Get-Sha256Hex ([System.IO.File]::ReadAllBytes($path))
    $entry.product_version = (Get-Item -LiteralPath $path).VersionInfo.ProductVersion
    $entry.file_version = (Get-Item -LiteralPath $path).VersionInfo.FileVersion
}
$base.release_baseline.release_date = '2026-09-09'

$base.current_release_additions = [ordered]@{
    version = '1.5.32'
    date = '2026-09-09'
    scope = '1.5.13-1.5.32: mevcut işlevleri koruyan arayüz, fiyat, Excel, bütünlük ve hesap bazlı Firebase/Sheets/Drive senkronu.'
    product_profit_override = $old.product_profit_override
    ledger_measure_updates = $old.ledger_measure_updates
    price_definition_propagation = $old.price_definition_propagation
    external_exports = [ordered]@{
        scope = 'Seçili müşteri, Ctrl ile seçili cari hareketleri, seçili müşteri hesaplarını veya tüm hesapları PDF/Excel olarak dışa aktarır.'
        excel = 'Seçili/tüm hesaplar Hesap Özetleri ve Hareketler sayfalarıyla üretilir.'
    }
    safe_standard_excel_import = [ordered]@{
        rule = 'Sipariş tutarı boşsa yalnız tek fiyat tanımına birebir eşleşen ve gerekli ölçü/süre bilgisi bulunan satır BTakip motoruyla hesaplanır.'
        unknown = 'Tanım, varyant veya ölçü belirsizse maliyet ve satış boş kalır; tahmin borcu yazılmaz.'
        append_only = 'Mevcut müşteri kartı/fiyat grubu korunur; tam aynı hareket ikinci kez eklenmez.'
    }
    ledger_composite_order = [ordered]@{
        selection = 'Cari sipariş formu bir ana kalem ile isteğe bağlı çoklu ek malzeme, baskı ve hizmet seçimi sunar.'
        calculation = 'Tüm seçilen kalemler Order.Lines içinde tutulur; UV Baskı + Pleksi + kesim gibi birleşik işlerin maliyet ve satışı müşterinin kart fiyat grubuyla hesaplanır.'
        duration = 'Dakika ile hesaplanan hizmetler için Süre (dk) alanı kullanılır.'
        continuity = 'Sipariş kaydedildikten sonra cari tablo yeni satırı seçer ve görünür tutar; ek seçimler sonraki siparişe taşınmaz.'
    }
    product_editor = [ordered]@{
        structure_tabs = "Fiyat tanımı Malzeme, Baskı ve Hizmet yatay sekmeleriyle seçilir. Baskı hazır seçimleri Solvent/UV/DTF; hizmet Lazer Kesim/Sıvama/Diğer; malzeme Branda/Folyo/OWV/Kumlama/Etiket'tir."
        currency = 'TL, USD veya yüzde para/birim seçimi ürünün fiyat giriş panelinde görünür.'
        save = 'Ürün Ekle paneli açar; ekleme ve güncelleme için alt işlem düğmesi Ürünü Kaydet olarak adlandırılır.'
    }
    column_and_context_tools = [ordered]@{
        columns = 'Tüm DataGridView tablolarında başlıktaki küçük simge kolonu gizler; başlığa sağ tıklama gizli kolonlar dahil aç/kapat menüsünü gösterir.'
        price_context = 'Fiyat tablosunda Kopyala, Yapıştır, Güncelle, Ekle ve Sil sağ tık menüsündedir; üstteki Sil düğmesi yoktur.'
        ledger_context = 'Cari tablosunda Kopyala, Yapıştır, Güncelle, Ekle, Sil ve seçili/tüm hesap dışa aktarma sağ tık menüsündedir.'
    }
    one_off_service = [ordered]@{
        behavior = 'Cari sipariş formunda baskı türü, malzeme ve tanımlı hizmetler ayrı seçilir. Diğer hizmet adı ve TL/m² maliyeti yalnız mevcut siparişin Lines kaydına eklenir; fiyat tanımı kataloğuna yazılmaz.'
    }
    cloud_sync = [ordered]@{
        firebase = 'Canlı bulut kopyası Firebase Firestore users/{uid}/records altında tutulur; güvenlik kuralı yalnız oturum açan uid alanına erişim verir.'
        accounts = 'Aynı Google hesabı başka bilgisayarda aynı kayıtları alır. Farklı Google hesabı ayrı Firestore alanı ve ayrı yerel Hesaplar/{uid} klasörü kullanır.'
        sheets = 'BTakip Veri adlı Google Sheets aynası Müşteriler, Fiyat Grupları, Fiyat Tanımları, Siparişler ve Tahsilatlar sayfalarını günceller.'
        drive = 'BTakip Yedekleri klasöründe günlük ve son sürüm AES-GCM şifreli tam yedek tutulur.'
        offline = 'Yerel hesap kopyası çevrimdışı çalışır; bağlantı geldiğinde Firestore ile eşitlenir.'
        owner = 'Firebase projesi btakip-trendybrander; ilk canlı hesap user_0003@example.invalid.'
    }
    data_boundary = 'Bu bağlam dosyası canlı müşteri hareketlerini gömmez. Yerel canlı hesaplar %USERPROFILE%\\btakip\\Hesaplar\\{uid}\\btakip-veri.json altında, bulut canlı kopyası Firestore üzerinde tutulur.'
}

$base.implementation_fidelity_notes = @($base.implementation_fidelity_notes | Where-Object { $_ -notmatch '^1\.5\.(1[3456789]|2[0123456789]|3[012]):' }) + @(
    '1.5.13: Cari/Müşteriler dışa aktarma menüsü seçili müşteri, seçili hareketler, seçili hesaplar ve tüm hesaplar kapsamlarını PDF/Excel olarak sunar.',
    '1.5.14: Standart Siparişler Excel içe aktarımında eksik tutar yalnız tanım ve gerekli ölçü/süre açıkça yeterliyse BTakip motoruyla hesaplanır; belirsiz satır boş bırakılır.',
    '1.5.15: Cari sipariş formu bir ana kalem ile çoklu ek malzeme/baskı/hizmet seçer; yeniden hesaplama, kaydedilen Lines listesindeki birleşik kalemleri korur.',
    '1.5.16: Fiyat tanımları yatay Malzeme/Baskı/Hizmet sekmeleri, görünür TL/USD seçimi ve Ürünü Kaydet akışı kullanır. Tablolarda kolon gizleme araçları ve fiyat/cari sağ tık işlemleri vardır; katalog dışı Diğer hizmet yalnız sipariş satırında saklanır.',
    '1.5.17: Geri Al ana başlıktan kaldırıldı; uygulamanın her sekmesinde erişilebilir durumda tutuldu. Bulut bağlantısı ekranı, Firestore ve Google Drive tabanlı kullanıcı oturumu gerçek olarak hazır olduğunda bağlanacaktır.',
    '1.5.18: Fiyat tanımı seçimi yatay hazır düğmeler yerine açılır liste kullanır. Yalnız Solvent/UV/DTF baskı; yalnız Lazer Kesim/Sıvama hizmettir. Tüm diğer fiyat tanımları malzemedir. Gizlenen kolonlar sabit kolon seçici simgesiyle yeniden görünür yapılabilir.',
    '1.5.19: Açılır fiyat seçimi ekrana bağlandıktan sonra doldurulur; uygulamanın açılışında boş seçim nedeniyle kapanma yaşanmaz.',
    '1.5.20: Malzeme açılır kutusu Malzeme seç metni ve standart küçük okla gösterilir. Kolon görünürlük menüsü kapanırken kendini yok etmez; bu menü kaynaklı uygulama kapanması engellenmiştir.',
    '1.5.21: Geri Al yalnız Müşteriler, Fiyat Tanımları, Cari ve Tahsilat ve Kâr Ayarları sekmelerinde gösterilir; Genel Bakış, Fiyat Hesaplama ve Senkron ve Yedek sekmelerinde gösterilmez.',
    '1.5.22: Geri Al ilgili sekmelerde sağ üstte değil, alt araç alanında solda yer alır.',
    "1.5.23: Pencere kapatma düğmesi BTakip'i görev çubuğundan kaldırır ve sağdaki bildirim alanı simgesine indirir. Simge çift tıklamayla açılır; simge menüsündeki Çıkış uygulamayı tamamen kapatır.",
    "1.5.24: Pencere kapatılırken bildirim alanı simgesi yeniden kaydedilir ve BTakip görev çubuğunda küçültülmüş halde kalır; simge görünmese bile uygulama erişilebilir durumdadır.",
    "1.5.25: Müşteri hesap özetinde dönem toplamları Toplam Borç ve Toplam Tahsilat olarak açıkça etiketlenir; hemen altında Güncel Açık Bakiye ayrıca gösterilir.",
    "1.5.26: Fiyat Hesaplama birden çok ayrı ürün hesabını Ürünü Hesaba Ekle ile tutar; sonraki ürün için form temizlenir ve ürünler birlikte siparişe dönüştürülebilir.",
    "1.5.27: Müşteriye Not Yolla öncesinde açıklama sütunu sorulur; işaretlenmezse hesap özeti açıklama kolonu olmadan üretilir.",
    "1.5.28: Müşteri notu seçeneği açıkça yalnız BTakip Açıklama sütununu anlatır; diğer cari sütunları her durumda korunur.",
    "1.5.29: Fiyat Hesaplama'da Hesabı Sıfırla birikmiş ürünleri, seçili kalemleri, ölçüleri ve sonuçları temizleyerek yeni hesap başlatır.",
    "1.5.30: Duvar Kağıdı Malzeme, Baskes Hizmet olarak sınıflandırılır; cari sipariş baskı seçimine Eco Solvent eklenir ve Baskes hizmet listesinde görünür.",
    '1.5.31: Kurulu uygulama dosyasının sürüm bütünlüğü aynı sürümle farklı dosya kurulumlarında güvenli biçimde doğrulanır.',
    '1.5.32: Google OAuth ile hesap seçilir; Firestore canlı senkronu, Google Sheets aynası, Drive günlük şifreli yedeği ve hesap başına ayrı yerel kayıt birlikte çalışır.'
)

[System.IO.File]::WriteAllText($outPath, ($base | ConvertTo-Json -Depth 100), [System.Text.UTF8Encoding]::new($false))
$check = Get-Content -Raw $outPath | ConvertFrom-Json
Write-Output "JSON=$outPath|VERSION=$($check.identity.current_version)|FILES=$(@($check.embedded_files).Count)|MANIFEST=$($check.snapshot_integrity.embedded_manifest_sha256)"
