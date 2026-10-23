$ErrorActionPreference='Stop'
$corel=New-Object -ComObject 'CorelDRAW.Application.17'
$doc=$corel.ActiveDocument
$expected='C:\Users\USER\Documents\Codex\2026-10-12\u\outputs\TMF_001-250_128cm.cdr'
if($doc.FullFileName -ne $expected -or $doc.Dirty -or $doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 250){throw 'Açık dosya beklenen durumda değil'}
$backup='C:\Users\USER\Documents\Codex\2026-10-12\u\work\TMF_before_outline_removal_'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.cdr'
Copy-Item -LiteralPath $expected -Destination $backup
if((Get-FileHash -LiteralPath $expected).Hash -ne (Get-FileHash -LiteralPath $backup).Hash){throw 'Yedek doğrulanamadı'}
$backgrounds=@()
for($i=1;$i -le $doc.ActivePage.Shapes.Count;$i++){
 $g=$doc.ActivePage.Shapes.Item($i)
 if([int]$g.Type -ne 7 -or $g.Shapes.Count -ne 6){throw 'Grup yapısı beklenenden farklı'}
 $s=$g.Shapes.Item(6)
 if([int]$s.Type -ne 1 -or [Math]::Abs($s.SizeWidth*25.4-148.4479) -gt 0.001 -or [Math]::Abs($s.SizeHeight*25.4-96.6366) -gt 0.001){throw 'Dış dikdörtgen doğrulanamadı'}
 $backgrounds+=,$s
}
$doc.BeginCommandGroup('Dış kenar çizgilerini kaldır')
$corel.Optimization=$true
try {
 foreach($s in $backgrounds){$s.Outline.SetNoOutline()}
} finally {
 $corel.Optimization=$false
 $doc.EndCommandGroup()
}
foreach($s in $backgrounds){if([int]$s.Outline.Type -ne 0){throw 'Çizgi kaldırma doğrulanamadı'}}
$doc.Save()
$corel.ActiveWindow.ActiveView.ToFitPage()
$corel.Refresh()
[pscustomobject]@{File=$doc.FullFileName;Removed=$backgrounds.Count;Count=$doc.ActivePage.Shapes.Count;Saved=(-not $doc.Dirty);WidthCM=$doc.ActivePage.SizeWidth*2.54;HeightCM=$doc.ActivePage.SizeHeight*2.54} | ConvertTo-Json
