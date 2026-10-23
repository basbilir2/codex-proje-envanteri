param()
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$form = New-Object System.Windows.Forms.Form
$form.Text = 'OpenCode - NVIDIA API anahtarı'
$form.Size = New-Object System.Drawing.Size(560,210)
$form.StartPosition = 'CenterScreen'
$label = New-Object System.Windows.Forms.Label
$label.Text = 'NVIDIA Build üzerinden oluşturduğunuz API anahtarını yapıştırın.'
$label.Location = New-Object System.Drawing.Point(20,20)
$label.AutoSize = $true
$form.Controls.Add($label)
$inputBox = New-Object System.Windows.Forms.TextBox
$inputBox.Location = New-Object System.Drawing.Point(20,55)
$inputBox.Width = 500
$inputBox.UseSystemPasswordChar = $true
$form.Controls.Add($inputBox)
$button = New-Object System.Windows.Forms.Button
$button.Text = 'Kaydet'
$button.Location = New-Object System.Drawing.Point(420,100)
$button.DialogResult = [System.Windows.Forms.DialogResult]::OK
$form.Controls.Add($button)
$form.AcceptButton = $button
if ($form.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { exit 2 }
$plainKey = $inputBox.Text.Trim()
if ($plainKey -notmatch '^nvapi-[A-Za-z0-9_-]{20,}$') {
    [System.Windows.Forms.MessageBox]::Show('Geçerli bir nvapi- anahtarı girilmedi. Kaydedilmedi.') | Out-Null
    exit 1
}
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$secretDir = Join-Path $workspace 'work\secrets'
New-Item -ItemType Directory -Force -Path $secretDir | Out-Null
$secureKey = ConvertTo-SecureString $plainKey -AsPlainText -Force
$encrypted = ConvertFrom-SecureString $secureKey
[IO.File]::WriteAllText((Join-Path $secretDir 'nvidia-key.dpapi'), $encrypted)
$inputBox.Clear()
$plainKey = $null
$form.Dispose()
[System.Windows.Forms.MessageBox]::Show('Anahtar bu Windows kullanıcısı için şifrelenerek kaydedildi. Codex sohbetine dönebilirsiniz.') | Out-Null
