$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$root='C:\Users\USER\Documents\Codex\2026-10-13\u'
$snapshot=$root+'\work\yarisci150-source-live-20261015.cdr'
$final=$root+'\outputs\Yarisci_001-150_59x89cm_2sayfa.cdr'
$source=$app.ActiveDocument;$sourceName=$source.Name;$sourceDirty=$source.Dirty
if($source.Name -ne 'Untitled-1' -or $source.FullFileName -ne '' -or $source.Pages.Count -ne 1 -or $source.ActivePage.Shapes.Count -ne 69){throw 'Unexpected source document'}
foreach($p in @($snapshot,$final)){if(Test-Path -LiteralPath $p){throw 'Job path already exists'}}
$app.AppWindow.WindowState=3;$app.AppWindow.Activate()
$clone=$source.Clone();$clone.SaveAs($snapshot,$app.CreateStructSaveAsOptions());$clone.Close()
if($source.Dirty -ne $sourceDirty){throw 'Original source state changed'}
$doc=$app.OpenDocument($snapshot);$page=$doc.ActivePage
$numIndices=@(1,3,20,22);$frameMap=@{1=2;3=4;20=21;22=23}
foreach($j in $numIndices){$s=$page.Shapes.Item($j);if($s.Type -ne 6 -or $s.Text.Story.Text -ne '001'){throw 'Number slot identification failed'}}
$bg=$page.Shapes.Item(69);$w=[double]$bg.SizeWidth;$h=[double]$bg.SizeHeight;$outline=[double]$bg.Outline.Width;$outlineType=$bg.Outline.Type
if([Math]::Abs($w*25.4-250) -gt 0.0001 -or [Math]::Abs($h*25.4-20) -gt 0.0001){throw 'Unexpected template dimensions'}
$pw=590.0/25.4;$ph=890.0/25.4;$pitchX=$w+$outline;$pitchY=$h+$outline
$leftMargin=($pw-(2*$w+$outline))/2;$topMargin=($ph-(44*$h+43*$outline))/2
if($leftMargin -lt $outline/2 -or $topMargin -lt $outline/2){throw '88 designs cannot fit without changing artwork'}
$doc.BeginCommandGroup('001-150 - 59x89 cm - sayfada 88 adet');$app.Optimization=$true
try{
 $base=$page.Shapes.All().Group();$base.Name='Yarisci_001'
 if($base.Shapes.Count -ne 69){throw 'Template grouping mismatch'}
 $styles=@{}
 foreach($j in $numIndices){$s=$base.Shapes.Item($j);$styles[$j]=[pscustomobject]@{Font=$s.Text.Story.Font;Size=$s.Text.Story.Size;Angle=$s.RotationAngle;DX=$s.CenterX-$base.LeftX;DY=$base.TopY-$s.CenterY}}
 $null=$doc.AddPages(1)
 $pages=@{}
 foreach($p in 1..2){$pg=$doc.Pages.Item($p);$pg.Activate();$pg.SetSize($pw,$ph);$pages[$p]=[pscustomobject]@{Page=$pg;Layer=$pg.ActiveLayer;Left=$pg.LeftX+$leftMargin;Top=$pg.TopY-$topMargin}}
 $doc.Pages.Item(1).Activate();$base.MoveToLayer($pages[1].Layer);$base.Move($pages[1].Left-$base.LeftX,$pages[1].Top-$base.TopY)
 for($n=2;$n -le 150;$n++){
  $p=[int][Math]::Floor(($n-1)/88.0)+1;$info=$pages[$p];$info.Page.Activate()
  $g=$base.Duplicate(0,0);$label=$n.ToString('000');$g.Name='Yarisci_'+$label;$g.MoveToLayer($info.Layer)
  foreach($j in $numIndices){$s=$g.Shapes.Item($j);$cx=$s.CenterX;$cy=$s.CenterY;$s.Text.Story.Text=$label;$s.Move($cx-$s.CenterX,$cy-$s.CenterY)}
  $offset=($n-1)%88;$col=$offset%2;$row=[int][Math]::Floor($offset/2.0)
  $g.Move($info.Left+$col*$pitchX-$g.LeftX,$info.Top-$row*$pitchY-$g.TopY)
  if($n%50 -eq 0){Write-Output "Created: $n / 150"}
 }
 $doc.ClearSelection();$doc.Pages.Item(1).Activate()
}finally{$app.Optimization=$false;$doc.EndCommandGroup();$app.Refresh()}
foreach($p in 1..2){$pg=$doc.Pages.Item($p);$count=if($p -eq 1){88}else{62};if($pg.Shapes.Count -ne $count){throw "Page transfer count mismatch: $p"};Write-Output "Placed page $p : $count designs"}
$doc.SaveAs($final,$app.CreateStructSaveAsOptions());if($doc.Dirty){throw 'Save failed'}
$doc.Close();$null=$app.OpenDocument($final);$doc=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $final){$doc=$d}}
if(!$doc -or $doc.Pages.Count -ne 2){throw 'Reopened document mismatch'}
$seen=@{};$groups=@{};$numberCount=0;$summary=@()
foreach($p in 1..2){
 $pg=$doc.Pages.Item($p);$count=if($p -eq 1){88}else{62}
 if($pg.Shapes.Count -ne $count -or [Math]::Abs($pg.SizeWidth-$pw) -gt 0.000001 -or [Math]::Abs($pg.SizeHeight-$ph) -gt 0.000001){throw 'Page dimension or count mismatch'}
 for($i=1;$i -le $pg.Shapes.Count;$i++){
  $g=$pg.Shapes.Item($i);if($g.Name -notmatch '^Yarisci_(\d{3})$'){throw 'Invalid saved group name'};$label=$Matches[1];$n=[int]$label
  $expectedPage=[int][Math]::Floor(($n-1)/88.0)+1;$offset=($n-1)%88;$col=$offset%2;$row=[int][Math]::Floor($offset/2.0)
  if($n -lt 1 -or $n -gt 150 -or $seen.ContainsKey($label) -or $label -ne $n.ToString('000') -or $expectedPage -ne $p -or $g.Shapes.Count -ne 69 -or [Math]::Abs($g.SizeWidth-$w) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$h) -gt 0.00005 -or [Math]::Abs($g.LeftX-($pg.LeftX+$leftMargin+$col*$pitchX)) -gt 0.00005 -or [Math]::Abs($g.TopY-($pg.TopY-$topMargin-$row*$pitchY)) -gt 0.00005){throw 'Sequence or placement mismatch'}
  if($g.LeftX-$outline/2 -lt $pg.LeftX-0.00005 -or $g.RightX+$outline/2 -gt $pg.RightX+0.00005 -or $g.TopY+$outline/2 -gt $pg.TopY+0.00005 -or $g.BottomY-$outline/2 -lt $pg.BottomY-0.00005){throw 'Page boundary overflow'}
  foreach($j in $numIndices){$s=$g.Shapes.Item($j);$box=$g.Shapes.Item($frameMap[$j]);$style=$styles[$j];if($s.Text.Story.Text -ne $label -or $s.Text.Story.Font -ne $style.Font -or [Math]::Abs($s.RotationAngle-$style.Angle) -gt 0.00001 -or [Math]::Abs(($s.CenterX-$g.LeftX)-$style.DX) -gt 0.00005 -or [Math]::Abs(($g.TopY-$s.CenterY)-$style.DY) -gt 0.00005){throw 'Number label/style/position mismatch'};if($s.LeftX -lt $box.LeftX-0.00005 -or $s.RightX -gt $box.RightX+0.00005 -or $s.TopY -gt $box.TopY+0.00005 -or $s.BottomY -lt $box.BottomY-0.00005){throw 'Number outside its original white box'};$numberCount++}
  $border=$g.Shapes.Item(69);if($border.Outline.Type -ne $outlineType -or [Math]::Abs($border.Outline.Width-$outline) -gt 0.000001){throw 'Original outline changed'}
  $seen[$label]=$true;$groups[$label]=$g
 }
 $first=if($p -eq 1){'001'}else{'089'};$last=if($p -eq 1){'088'}else{'150'};$summary+=[pscustomobject]@{Page=$p;Count=$count;First=$first;Last=$last;WidthCM=$pg.SizeWidth*2.54;HeightCM=$pg.SizeHeight*2.54};Write-Output "Verified page $p : $first - $last ($count designs)"
}
function ColorValue($c){$v=$c.ToString();$v.Substring(0,$v.LastIndexOf(','))}
$sourceBg=$source.ActivePage.Shapes.Item(69)
foreach($label in @('001','150')){
 $g=$groups[$label]
 foreach($j in 1..69){if($j -in $numIndices){continue};$a=$source.ActivePage.Shapes.Item($j);$b=$g.Shapes.Item($j)
  if($a.Type -ne $b.Type -or $a.Name -ne $b.Name -or [Math]::Abs($a.SizeWidth-$b.SizeWidth) -gt 0.00005 -or [Math]::Abs($a.SizeHeight-$b.SizeHeight) -gt 0.00005 -or [Math]::Abs(($a.CenterX-$sourceBg.CenterX)-($b.CenterX-$g.CenterX)) -gt 0.00005 -or [Math]::Abs(($a.CenterY-$sourceBg.CenterY)-($b.CenterY-$g.CenterY)) -gt 0.00005){throw 'Original artwork geometry changed'}
  if($a.Type -eq 6 -and ($a.Text.Story.Text -ne $b.Text.Story.Text -or $a.Text.Story.Font -ne $b.Text.Story.Font -or [Math]::Abs($a.Text.Story.Size-$b.Text.Story.Size) -gt 0.00001)){throw 'Original role text changed'}
  if($a.Type -eq 3){if($a.Curve.Nodes.Count -ne $b.Curve.Nodes.Count -or $a.Curve.SubPaths.Count -ne $b.Curve.SubPaths.Count -or $a.Fill.Type -ne $b.Fill.Type -or $a.Outline.Type -ne $b.Outline.Type){throw 'Original curves or styling changed'};if($a.Fill.Type -eq 1 -and (ColorValue $a.Fill.UniformColor) -ne (ColorValue $b.Fill.UniformColor)){throw 'Original artwork color changed'}}
 }
}
if($seen.Count -ne 150 -or $numberCount -ne 600 -or $source.Name -ne $sourceName -or $source.Dirty -ne $sourceDirty -or $source.ActivePage.Shapes.Count -ne 69){throw 'Final total or source integrity failure'}
$doc.Activate();$doc.Pages.Item(1).Activate();$doc.ClearSelection();$doc.ActiveWindow.ActiveView.ToFitPage();$app.Refresh()
[pscustomobject]@{File=$doc.FullFileName;Pages=$summary;Designs=150;NumberObjects=600;FourMatchingNumbersPerDesign=$true;AllNumbersInsideOriginalBoxes=$true;ArtworkAndOrientationPreserved=$true;OriginalUnsavedSourcePreserved=$true;SavedAndReopened=$true;SavedClean=(!$doc.Dirty)}|ConvertTo-Json -Depth 4|Tee-Object -FilePath ($root+'\work\yarisci150-pages-20261015-result.json')
