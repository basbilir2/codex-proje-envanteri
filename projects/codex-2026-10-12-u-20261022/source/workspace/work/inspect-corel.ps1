$ErrorActionPreference = 'Stop'
$corel = New-Object -ComObject 'CorelDRAW.Application.17'
$doc = $corel.ActiveDocument
[pscustomobject]@{Version=$corel.Version;Name=$doc.Name;FullFileName=$doc.FullFileName;Unit=$doc.Unit;PageCount=$doc.Pages.Count;Width=$doc.ActivePage.SizeWidth;Height=$doc.ActivePage.SizeHeight;Shapes=$doc.ActivePage.Shapes.Count;Dirty=$doc.Dirty} | ConvertTo-Json
function ReadShapes($shapes,$path) {
 for($i=1;$i -le $shapes.Count;$i++) {
  $s=$shapes.Item($i); $p="$path/$i"
  $text=$null; if([int]$s.Type -eq 6){$text=$s.Text.Story.Text}
  [pscustomobject]@{Path=$p;Type=[int]$s.Type;Name=$s.Name;Left=$s.LeftX;Top=$s.TopY;Width=$s.SizeWidth;Height=$s.SizeHeight;Text=$text} | ConvertTo-Json -Compress
  if([int]$s.Type -eq 7){ReadShapes $s.Shapes $p}
 }
}
ReadShapes $doc.ActivePage.Shapes ''

