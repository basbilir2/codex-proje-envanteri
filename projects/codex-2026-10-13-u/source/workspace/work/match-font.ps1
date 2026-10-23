$ErrorActionPreference='Stop'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$work=$app.ActiveDocument
if($work.FullFileName -notlike '*bracelet-working.cdr'){throw 'Wrong working document'}
$original=$work.ActivePage.Shapes.Item(3)
$points=@(for($i=1;$i -le $original.Curve.Nodes.Count;$i++){$p=$original.Curve.Nodes.Item($i);[pscustomobject]@{X=($p.PositionX-$original.LeftX)/$original.SizeWidth;Y=($p.PositionY-$original.BottomY)/$original.SizeHeight}})
$scratch=$app.CreateDocument()
$fonts=@('Arial','Arial Black','Arial Narrow','Arial Rounded MT Bold','Tahoma','Verdana','Calibri','Bahnschrift','Franklin Gothic Medium','Franklin Gothic Demi','Franklin Gothic Heavy','DIN2014-ExtraBold','Helvetica','Montserrat','Montserrat Black','Myriad Pro')
$results=@()
$app.Optimization=$true
try{
foreach($font in $fonts){foreach($bold in @(0,1)){
 $s=$scratch.ActiveLayer.CreateArtisticText(0,0,'001',0,0,$font,12,$bold,0)
 $s.ConvertToCurves()
 if($s.Type -eq 3 -and $s.Curve.Nodes.Count -eq 53){
  $sum=0
  for($i=1;$i -le 53;$i++){$p=$s.Curve.Nodes.Item($i);$x=($p.PositionX-$s.LeftX)/$s.SizeWidth;$y=($p.PositionY-$s.BottomY)/$s.SizeHeight;$best=100;foreach($q in $points){$d=($x-$q.X)*($x-$q.X)+($y-$q.Y)*($y-$q.Y);if($d -lt $best){$best=$d}};$sum+=$best}
  $results += [pscustomobject]@{Font=$font;Bold=$bold;Error=[Math]::Sqrt($sum/53);Aspect=$s.SizeWidth/$s.SizeHeight}
 }
}}
}finally{$app.Optimization=$false;$scratch.Close();$work.Activate();$app.Refresh()}
$results | Sort-Object Error | Select-Object -First 8 | ConvertTo-Json
$results | Sort-Object Error | Select-Object -First 1 | ConvertTo-Json | Set-Content -LiteralPath 'C:\Users\USER\Documents\Codex\2026-10-13\u\work\matched-font.json' -Encoding UTF8
