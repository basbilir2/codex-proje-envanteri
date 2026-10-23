Add-Type -AssemblyName System.Drawing
$workDir='C:\Users\USER\Documents\Codex\2026-10-17\outputs'
$basePath=Join-Path $workDir 'Corner-Cafe-adres-kampanya-v7.png'
$finalPath=Join-Path $workDir 'Corner-Cafe-tum-yemek-dokulari-v8.png'
$source=[System.Drawing.Bitmap]::new($basePath)
$generated=[System.Drawing.Bitmap]::new('C:\Users\USER\.codex\generated_images\01a158fc-9453-7a63-b06e-bcbb358fe334\exec-b1426021-7479-45af-9d19-3ff95edcbb40.png')
$sheet=[System.Drawing.Bitmap]::new(2304,2304)
$sg=[System.Drawing.Graphics]::FromImage($sheet)
$sg.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$sg.DrawImage($generated,[System.Drawing.Rectangle]::new(0,0,2304,2304))
$sg.Dispose()
$foods=Get-Content -LiteralPath (Join-Path $workDir 'urunler-v8-konumlar.json') -Raw | ConvertFrom-Json
$polygons=@{
 burger=@(@(347,318),@(355,297),@(380,280),@(416,269),@(461,266),@(502,270),@(539,282),@(568,299),@(586,324),@(596,348),@(610,341),@(612,321),@(621,327),@(627,349),@(644,328),@(655,335),@(648,354),@(675,350),@(688,356),@(676,374),@(699,371),@(699,393),@(695,421),@(693,459),@(685,481),@(605,487),@(583,497),@(391,500),@(371,492),@(365,482),@(337,468),@(329,414),@(332,372),@(338,350))
 manti=@(@(1298,174),@(1322,151),@(1362,133),@(1410,128),@(1459,133),@(1514,155),@(1514,285),@(1482,297),@(1330,297),@(1298,265))
 chicken_plate=@(@(940,499),@(981,481),@(1009,474),@(1024,475),@(1040,467),@(1062,469),@(1088,471),@(1100,478),@(1115,489),@(1134,494),@(1159,514),@(1180,536),@(1206,558),@(1223,584),@(1229,605),@(1226,629),@(1209,645),@(1184,656),@(1154,666),@(1105,674),@(1045,675),@(990,673),@(940,665),@(900,652),@(866,635),@(843,614),@(835,590),@(839,563),@(853,544),@(873,527),@(903,512))
 chicken_salad=@(@(291,576),@(316,559),@(371,550),@(443,550),@(481,558),@(508,577),@(522,609),@(522,683),@(497,708),@(439,708),@(355,708),@(311,693),@(291,669))
 bolognese=@(@(255,818),@(287,807),@(327,801),@(369,792),@(412,790),@(412,905),@(255,905))
 pesto=@(@(414,799),@(455,784),@(583,784),@(583,905),@(414,905))
}
$mask=[System.Drawing.Bitmap]::new($source.Width,$source.Height)
$mg=[System.Drawing.Graphics]::FromImage($mask)
$mg.Clear([System.Drawing.Color]::Black)
$g=[System.Drawing.Graphics]::FromImage($source)
$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
foreach($f in $foods){
 $path=[System.Drawing.Drawing2D.GraphicsPath]::new()
 if($polygons.ContainsKey($f.name)){
   [System.Drawing.PointF[]]$points=$polygons[$f.name] | ForEach-Object {[System.Drawing.PointF]::new($_[0],$_[1])}
   $path.AddPolygon($points)
 }else{
   $path.AddRectangle([System.Drawing.Rectangle]::new($f.x,$f.y,$f.w,$f.h))
 }
 $region=[System.Drawing.Region]::new($path)
 if($f.name -eq 'burger'){
   $region.Exclude([System.Drawing.Rectangle]::new(288,402,99,103))
   $offer=[System.Drawing.Drawing2D.GraphicsPath]::new()
   [System.Drawing.PointF[]]$offerPoints=@([System.Drawing.PointF]::new(547,264),[System.Drawing.PointF]::new(575,245),[System.Drawing.PointF]::new(665,215),[System.Drawing.PointF]::new(695,250),[System.Drawing.PointF]::new(687,279),[System.Drawing.PointF]::new(607,313),[System.Drawing.PointF]::new(579,325),[System.Drawing.PointF]::new(570,307))
   $offer.AddPolygon($offerPoints)
   $region.Exclude($offer)
   $offer.Dispose()
 }
 $g.SetClip($region,[System.Drawing.Drawing2D.CombineMode]::Replace)
 $g.DrawImage($sheet,[System.Drawing.Rectangle]::new($f.x,$f.y,$f.w,$f.h),[System.Drawing.Rectangle]::new($f.tx,$f.ty,$f.tw,$f.th),[System.Drawing.GraphicsUnit]::Pixel)
 $mg.FillRegion([System.Drawing.Brushes]::White,$region)
 $region.Dispose();$path.Dispose()
}
$g.Dispose();$mg.Dispose()
$source.Save($finalPath,[System.Drawing.Imaging.ImageFormat]::Png)
$mask.Save((Join-Path $workDir 'urunler-v8-degisen-alanlar.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$source.Dispose();$generated.Dispose();$sheet.Dispose();$mask.Dispose()
