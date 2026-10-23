$ErrorActionPreference='Stop'
$corel=New-Object -ComObject 'CorelDRAW.Application.17'
$final='C:\Users\USER\Documents\Codex\2026-10-12\u\outputs\Operator_001-250_128cm.cdr'
$doc=$corel.OpenDocument($final)
if($doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 250){throw 'Kayıtlı dosya doğrulanamadı'}
$doc.Activate()
$doc.ClearSelection()
$found=@()
for($i=1;$i -le $doc.ActivePage.Shapes.Count;$i++){
 $g=$doc.ActivePage.Shapes.Item($i)
 if($g.Name -in @('Operator_249','Operator_250')){
  if([int]$g.Shapes.Item(20).Outline.Type -ne 1){throw 'Kayıtlı dış çizgi eksik'}
  $num=$g.Shapes.Item(17).Text.Story.Text
  if($g.Name -ne ('Operator_'+$num)){throw 'Kayıtlı son numara hatalı'}
  $found+=$num; $g.Selected=$true
 }
}
if($found.Count -ne 2){throw 'Son numaralar bulunamadı'}
$corel.ActiveWindow.ActiveView.ToFitSelection()
$doc.Activate()
$doc.ClearSelection()
$corel.Refresh()
[pscustomobject]@{Reopened=$true;Count=$doc.ActivePage.Shapes.Count;LastNumbers=$found;Outlines=$true} | ConvertTo-Json


