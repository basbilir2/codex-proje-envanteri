$ErrorActionPreference='Stop'
$corel=New-Object -ComObject 'CorelDRAW.Application.17'
$doc=$corel.ActiveDocument
$final='C:\Users\USER\Documents\Codex\2026-10-12\u\outputs\TMF_001-250_128cm.cdr'
if($doc.Name -ne 'TMF-dizilim.cdr' -or $doc.ActivePage.Shapes.Count -ne 250 -or (Test-Path -LiteralPath $final)){throw 'Kayıt ön koşulu başarısız'}
$opt=$corel.CreateStructSaveAsOptions()
$doc.SaveAs($final,$opt)
if($doc.Dirty -or (Get-Item -LiteralPath $final).Length -eq 0){throw 'Kayıt doğrulanamadı'}
$doc.Close()
$doc=$corel.OpenDocument($final)
if($doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 250){throw 'Yeniden açma doğrulaması başarısız'}
$found=@{}
for($i=1;$i -le $doc.ActivePage.Shapes.Count;$i++){
 $g=$doc.ActivePage.Shapes.Item($i)
 if($g.Name -in @('TMF_001','TMF_008','TMF_009','TMF_249','TMF_250')){
  for($j=1;$j -le $g.Shapes.Count;$j++){
   $s=$g.Shapes.Item($j)
   if([int]$s.Type -eq 6 -and $s.Text.Story.Text -match '^\d{3}$'){$found[$g.Name]=$s.Text.Story.Text}
  }
 }
}
if($found.Count -ne 5){throw 'Kontrol örnekleri eksik'}
foreach($key in $found.Keys){if($key -ne ('TMF_'+$found[$key])){throw 'Kayıtlı numara eşleşmesi hatası'}}
$sourceHash=(Get-FileHash -LiteralPath 'C:\Users\USER\Downloads\aassa.cdr.zip' -Algorithm SHA256).Hash
if($sourceHash -ne (Get-Content -LiteralPath 'C:\Users\USER\Documents\Codex\2026-10-12\u\work\source-sha256.txt').Trim()){throw 'Kaynak dosya değişti'}
$doc.ClearSelection()
for($i=1;$i -le $doc.ActivePage.Shapes.Count;$i++){
 $g=$doc.ActivePage.Shapes.Item($i)
 if($g.Name -in @('TMF_249','TMF_250')){$g.Selected=$true}
}
$corel.ActiveWindow.ActiveView.ToFitSelection()
$doc.ClearSelection()
$corel.Refresh()
[pscustomobject]@{Saved=$true;Reopened=$true;File=$doc.FullFileName;Bytes=(Get-Item -LiteralPath $final).Length;Pages=$doc.Pages.Count;Count=$doc.ActivePage.Shapes.Count;WidthCM=$doc.ActivePage.SizeWidth*2.54;HeightCM=$doc.ActivePage.SizeHeight*2.54;Samples=$found;SourceUnchanged=$true} | ConvertTo-Json
