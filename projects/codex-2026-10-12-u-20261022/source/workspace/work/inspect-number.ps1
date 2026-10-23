$ErrorActionPreference='Stop'
$corel=New-Object -ComObject 'CorelDRAW.Application.17'
$doc=$corel.ActiveDocument
$n=$doc.ActivePage.Shapes.Item(1)
[pscustomobject]@{Text=$n.Text.Story.Text;Font=$n.Text.Story.Font;Size=$n.Text.Story.Size;Bold=$n.Text.Story.Bold;Italic=$n.Text.Story.Italic;Alignment=$n.Text.Story.Alignment;Reference=$doc.ReferencePoint;DocCount=$corel.Documents.Count;Layer=$n.Layer.Name;PageLeft=$doc.ActivePage.LeftX;PageTop=$doc.ActivePage.TopY;ShapeCount=$doc.ActivePage.Shapes.All.Count} | ConvertTo-Json
