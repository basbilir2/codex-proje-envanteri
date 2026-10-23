$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$root='C:\Users\USER\Documents\Codex\2026-10-13\u'
$target=$root+'\outputs\mekanik yan.cdr'
$backup=$root+'\work\mekanik-yan-before-gorevli.cdr'
$doc=$app.ActiveDocument
if($doc.FullFileName -ne $target -or $doc.Dirty -or $doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 350){throw 'Unexpected target document'}
if(Test-Path -LiteralPath $backup){throw 'Backup already exists'}
Copy-Item -LiteralPath $target -Destination $backup
$originalHash=(Get-FileHash -LiteralPath $target).Hash
if($originalHash -ne (Get-FileHash -LiteralPath $backup).Hash){throw 'Backup integrity failed'}
$textIndices=@(5,6,7,8);$numberIndices=@(1,2,3,4);$states=@{};$artworkSamples=@{}
function ColorValue($c){$v=$c.ToString();$v.Substring(0,$v.LastIndexOf(','))}
function ShapeState($s){
 $v=[ordered]@{Type=$s.Type;Name=$s.Name;W=$s.SizeWidth;H=$s.SizeHeight;CX=$s.CenterX;CY=$s.CenterY;Angle=$s.RotationAngle}
 if($s.Type -eq 3){$v.Nodes=$s.Curve.Nodes.Count;$v.Paths=$s.Curve.SubPaths.Count;$v.Fill=ColorValue $s.Fill.UniformColor;$v.Outline=$s.Outline.Type;$v.OutlineWidth=$s.Outline.Width}
 if($s.Type -eq 6){$v.Text=$s.Text.Story.Text;$v.Font=$s.Text.Story.Font;$v.Size=$s.Text.Story.Size;$v.Fill=ColorValue $s.Fill.UniformColor}
 if($s.Type -eq 7){$v.Children=$s.Shapes.Count}
 [pscustomobject]$v
}
$page=$doc.ActivePage;$pageWidth=$page.SizeWidth;$pageHeight=$page.SizeHeight
for($i=1;$i -le 350;$i++){
 $g=$page.Shapes.Item($i);$label=$g.Name.Substring(10)
 if($g.Type -ne 7 -or $g.Shapes.Count -ne 30 -or $states.ContainsKey($label)){throw 'Unexpected group structure'}
 $texts=@{}
 foreach($j in $textIndices){$s=$g.Shapes.Item($j);if($s.Type -ne 6 -or $s.Text.Story.Text -notin @('MEKANİKER','MECHANIC')){throw 'Unexpected text target'};$texts[$j]=ShapeState $s}
 foreach($j in $numberIndices){$s=$g.Shapes.Item($j);if($s.Type -ne 6 -or $s.Text.Story.Text -ne $label){throw 'Source number mismatch'}}
 $states[$label]=[pscustomobject]@{W=$g.SizeWidth;H=$g.SizeHeight;X=$g.LeftX;Y=$g.TopY;Text=$texts}
 if($label -in @('001','175','350')){$snap=@{};foreach($j in 1..30){if($j -in $textIndices){continue};$snap[$j]=ShapeState $g.Shapes.Item($j)};$artworkSamples[$label]=$snap}
}
$doc.BeginCommandGroup('Yalnız MEKANİKER ve MECHANIC yazılarını GÖREVLİ yap')
$app.Optimization=$true;$changed=0
try{
 for($i=1;$i -le 350;$i++){
  $g=$page.Shapes.Item($i);$label=$g.Name.Substring(10)
  foreach($j in $textIndices){
   $s=$g.Shapes.Item($j);$before=$states[$label].Text[$j]
   $s.Text.Story.Text='GÖREVLİ'
   $s.SetSize($before.W,$before.H)
   $s.Move($before.CX-$s.CenterX,$before.CY-$s.CenterY)
   $changed++
  }
  if($i%70 -eq 0){Write-Output "Updated: $i / 350"}
 }
 $doc.ClearSelection()
}finally{$app.Optimization=$false;$doc.EndCommandGroup();$app.Refresh()}
if($changed -ne 1400){throw 'Changed text count mismatch'}
$doc.Save();if($doc.Dirty){throw 'Save failed'}
$doc.Close();$null=$app.OpenDocument($target)
$doc=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $target){$doc=$d}}
if(!$doc -or $doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 350){throw 'Saved document structure mismatch'}
$page=$doc.ActivePage;$labels=@{};$verified=0;$numbers=0
if([Math]::Abs($page.SizeWidth-$pageWidth) -gt 0.000001 -or [Math]::Abs($page.SizeHeight-$pageHeight) -gt 0.000001){throw 'Page dimensions changed'}
for($i=1;$i -le 350;$i++){
 $g=$page.Shapes.Item($i);$label=$g.Name.Substring(10);$prior=$states[$label]
 if(!$prior -or $labels.ContainsKey($label) -or $g.Shapes.Count -ne 30 -or [Math]::Abs($g.SizeWidth-$prior.W) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$prior.H) -gt 0.00005 -or [Math]::Abs($g.LeftX-$prior.X) -gt 0.00005 -or [Math]::Abs($g.TopY-$prior.Y) -gt 0.00005){throw 'Group or placement changed'}
 $labels[$label]=$true
 foreach($j in $textIndices){
  $s=$g.Shapes.Item($j);$before=$prior.Text[$j]
  if($s.Text.Story.Text -ne 'GÖREVLİ' -or $s.Text.Story.Font -ne $before.Font -or $s.Name -ne $before.Name -or [Math]::Abs($s.SizeWidth-$before.W) -gt 0.00005 -or [Math]::Abs($s.SizeHeight-$before.H) -gt 0.00005 -or [Math]::Abs($s.CenterX-$before.CX) -gt 0.00005 -or [Math]::Abs($s.CenterY-$before.CY) -gt 0.00005 -or [Math]::Abs($s.RotationAngle-$before.Angle) -gt 0.00001 -or (ColorValue $s.Fill.UniformColor) -ne $before.Fill){throw "Text dimensions or appearance mismatch: $label"}
  $verified++
 }
 foreach($j in $numberIndices){if($g.Shapes.Item($j).Text.Story.Text -ne $label){throw 'Number changed'};$numbers++}
 if($artworkSamples.ContainsKey($label)){
  foreach($j in $artworkSamples[$label].Keys){
   $a=$artworkSamples[$label][$j];$b=ShapeState $g.Shapes.Item($j)
   foreach($field in @('Type','Name','Nodes','Paths','Fill','Outline','Text','Font','Children')){if($a.$field -ne $b.$field){throw "Untouched artwork changed: $field"}}
   foreach($field in @('W','H','CX','CY','Angle','OutlineWidth','Size')){if([Math]::Abs([double]$a.$field-[double]$b.$field) -gt 0.00005){throw "Untouched artwork geometry changed: $field"}}
  }
 }
 if($i%70 -eq 0){Write-Output "Verified: $i / 350"}
}
if($verified -ne 1400 -or $numbers -ne 1400 -or $labels.Count -ne 350){throw 'Final counts mismatch'}
$doc.Activate();$doc.ClearSelection();$doc.ActiveWindow.ActiveView.ToFitPage();$app.Refresh()
[pscustomobject]@{File=$doc.FullFileName;Groups=350;Replacements=$verified;NewText='GÖREVLİ';TextDimensionsPositionsOrientationsPreserved=$true;NumbersUnchanged=$numbers;ArtworkAndLayoutPreserved=$true;PageWidthCM=$page.SizeWidth*2.54;SavedAndReopened=$true;SavedClean=(!$doc.Dirty)}|ConvertTo-Json|Tee-Object -FilePath ($root+'\work\mekanik-yan-gorevli-result.json')
