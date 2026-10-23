$ErrorActionPreference='Stop'
$corel=New-Object -ComObject 'CorelDRAW.Application.17'
$doc=$corel.ActiveDocument
if($doc.Name -ne 'TMF-dizilim.cdr' -or $doc.ActivePage.Shapes.Count -ne 250){throw 'Dizilim beklenen durumda değil'}
$page=$doc.ActivePage
$base=$null
for($i=1;$i -le $page.Shapes.Count;$i++){$s=$page.Shapes.Item($i);if($s.Name -eq 'TMF_001'){$base=$s;break}}
$w=[double]$base.SizeWidth; $h=[double]$base.SizeHeight; $cols=8; $rows=32
$left=[double]$page.LeftX; $top=[double]$page.TopY
if($doc.Pages.Count -ne 1 -or $doc.ActivePage.Shapes.Count -ne 250){throw 'Sayfa/adet kontrolü başarısız'}
$records=@()
for($i=1;$i -le $page.Shapes.Count;$i++){
 $g=$page.Shapes.Item($i)
 if([int]$g.Type -ne 7 -or $g.Shapes.Count -ne 6){throw 'Tasarım yapısı değişti'}
 $num=$null
 for($j=1;$j -le $g.Shapes.Count;$j++){$s=$g.Shapes.Item($j); if([int]$s.Type -eq 6 -and $s.Text.Story.Text -match '^\d{3}$'){$num=$s}}
 $n=[int]$num.Text.Story.Text
 $col=($n-1)%$cols; $row=[int][Math]::Floor(($n-1)/$cols)
 if([Math]::Abs($g.LeftX-($left+$col*$w)) -gt 0.00005 -or [Math]::Abs($g.TopY-($top-$row*$h)) -gt 0.00005){throw "Konum hatası: $n"}
 if([Math]::Abs($g.SizeWidth-$w) -gt 0.00005 -or [Math]::Abs($g.SizeHeight-$h) -gt 0.00005){throw "Ölçü hatası: $n"}
 if($g.RightX -gt $page.RightX+0.00005 -or $g.BottomY -lt $page.BottomY-0.00005 -or $g.LeftX -lt $page.LeftX-0.00005 -or $g.TopY -gt $page.TopY+0.00005){throw "Sayfa taşması: $n"}
 if($num.Text.Story.Font -ne 'Franklin Gothic Heavy' -or [Math]::Abs($num.Text.Story.Size-75.264) -gt 0.00005){throw "Numara biçimi değişti: $n"}
 $records += [pscustomobject]@{Number=$num.Text.Story.Text;Row=$row+1;Column=$col+1;LeftMM=($g.LeftX-$left)*25.4;TopMM=($top-$g.TopY)*25.4;WidthMM=$g.SizeWidth*25.4;HeightMM=$g.SizeHeight*25.4}
}
$sorted=@($records | Sort-Object {[int]$_.Number})
if(($sorted.Number -join ',') -ne ((1..250 | ForEach-Object {$_.ToString('000')}) -join ',')){throw '001-250 tam ve benzersiz değil'}
$final='C:\Users\USER\Documents\Codex\2026-10-12\u\outputs\TMF_001-250_128cm.cdr'
if(Test-Path -LiteralPath $final){throw 'Sonuç dosyası zaten var'}
$doc.SaveAs($final)
$sourceHash=(Get-FileHash -LiteralPath 'C:\Users\USER\Downloads\aassa.cdr.zip' -Algorithm SHA256).Hash
if($sourceHash -ne (Get-Content -LiteralPath 'C:\Users\USER\Documents\Codex\2026-10-12\u\work\source-sha256.txt').Trim()){throw 'Kaynak dosya değişti'}
$sorted | ConvertTo-Json | Set-Content -LiteralPath 'C:\Users\USER\Documents\Codex\2026-10-12\u\work\layout-check.json' -Encoding UTF8
$corel.ActiveWindow.ActiveView.ToFitPage()
[pscustomobject]@{File=$doc.FullFileName;Pages=$doc.Pages.Count;Count=$page.Shapes.Count;Columns=$cols;Rows=$rows;WidthCM=$page.SizeWidth*2.54;HeightCM=$page.SizeHeight*2.54;DesignWidthCM=$w*2.54;DesignHeightCM=$h*2.54;OccupiedWidthCM=$cols*$w*2.54;LastRow=($sorted | Where-Object Row -eq 32).Number;SourceUnchanged=$true;Saved=(-not $doc.Dirty)} | ConvertTo-Json

$corel.Refresh()
