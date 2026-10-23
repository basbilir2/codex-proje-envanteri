$ErrorActionPreference='Stop'
$workRoot=Split-Path -Parent $PSCommandPath
$originalFile='C:\Users\USER\Downloads\yarısss.cdr.zip'
$priorFile='C:\Users\USER\Downloads\Racer_001-150_59cm.cdr'
$snapshotFile=Join-Path $workRoot 'Racer-YeniRenk-acik-surum.cdr'
$finalFile='C:\Users\USER\Downloads\Racer_YeniRenk_001-150_59cm.cdr'
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$source=$app.ActiveDocument
if($source.FullFileName -ne $originalFile -or $source.ActivePage.Shapes.Count -ne 69 -or -not $source.Dirty){throw 'Expected recolored live source is not active.'}
if((Test-Path -LiteralPath $snapshotFile) -or (Test-Path -LiteralPath $finalFile)){throw 'Do not overwrite an existing color output.'}
function Get-LiveSignature($document){
    $records=foreach($s in $document.ActivePage.Shapes){
        $fill='none';$text=$null
        if($s.Fill.Type -eq 1){$c=$s.Fill.UniformColor;$fill='{0}|{1}|{2}|{3}|{4}' -f $c.Type,$c.CMYKCyan,$c.CMYKMagenta,$c.CMYKYellow,$c.CMYKBlack}
        if($s.Type -eq 6){$text=$s.Text.Story.Text}
        [pscustomobject]@{ID=$s.StaticID;Type=$s.Type;Name=$s.Name;Left=$s.LeftX;Top=$s.TopY;Width=$s.SizeWidth;Height=$s.SizeHeight;Angle=$s.RotationAngle;Text=$text;FillType=$s.Fill.Type;FillColor=$fill;OutlineType=$s.Outline.Type;OutlineWidth=$s.Outline.Width}
    }
    return ($records|Sort-Object ID|ConvertTo-Json -Depth 5 -Compress)
}
$liveBefore=Get-LiveSignature $source
$originalHash=(Get-FileHash -LiteralPath $originalFile).Hash
$priorHash=(Get-FileHash -LiteralPath $priorFile).Hash
$backupFile=Join-Path $workRoot 'Racer-disk-kaynagi-yeni-renk-oncesi.cdr'
if(Test-Path -LiteralPath $backupFile){if((Get-FileHash -LiteralPath $backupFile).Hash -ne $originalHash){throw 'Existing disk backup differs.'}}else{Copy-Item -LiteralPath $originalFile -Destination $backupFile}
$snapshot=$source.Clone()
if($null -eq $snapshot -or $snapshot.ActivePage.Shapes.Count -ne 69){throw 'In-memory snapshot structure differs.'}
$snapshot.SaveAs($snapshotFile,$app.CreateStructSaveAsOptions())
if($snapshot.FullFileName -ne $snapshotFile -or $snapshot.Dirty -or $source.FullFileName -ne $originalFile -or -not $source.Dirty){throw 'Live snapshot isolation failed.'}
if((Get-LiveSignature $source) -ne $liveBefore){throw 'Original live artwork was changed.'}
# Clone is deliberately windowless and is not listed in Documents. Open the
# saved snapshot for the existing layout adapter, without activating the clone.
$null=$app.OpenDocument($snapshotFile)
$visibleSnapshot=$null
foreach($d in $app.Documents){if($d.FullFileName -eq $snapshotFile){$visibleSnapshot=$d;break}}
if($null -eq $visibleSnapshot){throw 'Saved live snapshot did not open.'}
$visibleSnapshot.Activate()
& (Join-Path $workRoot 'layout-racer.ps1') -SourceFile $snapshotFile -FinalFile $finalFile
if((Get-FileHash -LiteralPath $priorFile).Hash -ne $priorHash -or (Get-FileHash -LiteralPath $originalFile).Hash -ne $originalHash){throw 'Previous result or original disk file changed.'}
if(-not $source.Dirty -or (Get-LiveSignature $source) -ne $liveBefore){throw 'Original unsaved edits were changed.'}
$output=$null
foreach($d in $app.Documents){if($d.FullFileName -eq $finalFile){$output=$d;break}}
if($null -eq $output){throw 'New output is not open.'}
$whiteLogoFields=0
foreach($g in $output.ActivePage.Shapes){
    $logos=0
    foreach($s in $g.Shapes){
        if($s.Name -eq 'Artwork_09'){
            if($s.Fill.Type -ne 1 -or $s.Outline.Type -ne 0){throw 'Recolored logo fill/outline changed.'}
            $c=$s.Fill.UniformColor
            if($c.Type -ne 2 -or $c.CMYKCyan -ne 0 -or $c.CMYKMagenta -ne 0 -or $c.CMYKYellow -ne 0 -or $c.CMYKBlack -ne 0){throw 'New white logo color was not preserved.'}
            $logos++;$whiteLogoFields++
        }
    }
    if($logos -ne 3){throw 'Incorrect logo count in a copy.'}
}
$output.Activate()
if(-not $visibleSnapshot.Dirty){$visibleSnapshot.Close();$output.Activate()}
$result=[pscustomobject]@{File=$finalFile;Designs=150;Numbers='001-150';Columns=2;Rows=75;PageWidthCM=$output.ActivePage.SizeWidth*2.54;PageHeightCM=$output.ActivePage.SizeHeight*2.54;NewWhiteLogoFieldsChecked=$whiteLogoFields;NewColorsPreserved=$true;PriorResultUnchanged=$true;OriginalLiveEditsPreserved=$true;OriginalDiskFileUnchanged=$true;LiveSnapshot=$snapshotFile;PriorResultSHA256=$priorHash;SavedAndReopened=$true}
$result|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $workRoot 'yeni-renk-dogrulama.json') -Encoding UTF8
$result|ConvertTo-Json -Depth 4
