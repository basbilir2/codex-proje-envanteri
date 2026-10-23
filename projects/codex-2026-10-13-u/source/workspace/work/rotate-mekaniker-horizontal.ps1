$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$root='C:\Users\USER\Documents\Codex\2026-10-13\u'
$source=$app.ActiveDocument
$sourceFile='C:\Users\USER\Downloads\mekaniker.cdr'
$backup=$root+'\work\mekaniker-vertical-before-horizontal.cdr'
$working=$root+'\work\mekaniker-horizontal-working.cdr'
$final=$root+'\outputs\Mekaniker_Bileklik_001-350_Yatay_59cm.cdr'
if($source.FullFileName -ne $sourceFile -or $source.Dirty -or $source.ActivePage.Shapes.Count -ne 350 -or $source.Pages.Count -ne 1){throw 'Unexpected source document'}
foreach($p in @($backup,$working,$final)){if(Test-Path -LiteralPath $p){throw 'Output path already exists'}}
Copy-Item -LiteralPath $sourceFile -Destination $backup
$sourceHash=(Get-FileHash -LiteralPath $sourceFile).Hash
if($sourceHash -ne (Get-FileHash -LiteralPath $backup).Hash){throw 'Backup mismatch'}
$sourceGroups=@{}
for($i=1;$i -le 350;$i++){$g=$source.ActivePage.Shapes.Item($i);if($g.Type -ne 7 -or $g.Shapes.Count -ne 30 -or $g.Name -notmatch '^Mekaniker_(\d{3})$'){throw 'Unexpected artwork structure'};$label=$Matches[1];if($sourceGroups.ContainsKey($label)){throw 'Repeated group'};$sourceGroups[$label]=$g}
$sample=$sourceGroups['001'];$originalW=$sample.SizeWidth;$originalH=$sample.SizeHeight
$numberIndices=@();$borderIndex=0
for($j=1;$j -le 30;$j++){$s=$sample.Shapes.Item($j);if($s.Name -like 'Numara_*'){$numberIndices+=$j};if($s.Name -eq 'Artwork_30'){$borderIndex=$j}}
if($numberIndices.Count -ne 4 -or !$borderIndex){throw 'Number slots not identified'}
$outline=[double]$sample.Shapes.Item($borderIndex).Outline.Width
$w=[double]$originalH;$h=[double]$originalW;$pitchX=$w+$outline;$pitchY=$h+$outline;$margin=$outline/2;$pageWidth=590.0/25.4
$cols=[int][Math]::Floor($pageWidth/$pitchX);$rows=[int][Math]::Ceiling(350.0/$cols)
if($cols -ne 2 -or $rows -ne 175){throw 'Unexpected horizontal layout geometry'}
$clone=$source.Clone();$clone.SaveAs($working,$app.CreateStructSaveAsOptions());$clone.Close()
$doc=$app.OpenDocument($working);$page=$doc.ActivePage
$doc.BeginCommandGroup('Mekaniker bütün tasarımı yatay çevir - 59 cm')
$app.Optimization=$true
try{
 $page.SetSize($pageWidth,$rows*$h+($rows-1)*$outline+2*$margin)
 $left=$page.LeftX+$margin;$top=$page.TopY-$margin
 for($i=1;$i -le 350;$i++){
  $g=$page.Shapes.Item($i);$n=[int]$g.Name.Substring(10)
  $g.Rotate(-90)
  $col=($n-1)%$cols;$row=[int][Math]::Floor(($n-1)/$cols)
  $g.Move($left+$col*$pitchX-$g.LeftX,$top-$row*$pitchY-$g.TopY)
  if($i%70 -eq 0){Write-Output "Rotated: $i / 350"}
 }
 $doc.ClearSelection()
}finally{$app.Optimization=$false;$doc.EndCommandGroup();$app.Refresh()}
$doc.SaveAs($final,$app.CreateStructSaveAsOptions());if($doc.Dirty){throw 'Save failed'}
$doc.Close();$null=$app.OpenDocument($final)
$doc=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $final){$doc=$d}}
if(!$doc -or $doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 350){throw 'Reopened output mismatch'}
$page=$doc.ActivePage;$seen=@{};$groups=@{};$numbers=0
for($i=1;$i -le 350;$i++){
 $g=$page.Shapes.Item($i);$label=$g.Name.Substring(10);$n=[int]$label
 if($g.Type -ne 7 -or $g.Shapes.Count -ne 30 -or $n -lt 1 -or $n -gt 350 -or $label -ne $n.ToString('000') -or $seen.ContainsKey($label)){throw 'Group sequence mismatch'}
 $seen[$label]=$true;$groups[$label]=$g
 $col=($n-1)%$cols;$row=[int][Math]::Floor(($n-1)/$cols)
 if([Math]::Abs($g.SizeWidth-$w) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$h) -gt 0.00005 -or [Math]::Abs($g.LeftX-($left+$col*$pitchX)) -gt 0.00005 -or [Math]::Abs($g.TopY-($top-$row*$pitchY)) -gt 0.00005){throw "Layout mismatch: $label"}
 if($g.LeftX-$margin -lt $page.LeftX-0.00005 -or $g.RightX+$margin -gt $page.RightX+0.00005 -or $g.TopY+$margin -gt $page.TopY+0.00005 -or $g.BottomY-$margin -lt $page.BottomY-0.00005){throw 'Page boundary overflow'}
 foreach($j in $numberIndices){$s=$g.Shapes.Item($j);if($s.Type -ne 6 -or $s.Text.Story.Text -ne $label){throw "Number mismatch: $label"};$numbers++}
 $b=$g.Shapes.Item($borderIndex);if($b.Outline.Type -ne 1 -or [Math]::Abs($b.Outline.Width-$outline) -gt 0.000001){throw 'Border was changed'}
 if($i%70 -eq 0){Write-Output "Verified: $i / 350"}
}
function ColorValue($c){$v=$c.ToString();$v.Substring(0,$v.LastIndexOf(','))}
foreach($label in @('001','175','350')){
 $original=$sourceGroups[$label];$turned=$groups[$label]
 for($j=1;$j -le 30;$j++){
  $a=$original.Shapes.Item($j);$b=$turned.Shapes.Item($j)
  if($a.Type -ne $b.Type -or $a.Name -ne $b.Name -or [Math]::Abs($a.SizeWidth-$b.SizeHeight) -gt 0.00005 -or [Math]::Abs($a.SizeHeight-$b.SizeWidth) -gt 0.00005){throw 'Artwork size or structure changed'}
  $dx=$a.CenterX-$original.CenterX;$dy=$a.CenterY-$original.CenterY
  if([Math]::Abs(($b.CenterX-$turned.CenterX)-$dy) -gt 0.00005 -or [Math]::Abs(($b.CenterY-$turned.CenterY)+$dx) -gt 0.00005){throw 'Internal artwork positioning changed'}
  if($a.Type -eq 6){if($a.Text.Story.Text -ne $b.Text.Story.Text -or $a.Text.Story.Font -ne $b.Text.Story.Font -or [Math]::Abs($a.Text.Story.Size-$b.Text.Story.Size) -gt 0.00001){throw 'Artwork text changed'}}
  if($a.Type -eq 3){if($a.Curve.Nodes.Count -ne $b.Curve.Nodes.Count -or $a.Curve.SubPaths.Count -ne $b.Curve.SubPaths.Count -or (ColorValue $a.Fill.UniformColor) -ne (ColorValue $b.Fill.UniformColor)){throw 'Artwork curve or color changed'}}
  if($a.Type -eq 7 -and $a.Shapes.Count -ne $b.Shapes.Count){throw 'Nested artwork structure changed'}
 }
}
if($seen.Count -ne 350 -or $numbers -ne 1400 -or $source.Dirty -or (Get-FileHash -LiteralPath $sourceFile).Hash -ne $sourceHash){throw 'Count or source integrity failure'}
$doc.Activate();$doc.ClearSelection();$doc.ActiveWindow.ActiveView.ToFitPage();$app.Refresh()
[pscustomobject]@{File=$doc.FullFileName;Reopened=$true;Count=350;Numbers=$numbers;Columns=$cols;Rows=$rows;ArtworkWidthCM=$w*2.54;ArtworkHeightCM=$h*2.54;PageWidthCM=$page.SizeWidth*2.54;PageHeightCM=$page.SizeHeight*2.54;ContentWidthCM=($cols*$w+($cols-1)*$outline+$outline)*2.54;Rotation='90 degrees clockwise';ArtworkPreserved=$true;SourcePreserved=$true;SavedClean=(!$doc.Dirty)}|ConvertTo-Json|Tee-Object -FilePath ($root+'\work\mekaniker-horizontal-result.json')
