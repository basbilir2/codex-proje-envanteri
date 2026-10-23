$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$groups=@{}
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -like '*59cm.cdr'){$doc=$d};if($d.FullFileName -like '*.zip'){$source=$d}}
for($i=1;$i -le $doc.ActivePage.Shapes.Count;$i++){$g=$doc.ActivePage.Shapes.Item($i);$groups[$g.Name.Substring(9)]=$g}
function Compare-Artwork($a,$b,$ax,$ay,$bx,$by){
 if($a.Type -ne $b.Type -or [Math]::Abs($a.SizeWidth-$b.SizeWidth) -gt 0.00005 -or [Math]::Abs($a.SizeHeight-$b.SizeHeight) -gt 0.00005 -or [Math]::Abs(($a.LeftX-$ax)-($b.LeftX-$bx)) -gt 0.00005 -or [Math]::Abs(($ay-$a.TopY)-($by-$b.TopY)) -gt 0.00005){throw 'Artwork geometry changed'}
 if($a.Type -eq 7){if($a.Shapes.Count -ne $b.Shapes.Count){throw 'Artwork group changed'};for($k=1;$k -le $a.Shapes.Count;$k++){Compare-Artwork $a.Shapes.Item($k) $b.Shapes.Item($k) $ax $ay $bx $by}}
 if($a.Type -eq 3){
  if($a.Curve.Nodes.Count -ne $b.Curve.Nodes.Count -or $a.Curve.SubPaths.Count -ne $b.Curve.SubPaths.Count -or $a.Fill.Type -ne $b.Fill.Type -or $a.Fill.UniformColor.ToString() -ne $b.Fill.UniformColor.ToString() -or $a.Outline.Type -ne $b.Outline.Type -or [Math]::Abs($a.Outline.Width-$b.Outline.Width) -gt 0.000001){[pscustomobject]@{OriginalNodes=$a.Curve.Nodes.Count;SavedNodes=$b.Curve.Nodes.Count;OriginalPaths=$a.Curve.SubPaths.Count;SavedPaths=$b.Curve.SubPaths.Count;OriginalColor=$a.Fill.UniformColor.ToString();SavedColor=$b.Fill.UniformColor.ToString();OriginalOutline=$a.Outline.Type;SavedOutline=$b.Outline.Type;OriginalWidth=$a.Outline.Width;SavedWidth=$b.Outline.Width}|ConvertTo-Json;throw 'Curve or color changed'}
  for($k=1;$k -le $a.Curve.Nodes.Count;$k++){$pa=$a.Curve.Nodes.Item($k);$pb=$b.Curve.Nodes.Item($k);if([Math]::Abs(($pa.PositionX-$ax)-($pb.PositionX-$bx)) -gt 0.00005 -or [Math]::Abs(($ay-$pa.PositionY)-($by-$pb.PositionY)) -gt 0.00005){throw 'Curve point changed'}}
 }
}
$sourceBg=$source.ActivePage.Shapes.Item(22)
foreach($label in @('001','002','250')){
 $g=$groups[$label];$targetShapes=@();for($j=1;$j -le 22;$j++){$s=$g.Shapes.Item($j);if($s.Type -ne 6){$targetShapes+=$s}}
 foreach($j in 1..22){if($j -in @(3,7,12,16)){continue};$a=$source.ActivePage.Shapes.Item($j);$candidates=@($targetShapes|Where-Object{[Math]::Abs(($_.LeftX-$g.LeftX)-($a.LeftX-$sourceBg.LeftX)) -lt 0.00005 -and [Math]::Abs(($g.TopY-$_.TopY)-($sourceBg.TopY-$a.TopY)) -lt 0.00005});if($candidates.Count -ne 1){throw 'Artwork match not unique'};Compare-Artwork $a $candidates[0] $sourceBg.LeftX $sourceBg.TopY $g.LeftX $g.TopY}
}
