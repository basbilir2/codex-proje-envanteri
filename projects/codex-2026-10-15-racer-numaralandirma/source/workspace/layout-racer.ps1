param(
    [string]$SourceFile='C:\Users\USER\Downloads\yarısss.cdr.zip',
    [string]$FinalFile='C:\Users\USER\Downloads\Racer_001-150_59cm.cdr'
)
$ErrorActionPreference='Stop'
$workRoot=Split-Path -Parent $PSCommandPath
$workingFile=Join-Path $workRoot ([IO.Path]::GetFileNameWithoutExtension($FinalFile)+'-calisma.cdr')
$app=New-Object -ComObject 'CorelDRAW.Application.17'
$source=$app.ActiveDocument
if($source.FullFileName -ne $sourceFile -or $source.Dirty -or $source.ActivePage.Shapes.Count -ne 69){throw 'Open source differs from inspected source.'}
if(Test-Path -LiteralPath $finalFile){throw 'Output already exists; do not overwrite.'}
$sourceHash=(Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash
Copy-Item -LiteralPath $sourceFile -Destination $workingFile -ErrorAction Stop
if((Get-FileHash -LiteralPath $workingFile).Hash -ne $sourceHash){throw 'Source copy verification failed.'}
$doc=$app.OpenDocument($workingFile)
if($doc.FullFileName -ne $workingFile -or $doc.ActivePage.Shapes.Count -ne 69){throw 'Working copy verification failed.'}
$previousOptimization=$app.Optimization
$doc.BeginCommandGroup('RACER 001-150 - 59 cm')
$app.Optimization=$true
$numberIndices=@();$template=@();$sourceNumberStyle=@{}
try {
    $page=$doc.ActivePage
    $base=$page.Shapes.All().Group()
    $base.Name='Racer_001'
    $width=[double]$base.SizeWidth;$height=[double]$base.SizeHeight
    if([math]::Abs($width*25.4-250) -gt .01 -or [math]::Abs($height*25.4-20) -gt .01){throw 'Template dimensions changed.'}
    for($j=1;$j -le $base.Shapes.Count;$j++){
        $s=$base.Shapes.Item($j)
        $text=$null
        if($s.Type -eq 6){$text=$s.Text.Story.Text}
        if($s.Type -eq 6 -and $text -eq '001'){
            $numberIndices+=$j
            $sourceNumberStyle[$j]=[pscustomobject]@{Font=$s.Text.Story.Font;Size=[double]$s.Text.Story.Size;Angle=[double]$s.RotationAngle;CenterX=[double]$s.CenterX-$base.LeftX;CenterY=[double]$s.CenterY-$base.TopY;FillType=$s.Fill.Type;OutlineType=$s.Outline.Type}
        } else {
            $template+=[pscustomobject]@{Index=$j;Type=[int]$s.Type;Name=$s.Name;Text=$text;Left=[double]$s.LeftX-$base.LeftX;Top=[double]$s.TopY-$base.TopY;Width=[double]$s.SizeWidth;Height=[double]$s.SizeHeight;Angle=[double]$s.RotationAngle;FillType=[int]$s.Fill.Type;OutlineType=[int]$s.Outline.Type;OutlineWidth=[double]$s.Outline.Width}
        }
    }
    if($numberIndices.Count -ne 4){throw 'Expected exactly four repeated number fields in each design.'}
    # The full design and its orientation stay at the original 250 x 20 mm.
    $pageWidth=590.0/25.4
    $margin=.1/25.4
    $columns=[int][math]::Floor(($pageWidth-2*$margin)/$width)
    $rows=[int][math]::Ceiling(150.0/$columns)
    if($columns -ne 2 -or $rows -ne 75){throw 'Unexpected wrap geometry.'}
    $page.SetSize($pageWidth,$rows*$height+2*$margin)
    $left=[double]$page.LeftX+$margin;$top=[double]$page.TopY-$margin
    $base.Move($left-$base.LeftX,$top-$base.TopY)
    for($n=2;$n -le 150;$n++){
        $g=$base.Duplicate(0,0)
        $label=$n.ToString('000');$g.Name='Racer_'+$label
        foreach($index in $numberIndices){
            $number=$g.Shapes.Item($index)
            $cx=[double]$number.CenterX;$cy=[double]$number.CenterY
            $number.Text.Story.Text=$label
            $number.Move($cx-$number.CenterX,$cy-$number.CenterY)
        }
        $column=($n-1)%$columns;$row=[int][math]::Floor(($n-1)/$columns)
        $g.Move(($left+$column*$width)-$g.LeftX,($top-$row*$height)-$g.TopY)
    }
    if($page.Shapes.Count -ne 150){throw 'Count mismatch before saving.'}
    $doc.ClearSelection()
} finally {
    $app.Optimization=$previousOptimization
    $doc.EndCommandGroup()
}
if($source.Dirty -or (Get-FileHash -LiteralPath $sourceFile).Hash -ne $sourceHash){throw 'Source changed unexpectedly.'}
$doc.SaveAs($finalFile,$app.CreateStructSaveAsOptions())
if($doc.Dirty -or -not (Test-Path -LiteralPath $finalFile)){throw 'Save did not complete.'}
$doc.Close()
$null=$app.OpenDocument($finalFile)
$doc=$null
foreach($openDoc in $app.Documents){if($openDoc.FullFileName -eq $finalFile){$doc=$openDoc;break}}
if($null -eq $doc){throw 'Saved output was not reopened.'}
$doc.Activate()
$page=$doc.ActivePage
if($doc.Pages.Count -ne 1 -or $page.Shapes.Count -ne 150){throw 'Reopened page/count mismatch.'}
$numbers=@();$checkedNumbers=0;$checkedArt=0
$left=[double]$page.LeftX+$margin;$top=[double]$page.TopY-$margin
$tol=.00005
foreach($g in $page.Shapes){
    if($g.Type -ne 7 -or $g.Shapes.Count -ne 69 -or $g.Name -notmatch '^Racer_(\d{3})$'){throw 'Reopened design structure mismatch.'}
    $label=$Matches[1];$n=[int]$label;$numbers+=$label
    if($n -lt 1 -or $n -gt 150 -or $label -ne $n.ToString('000')){throw 'Number format/range mismatch.'}
    $column=($n-1)%$columns;$row=[int][math]::Floor(($n-1)/$columns)
    if([math]::Abs($g.LeftX-($left+$column*$width)) -gt $tol -or [math]::Abs($g.TopY-($top-$row*$height)) -gt $tol){throw "Position mismatch: $label"}
    if([math]::Abs($g.SizeWidth-$width) -gt $tol -or [math]::Abs($g.SizeHeight-$height) -gt $tol){throw "Design scaled: $label"}
    if($g.LeftX -lt $page.LeftX-$tol -or $g.RightX -gt $page.RightX+$tol -or $g.TopY -gt $page.TopY+$tol -or $g.BottomY -lt $page.BottomY-$tol){throw "Page overflow: $label"}
    foreach($index in $numberIndices){
        $s=$g.Shapes.Item($index);$style=$sourceNumberStyle[$index]
        if($s.Type -ne 6 -or $s.Text.Story.Text -ne $label){throw "Number field mismatch: $label"}
        if($s.Text.Story.Font -ne $style.Font -or [math]::Abs($s.Text.Story.Size-$style.Size) -gt .00001 -or [math]::Abs($s.RotationAngle-$style.Angle) -gt .00001){throw "Number styling changed: $label"}
        if([math]::Abs(($s.CenterX-$g.LeftX)-$style.CenterX) -gt $tol -or [math]::Abs(($s.CenterY-$g.TopY)-$style.CenterY) -gt $tol){throw "Number no longer centered: $label"}
        if($s.Fill.Type -ne $style.FillType -or $s.Outline.Type -ne $style.OutlineType){throw "Number fill/outline mismatch: $label"}
        $checkedNumbers++
    }
    if($n -in @(1,75,150)){
        foreach($art in $template){
            $s=$g.Shapes.Item($art.Index)
            if($s.Type -ne $art.Type -or $s.Name -ne $art.Name -or $s.Fill.Type -ne $art.FillType -or $s.Outline.Type -ne $art.OutlineType -or [math]::Abs($s.Outline.Width-$art.OutlineWidth) -gt .000001){throw "Artwork style changed: $label"}
            if([math]::Abs(($s.LeftX-$g.LeftX)-$art.Left) -gt $tol -or [math]::Abs(($s.TopY-$g.TopY)-$art.Top) -gt $tol -or [math]::Abs($s.SizeWidth-$art.Width) -gt $tol -or [math]::Abs($s.SizeHeight-$art.Height) -gt $tol -or [math]::Abs($s.RotationAngle-$art.Angle) -gt .00001){throw "Artwork geometry changed: $label"}
            if($s.Type -eq 6 -and $s.Text.Story.Text -ne $art.Text){throw "Artwork text changed: $label"}
            $checkedArt++
        }
    }
}
if((($numbers|Sort-Object)-join ',') -ne ((1..150|ForEach-Object{$_.ToString('000')})-join ',')){throw 'Duplicate or missing sequence.'}
if([math]::Abs($page.SizeWidth*25.4-590) -gt .0001){throw 'Page is not 59 cm wide.'}
if($source.Dirty -or (Get-FileHash -LiteralPath $sourceFile).Hash -ne $sourceHash){throw 'Source preservation check failed.'}
$doc.ClearSelection()
$app.ActiveWindow.ActiveView.ToFitPage()
$app.Refresh()
$result=[pscustomobject]@{File=$doc.FullFileName;SourceFile=$sourceFile;SourceSHA256=$sourceHash;SourceUnchanged=$true;SavedAndReopened=$true;DesignCount=150;Numbers='001-150';RepeatedNumberFields=4;NumberFieldsChecked=$checkedNumbers;ArtworkObjectsSampled=$checkedArt;OriginalDesignWidthCM=$width*2.54;OriginalDesignHeightCM=$height*2.54;PageWidthCM=$page.SizeWidth*2.54;PageHeightCM=$page.SizeHeight*2.54;Columns=$columns;Rows=$rows;FontSizeRotationAndCentersPreserved=$true;OriginalArtworkAndOutlinesPreserved=$true;Bytes=(Get-Item -LiteralPath $finalFile).Length}
$result|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $workRoot ([IO.Path]::GetFileNameWithoutExtension($FinalFile)+'-sonuc.json')) -Encoding UTF8
$result|ConvertTo-Json -Depth 5
