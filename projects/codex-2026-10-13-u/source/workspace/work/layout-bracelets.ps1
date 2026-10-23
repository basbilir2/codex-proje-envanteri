$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$sourceFile='C:\Users\USER\Downloads\YARIŞÇI BİLEKLİK2.cdr.zip'
$workFile='C:\Users\USER\Documents\Codex\2026-10-13\u\work\bracelet-working.cdr'
$final='C:\Users\USER\Documents\Codex\2026-10-13\u\outputs\Yarisci_Bileklik_001-250_59cm.cdr'
if(Test-Path -LiteralPath $final){throw 'Output already exists'}
$source=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $sourceFile){$source=$d}}
if(!$source -or $source.Dirty){throw 'Source state changed'}
$sourceHash=(Get-FileHash -LiteralPath $sourceFile).Hash
if($sourceHash -ne (Get-FileHash -LiteralPath 'C:\Users\USER\Documents\Codex\2026-10-13\u\work\source-original.cdr').Hash){throw 'Backup mismatch'}
$current=$app.ActiveDocument
if($current.FullFileName -eq $workFile){$current.Close()}
$doc=$app.OpenDocument($workFile)
$page=$doc.ActivePage
if($page.Shapes.Count -ne 22){throw 'Unexpected source structure'}
$slots=@()
foreach($i in @(3,7,12,16)){
 $s=$page.Shapes.Item($i)
 if($s.Type -ne 3 -or $s.Curve.Nodes.Count -ne 53){throw 'Number identification failed'}
 $slots += [pscustomobject]@{Shape=$s;W=$s.SizeWidth;H=$s.SizeHeight;CX=$s.CenterX;CY=$s.CenterY;Rotation=$s.RotationAngle;Color=$s.Fill.UniformColor}
}
$background=$page.Shapes.Item(22)
$outline=[double]$background.Outline.Width
$w=[double]$background.SizeWidth;$h=[double]$background.SizeHeight
$pitchX=$w+$outline;$pitchY=$h+$outline;$margin=$outline/2
$pageWidth=590.0/25.4
$cols=[int][Math]::Floor(($pageWidth-$outline+$outline)/$pitchX)
$rows=[int][Math]::Ceiling(250.0/$cols)
if($cols -ne 29 -or $rows -ne 9){throw 'Layout geometry mismatch'}
$doc.BeginCommandGroup('250 bileklik - dört numara - 59 cm')
$app.Optimization=$true
try{
 $slotIndex=0
 foreach($slot in $slots){
  $slotIndex++
  $text=$doc.ActiveLayer.CreateArtisticText(0,0,'001',0,0,'Arial Black',12,0,0)
  $text.Name='Numara_'+$slotIndex
  $text.SetSize($slot.W,$slot.H)
  $text.Rotate($slot.Rotation%360)
  $text.Fill.ApplyUniformFill($slot.Color)
  $text.Outline.SetNoOutline()
  $text.Move($slot.CX-$text.CenterX,$slot.CY-$text.CenterY)
  $slot.Shape.Delete()
 }
 if($page.Shapes.Count -ne 22){throw 'Number replacement structure mismatch'}
 $base=$page.Shapes.All().Group();$base.Name='Bileklik_001'
 $baseNumbers=@()
 for($j=1;$j -le $base.Shapes.Count;$j++){$s=$base.Shapes.Item($j);if($s.Type -eq 6){$baseNumbers += [pscustomobject]@{Name=$s.Name;DX=$s.CenterX-$base.LeftX;DY=$base.TopY-$s.CenterY;Rotation=$s.RotationAngle;Font=$s.Text.Story.Font;Color=$s.Fill.UniformColor.ToString()}}}
 if($baseNumbers.Count -ne 4){throw 'Four number slots not found'}
 $page.SetSize($pageWidth,$rows*$h+($rows-1)*$outline+2*$margin)
 $left=$page.LeftX+$margin;$top=$page.TopY-$margin
 $base.Move($left-$base.LeftX,$top-$base.TopY)
 for($n=2;$n -le 250;$n++){
  $label=$n.ToString('000');$g=$base.Duplicate(0,0);$g.Name='Bileklik_'+$label
  for($j=1;$j -le $g.Shapes.Count;$j++){
   $s=$g.Shapes.Item($j)
   if($s.Type -eq 6){$cx=$s.CenterX;$cy=$s.CenterY;$s.Text.Story.Text=$label;$s.Move($cx-$s.CenterX,$cy-$s.CenterY)}
  }
  $col=($n-1)%$cols;$row=[int][Math]::Floor(($n-1)/$cols)
  $g.Move($left+$col*$pitchX-$g.LeftX,$top-$row*$pitchY-$g.TopY)
 }
 $doc.ClearSelection()
}finally{$app.Optimization=$false;$doc.EndCommandGroup();$app.Refresh()}
$labels=@();$totalNumbers=0
for($i=1;$i -le $page.Shapes.Count;$i++){
 $g=$page.Shapes.Item($i);$label=$g.Name.Substring(9);$n=[int]$label
 if($g.Type -ne 7 -or $g.Shapes.Count -ne 22 -or $label -ne $n.ToString('000')){throw 'Group structure mismatch'}
 $col=($n-1)%$cols;$row=[int][Math]::Floor(($n-1)/$cols)
 if([Math]::Abs($g.LeftX-($left+$col*$pitchX)) -gt 0.00005 -or [Math]::Abs($g.TopY-($top-$row*$pitchY)) -gt 0.00005){throw "Position mismatch $label"}
 if([Math]::Abs($g.SizeWidth-$w) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$h) -gt 0.00005){throw "Artwork size mismatch $label"}
 if($g.LeftX-$margin -lt $page.LeftX-0.00005 -or $g.RightX+$margin -gt $page.RightX+0.00005 -or $g.BottomY-$margin -lt $page.BottomY-0.00005 -or $g.TopY+$margin -gt $page.TopY+0.00005){throw "Page overflow $label"}
 $textCount=0
 for($j=1;$j -le $g.Shapes.Count;$j++){
  $s=$g.Shapes.Item($j)
  if($s.Type -eq 6){
   $textCount++;$totalNumbers++
   $slot=@($baseNumbers | Where-Object Name -eq $s.Name)[0]
   if($s.Text.Story.Text -ne $label -or $s.Text.Story.Font -ne 'Arial Black' -or [Math]::Abs($s.RotationAngle-$slot.Rotation) -gt 0.00001 -or $s.Fill.UniformColor.ToString() -ne $slot.Color){throw "Number content or style mismatch $label"}
   if([Math]::Abs(($s.CenterX-$g.LeftX)-$slot.DX) -gt 0.00005 -or [Math]::Abs(($g.TopY-$s.CenterY)-$slot.DY) -gt 0.00005){throw "Number position mismatch $label"}
   if($s.SizeWidth -gt 0.60 -or $s.SizeHeight -gt 0.11){throw "Number exceeds white box $label"}
  }
 }
 if($textCount -ne 4){throw "Not four numbers in $label"}
 $labels+=$label
}
if($page.Shapes.Count -ne 250 -or $totalNumbers -ne 1000 -or (($labels|Sort-Object)-join ',') -ne ((1..250|ForEach-Object{$_.ToString('000')})-join ',')){throw 'Count or sequence mismatch'}
$doc.SaveAs($final,$app.CreateStructSaveAsOptions())
if($doc.Dirty -or !(Test-Path -LiteralPath $final)){throw 'Save failed'}
if($source.Dirty -or (Get-FileHash -LiteralPath $sourceFile).Hash -ne $sourceHash){throw 'Source integrity mismatch'}
$doc.ActiveWindow.ActiveView.ToFitPage()
[pscustomobject]@{File=$final;Count=250;NumberCount=$totalNumbers;Columns=$cols;Rows=$rows;LastRow=250%$cols;PageWidthCM=$page.SizeWidth*2.54;PageHeightCM=$page.SizeHeight*2.54;ArtworkWidthCM=$w*2.54;ArtworkHeightCM=$h*2.54;ContentWidthCM=($cols*$w+($cols-1)*$outline+$outline)*2.54;SourcePreserved=$true;Saved=$true}|ConvertTo-Json | Tee-Object -FilePath 'C:\Users\USER\Documents\Codex\2026-10-13\u\work\layout-result.json'
