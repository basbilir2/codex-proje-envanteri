$ErrorActionPreference = 'Stop'
$taskDeps = Join-Path $PSScriptRoot '.deps'
$taskDestination = Join-Path $taskDeps 'rife-ncnn-vulkan-20221029'
$taskExecutable = Join-Path $taskDestination 'rife-ncnn-vulkan-20221029-windows\rife-ncnn-vulkan.exe'
if (Test-Path -LiteralPath $taskDestination) {
    if ((Test-Path -LiteralPath $taskExecutable) -and
        (Test-Path -LiteralPath (Join-Path $taskDestination 'rife-ncnn-vulkan-20221029-windows\rife-v4.6\flownet.bin'))) {
        Write-Host 'Yerel RIFE zaten kurulu; mevcut dosyalara dokunulmadı.'
        exit 0
    }
    throw 'Kurulum klasörü mevcut ama eksik. Mevcut dosyalar korunarak işlem durduruldu.'
}
New-Item -ItemType Directory -Path $taskDeps -Force | Out-Null
$taskArchive = Join-Path $taskDeps 'rife-ncnn-vulkan-20221029-windows.zip'
if (-not (Test-Path -LiteralPath $taskArchive)) {
    Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/rife-ncnn-vulkan-20221029-windows.zip' -OutFile $taskArchive
}
$taskExpected = 'D8E4D772D26CD8006EF0AD0BC82EB191B53C68677D1AE2F42506D74CBBBEA606'
if ((Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash -ne $taskExpected) {
    throw 'Resmi RIFE arşivi doğrulanamadı; çalıştırılmadı ve mevcut dosyalar korunuyor.'
}
Expand-Archive -LiteralPath $taskArchive -DestinationPath $taskDestination
if (-not (Test-Path -LiteralPath $taskExecutable)) { throw 'RIFE çıkarma sonrası doğrulanamadı.' }
Write-Host 'RIFE 4.6 yerel motoru hazır. Lenticular Studio ekranında Animasyon seçin.'
