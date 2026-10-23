$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$root='C:\Users\USER\Documents\Codex\2026-10-13\u'
$source=$app.ActiveDocument;$sourceFile='C:\Users\USER\Downloads\mekaniker.cdr'
$diskBackup=$root+'\work\mekaniker-pairs350-source-disk.cdr'
$snapshot=$root+'\work\mekaniker-pairs350-source-live.cdr'
$final=$root+'\outputs\Mekaniker_001-1_175-2_350adet_Yatay_59cm.cdr'
if($source.FullFileName -ne $sourceFile -or $source.Pages.Count -ne 1 -or $source.ActivePage.Shapes.Count -ne 30){throw 'Unexpected open source'}
foreach($p in @($diskBackup,$snapshot,$final)){if(Test-Path -LiteralPath $p){throw 'Job path already exists'}}
$sourceDirty=$source.Dirty;Copy-Item -LiteralPath $sourceFile -Destination $diskBackup
$sourceHash=(Get-FileHash -LiteralPath $sourceFile).Hash
if($sourceHash -ne (Get-FileHash -LiteralPath $diskBackup).Hash){throw 'Disk backup mismatch'}
$clone=$source.Clone();$clone.SaveAs($snapshot,$app.CreateStructSaveAsOptions());$clone.Close()
if($source.Dirty -ne $sourceDirty){throw 'Source dirty state changed'}
$doc=$app.OpenDocument($snapshot);$page=$doc.ActivePage
$frameMap=@{1=23;2=22;3=20;4=19}
foreach($j in 1..4){$s=$page.Shapes.Item($j);if($s.Type -ne 6 -or $s.Text.Story.Text -ne '001' -or $s.Name -notlike 'Numara_*'){throw 'Number slots mismatch'}}
if($page.Shapes.Item(5).Text.Story.Text -ne 'MECHANIC' -or $page.Shapes.Item(6).Text.Story.Text -ne 'MEKANİKER' -or $page.Shapes.Item(7).Text.Story.Text -ne 'MEKANİKER' -or $page.Shapes.Item(8).Text.Story.Text -ne 'MECHANIC'){throw 'Role labels mismatch'}
$bg=$page.Shapes.Item(30);$w=[double]$bg.SizeHeight;$h=[double]$bg.SizeWidth;$outline=[double]$bg.Outline.Width;$outlineType=$bg.Outline.Type
if([Math]::Abs($w*25.4-250) -gt 0.0001 -or [Math]::Abs($h*25.4-19.9998) -gt 0.0001){throw 'Unexpected design dimensions'}
$margin=$outline/2;$pitchX=$w+$outline;$pitchY=$h+$outline;$pageWidth=590.0/25.4;$cols=[int][Math]::Floor($pageWidth/$pitchX);$rows=175
if($cols -ne 2){throw 'Two-column layout cannot fit'}
function LabelFor($n){'{0:000}-{1}' -f [int][Math]::Ceiling($n/2.0),((($n-1)%2)+1)}
$doc.BeginCommandGroup('Mekaniker 001-1 / 001-2 ... 175-1 / 175-2 yatay');$app.Optimization=$true
try{
 $base=$page.Shapes.All().Group();$base.Rotate(-90);$base.Name='Mekaniker_001-1'
 $numberStyles=@{}
 foreach($j in 1..4){$s=$base.Shapes.Item($j);$numberStyles[$j]=[pscustomobject]@{Font=$s.Text.Story.Font;Size=$s.Text.Story.Size;Angle=$s.RotationAngle;DX=$s.CenterX-$base.LeftX;DY=$base.TopY-$s.CenterY};$cx=$s.CenterX;$cy=$s.CenterY;$s.Text.Story.Text='001-1';$s.Move($cx-$s.CenterX,$cy-$s.CenterY)}
 $page.SetSize($pageWidth,$rows*$h+($rows-1)*$outline+2*$margin);$left=$page.LeftX+$margin;$top=$page.TopY-$margin
 $base.Move($left-$base.LeftX,$top-$base.TopY)
 for($n=2;$n -le 350;$n++){
  $label=LabelFor $n;$g=$base.Duplicate(0,0);$g.Name='Mekaniker_'+$label
  foreach($j in 1..4){$s=$g.Shapes.Item($j);$cx=$s.CenterX;$cy=$s.CenterY;$s.Text.Story.Text=$label;$s.Move($cx-$s.CenterX,$cy-$s.CenterY)}
  $col=($n-1)%2;$row=[int][Math]::Floor(($n-1)/2.0);$g.Move($left+$col*$pitchX-$g.LeftX,$top-$row*$pitchY-$g.TopY)
  if($n%70 -eq 0){Write-Output "Created: $n / 350"}
 }
 $doc.ClearSelection()
}finally{$app.Optimization=$false;$doc.EndCommandGroup();$app.Refresh()}
$doc.SaveAs($final,$app.CreateStructSaveAsOptions());if($doc.Dirty){throw 'Save failed'}
$doc.Close();$null=$app.OpenDocument($final);$doc=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $final){$doc=$d}}
if(!$doc -or $doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 350){throw 'Reopened output mismatch'}
$page=$doc.ActivePage;$groups=@{};$numbers=0;$maxNumberLength=0
for($i=1;$i -le 350;$i++){
 $g=$page.Shapes.Item($i)
 if($g.Name -notmatch '^Mekaniker_(\d{3})-([12])$'){throw 'Invalid group label'}
 $a=[int]$Matches[1];$b=[int]$Matches[2];$n=($a-1)*2+$b;$label=LabelFor $n
 if($n -lt 1 -or $n -gt 350 -or $g.Name -ne ('Mekaniker_'+$label) -or $groups.ContainsKey($label) -or $g.Shapes.Count -ne 30){throw 'Pair sequence mismatch'}
 $groups[$label]=$g;$col=$b-1;$row=$a-1
 if([Math]::Abs($g.SizeWidth-$w) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$h) -gt 0.00005 -or [Math]::Abs($g.LeftX-($left+$col*$pitchX)) -gt 0.00005 -or [Math]::Abs($g.TopY-($top-$row*$pitchY)) -gt 0.00005){throw 'Layout mismatch'}
 if($g.LeftX-$margin -lt $page.LeftX-0.00005 -or $g.RightX+$margin -gt $page.RightX+0.00005 -or $g.TopY+$margin -gt $page.TopY+0.00005 -or $g.BottomY-$margin -lt $page.BottomY-0.00005){throw 'Page overflow'}
 foreach($j in 1..4){
  $s=$g.Shapes.Item($j);$style=$numberStyles[$j];$box=$g.Shapes.Item($frameMap[$j])
  if($s.Text.Story.Text -ne $label -or $s.Text.Story.Font -ne $style.Font -or [Math]::Abs($s.Text.Story.Size-$style.Size) -gt 0.00001 -or [Math]::Abs($s.RotationAngle-$style.Angle) -gt 0.00001 -or [Math]::Abs(($s.CenterX-$g.LeftX)-$style.DX) -gt 0.00005 -or [Math]::Abs(($g.TopY-$s.CenterY)-$style.DY) -gt 0.00005){throw 'Number content/style mismatch'}
  if($s.LeftX -lt $box.LeftX-0.00005 -or $s.RightX -gt $box.RightX+0.00005 -or $s.TopY -gt $box.TopY+0.00005 -or $s.BottomY -lt $box.BottomY-0.00005){throw "Number does not fit white box: $label"}
  $numbers++;$maxNumberLength=[Math]::Max($maxNumberLength,$s.SizeHeight*25.4)
 }
 foreach($j in 5..8){$s=$g.Shapes.Item($j);if($s.Text.Story.Text -ne $source.ActivePage.Shapes.Item($j).Text.Story.Text){throw 'Role text changed'}}
 $border=$g.Shapes.Item(30);if($border.Outline.Type -ne $outlineType -or [Math]::Abs($border.Outline.Width-$outline) -gt 0.000001){throw 'Border changed'}
 if($i%70 -eq 0){Write-Output "Verified: $i / 350"}
}
function ColorValue($c){$v=$c.ToString();$v.Substring(0,$v.LastIndexOf(','))}
$sourceBg=$source.ActivePage.Shapes.Item(30)
foreach($label in @('001-1','175-2')){
 $g=$groups[$label]
 foreach($j in 5..30){
  $a=$source.ActivePage.Shapes.Item($j);$b=$g.Shapes.Item($j);$dx=$a.CenterX-$sourceBg.CenterX;$dy=$a.CenterY-$sourceBg.CenterY
  if($a.Type -ne $b.Type -or $a.Name -ne $b.Name -or [Math]::Abs($a.SizeWidth-$b.SizeHeight) -gt 0.00005 -or [Math]::Abs($a.SizeHeight-$b.SizeWidth) -gt 0.00005 -or [Math]::Abs(($b.CenterX-$g.CenterX)-$dy) -gt 0.00005 -or [Math]::Abs(($b.CenterY-$g.CenterY)+$dx) -gt 0.00005){throw 'Rotated artwork geometry mismatch'}
  if($a.Type -eq 6){if($a.Text.Story.Text -ne $b.Text.Story.Text -or $a.Text.Story.Font -ne $b.Text.Story.Font -or [Math]::Abs($a.Text.Story.Size-$b.Text.Story.Size) -gt 0.00001){throw 'Role text style changed'}}
  if($a.Type -eq 3){if($a.Curve.Nodes.Count -ne $b.Curve.Nodes.Count -or $a.Curve.SubPaths.Count -ne $b.Curve.SubPaths.Count -or (ColorValue $a.Fill.UniformColor) -ne (ColorValue $b.Fill.UniformColor)){throw 'Artwork curve/color changed'}}
  if($a.Type -eq 7 -and $a.Shapes.Count -ne $b.Shapes.Count){throw 'Nested artwork changed'}
 }
}
if($groups.Count -ne 350 -or $numbers -ne 1400 -or $source.Dirty -ne $sourceDirty -or (Get-FileHash -LiteralPath $sourceFile).Hash -ne $sourceHash){throw 'Count or original source integrity mismatch'}
$doc.Activate();$doc.ClearSelection();$doc.ActiveWindow.ActiveView.ToFitPage();$app.Refresh()
[pscustomobject]@{File=$doc.FullFileName;Count=350;NumberCount=1400;Sequence='001-1,001-2,...,175-1,175-2';Columns=2;Rows=175;PageWidthCM=$page.SizeWidth*2.54;ContentWidthCM=($cols*$w+($cols-1)*$outline+$outline)*2.54;AllNumbersFitWhiteBoxes=$true;MaxNumberLengthMM=$maxNumberLength;RoleTextAndArtworkPreserved=$true;UnsavedSourceCaptured=$sourceDirty;OriginalSourcePreserved=$true;SavedAndReopened=$true;SavedClean=(!$doc.Dirty)}|ConvertTo-Json|Tee-Object -FilePath ($root+'\work\mekaniker-pairs350-result.json')
