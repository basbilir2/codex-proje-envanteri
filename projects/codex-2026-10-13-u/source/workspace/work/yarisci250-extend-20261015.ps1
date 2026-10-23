$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$root='C:\Users\USER\Documents\Codex\2026-10-13\u'
$inputFile=$root+'\outputs\Yarisci_001-150_59x89cm_2sayfa.cdr'
$snapshot=$root+'\work\yarisci250-working-20261015.cdr'
$final=$root+'\outputs\Yarisci_001-250_59x89cm_3sayfa.cdr'
$source=$app.ActiveDocument
if($source.FullFileName -ne $inputFile -or $source.Dirty -or $source.Pages.Count -ne 2 -or $source.Pages.Item(1).Shapes.Count -ne 88 -or $source.Pages.Item(2).Shapes.Count -ne 62){throw 'Unexpected input document'}
foreach($path in @($snapshot,$final)){if(Test-Path -LiteralPath $path){throw 'Output path already exists'}}
$sourceHash=(Get-FileHash -LiteralPath $inputFile -Algorithm SHA256).Hash
$app.AppWindow.WindowState=3;$app.AppWindow.Activate()
$clone=$source.Clone();$clone.SaveAs($snapshot,$app.CreateStructSaveAsOptions());$clone.Close()
$doc=$app.OpenDocument($snapshot)
$numIndices=@(1,3,20,22);$frameMap=@{1=2;3=4;20=21;22=23}
$base=$null;$original=@{}
foreach($p in 1..2){$pg=$doc.Pages.Item($p);for($i=1;$i -le $pg.Shapes.Count;$i++){$g=$pg.Shapes.Item($i);$original[$g.Name]=@($p,$g.LeftX,$g.TopY,$g.SizeWidth,$g.SizeHeight);if($g.Name -eq 'Yarisci_001'){$base=$g}}}
if(!$base -or $base.Shapes.Count -ne 69){throw 'Template missing'}
$w=[double]$base.SizeWidth;$h=[double]$base.SizeHeight
if([Math]::Abs($w*25.4-250) -gt 0.0001 -or [Math]::Abs($h*25.4-20) -gt 0.0001){throw 'Unexpected template size'}
$styles=@{}
foreach($j in $numIndices){$s=$base.Shapes.Item($j);if($s.Text.Story.Text -ne '001'){throw 'Template number mismatch'};$styles[$j]=[pscustomobject]@{Font=$s.Text.Story.Font;Size=$s.Text.Story.Size;Angle=$s.RotationAngle;DX=$s.CenterX-$base.LeftX;DY=$base.TopY-$s.CenterY}}
$pw=590.0/25.4;$ph=890.0/25.4;$leftMargin=($pw-2*$w)/2;$topMargin=($ph-44*$h)/2
$doc.BeginCommandGroup('001-250 - 59x89 cm - sayfada 88 adet');$app.Optimization=$true
try{
 $null=$doc.AddPages(1);$doc.Pages.Item(3).SetSize($pw,$ph)
 $pages=@{}
 foreach($p in 1..3){$pg=$doc.Pages.Item($p);$pg.Activate();if([Math]::Abs($pg.SizeWidth-$pw) -gt 0.000001 -or [Math]::Abs($pg.SizeHeight-$ph) -gt 0.000001){throw 'Page dimensions mismatch'};$pages[$p]=[pscustomobject]@{Page=$pg;Layer=$pg.ActiveLayer;Left=$pg.LeftX+$leftMargin;Top=$pg.TopY-$topMargin}}
 for($n=151;$n -le 250;$n++){
  $p=[int][Math]::Floor(($n-1)/88.0)+1;$info=$pages[$p];$info.Page.Activate()
  $g=$base.Duplicate(0,0);$label=$n.ToString('000');$g.Name='Yarisci_'+$label;$g.MoveToLayer($info.Layer)
  foreach($j in $numIndices){$s=$g.Shapes.Item($j);$cx=$s.CenterX;$cy=$s.CenterY;$s.Text.Story.Text=$label;$s.Move($cx-$s.CenterX,$cy-$s.CenterY)}
  $offset=($n-1)%88;$col=$offset%2;$row=[int][Math]::Floor($offset/2.0)
  $g.Move($info.Left+$col*$w-$g.LeftX,$info.Top-$row*$h-$g.TopY)
  if($n%25 -eq 0){Write-Output "Created through: $n"}
 }
 $doc.ClearSelection();$doc.Pages.Item(1).Activate()
}finally{$app.Optimization=$false;$doc.EndCommandGroup();$app.Refresh()}
$counts=@(88,88,74)
foreach($p in 1..3){if($doc.Pages.Item($p).Shapes.Count -ne $counts[$p-1]){throw "Page transfer failure: $p"}}
$doc.SaveAs($final,$app.CreateStructSaveAsOptions());if($doc.Dirty){throw 'Save failed'}
$doc.Close();$null=$app.OpenDocument($final);$doc=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $final){$doc=$d}}
if(!$doc -or $doc.Pages.Count -ne 3){throw 'Reopened output mismatch'}
$seen=@{};$numberCount=0;$summary=@();$lastGroup=$null
foreach($p in 1..3){
 $pg=$doc.Pages.Item($p)
 if($pg.Shapes.Count -ne $counts[$p-1] -or [Math]::Abs($pg.SizeWidth-$pw) -gt 0.000001 -or [Math]::Abs($pg.SizeHeight-$ph) -gt 0.000001){throw 'Saved page dimensions or count mismatch'}
 for($i=1;$i -le $pg.Shapes.Count;$i++){
  $g=$pg.Shapes.Item($i);if($g.Name -notmatch '^Yarisci_(\d{3})$'){throw 'Invalid group name'};$label=$Matches[1];$n=[int]$label
  $expectedPage=[int][Math]::Floor(($n-1)/88.0)+1;$offset=($n-1)%88;$col=$offset%2;$row=[int][Math]::Floor($offset/2.0)
  if($n -lt 1 -or $n -gt 250 -or $seen.ContainsKey($label) -or $expectedPage -ne $p -or $g.Shapes.Count -ne 69 -or [Math]::Abs($g.SizeWidth-$w) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$h) -gt 0.00005 -or [Math]::Abs($g.LeftX-($pg.LeftX+$leftMargin+$col*$w)) -gt 0.00005 -or [Math]::Abs($g.TopY-($pg.TopY-$topMargin-$row*$h)) -gt 0.00005){throw "Sequence or placement mismatch: $label"}
  if($g.LeftX -lt $pg.LeftX-0.00005 -or $g.RightX -gt $pg.RightX+0.00005 -or $g.TopY -gt $pg.TopY+0.00005 -or $g.BottomY -lt $pg.BottomY-0.00005){throw 'Page overflow'}
  if($n -le 150){$old=$original[$g.Name];if($old[0] -ne $p -or [Math]::Abs($g.LeftX-$old[1]) -gt 0.00005 -or [Math]::Abs($g.TopY-$old[2]) -gt 0.00005 -or [Math]::Abs($g.SizeWidth-$old[3]) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$old[4]) -gt 0.00005){throw 'Existing layout changed'}}
  foreach($j in $numIndices){$s=$g.Shapes.Item($j);$box=$g.Shapes.Item($frameMap[$j]);$style=$styles[$j];if($s.Text.Story.Text -ne $label -or $s.Text.Story.Font -ne $style.Font -or [Math]::Abs($s.Text.Story.Size-$style.Size) -gt 0.00001 -or [Math]::Abs($s.RotationAngle-$style.Angle) -gt 0.00001 -or [Math]::Abs(($s.CenterX-$g.LeftX)-$style.DX) -gt 0.00005 -or [Math]::Abs(($g.TopY-$s.CenterY)-$style.DY) -gt 0.00005){throw "Number style mismatch: $label"};if($s.LeftX -lt $box.LeftX-0.00005 -or $s.RightX -gt $box.RightX+0.00005 -or $s.TopY -gt $box.TopY+0.00005 -or $s.BottomY -lt $box.BottomY-0.00005){throw 'Number outside white box'};$numberCount++}
  $seen[$label]=$true;if($n -eq 1){$base=$g};if($n -eq 250){$lastGroup=$g}
 }
 $first=(($p-1)*88+1).ToString('000');$last=([Math]::Min($p*88,250)).ToString('000')
 $summary+=[pscustomobject]@{Page=$p;Count=$counts[$p-1];First=$first;Last=$last;WidthCM=$pg.SizeWidth*2.54;HeightCM=$pg.SizeHeight*2.54};Write-Output "Verified page $p : $first - $last"
}
function ColorValue($c){$v=$c.ToString();$v.Substring(0,$v.LastIndexOf(','))}
foreach($j in 1..69){if($j -in $numIndices){continue};$a=$base.Shapes.Item($j);$b=$lastGroup.Shapes.Item($j)
 if($a.Type -ne $b.Type -or $a.Name -ne $b.Name -or [Math]::Abs($a.SizeWidth-$b.SizeWidth) -gt 0.00005 -or [Math]::Abs($a.SizeHeight-$b.SizeHeight) -gt 0.00005 -or [Math]::Abs(($a.CenterX-$base.CenterX)-($b.CenterX-$lastGroup.CenterX)) -gt 0.00005 -or [Math]::Abs(($a.CenterY-$base.CenterY)-($b.CenterY-$lastGroup.CenterY)) -gt 0.00005 -or $a.Fill.Type -ne $b.Fill.Type -or $a.Outline.Type -ne $b.Outline.Type){throw 'Artwork changed'}
 if($a.Type -eq 6 -and ($a.Text.Story.Text -ne $b.Text.Story.Text -or $a.Text.Story.Font -ne $b.Text.Story.Font -or [Math]::Abs($a.Text.Story.Size-$b.Text.Story.Size) -gt 0.00001)){throw 'Role text changed'}
 if($a.Type -eq 3 -and ($a.Curve.Nodes.Count -ne $b.Curve.Nodes.Count -or $a.Curve.SubPaths.Count -ne $b.Curve.SubPaths.Count)){throw 'Curve changed'}
 if($a.Fill.Type -eq 1 -and (ColorValue $a.Fill.UniformColor) -ne (ColorValue $b.Fill.UniformColor)){throw 'Artwork color changed'}
}
if($seen.Count -ne 250 -or $numberCount -ne 1000 -or $source.Dirty -or (Get-FileHash -LiteralPath $inputFile -Algorithm SHA256).Hash -ne $sourceHash){throw 'Final total or source integrity failure'}
$doc.Activate();$doc.Pages.Item(1).Activate();$doc.ClearSelection();$doc.ActiveWindow.ActiveView.ToFitPage();$app.Refresh()
[pscustomobject]@{File=$doc.FullFileName;Pages=$summary;Designs=250;NumberObjects=1000;FourMatchingNumbersPerDesign=$true;AllNumbersInsideOriginalBoxes=$true;Existing150Preserved=$true;ArtworkPreserved=$true;SourceFileHashUnchanged=$true;SavedAndReopened=$true;SavedClean=(!$doc.Dirty)}|ConvertTo-Json -Depth 4|Tee-Object -FilePath ($root+'\work\yarisci250-extend-20261015-result.json')
