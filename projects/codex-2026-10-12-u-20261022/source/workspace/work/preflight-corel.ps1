$ErrorActionPreference='Stop'
$corel=New-Object -ComObject 'CorelDRAW.Application.17'
$source=$corel.ActiveDocument
if($source.FullFileName -ne 'C:\Users\USER\Downloads\aassa.cdr.zip' -or $source.Dirty){throw 'Kaynak kimliği veya kayıt durumu değişti'}
$workPath='C:\Users\USER\Documents\Codex\2026-10-12\u\work\TMF-dizilim.cdr'
if(Test-Path -LiteralPath $workPath){throw 'Çalışma kopyası zaten var'}
Copy-Item -LiteralPath $source.FullFileName -Destination $workPath
$h1=(Get-FileHash -LiteralPath $source.FullFileName -Algorithm SHA256).Hash
$h2=(Get-FileHash -LiteralPath $workPath -Algorithm SHA256).Hash
if($h1 -ne $h2){throw 'Kopya doğrulanamadı'}
$h1 | Set-Content -LiteralPath 'C:\Users\USER\Documents\Codex\2026-10-12\u\work\source-sha256.txt'
$doc=$corel.OpenDocument($workPath)
$doc.BeginCommandGroup('001-250 dizilim')
try {
 $g=$doc.ActivePage.Shapes.All().Group()
 $g.Name='TMF_001'
 $num=$null
 for($i=1;$i -le $g.Shapes.Count;$i++){ $s=$g.Shapes.Item($i); if([int]$s.Type -eq 6 -and $s.Text.Story.Text -eq '001'){$num=$s} }
 if($null -eq $num){throw 'Numara nesnesi bulunamadı'}
 $copy=$g.Duplicate($g.SizeWidth,0)
 $copy.Name='TMF_002'
 for($i=1;$i -le $copy.Shapes.Count;$i++){
  $s=$copy.Shapes.Item($i)
  if([int]$s.Type -eq 6 -and $s.Text.Story.Text -eq '001'){
   $left=$s.LeftX; $top=$s.TopY; $s.Text.Story.Text='002'; $s.Move($left-$s.LeftX,$top-$s.TopY)
   [pscustomobject]@{OriginalFont=$num.Text.Story.Font;NewFont=$s.Text.Story.Font;OriginalWidth=$num.SizeWidth;NewWidth=$s.SizeWidth;OriginalHeight=$num.SizeHeight;NewHeight=$s.SizeHeight;Text=$s.Text.Story.Text} | ConvertTo-Json
  }
 }
 $doc.ClearSelection()
 $corel.ActiveWindow.ActiveView.ToFitAllObjects()
 [pscustomobject]@{Name=$doc.Name;Groups=$doc.ActivePage.Shapes.Count;DesignWidthMM=$g.SizeWidth*25.4;DesignHeightMM=$g.SizeHeight*25.4;Children=$g.Shapes.Count;SourceHash=$h1} | ConvertTo-Json
} finally {$doc.EndCommandGroup()}
