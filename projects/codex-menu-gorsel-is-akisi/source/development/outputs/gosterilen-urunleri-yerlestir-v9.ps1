Add-Type -AssemblyName System.Drawing
$dir='C:\Users\USER\Documents\Codex\2026-10-17\outputs'
$menu=[System.Drawing.Bitmap]::new((Join-Path $dir 'Corner-Cafe-tum-urunler-son-v8.png'))
$shown=[System.Drawing.Bitmap]::new('C:\Users\USER\.codex\generated_images\01a158fc-9453-7a63-b06e-bcbb358fe334\exec-b1426021-7479-45af-9d19-3ff95edcbb40.png')
$sheet=[System.Drawing.Bitmap]::new(2304,2304)
$sg=[System.Drawing.Graphics]::FromImage($sheet)
$sg.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$sg.DrawImage($shown,[System.Drawing.Rectangle]::new(0,0,2304,2304))
$sg.Dispose()
$g=[System.Drawing.Graphics]::FromImage($menu)
$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$mask=[System.Drawing.Bitmap]::new(1536,1024)
$mg=[System.Drawing.Graphics]::FromImage($mask)
$mg.Clear([System.Drawing.Color]::Black)
$expected=[System.Drawing.Bitmap]::new(1536,1024)
$eg=[System.Drawing.Graphics]::FromImage($expected)
$eg.Clear([System.Drawing.Color]::Black)
$eg.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$foods=Get-Content -LiteralPath (Join-Path $dir 'urunler-v8-konumlar.json') -Raw | ConvertFrom-Json
foreach($f in $foods){
 if($f.name -notin @('chicken_salad','tuna_salad','bolognese','pesto','napolitan')){continue}
 $region=[System.Drawing.Region]::new([System.Drawing.Rectangle]::new($f.x,$f.y,$f.w,$f.h))
 if($f.name -eq 'chicken_salad'){$region.Exclude([System.Drawing.Rectangle]::new(291,543,190,7))}
 if($f.name -in @('bolognese','pesto')){
  $path=[System.Drawing.Drawing2D.GraphicsPath]::new()
  $coordinates=if($f.name -eq 'bolognese'){@(@(255,818),@(287,807),@(327,801),@(369,792),@(412,790),@(412,905),@(255,905))}else{@(@(414,799),@(455,784),@(583,784),@(583,905),@(414,905))}
  [System.Drawing.PointF[]]$points=$coordinates | ForEach-Object {[System.Drawing.PointF]::new($_[0],$_[1])}
  $path.AddPolygon($points)
  $region.Intersect($path)
  $path.Dispose()
 }
 $dst=[System.Drawing.Rectangle]::new($f.x,$f.y,$f.w,$f.h)
 $src=[System.Drawing.Rectangle]::new($f.tx,$f.ty,$f.tw,$f.th)
 $g.SetClip($region,[System.Drawing.Drawing2D.CombineMode]::Replace)
 $g.DrawImage($sheet,$dst,$src,[System.Drawing.GraphicsUnit]::Pixel)
 $eg.DrawImage($sheet,$dst,$src,[System.Drawing.GraphicsUnit]::Pixel)
 $mg.FillRegion([System.Drawing.Brushes]::White,$region)
 $region.Dispose()
}
$g.Dispose();$mg.Dispose();$eg.Dispose()
$menu.Save((Join-Path $dir 'Corner-Cafe-gosterilen-salata-makarnalar-v9.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$mask.Save((Join-Path $dir 'gosterilen-urunler-v9-maskesi.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$expected.Save((Join-Path $dir 'gosterilen-urunler-v9-kaynak-kontrol.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$menu.Dispose();$shown.Dispose();$sheet.Dispose();$mask.Dispose();$expected.Dispose()
