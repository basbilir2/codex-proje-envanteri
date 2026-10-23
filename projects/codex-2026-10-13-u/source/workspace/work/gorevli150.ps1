$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$root='C:\Users\USER\Documents\Codex\2026-10-13\u'
$sourceFile='C:\Users\USER\Downloads\görevvli.cdr (1).zip'
$backup=$root+'\work\gorevli150-original.cdr'
$working=$root+'\work\gorevli150-working.cdr'
$final=$root+'\outputs\Gorevli_Bileklik_001-150_Yatay_59cm.cdr'
$source=$app.ActiveDocument
if($source.FullFileName -ne $sourceFile -or $source.Dirty -or $source.Pages.Count -ne 1 -or $source.ActivePage.Shapes.Count -ne 30){throw 'Unexpected source'}
foreach($p in @($backup,$working,$final)){if(Test-Path -LiteralPath $p){throw 'Output path already exists'}}
Copy-Item -LiteralPath $sourceFile -Destination $backup
$hash=(Get-FileHash -LiteralPath $sourceFile).Hash
if($hash -ne (Get-FileHash -LiteralPath $backup).Hash){throw 'Backup mismatch'}
$clone=$source.Clone();$clone.SaveAs($working,$app.CreateStructSaveAsOptions());$clone.Close()
$doc=$app.OpenDocument($working);$page=$doc.ActivePage
foreach($j in 1..4){$s=$page.Shapes.Item($j);if($s.Name -notlike 'Numara_*' -or $s.Type -ne 6 -or $s.Text.Story.Text -ne '001'){throw 'Number slots mismatch'}}
foreach($j in 5..8){if($page.Shapes.Item($j).Text.Story.Text -ne 'GÖREVLİ'){throw 'Artwork labels mismatch'}}
$bg=$page.Shapes.Item(30);$w=[double]$bg.SizeWidth;$h=[double]$bg.SizeHeight;$outline=[double]$bg.Outline.Width
if([Math]::Abs($w*25.4-250) -gt 0.0001 -or [Math]::Abs($h*25.4-19.9998) -gt 0.0001){throw 'Source dimensions mismatch'}
$margin=$outline/2;$pitchX=$w+$outline;$pitchY=$h+$outline;$pageWidth=590.0/25.4
$cols=[int][Math]::Floor($pageWidth/$pitchX);$rows=[int][Math]::Ceiling(150.0/$cols)
if($cols -ne 2 -or $rows -ne 75){throw 'Layout calculation mismatch'}
$doc.BeginCommandGroup('GÖREVLİ 001-150 yatay - 59 cm');$app.Optimization=$true
try{
 $base=$page.Shapes.All().Group();$base.Name='Gorevli_001'
 $page.SetSize($pageWidth,$rows*$h+($rows-1)*$outline+2*$margin)
 $left=$page.LeftX+$margin;$top=$page.TopY-$margin;$base.Move($left-$base.LeftX,$top-$base.TopY)
 for($n=2;$n -le 150;$n++){
  $label=$n.ToString('000');$g=$base.Duplicate(0,0);$g.Name='Gorevli_'+$label
  foreach($j in 1..4){$s=$g.Shapes.Item($j);$cx=$s.CenterX;$cy=$s.CenterY;$s.Text.Story.Text=$label;$s.Move($cx-$s.CenterX,$cy-$s.CenterY)}
  $col=($n-1)%$cols;$row=[int][Math]::Floor(($n-1)/$cols);$g.Move($left+$col*$pitchX-$g.LeftX,$top-$row*$pitchY-$g.TopY)
  if($n%50 -eq 0){Write-Output "Created: $n / 150"}
 }
 $doc.ClearSelection()
}finally{$app.Optimization=$false;$doc.EndCommandGroup();$app.Refresh()}
$doc.SaveAs($final,$app.CreateStructSaveAsOptions());if($doc.Dirty){throw 'Save failed'}
$doc.Close();$null=$app.OpenDocument($final)
$doc=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $final){$doc=$d}}
if(!$doc -or $doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 150){throw 'Saved count mismatch'}
$page=$doc.ActivePage;$groups=@{};$numbers=0
for($i=1;$i -le 150;$i++){
 $g=$page.Shapes.Item($i);$label=$g.Name.Substring(8);$n=[int]$label
 if($g.Type -ne 7 -or $g.Shapes.Count -ne 30 -or $n -lt 1 -or $n -gt 150 -or $label -ne $n.ToString('000') -or $groups.ContainsKey($label)){throw 'Sequence mismatch'}
 $groups[$label]=$g;$col=($n-1)%$cols;$row=[int][Math]::Floor(($n-1)/$cols)
 if([Math]::Abs($g.SizeWidth-$w) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$h) -gt 0.00005 -or [Math]::Abs($g.LeftX-($left+$col*$pitchX)) -gt 0.00005 -or [Math]::Abs($g.TopY-($top-$row*$pitchY)) -gt 0.00005){throw 'Geometry mismatch'}
 if($g.LeftX-$margin -lt $page.LeftX-0.00005 -or $g.RightX+$margin -gt $page.RightX+0.00005 -or $g.TopY+$margin -gt $page.TopY+0.00005 -or $g.BottomY-$margin -lt $page.BottomY-0.00005){throw 'Page overflow'}
 foreach($j in 1..4){if($g.Shapes.Item($j).Text.Story.Text -ne $label){throw 'Number mismatch'};$numbers++}
 foreach($j in 5..8){if($g.Shapes.Item($j).Text.Story.Text -ne 'GÖREVLİ'){throw 'Artwork label changed'}}
 $b=$g.Shapes.Item(30);if($b.Outline.Type -ne $bg.Outline.Type -or [Math]::Abs($b.Outline.Width-$outline) -gt 0.000001){throw 'Border changed'}
 if($i%50 -eq 0){Write-Output "Verified: $i / 150"}
}
function ColorValue($c){$v=$c.ToString();$v.Substring(0,$v.LastIndexOf(','))}
foreach($label in @('001','150')){
 $g=$groups[$label];$sourceBg=$source.ActivePage.Shapes.Item(30)
 foreach($j in 5..30){
  $a=$source.ActivePage.Shapes.Item($j);$b=$g.Shapes.Item($j)
  if($a.Type -ne $b.Type -or $a.Name -ne $b.Name -or [Math]::Abs($a.SizeWidth-$b.SizeWidth) -gt 0.00005 -or [Math]::Abs($a.SizeHeight-$b.SizeHeight) -gt 0.00005 -or [Math]::Abs(($a.LeftX-$sourceBg.LeftX)-($b.LeftX-$g.LeftX)) -gt 0.00005 -or [Math]::Abs(($sourceBg.TopY-$a.TopY)-($g.TopY-$b.TopY)) -gt 0.00005){throw 'Artwork geometry changed'}
  if($a.Type -eq 6){if($a.Text.Story.Text -ne $b.Text.Story.Text -or $a.Text.Story.Font -ne $b.Text.Story.Font -or [Math]::Abs($a.Text.Story.Size-$b.Text.Story.Size) -gt 0.00001){throw 'Artwork text changed'}}
  if($a.Type -eq 3){if($a.Curve.Nodes.Count -ne $b.Curve.Nodes.Count -or $a.Curve.SubPaths.Count -ne $b.Curve.SubPaths.Count -or (ColorValue $a.Fill.UniformColor) -ne (ColorValue $b.Fill.UniformColor)){throw 'Artwork curve or color changed'}}
  if($a.Type -eq 7 -and $a.Shapes.Count -ne $b.Shapes.Count){throw 'Nested artwork changed'}
 }
}
if($numbers -ne 600 -or $groups.Count -ne 150 -or $source.Dirty -or (Get-FileHash -LiteralPath $sourceFile).Hash -ne $hash){throw 'Count or source integrity failure'}
$doc.Activate();$doc.ClearSelection();$doc.ActiveWindow.ActiveView.ToFitPage();$app.Refresh()
[pscustomobject]@{File=$doc.FullFileName;Reopened=$true;Count=150;Numbers=600;Sequence='001-150';Columns=$cols;Rows=$rows;PageWidthCM=$page.SizeWidth*2.54;PageHeightCM=$page.SizeHeight*2.54;ContentWidthCM=($cols*$w+($cols-1)*$outline+$outline)*2.54;ArtworkPreserved=$true;SourcePreserved=$true;SavedClean=(!$doc.Dirty)}|ConvertTo-Json|Tee-Object -FilePath ($root+'\work\gorevli150-result.json')
