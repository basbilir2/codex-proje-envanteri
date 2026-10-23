Add-Type -AssemblyName System.Drawing
$dir='C:\Users\USER\Documents\Codex\2026-10-17\outputs'
$menu=[System.Drawing.Bitmap]::new((Join-Path $dir 'Corner-Cafe-adres-kampanya-v7.png'))
$newPhotos=[System.Drawing.Bitmap]::new('C:\Users\USER\.codex\generated_images\01a158fc-9453-7a63-b06e-bcbb358fe334\exec-081f8bc1-67ea-40a6-abef-2fd870cd5361.png')
$mask=[System.Drawing.Bitmap]::new($menu.Width,$menu.Height)
$mg=[System.Drawing.Graphics]::FromImage($mask)
$mg.Clear([System.Drawing.Color]::Black)
$g=[System.Drawing.Graphics]::FromImage($menu)
$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
function Region-Polygon($pairs){
 $p=[System.Drawing.Drawing2D.GraphicsPath]::new()
 [System.Drawing.PointF[]]$points=$pairs | ForEach-Object {[System.Drawing.PointF]::new($_[0],$_[1])}
 $p.AddPolygon($points)
 $region=[System.Drawing.Region]::new($p)
 $p.Dispose()
 return ,$region
}
function Draw-Food($photo,$dst,$src,$region,$attributes=$null){
 $g.SetClip($region,[System.Drawing.Drawing2D.CombineMode]::Replace)
 if($null -eq $attributes){
  $g.DrawImage($photo,$dst,$src,[System.Drawing.GraphicsUnit]::Pixel)
 }else{
  $g.DrawImage($photo,$dst,$src.X,$src.Y,$src.Width,$src.Height,[System.Drawing.GraphicsUnit]::Pixel,$attributes)
 }
 $mg.FillRegion([System.Drawing.Brushes]::White,$region)
 $region.Dispose()
}
$burger=Region-Polygon @(@(340,348),@(343,326),@(354,307),@(374,287),@(410,273),@(449,267),@(486,272),@(529,287),@(566,307),@(586,331),@(596,350),@(599,376),@(599,417),@(599,458),@(593,483),@(581,500),@(375,500),@(346,488),@(335,466),@(329,430),@(329,389),@(333,362))
$burger.Exclude([System.Drawing.Rectangle]::new(288,402,99,103))
$offer=[System.Drawing.Drawing2D.GraphicsPath]::new()
[System.Drawing.PointF[]]$offerPoints=@([System.Drawing.PointF]::new(547,264),[System.Drawing.PointF]::new(575,245),[System.Drawing.PointF]::new(665,215),[System.Drawing.PointF]::new(695,250),[System.Drawing.PointF]::new(687,279),[System.Drawing.PointF]::new(607,313),[System.Drawing.PointF]::new(579,325),[System.Drawing.PointF]::new(570,307))
$offer.AddPolygon($offerPoints)
$burger.Exclude($offer)
$offer.Dispose()
Draw-Food $newPhotos ([System.Drawing.Rectangle]::new(329,266,270,234)) ([System.Drawing.Rectangle]::new(24,158,374,334)) $burger
$fries=[System.Drawing.Region]::new([System.Drawing.Rectangle]::new(599,319,100,166))
Draw-Food $newPhotos ([System.Drawing.Rectangle]::new(585,319,114,166)) ([System.Drawing.Rectangle]::new(395,141,227,335)) $fries
$pizzaOutline=[System.Drawing.Drawing2D.GraphicsPath]::new()
$pizzaOutline.AddEllipse([System.Drawing.Rectangle]::new(807,131,209,223))
$pizza=[System.Drawing.Region]::new($pizzaOutline);$pizzaOutline.Dispose()
Draw-Food $newPhotos ([System.Drawing.Rectangle]::new(807,131,209,223)) ([System.Drawing.Rectangle]::new(21,647,593,500)) $pizza
$manti=[System.Drawing.Region]::new([System.Drawing.Rectangle]::new(1298,128,216,169))
Draw-Food $newPhotos ([System.Drawing.Rectangle]::new(1298,128,216,169)) ([System.Drawing.Rectangle]::new(633,666,608,486)) $manti
$plate=Region-Polygon @(@(940,499),@(981,481),@(1009,474),@(1024,475),@(1040,467),@(1062,469),@(1088,471),@(1100,478),@(1115,489),@(1134,494),@(1159,514),@(1180,536),@(1206,558),@(1223,584),@(1229,605),@(1226,629),@(1209,645),@(1184,656),@(1154,666),@(1105,674),@(1045,675),@(990,673),@(940,665),@(900,652),@(866,635),@(843,614),@(835,590),@(839,563),@(853,544),@(873,527),@(903,512))
Draw-Food $newPhotos ([System.Drawing.Rectangle]::new(825,465,410,210)) ([System.Drawing.Rectangle]::new(633,121,607,374)) $plate
$matrix=[System.Drawing.Imaging.ColorMatrix]::new()
$matrix.Matrix00=1.06;$matrix.Matrix11=1.06;$matrix.Matrix22=1.06
$matrix.Matrix40=0.025;$matrix.Matrix41=0.025;$matrix.Matrix42=0.025
$photoAttributes=[System.Drawing.Imaging.ImageAttributes]::new()
$photoAttributes.SetColorMatrix($matrix)
$realFoods=@(
 @{file='WhatsApp Image 2026-10-20 at 15.38.01.jpeg';x=291;y=543;w=231;h=165;shape='salad'},
 @{file='WhatsApp Image 2026-10-20 at 15.40.45.jpeg';x=526;y=537;w=225;h=171;shape='ellipse'},
 @{file='WhatsApp Image 2026-10-20 at 16.44.19.jpeg';x=255;y=784;w=157;h=121;shape='bolognese'},
 @{file='WhatsApp Image 2026-10-20 at 16.44.19 (1).jpeg';x=414;y=784;w=169;h=121;shape='pesto'},
 @{file='WhatsApp Image 2026-10-20 at 16.44.19 (2).jpeg';x=585;y=784;w=166;h=121;shape='ellipse'}
)
foreach($f in $realFoods){
 $real=[System.Drawing.Bitmap]::new((Join-Path 'C:\Users\USER\Downloads' $f.file))
 $photoWindow=[System.Drawing.Region]::new([System.Drawing.Rectangle]::new($f.x,$f.y,$f.w,$f.h))
 if($f.shape -eq 'salad'){$photoWindow.Exclude([System.Drawing.Rectangle]::new(291,543,190,7))}
 if($f.shape -eq 'bolognese'){
  $windowLimit=Region-Polygon @(@(255,818),@(287,807),@(327,801),@(369,792),@(412,790),@(412,905),@(255,905))
  $photoWindow.Intersect($windowLimit);$windowLimit.Dispose()
 }
 if($f.shape -eq 'pesto'){
  $windowLimit=Region-Polygon @(@(414,799),@(455,784),@(583,784),@(583,905),@(414,905))
  $photoWindow.Intersect($windowLimit);$windowLimit.Dispose()
 }
 $photoWindow.Dispose()
 $outline=[System.Drawing.Drawing2D.GraphicsPath]::new()
 $outline.AddEllipse([System.Drawing.Rectangle]::new($f.x,$f.y,$f.w,$f.h))
 $region=[System.Drawing.Region]::new($outline)
 $outline.Dispose()
 if($f.shape -eq 'salad'){$region.Exclude([System.Drawing.Rectangle]::new(291,543,190,7))}
 if($f.shape -eq 'bolognese'){
  $limit=Region-Polygon @(@(255,818),@(287,807),@(327,801),@(369,792),@(412,790),@(412,905),@(255,905))
  $region.Intersect($limit);$limit.Dispose()
 }
 if($f.shape -eq 'pesto'){
  $limit=Region-Polygon @(@(414,799),@(455,784),@(583,784),@(583,905),@(414,905))
  $region.Intersect($limit);$limit.Dispose()
 }
 Draw-Food $real ([System.Drawing.Rectangle]::new($f.x,$f.y,$f.w,$f.h)) ([System.Drawing.Rectangle]::new(74,181,1367,1154)) $region $photoAttributes
 $real.Dispose()
}
$g.Dispose();$mg.Dispose();$photoAttributes.Dispose()
$original=[System.Drawing.Bitmap]::new((Join-Path $dir 'Corner-Cafe-adres-kampanya-v7.png'))
foreach($protected in @(@(1298,128,216,16,'red'),@(825,465,410,20,'yellow'),@(807,131,64,5,'yellow'))){
 for($py=$protected[1];$py -lt ($protected[1]+$protected[3]);$py++){
  for($px=$protected[0];$px -lt ($protected[0]+$protected[2]);$px++){
   $color=$original.GetPixel($px,$py)
   $keep=if($protected[4] -eq 'red'){($color.R -gt 110)-and($color.R -gt $color.G*1.6)-and($color.R -gt $color.B*1.6)}else{($color.R -gt 160)-and($color.G -gt 100)-and($color.B -lt 80)}
   if($keep){$menu.SetPixel($px,$py,$color);$mask.SetPixel($px,$py,[System.Drawing.Color]::Black)}
  }
 }
}
$original.Dispose()
$menu.Save((Join-Path $dir 'Corner-Cafe-tum-urunler-son-v8.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$mask.Save((Join-Path $dir 'tum-urunler-v8-degisim-maskesi.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$menu.Dispose();$newPhotos.Dispose();$mask.Dispose()
