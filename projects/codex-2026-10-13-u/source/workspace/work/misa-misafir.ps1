$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$root='C:\Users\USER\Documents\Codex\2026-10-13\u'
$source=$app.ActiveDocument;$sourceFile='C:\Users\USER\Downloads\misa.cdr.zip'
$target=$root+'\outputs\Misafir_Bileklik_001-150_Yatay_59cm.cdr'
$backup=$root+'\work\misa-before-misafir-20261014.cdr'
if($source.FullFileName -ne $sourceFile -or $source.Dirty -or $source.Pages.Count -ne 1 -or $source.ActivePage.Shapes.Count -ne 150){throw 'Unexpected source document'}
foreach($p in @($target,$backup)){if(Test-Path -LiteralPath $p){throw 'Output path already exists'}}
Copy-Item -LiteralPath $sourceFile -Destination $backup
$sourceHash=(Get-FileHash -LiteralPath $sourceFile).Hash
if($sourceHash -ne (Get-FileHash -LiteralPath $backup).Hash){throw 'Backup mismatch'}
$clone=$source.Clone();$clone.SaveAs($target,$app.CreateStructSaveAsOptions());$clone.Close()
$doc=$app.OpenDocument($target);$page=$doc.ActivePage
function ColorValue($c){$v=$c.ToString();$v.Substring(0,$v.LastIndexOf(','))}
function ShapeState($s){
 $v=[ordered]@{Type=$s.Type;Name=$s.Name;W=$s.SizeWidth;H=$s.SizeHeight;CX=$s.CenterX;CY=$s.CenterY;Angle=$s.RotationAngle}
 if($s.Type -eq 3){$v.Nodes=$s.Curve.Nodes.Count;$v.Paths=$s.Curve.SubPaths.Count;$v.Fill=ColorValue $s.Fill.UniformColor;$v.Outline=$s.Outline.Type;$v.OutlineWidth=$s.Outline.Width}
 if($s.Type -eq 6){$v.Text=$s.Text.Story.Text;$v.Font=$s.Text.Story.Font;$v.Size=$s.Text.Story.Size;$v.Fill=ColorValue $s.Fill.UniformColor}
 if($s.Type -eq 7){$v.Children=$s.Shapes.Count}
 [pscustomobject]$v
}
$before=@{};$samples=@{};$pw=$page.SizeWidth;$ph=$page.SizeHeight;$targetCount=0
for($i=1;$i -le 150;$i++){
 $g=$page.Shapes.Item($i)
 if($g.Type -ne 7 -or $g.Shapes.Count -ne 30){throw 'Unexpected design structure'}
 $texts=@{};$numbers=@{}
 for($j=1;$j -le 30;$j++){
  $s=$g.Shapes.Item($j)
  if($s.Type -eq 6 -and $s.Text.Story.Text -eq 'GÖREVLİ'){$texts[$j]=ShapeState $s;$targetCount++}
  if($s.Name -like 'Numara_*'){$numbers[$j]=$s.Text.Story.Text}
 }
 if($texts.Count -ne 4 -or $numbers.Count -ne 4){throw 'Text or number slots mismatch'}
 $before[$i]=[pscustomobject]@{Name=$g.Name;W=$g.SizeWidth;H=$g.SizeHeight;X=$g.LeftX;Y=$g.TopY;Texts=$texts;Numbers=$numbers}
 if($i -in @(1,75,150)){$snapshot=@{};foreach($j in 1..30){if(!$texts.ContainsKey($j)){$snapshot[$j]=ShapeState $g.Shapes.Item($j)}};$samples[$i]=$snapshot}
}
if($targetCount -ne 600){throw 'Unexpected replacement count'}
$doc.BeginCommandGroup('Yalnız GÖREVLİ yazılarını MİSAFİR olarak değiştir');$app.Optimization=$true
try{
 for($i=1;$i -le 150;$i++){
  $g=$page.Shapes.Item($i)
  foreach($j in $before[$i].Texts.Keys){$s=$g.Shapes.Item($j);$old=$before[$i].Texts[$j];$s.Text.Story.Text='MİSAFİR';$s.SetSize($old.W,$old.H);$s.Move($old.CX-$s.CenterX,$old.CY-$s.CenterY)}
  if($i%50 -eq 0){Write-Output "Updated: $i / 150"}
 }
 $doc.ClearSelection()
}finally{$app.Optimization=$false;$doc.EndCommandGroup();$app.Refresh()}
$doc.Save();if($doc.Dirty){throw 'Save failed'}
$doc.Close();$null=$app.OpenDocument($target);$doc=$null
for($i=1;$i -le $app.Documents.Count;$i++){$d=$app.Documents.Item($i);if($d.FullFileName -eq $target){$doc=$d}}
if(!$doc -or $doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 150){throw 'Reopened document mismatch'}
$page=$doc.ActivePage;$verified=0;$numbersVerified=0
if([Math]::Abs($page.SizeWidth-$pw) -gt 0.000001 -or [Math]::Abs($page.SizeHeight-$ph) -gt 0.000001){throw 'Page dimensions changed'}
for($i=1;$i -le 150;$i++){
 $g=$page.Shapes.Item($i);$old=$before[$i]
 if($g.Name -ne $old.Name -or $g.Shapes.Count -ne 30 -or [Math]::Abs($g.SizeWidth-$old.W) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$old.H) -gt 0.00005 -or [Math]::Abs($g.LeftX-$old.X) -gt 0.00005 -or [Math]::Abs($g.TopY-$old.Y) -gt 0.00005){throw 'Design layout changed'}
 foreach($j in $old.Texts.Keys){
  $s=$g.Shapes.Item($j);$prior=$old.Texts[$j]
  if($s.Text.Story.Text -ne 'MİSAFİR' -or $s.Text.Story.Font -ne $prior.Font -or $s.Name -ne $prior.Name -or [Math]::Abs($s.SizeWidth-$prior.W) -gt 0.00005 -or [Math]::Abs($s.SizeHeight-$prior.H) -gt 0.00005 -or [Math]::Abs($s.CenterX-$prior.CX) -gt 0.00005 -or [Math]::Abs($s.CenterY-$prior.CY) -gt 0.00005 -or [Math]::Abs($s.RotationAngle-$prior.Angle) -gt 0.00001 -or (ColorValue $s.Fill.UniformColor) -ne $prior.Fill){throw 'Replacement text dimensions/style mismatch'}
  $verified++
 }
 foreach($j in $old.Numbers.Keys){if($g.Shapes.Item($j).Text.Story.Text -ne $old.Numbers[$j]){throw 'Number changed'};$numbersVerified++}
 if($samples.ContainsKey($i)){
  foreach($j in $samples[$i].Keys){$a=$samples[$i][$j];$b=ShapeState $g.Shapes.Item($j)
   foreach($field in @('Type','Name','Nodes','Paths','Fill','Outline','Text','Font','Children')){if($a.$field -ne $b.$field){throw 'Untouched artwork changed'}}
   foreach($field in @('W','H','CX','CY','Angle','OutlineWidth','Size')){if([Math]::Abs([double]$a.$field-[double]$b.$field) -gt 0.00005){throw 'Untouched artwork geometry changed'}}
  }
 }
 if($i%50 -eq 0){Write-Output "Verified: $i / 150"}
}
if($verified -ne 600 -or $numbersVerified -ne 600 -or $source.Dirty -or (Get-FileHash -LiteralPath $sourceFile).Hash -ne $sourceHash){throw 'Count or source integrity failure'}
$doc.Activate();$doc.ClearSelection();$doc.ActiveWindow.ActiveView.ToFitPage();$app.Refresh()
[pscustomobject]@{File=$doc.FullFileName;Designs=150;Replacements=$verified;NewText='MİSAFİR';NumberLabelsPreserved=$numbersVerified;DimensionsPositionsOrientationsPreserved=$true;ArtworkAndLayoutPreserved=$true;SourcePreserved=$true;SavedAndReopened=$true;SavedClean=(!$doc.Dirty)}|ConvertTo-Json|Tee-Object -FilePath ($root+'\work\misa-misafir-result.json')
