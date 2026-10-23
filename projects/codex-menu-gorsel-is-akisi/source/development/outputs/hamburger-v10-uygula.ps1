$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$dir='C:\Users\USER\Documents\Codex\2026-10-17\outputs'
$basePath=Join-Path $dir 'Corner-Cafe-gosterilen-salata-makarnalar-v9.png'
$outputPath=Join-Path $dir 'Corner-Cafe-sadece-hamburger-patates-v10.png'
$menu=[System.Drawing.Bitmap]::new($basePath)
$generated=[System.Drawing.Bitmap]::new('C:\Users\USER\.codex\generated_images\01a158fc-9453-7a63-b06e-bcbb358fe334\exec-75afd29f-96ee-4459-8257-2ee183a1f94a.png')
$patch=[System.Drawing.Bitmap]::new(435,255)
$pg=[System.Drawing.Graphics]::FromImage($patch)
$pg.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$pg.DrawImage($generated,[System.Drawing.Rectangle]::new(0,0,435,255))
$pg.Dispose()
$path=[System.Drawing.Drawing2D.GraphicsPath]::new()
$outline=@(@(324,350),@(330,316),@(351,288),@(393,269),@(454,266),@(502,266),@(537,275),@(562,287),@(583,308),@(596,325),@(604,328),@(609,319),@(620,322),@(647,319),@(671,318),@(699,318),@(699,485),@(692,494),@(601,496),@(580,505),@(382,505),@(371,495),@(330,492),@(320,465),@(322,405),@(326,373))
[System.Drawing.PointF[]]$points=$outline | ForEach-Object {[System.Drawing.PointF]::new($_[0],$_[1])}
$path.AddPolygon($points)
$allowed=[System.Drawing.Region]::new($path)
$path.Dispose()
$badge=[System.Drawing.Drawing2D.GraphicsPath]::new()
$badge.AddEllipse([System.Drawing.Rectangle]::new(288,402,100,103))
$allowed.Exclude($badge)
$badge.Dispose()
$offer=[System.Drawing.Drawing2D.GraphicsPath]::new()
[System.Drawing.PointF[]]$offerPoints=@([System.Drawing.PointF]::new(547,264),[System.Drawing.PointF]::new(575,245),[System.Drawing.PointF]::new(665,215),[System.Drawing.PointF]::new(695,250),[System.Drawing.PointF]::new(687,279),[System.Drawing.PointF]::new(607,313),[System.Drawing.PointF]::new(579,325),[System.Drawing.PointF]::new(570,307))
$offer.AddPolygon($offerPoints)
$allowed.Exclude($offer)
$offer.Dispose()
$g=[System.Drawing.Graphics]::FromImage($menu)
$g.SetClip($allowed,[System.Drawing.Drawing2D.CombineMode]::Replace)
$g.DrawImageUnscaled($patch,285,255)
$g.Dispose()
$mask=[System.Drawing.Bitmap]::new(1536,1024)
$mg=[System.Drawing.Graphics]::FromImage($mask)
$mg.Clear([System.Drawing.Color]::Black)
$mg.FillRegion([System.Drawing.Brushes]::White,$allowed)
$mg.Dispose();$allowed.Dispose()
$menu.Save($outputPath,[System.Drawing.Imaging.ImageFormat]::Png)
$mask.Save((Join-Path $dir 'hamburger-v10-degisim-maskesi.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$menu.Dispose();$generated.Dispose();$patch.Dispose();$mask.Dispose()
Add-Type -TypeDefinition @'
public static class BurgerOnlyAudit {
 public static long[] Check(byte[] a,byte[] b,byte[] mask){
  long changed=0,outside=0;
  for(int i=0;i<a.Length;i+=4){
   bool diff=false;for(int c=0;c<4;c++)if(a[i+c]!=b[i+c])diff=true;
   if(diff){changed++;if(mask[i+2]==0)outside++;}
  }
  return new long[]{changed,outside};
 }
}
'@
function Read-BurgerBytes($path){
 $bitmap=[System.Drawing.Bitmap]::new($path)
 $data=$bitmap.LockBits([System.Drawing.Rectangle]::new(0,0,1536,1024),[System.Drawing.Imaging.ImageLockMode]::ReadOnly,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $bytes=[byte[]]::new(1536*1024*4)
 for($y=0;$y -lt 1024;$y++){[System.Runtime.InteropServices.Marshal]::Copy([IntPtr]::Add($data.Scan0,$y*$data.Stride),$bytes,$y*1536*4,1536*4)}
 $bitmap.UnlockBits($data);$bitmap.Dispose();return ,$bytes
}
$before=Read-BurgerBytes $basePath
$after=Read-BurgerBytes $outputPath
$maskBytes=Read-BurgerBytes (Join-Path $dir 'hamburger-v10-degisim-maskesi.png')
$counts=[BurgerOnlyAudit]::Check($before,$after,$maskBytes)
$report=@{changed_hamburger_fries_pixels=$counts[0];changed_pixels_outside_hamburger_fries=$counts[1];source='Corner-Cafe-gosterilen-salata-makarnalar-v9.png';output='Corner-Cafe-sadece-hamburger-patates-v10.png'}
$report | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $dir 'hamburger-v10-kontrol.json') -Encoding utf8
if($counts[0] -eq 0 -or $counts[1] -ne 0){throw 'Hamburger disinda fark saptandi'}
$report | ConvertTo-Json -Compress
