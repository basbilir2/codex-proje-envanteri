$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$root='C:\Users\USER\Documents\Codex\2026-10-13\u'
$inputFile=$root+'\outputs\Mekaniker_001-1_175-2_350adet_Yatay_59cm.cdr'
$working=$root+'\work\mekaniker-pairs-pages-working.cdr'
$final=$root+'\outputs\Mekaniker_001-1_175-2_59x89cm_4sayfa.cdr'
foreach($p in @($working,$final)){if(Test-Path -LiteralPath $p){throw 'Pagination path already exists'}}
$source=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $inputFile){$source=$d}}
if(!$source -or $source.Dirty -or $source.Pages.Count -ne 1 -or $source.ActivePage.Shapes.Count -ne 350){throw 'Numbered source not ready'}
$sourceHash=(Get-FileHash -LiteralPath $inputFile).Hash
$clone=$source.Clone();$clone.SaveAs($working,$app.CreateStructSaveAsOptions());$clone.Close()
$doc=$app.OpenDocument($working);$items=@();$sampleBefore=@{}
function LabelFor($n){'{0:000}-{1}' -f [int][Math]::Ceiling($n/2.0),((($n-1)%2)+1)}
for($i=1;$i -le 350;$i++){
 $g=$doc.ActivePage.Shapes.Item($i)
 if($g.Name -notmatch '^Mekaniker_(\d{3})-([12])$'){throw 'Invalid group name'}
 $n=([int]$Matches[1]-1)*2+[int]$Matches[2];$label=LabelFor $n
 $items += [pscustomobject]@{N=$n;Label=$label;Shape=$g;W=$g.SizeWidth;H=$g.SizeHeight}
 if($n -in @(1,350)){
  $snap=@{}
  for($j=1;$j -le 30;$j++){$s=$g.Shapes.Item($j);$v=[ordered]@{Type=$s.Type;Name=$s.Name;W=$s.SizeWidth;H=$s.SizeHeight;DX=$s.CenterX-$g.CenterX;DY=$s.CenterY-$g.CenterY;Angle=$s.RotationAngle};if($s.Type -eq 6){$v.Text=$s.Text.Story.Text;$v.Font=$s.Text.Story.Font;$v.Size=$s.Text.Story.Size};if($s.Type -eq 3){$v.Nodes=$s.Curve.Nodes.Count;$v.Paths=$s.Curve.SubPaths.Count};if($s.Type -eq 7){$v.Children=$s.Shapes.Count};$snap[$j]=[pscustomobject]$v};$sampleBefore[$label]=$snap
 }
}
$items=@($items|Sort-Object N)
if(($items.N -join ',') -ne ((1..350)-join ',')){throw 'Source sequence mismatch'}
$w=$items[0].W;$h=$items[0].H;$border=$items[0].Shape.Shapes.Item(30);$outline=[double]$border.Outline.Width
$pitchX=$w+$outline;$pitchY=$h+$outline;$pw=590.0/25.4;$ph=890.0/25.4
$leftMargin=($pw-(2*$w+$outline))/2;$topMargin=($ph-(44*$h+43*$outline))/2
if($leftMargin -lt $outline/2 -or $topMargin -lt $outline/2){throw '88 designs do not fit the requested page'}
$doc.BeginCommandGroup('59x89 cm sayfalarda 88 bileklik');$app.Optimization=$true
try{
 $null=$doc.AddPages(3);$pageInfo=@{}
 for($p=1;$p -le 4;$p++){$page=$doc.Pages.Item($p);$page.Activate();$page.SetSize($pw,$ph);$layer=$page.ActiveLayer;if(!$layer){$layer=$page.CreateLayer('Bileklikler')};$pageInfo[$p]=[pscustomobject]@{Page=$page;Layer=$layer;Left=$page.LeftX+$leftMargin;Top=$page.TopY-$topMargin}}
 foreach($item in $items){
  $p=[int][Math]::Floor(($item.N-1)/88.0)+1;$offset=($item.N-1)%88;$col=$offset%2;$row=[int][Math]::Floor($offset/2.0);$info=$pageInfo[$p];$g=$item.Shape
  if($p -ne 1){$g.MoveToLayer($info.Layer)}
  $g.Move($info.Left+$col*$pitchX-$g.LeftX,$info.Top-$row*$pitchY-$g.TopY)
 }
 $doc.ClearSelection();$doc.Pages.Item(1).Activate()
}finally{$app.Optimization=$false;$doc.EndCommandGroup();$app.Refresh()}
$doc.SaveAs($final,$app.CreateStructSaveAsOptions());if($doc.Dirty){throw 'Pagination save failed'}
$doc.Close();$null=$app.OpenDocument($final);$doc=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $final){$doc=$d}}
if(!$doc -or $doc.Pages.Count -ne 4){throw 'Saved page count mismatch'}
$seen=@{};$total=0;$numberCount=0;$summary=@();$frameMap=@{1=23;2=22;3=20;4=19}
for($p=1;$p -le 4;$p++){
 $page=$doc.Pages.Item($p);$expectedCount=if($p -lt 4){88}else{86}
 if($page.Shapes.Count -ne $expectedCount -or [Math]::Abs($page.SizeWidth-$pw) -gt 0.000001 -or [Math]::Abs($page.SizeHeight-$ph) -gt 0.000001){throw 'Page size or design count mismatch'}
 $expectedLeft=$page.LeftX+$leftMargin;$expectedTop=$page.TopY-$topMargin
 for($i=1;$i -le $page.Shapes.Count;$i++){
  $g=$page.Shapes.Item($i);if($g.Name -notmatch '^Mekaniker_(\d{3})-([12])$'){throw 'Invalid saved group name'}
  $n=([int]$Matches[1]-1)*2+[int]$Matches[2];$label=LabelFor $n;$expectedPage=[int][Math]::Floor(($n-1)/88.0)+1;$offset=($n-1)%88;$col=$offset%2;$row=[int][Math]::Floor($offset/2.0)
  if($n -lt 1 -or $n -gt 350 -or $seen.ContainsKey($label) -or $expectedPage -ne $p -or $g.Shapes.Count -ne 30 -or [Math]::Abs($g.SizeWidth-$w) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$h) -gt 0.00005 -or [Math]::Abs($g.LeftX-($expectedLeft+$col*$pitchX)) -gt 0.00005 -or [Math]::Abs($g.TopY-($expectedTop-$row*$pitchY)) -gt 0.00005){throw 'Saved pagination or sequence mismatch'}
  if($g.LeftX-$outline/2 -lt $page.LeftX-0.00005 -or $g.RightX+$outline/2 -gt $page.RightX+0.00005 -or $g.TopY+$outline/2 -gt $page.TopY+0.00005 -or $g.BottomY-$outline/2 -lt $page.BottomY-0.00005){throw 'Design outside page'}
  foreach($j in 1..4){$s=$g.Shapes.Item($j);$box=$g.Shapes.Item($frameMap[$j]);if($s.Text.Story.Text -ne $label -or $s.LeftX -lt $box.LeftX-0.00005 -or $s.RightX -gt $box.RightX+0.00005 -or $s.TopY -gt $box.TopY+0.00005 -or $s.BottomY -lt $box.BottomY-0.00005){throw 'Number content or box fit mismatch'};$numberCount++}
  if($g.Shapes.Item(5).Text.Story.Text -ne 'MECHANIC' -or $g.Shapes.Item(6).Text.Story.Text -ne 'MEKANİKER' -or $g.Shapes.Item(7).Text.Story.Text -ne 'MEKANİKER' -or $g.Shapes.Item(8).Text.Story.Text -ne 'MECHANIC'){throw 'Role text changed'}
  if($sampleBefore.ContainsKey($label)){
   foreach($j in 1..30){$a=$sampleBefore[$label][$j];$b=$g.Shapes.Item($j);if($a.Type -ne $b.Type -or $a.Name -ne $b.Name -or [Math]::Abs($a.W-$b.SizeWidth) -gt 0.00005 -or [Math]::Abs($a.H-$b.SizeHeight) -gt 0.00005 -or [Math]::Abs($a.DX-($b.CenterX-$g.CenterX)) -gt 0.00005 -or [Math]::Abs($a.DY-($b.CenterY-$g.CenterY)) -gt 0.00005 -or [Math]::Abs($a.Angle-$b.RotationAngle) -gt 0.00001){throw 'Internal artwork geometry changed'};if($a.Type -eq 6 -and ($a.Text -ne $b.Text.Story.Text -or $a.Font -ne $b.Text.Story.Font -or [Math]::Abs($a.Size-$b.Text.Story.Size) -gt 0.00001)){throw 'Artwork font changed'};if($a.Type -eq 3 -and ($a.Nodes -ne $b.Curve.Nodes.Count -or $a.Paths -ne $b.Curve.SubPaths.Count)){throw 'Artwork curves changed'}}
  }
  $seen[$label]=$true;$total++
 }
 $first=LabelFor (($p-1)*88+1);$last=LabelFor ([Math]::Min($p*88,350));$summary+=[pscustomobject]@{Page=$p;Count=$expectedCount;First=$first;Last=$last;WidthCM=$page.SizeWidth*2.54;HeightCM=$page.SizeHeight*2.54}
 Write-Output "Verified page $p : $first - $last ($expectedCount designs)"
}
if($total -ne 350 -or $numberCount -ne 1400 -or $source.Dirty -or (Get-FileHash -LiteralPath $inputFile).Hash -ne $sourceHash){throw 'Final count or input integrity mismatch'}
$doc.Activate();$doc.Pages.Item(1).Activate();$doc.ClearSelection();$doc.ActiveWindow.ActiveView.ToFitPage();$app.Refresh()
[pscustomobject]@{File=$doc.FullFileName;Pages=$summary;TotalDesigns=$total;TotalNumbers=$numberCount;NumberPatternVerified=$true;AllNumbersFitWhiteBoxes=$true;ArtworkPreserved=$true;SavedAndReopened=$true;SavedClean=(!$doc.Dirty)}|ConvertTo-Json -Depth 4|Tee-Object -FilePath ($root+'\work\mekaniker-pairs-pages-result.json')
