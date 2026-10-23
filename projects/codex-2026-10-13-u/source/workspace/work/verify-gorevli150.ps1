$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$root='C:\Users\USER\Documents\Codex\2026-10-13\u'
$sourceFile='C:\Users\USER\Downloads\görevvli.cdr (1).zip'
$final=$root+'\outputs\Gorevli_Bileklik_001-150_Yatay_59cm.cdr'
$source=$null;$doc=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $sourceFile){$source=$d};if($d.FullFileName -eq $final){$doc=$d}}
if(!$source -or !$doc -or $doc.Dirty -or $doc.ActivePage.Shapes.Count -ne 150){throw 'Saved output not ready'}
$hash=(Get-FileHash -LiteralPath ($root+'\work\gorevli150-original.cdr')).Hash
$bg=$source.ActivePage.Shapes.Item(30);$w=[double]$bg.SizeWidth;$h=[double]$bg.SizeHeight;$outline=[double]$bg.Outline.Width;$outlineType=$bg.Outline.Type
$margin=$outline/2;$pitchX=$w+$outline;$pitchY=$h+$outline;$cols=2;$rows=75
$left=$doc.ActivePage.LeftX+$margin;$top=$doc.ActivePage.TopY-$margin
$page=$doc.ActivePage;$groups=@{};$numbers=0
for($i=1;$i -le 150;$i++){
 $g=$page.Shapes.Item($i);$label=$g.Name.Substring(8);$n=[int]$label
 if($g.Type -ne 7 -or $g.Shapes.Count -ne 30 -or $n -lt 1 -or $n -gt 150 -or $label -ne $n.ToString('000') -or $groups.ContainsKey($label)){throw 'Sequence mismatch'}
 $groups[$label]=$g;$col=($n-1)%$cols;$row=[int][Math]::Floor(($n-1)/$cols)
 if([Math]::Abs($g.SizeWidth-$w) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$h) -gt 0.00005 -or [Math]::Abs($g.LeftX-($left+$col*$pitchX)) -gt 0.00005 -or [Math]::Abs($g.TopY-($top-$row*$pitchY)) -gt 0.00005){throw 'Geometry mismatch'}
 if($g.LeftX-$margin -lt $page.LeftX-0.00005 -or $g.RightX+$margin -gt $page.RightX+0.00005 -or $g.TopY+$margin -gt $page.TopY+0.00005 -or $g.BottomY-$margin -lt $page.BottomY-0.00005){throw 'Page overflow'}
 foreach($j in 1..4){if($g.Shapes.Item($j).Text.Story.Text -ne $label){throw 'Number mismatch'};$numbers++}
 foreach($j in 5..8){if($g.Shapes.Item($j).Text.Story.Text -ne 'GÖREVLİ'){throw 'Artwork label changed'}}
 $b=$g.Shapes.Item(30);if($b.Outline.Type -ne $outlineType -or [Math]::Abs($b.Outline.Width-$outline) -gt 0.000001){throw 'Border changed'}
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
