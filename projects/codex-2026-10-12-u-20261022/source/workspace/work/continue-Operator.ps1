$ErrorActionPreference='Stop'
$corel=New-Object -ComObject 'CorelDRAW.Application.17'
$source=$corel.ActiveDocument
$sourceFile='C:\Users\USER\Downloads\tugrrrullllll.cdr.zip'
if($source.FullFileName -ne 'C:\Users\USER\Documents\Codex\2026-10-12\u\work\Operator-dizilim-20261012-180115.cdr' -or $source.ActivePage.Shapes.Count -ne 20){throw 'Çalışma kopyası beklenen durumda değil'}
$sourceHash=(Get-FileHash -LiteralPath $sourceFile).Hash
$sourceDirty=$source.Dirty
$final='C:\Users\USER\Documents\Codex\2026-10-12\u\outputs\Operator_001-250_128cm.cdr'
if(Test-Path -LiteralPath $final){throw 'Sonuç dosyası zaten var'}
$doc=$source.Clone()
if($doc.ActivePage.Shapes.Count -ne 20){throw 'Kopya yapısı doğrulanamadı'}
$doc.BeginCommandGroup('001-250, 128 cm, dış çizgi korunarak')
$corel.Optimization=$true
try {
 $page=$doc.ActivePage
 $base=$page.Shapes.All().Group()
 $base.Name='Operator_001'
 $numIndex=0; $bgIndex=0
 for($j=1;$j -le $base.Shapes.Count;$j++){
  $s=$base.Shapes.Item($j)
  if([int]$s.Type -eq 6 -and $s.Text.Story.Text -eq '001'){$numIndex=$j}
  if([int]$s.Type -eq 1 -and [Math]::Abs($s.SizeWidth-$base.SizeWidth) -lt 0.00005 -and [Math]::Abs($s.SizeHeight-$base.SizeHeight) -lt 0.00005){$bgIndex=$j}
 }
 if($numIndex -eq 0 -or $bgIndex -eq 0){throw 'Numara veya dış çerçeve bulunamadı'}
 $number=$base.Shapes.Item($numIndex)
 $font=$number.Text.Story.Font; $fontSize=$number.Text.Story.Size
 $bg=$base.Shapes.Item($bgIndex)
 $outlineType=[int]$bg.Outline.Type; $outlineWidth=[double]$bg.Outline.Width
 if($outlineType -ne 1){throw 'Dış çizgi beklenen durumda değil'}
 $w=[double]$base.SizeWidth; $h=[double]$base.SizeHeight
 $pageWidth=1280.0/25.4
 $margin=$outlineWidth/2.0
 $cols=[int][Math]::Floor(($pageWidth-2*$margin)/$w)
 $rows=[int][Math]::Ceiling(250.0/$cols)
 if($cols -ne 8 -or $rows -ne 32){throw 'Dizilim hesabı beklenenden farklı'}
 $page.SetSize($pageWidth,$rows*$h+2*$margin)
 $left=[double]$page.LeftX+$margin; $top=[double]$page.TopY-$margin
 $base.Move($left-$base.LeftX,$top-$base.TopY)
 for($n=2;$n -le 250;$n++){
  $g=$base.Duplicate(0,0)
  $label=$n.ToString('000'); $g.Name='Operator_'+$label
  $num=$g.Shapes.Item($numIndex)
  $nx=$num.LeftX; $ny=$num.TopY
  $num.Text.Story.Text=$label
  $num.Move($nx-$num.LeftX,$ny-$num.TopY)
  $col=($n-1)%$cols; $row=[int][Math]::Floor(($n-1)/$cols)
  $g.Move(($left+$col*$w)-$g.LeftX,($top-$row*$h)-$g.TopY)
 }
 $doc.ClearSelection()
} finally {
 $corel.Optimization=$false
 $doc.EndCommandGroup()
}
if($doc.Pages.Count -ne 1 -or $page.Shapes.Count -ne 250){throw 'Sayfa veya adet hatası'}
$numbers=@()
for($i=1;$i -le $page.Shapes.Count;$i++){
 $g=$page.Shapes.Item($i)
 if([int]$g.Type -ne 7 -or $g.Shapes.Count -ne 20){throw 'Tasarım yapısı değişti'}
 $num=$g.Shapes.Item($numIndex); $label=$num.Text.Story.Text; $n=[int]$label
 if($label -ne $n.ToString('000') -or $g.Name -ne ('Operator_'+$label)){throw 'Numara doğrulaması başarısız'}
 $numbers+=$label
 $col=($n-1)%$cols; $row=[int][Math]::Floor(($n-1)/$cols)
 if([Math]::Abs($g.LeftX-($left+$col*$w)) -gt 0.00005 -or [Math]::Abs($g.TopY-($top-$row*$h)) -gt 0.00005){throw "Konum hatası: $label"}
 if([Math]::Abs($g.SizeWidth-$w) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$h) -gt 0.00005){throw "Ölçü hatası: $label"}
 if($g.LeftX-$margin -lt $page.LeftX-0.00005 -or $g.TopY+$margin -gt $page.TopY+0.00005 -or $g.RightX+$margin -gt $page.RightX+0.00005 -or $g.BottomY-$margin -lt $page.BottomY-0.00005){throw "Çizgi dahil sayfa taşması: $label"}
 $bg=$g.Shapes.Item($bgIndex)
 if([int]$bg.Outline.Type -ne $outlineType -or [Math]::Abs($bg.Outline.Width-$outlineWidth) -gt 0.000001){throw "Dış çizgi değişti: $label"}
 if($num.Text.Story.Font -ne $font -or [Math]::Abs($num.Text.Story.Size-$fontSize) -gt 0.000001){throw "Numara biçimi değişti: $label"}
}
if((($numbers | Sort-Object) -join ',') -ne ((1..250 | ForEach-Object {$_.ToString('000')}) -join ',')){throw '001-250 dizisi eksik veya tekrarlı'}
$corel.ActiveWindow.ActiveView.ToFitPage()
$doc.SaveAs($final,$corel.CreateStructSaveAsOptions())
if($doc.Dirty -or (Get-Item -LiteralPath $final).Length -eq 0){throw 'Kayıt doğrulanamadı'}
if((Get-FileHash -LiteralPath $sourceFile).Hash -ne $sourceHash -or $source.Dirty -ne $sourceDirty){throw 'Kaynak değişti'}
$corel.Refresh()
[pscustomobject]@{File=$doc.FullFileName;Count=$page.Shapes.Count;Columns=$cols;Rows=$rows;WidthCM=$page.SizeWidth*2.54;HeightCM=$page.SizeHeight*2.54;OutlinePreserved=$true;OutlineWidthMM=$outlineWidth*25.4;SourcePreserved=$true;Saved=$true} | ConvertTo-Json

