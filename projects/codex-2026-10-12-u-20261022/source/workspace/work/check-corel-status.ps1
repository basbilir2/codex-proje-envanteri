$ErrorActionPreference='Stop'
$corel=New-Object -ComObject 'CorelDRAW.Application.17'
$doc=$corel.ActiveDocument
[pscustomobject]@{Name=$doc.Name;Count=$doc.ActivePage.Shapes.Count;PageWidthMM=$doc.ActivePage.SizeWidth*25.4;PageHeightMM=$doc.ActivePage.SizeHeight*25.4} | ConvertTo-Json
for($i=1;$i -le $doc.ActivePage.Shapes.Count;$i++){
 $g=$doc.ActivePage.Shapes.Item($i)
 if($g.Name -in @('TMF_001','TMF_111','TMF_250')) {
  for($j=1;$j -le $g.Shapes.Count;$j++) {
   $s=$g.Shapes.Item($j)
   if([int]$s.Type -eq 6 -and $s.Text.Story.Text -match '^\d{3}$') {
    [pscustomobject]@{Group=$g.Name;Text=$s.Text.Story.Text;Font=$s.Text.Story.Font;Size=$s.Text.Story.Size;Height=$s.SizeHeight;Width=$s.SizeWidth;Left=$g.LeftX;Top=$g.TopY;PageLeft=$doc.ActivePage.LeftX;PageTop=$doc.ActivePage.TopY} | ConvertTo-Json
   }
  }
 }
}
$corel.ActiveWindow.ActiveView.ToFitPage()
$corel.Refresh()
