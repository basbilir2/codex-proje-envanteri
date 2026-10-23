$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$sourceFile='C:\Users\USER\Downloads\misaifr.cdr.zip'
$root='C:\Users\USER\Documents\Codex\2026-10-13\u'
$backup=$root+'\work\misafir-source-original.cdr'
$working=$root+'\work\misafir-working.cdr'
$final=$root+'\outputs\Misafir_Bileklik_001-350_59cm.cdr'
$source=$app.ActiveDocument
if($source.FullFileName -ne $sourceFile -or $source.Dirty -or $source.Pages.Count -ne 1 -or $source.ActivePage.Shapes.Count -ne 30){throw 'Unexpected source state'}
if((Test-Path -LiteralPath $final) -or (Test-Path -LiteralPath $working) -or (Test-Path -LiteralPath $backup)){throw 'Job paths already exist'}
Copy-Item -LiteralPath $sourceFile -Destination $backup
$sourceHash=(Get-FileHash -LiteralPath $sourceFile).Hash
if($sourceHash -ne (Get-FileHash -LiteralPath $backup).Hash){throw 'Backup integrity failed'}
$clone=$source.Clone();$clone.SaveAs($working,$app.CreateStructSaveAsOptions());$clone.Close()
$doc=$app.OpenDocument($working);$page=$doc.ActivePage
$numberIndices=@(15,17,20,22)
$slots=@()
for($i=1;$i -le 30;$i++){
 $s=$page.Shapes.Item($i)
 if($i -in $numberIndices){
  if($s.Type -ne 3 -or $s.Curve.Nodes.Count -ne 53 -or $s.Curve.SubPaths.Count -ne 5){throw 'Number shape mismatch'}
  $slots += [pscustomobject]@{Shape=$s;W=$s.SizeWidth;H=$s.SizeHeight;CX=$s.CenterX;CY=$s.CenterY;Angle=$s.RotationAngle;Color=$s.Fill.UniformColor}
 }else{$s.Name='Artwork_'+$i.ToString('00')}
}
$bg=$page.Shapes.Item(30);$w=[double]$bg.SizeWidth;$h=[double]$bg.SizeHeight;$outline=[double]$bg.Outline.Width
if([Math]::Abs($w*25.4-19.9998) -gt 0.0001 -or [Math]::Abs($h*25.4-250) -gt 0.0001 -or [Math]::Abs($outline*25.4-0.2) -gt 0.0001){throw 'Unexpected dimensions'}
$pitchX=$w+$outline;$pitchY=$h+$outline;$margin=$outline/2;$pageWidth=590.0/25.4
$cols=[int][Math]::Floor($pageWidth/$pitchX);$rows=[int][Math]::Ceiling(350.0/$cols)
if($cols -ne 29 -or $rows -ne 13){throw 'Wrap calculation mismatch'}
$doc.BeginCommandGroup('Misafir 001-350 - 59 cm')
$app.Optimization=$true
try{
 $slotID=0
 foreach($slot in $slots){
  $slotID++;$s=$doc.ActiveLayer.CreateArtisticText(0,0,'001',0,0,'Arial Black',12,0,0)
  $s.Name='Numara_'+$slotID;$s.SetSize($slot.W,$slot.H);$s.Rotate($slot.Angle%360)
  $s.Fill.ApplyUniformFill($slot.Color);$s.Outline.SetNoOutline();$s.Move($slot.CX-$s.CenterX,$slot.CY-$s.CenterY)
  $slot.Shape.Delete()
 }
 $base=$page.Shapes.All().Group();$base.Name='Misafir_001'
 $numberSlots=@();$artworkIndices=@{}
 for($j=1;$j -le $base.Shapes.Count;$j++){
  $s=$base.Shapes.Item($j)
  if($s.Name -like 'Numara_*'){$numberSlots+=[pscustomobject]@{Index=$j;DX=$s.CenterX-$base.LeftX;DY=$base.TopY-$s.CenterY;Angle=$s.RotationAngle}}
  if($s.Name -like 'Artwork_*'){$artworkIndices[$s.Name]=$j}
 }
 if($numberSlots.Count -ne 4 -or $artworkIndices.Count -ne 26 -or $base.Shapes.Count -ne 30){throw 'Number replacement structure mismatch'}
 $page.SetSize($pageWidth,$rows*$h+($rows-1)*$outline+2*$margin)
 $left=$page.LeftX+$margin;$top=$page.TopY-$margin;$base.Move($left-$base.LeftX,$top-$base.TopY)
 for($n=2;$n -le 350;$n++){
  $label=$n.ToString('000');$g=$base.Duplicate(0,0);$g.Name='Misafir_'+$label
  foreach($slot in $numberSlots){$s=$g.Shapes.Item($slot.Index);$cx=$s.CenterX;$cy=$s.CenterY;$s.Text.Story.Text=$label;$s.Move($cx-$s.CenterX,$cy-$s.CenterY)}
  $col=($n-1)%$cols;$row=[int][Math]::Floor(($n-1)/$cols);$g.Move($left+$col*$pitchX-$g.LeftX,$top-$row*$pitchY-$g.TopY)
  if($n%50 -eq 0){Write-Output "Created: $n / 350"}
 }
 $doc.ClearSelection()
}finally{$app.Optimization=$false;$doc.EndCommandGroup();$app.Refresh()}
if($page.Shapes.Count -ne 350){throw 'Copy count mismatch'}
$doc.SaveAs($final,$app.CreateStructSaveAsOptions())
if($doc.Dirty){throw 'Save failed'}
$doc.Close();$null=$app.OpenDocument($final)
$doc=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $final){$doc=$d}}
if(!$doc -or $doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 350){throw 'Reopened file mismatch'}
$page=$doc.ActivePage;$seen=@{};$groups=@{};$totalNumbers=0
$bgIndex=$artworkIndices['Artwork_30']
for($i=1;$i -le 350;$i++){
 $g=$page.Shapes.Item($i);$label=$g.Name.Substring(8);$n=[int]$label
 if($n -lt 1 -or $n -gt 350 -or $label -ne $n.ToString('000') -or $seen.ContainsKey($label) -or $g.Type -ne 7 -or $g.Shapes.Count -ne 30){throw "Group or sequence mismatch: $label"}
 $seen[$label]=$true;$groups[$label]=$g
 $col=($n-1)%$cols;$row=[int][Math]::Floor(($n-1)/$cols)
 if([Math]::Abs($g.LeftX-($left+$col*$pitchX)) -gt 0.00005 -or [Math]::Abs($g.TopY-($top-$row*$pitchY)) -gt 0.00005 -or [Math]::Abs($g.SizeWidth-$w) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$h) -gt 0.00005){throw "Geometry mismatch: $label"}
 if($g.LeftX-$margin -lt $page.LeftX-0.00005 -or $g.RightX+$margin -gt $page.RightX+0.00005 -or $g.TopY+$margin -gt $page.TopY+0.00005 -or $g.BottomY-$margin -lt $page.BottomY-0.00005){throw "Page overflow: $label"}
 foreach($slot in $numberSlots){$s=$g.Shapes.Item($slot.Index);if($s.Type -ne 6 -or $s.Text.Story.Text -ne $label){throw "Number mismatch: $label"};$totalNumbers++}
 $border=$g.Shapes.Item($bgIndex)
 if($border.Outline.Type -ne 1 -or [Math]::Abs($border.Outline.Width-$outline) -gt 0.000001){throw "Border mismatch: $label"}
 if($i%70 -eq 0){Write-Output "Verified: $i / 350"}
}
if($seen.Count -ne 350 -or $totalNumbers -ne 1400){throw 'Final count mismatch'}
function ColorValue($c){$value=$c.ToString();return $value.Substring(0,$value.LastIndexOf(','))}
function CompareArtwork($a,$b,$ax,$ay,$bx,$by){
 if($a.Type -ne $b.Type -or [Math]::Abs($a.SizeWidth-$b.SizeWidth) -gt 0.00005 -or [Math]::Abs($a.SizeHeight-$b.SizeHeight) -gt 0.00005 -or [Math]::Abs(($a.LeftX-$ax)-($b.LeftX-$bx)) -gt 0.00005 -or [Math]::Abs(($ay-$a.TopY)-($by-$b.TopY)) -gt 0.00005){throw 'Artwork geometry mismatch'}
 if($a.Type -eq 7){if($a.Shapes.Count -ne $b.Shapes.Count){throw 'Nested shape count mismatch'};for($k=1;$k -le $a.Shapes.Count;$k++){CompareArtwork $a.Shapes.Item($k) $b.Shapes.Item($k) $ax $ay $bx $by}}
 if($a.Type -eq 3){if($a.Curve.Nodes.Count -ne $b.Curve.Nodes.Count -or $a.Curve.SubPaths.Count -ne $b.Curve.SubPaths.Count -or (ColorValue $a.Fill.UniformColor) -ne (ColorValue $b.Fill.UniformColor) -or $a.Outline.Type -ne $b.Outline.Type -or [Math]::Abs($a.Outline.Width-$b.Outline.Width) -gt 0.000001){throw 'Artwork curve/color mismatch'}}
 if($a.Type -eq 6){if($a.Text.Story.Text -ne $b.Text.Story.Text -or $a.Text.Story.Font -ne $b.Text.Story.Font -or [Math]::Abs($a.Text.Story.Size-$b.Text.Story.Size) -gt 0.00001){throw 'Guest label mismatch'}}
}
$sourceBg=$source.ActivePage.Shapes.Item(30)
foreach($label in @('001','350')){
 $g=$groups[$label]
 foreach($j in 1..30){if($j -in $numberIndices){continue};$a=$source.ActivePage.Shapes.Item($j);$b=$g.Shapes.Item($artworkIndices['Artwork_'+$j.ToString('00')]);CompareArtwork $a $b $sourceBg.LeftX $sourceBg.TopY $g.LeftX $g.TopY}
 foreach($slot in $numberSlots){$s=$g.Shapes.Item($slot.Index);if($s.Text.Story.Font -ne 'Arial Black' -or [Math]::Abs($s.RotationAngle-$slot.Angle) -gt 0.00001 -or [Math]::Abs(($s.CenterX-$g.LeftX)-$slot.DX) -gt 0.00005 -or [Math]::Abs(($g.TopY-$s.CenterY)-$slot.DY) -gt 0.00005){throw 'Number style/position mismatch'}}
}
if($source.Dirty -or (Get-FileHash -LiteralPath $sourceFile).Hash -ne $sourceHash){throw 'Source was changed'}
$doc.Activate();$doc.ClearSelection();$doc.ActiveWindow.ActiveView.ToFitPage();$app.Refresh()
[pscustomobject]@{File=$doc.FullFileName;Reopened=$true;Count=350;Numbers=1400;Columns=$cols;Rows=$rows;LastRow=350%$cols;PageWidthCM=$page.SizeWidth*2.54;PageHeightCM=$page.SizeHeight*2.54;ContentWidthCM=($cols*$w+($cols-1)*$outline+$outline)*2.54;ArtworkPreserved=$true;SourcePreserved=$true;SavedClean=(!$doc.Dirty)}|ConvertTo-Json|Tee-Object -FilePath ($root+'\work\misafir350-result.json')
