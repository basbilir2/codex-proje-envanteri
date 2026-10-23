$projectPath = $PSScriptRoot
Set-Location -LiteralPath $projectPath
Write-Host 'Elmas Apartmani onizleme: http://127.0.0.1:4173'
Write-Host 'Ornek veriler kullanilir. Durdurmak icin Ctrl+C.'
node (Join-Path $projectPath 'preview\server.mjs')
