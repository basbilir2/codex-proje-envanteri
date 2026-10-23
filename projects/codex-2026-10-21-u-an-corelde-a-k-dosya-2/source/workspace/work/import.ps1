$ErrorActionPreference = 'Stop'
$app = New-Object -ComObject 'CorelDRAW.Application.17'
$doc = $app.ActiveDocument
if ($doc.Name -ne 'Untitled-1' -or $doc.ActivePage.Shapes.Count -ne 0) { throw 'Unexpected target document' }
$saveOptions = $app.CreateStructSaveAsOptions()
$doc.SaveAs('C:\Users\USER\Documents\Codex\2026-10-21\u-an-corelde-a-k-dosya-2\work\Acik_Corel_Oncesi.cdr', $saveOptions)
$doc.Unit = 3
$doc.ActivePage.SetSize(600,2100)
$importOptions = $app.CreateStructImportOptions()
$filter = $doc.ActiveLayer.ImportEx('C:\Users\USER\Documents\Codex\2026-10-21\u-an-corelde-a-k-dosya-2\outputs\Yali1925_19_A4_60cm_Dizilim.pdf',0,$importOptions)
$filter.Finish()
'IMPORT_COMPLETE'
