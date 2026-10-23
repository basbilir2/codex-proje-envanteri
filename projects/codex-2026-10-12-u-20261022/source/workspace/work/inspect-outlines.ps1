$ErrorActionPreference='Stop'
$corel=New-Object -ComObject 'CorelDRAW.Application.17'
$doc=$corel.ActiveDocument
[pscustomobject]@{Name=$doc.Name;Path=$doc.FullFileName;Dirty=$doc.Dirty;Count=$doc.ActivePage.Shapes.Count} | ConvertTo-Json
$g=$doc.ActivePage.Shapes.Item(1)
for($j=1;$j -le $g.Shapes.Count;$j++){
 $s=$g.Shapes.Item($j)
 [pscustomobject]@{Index=$j;Type=[int]$s.Type;WidthMM=$s.SizeWidth*25.4;HeightMM=$s.SizeHeight*25.4;OutlineType=[int]$s.Outline.Type;OutlineWidthMM=$s.Outline.Width*25.4;Text=$(if([int]$s.Type -eq 6){$s.Text.Story.Text})} | ConvertTo-Json -Compress
}
