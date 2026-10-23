$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$final='C:\Users\USER\Documents\Codex\2026-10-13\u\outputs\Yarisci_Bileklik_001-250_59cm.cdr'
$opened=$null;$source=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $final){$opened=$d};if($d.FullFileName -eq 'C:\Users\USER\Downloads\YARIŞÇI BİLEKLİK2.cdr.zip'){$source=$d}}
if(!$opened -or $opened.Dirty){throw 'Saved output not ready'}
$opened.Close()
$null=$app.OpenDocument($final)
$doc=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $final){$doc=$d}}
if(!$doc -or $doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 250){throw 'Reopened document count mismatch'}
$page=$doc.ActivePage;$labels=@();$textCount=0;$groups=@{}
$first=$page.Shapes.Item(1);$textIndices=@();$borderIndex=0
for($j=1;$j -le $first.Shapes.Count;$j++){$s=$first.Shapes.Item($j);if($s.Type -eq 6){$textIndices+=$j};if($s.Type -eq 3 -and [Math]::Abs($s.SizeHeight-250.0/25.4) -lt 0.00005){$borderIndex=$j}}
if($textIndices.Count -ne 4 -or !$borderIndex){throw 'Expected slots missing'}
for($i=1;$i -le 250;$i++){
 $g=$page.Shapes.Item($i);$label=$g.Name.Substring(9);$n=[int]$label;$groups[$label]=$g
 if($g.Type -ne 7 -or $g.Shapes.Count -ne 22 -or $label -ne $n.ToString('000')){throw 'Group mismatch'}
 $count=0;$borderCount=0
 foreach($j in $textIndices){
  $s=$g.Shapes.Item($j)
  if($s.Type -eq 6){if($s.Text.Story.Text -ne $label){throw "Label mismatch $label"};$count++;$textCount++}
 }
 $border=$g.Shapes.Item($borderIndex)
 if($border.Type -ne 3 -or $border.Outline.Type -ne 1 -or [Math]::Abs($border.Outline.Width-0.2/25.4) -gt 0.000001){throw 'Border changed'}
 if($count -ne 4){throw 'Number count mismatch'}
 $labels+=$label
}
if($textCount -ne 1000 -or (($labels|Sort-Object)-join ',') -ne ((1..250|ForEach-Object{$_.ToString('000')})-join ',')){throw 'Sequence mismatch'}
function Compare-Artwork($a,$b,$ax,$ay,$bx,$by){
 if($a.Type -ne $b.Type -or [Math]::Abs($a.SizeWidth-$b.SizeWidth) -gt 0.00005 -or [Math]::Abs($a.SizeHeight-$b.SizeHeight) -gt 0.00005 -or [Math]::Abs(($a.LeftX-$ax)-($b.LeftX-$bx)) -gt 0.00005 -or [Math]::Abs(($ay-$a.TopY)-($by-$b.TopY)) -gt 0.00005){throw 'Artwork geometry changed'}
 if($a.Type -eq 7){if($a.Shapes.Count -ne $b.Shapes.Count){throw 'Artwork group changed'};for($k=1;$k -le $a.Shapes.Count;$k++){Compare-Artwork $a.Shapes.Item($k) $b.Shapes.Item($k) $ax $ay $bx $by}}
 if($a.Type -eq 3){
  if($a.Curve.Nodes.Count -ne $b.Curve.Nodes.Count -or $a.Curve.SubPaths.Count -ne $b.Curve.SubPaths.Count -or $a.Fill.Type -ne $b.Fill.Type -or $a.Fill.UniformColor.ToString() -ne $b.Fill.UniformColor.ToString() -or $a.Outline.Type -ne $b.Outline.Type -or [Math]::Abs($a.Outline.Width-$b.Outline.Width) -gt 0.000001){throw 'Curve or color changed'}
  for($k=1;$k -le $a.Curve.Nodes.Count;$k++){$pa=$a.Curve.Nodes.Item($k);$pb=$b.Curve.Nodes.Item($k);if([Math]::Abs(($pa.PositionX-$ax)-($pb.PositionX-$bx)) -gt 0.00005 -or [Math]::Abs(($ay-$pa.PositionY)-($by-$pb.PositionY)) -gt 0.00005){throw 'Curve point changed'}}
 }
}
$sourceBg=$source.ActivePage.Shapes.Item(22)
foreach($label in @('001','002','250')){
 $g=$groups[$label];$targetShapes=@();for($j=1;$j -le 22;$j++){$s=$g.Shapes.Item($j);if($s.Type -ne 6){$targetShapes+=$s}}
 foreach($j in 1..22){if($j -in @(3,7,12,16)){continue};$a=$source.ActivePage.Shapes.Item($j);$candidates=@($targetShapes|Where-Object{[Math]::Abs(($_.LeftX-$g.LeftX)-($a.LeftX-$sourceBg.LeftX)) -lt 0.00005 -and [Math]::Abs(($g.TopY-$_.TopY)-($sourceBg.TopY-$a.TopY)) -lt 0.00005});if($candidates.Count -ne 1){throw 'Artwork match not unique'};Compare-Artwork $a $candidates[0] $sourceBg.LeftX $sourceBg.TopY $g.LeftX $g.TopY}
}
if($source.Dirty -or (Get-FileHash -LiteralPath $source.FullFileName).Hash -ne (Get-FileHash -LiteralPath 'C:\Users\USER\Documents\Codex\2026-10-13\u\work\source-original.cdr').Hash){throw 'Source changed'}
$doc.Activate();$doc.ClearSelection();$doc.ActiveWindow.ActiveView.ToFitPage()
[pscustomobject]@{ReopenedFile=$doc.FullFileName;Groups=250;Numbers=1000;Sequence='001-250';FourPerGroup=$true;ArtworkCurvesColorsAndBordersVerified=$true;SourcePreserved=$true;WidthCM=$page.SizeWidth*2.54;HeightCM=$page.SizeHeight*2.54;SavedClean=(!$doc.Dirty)}|ConvertTo-Json | Tee-Object -FilePath 'C:\Users\USER\Documents\Codex\2026-10-13\u\work\reopen-verification.json'
