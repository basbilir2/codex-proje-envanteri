$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$dir='C:\Users\USER\Documents\Codex\2026-10-17\outputs'
$basePath=Join-Path $dir 'Corner-Cafe-sadece-hamburger-patates-v10.png'
$finalPath=Join-Path $dir 'Corner-Cafe-sadece-kola-duzeltildi-v11.png'
$original=[System.Drawing.Bitmap]::new($basePath)
$menu=[System.Drawing.Bitmap]::new($basePath)
$generated=[System.Drawing.Bitmap]::new('C:\Users\USER\.codex\generated_images\01a158fc-9453-7a63-b06e-bcbb358fe334\exec-00e679b0-828b-4048-901c-31e3d4d519b7.png')
$patch=[System.Drawing.Bitmap]::new(335,294)
$pg=[System.Drawing.Graphics]::FromImage($patch)
$pg.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$pg.DrawImage($generated,[System.Drawing.Rectangle]::new(0,0,335,294))
$pg.Dispose()
$path=[System.Drawing.Drawing2D.GraphicsPath]::new()
$outline=@(@(1450,677),@(1495,677),@(1496,704),@(1498,726),@(1508,750),@(1515,776),@(1515,930),@(1508,947),@(1441,951),@(1434,945),@(1434,936),@(1445,926),@(1445,853),@(1419,853),@(1419,779),@(1433,747),@(1443,727),@(1451,704))
[System.Drawing.PointF[]]$points=$outline | ForEach-Object {[System.Drawing.PointF]::new($_[0],$_[1])}
$path.AddPolygon($points)
$allowed=[System.Drawing.Region]::new($path)
$path.Dispose()
$allowed.Exclude([System.Drawing.Rectangle]::new(1185,675,241,101))
$allowed.Exclude([System.Drawing.Rectangle]::new(1185,776,235,77))
$allowed.Exclude([System.Drawing.Rectangle]::new(1185,853,260,73))
$g=[System.Drawing.Graphics]::FromImage($menu)
$g.SetClip($allowed,[System.Drawing.Drawing2D.CombineMode]::Replace)
$g.DrawImageUnscaled($patch,1185,675)
$g.Dispose()
$mask=[System.Drawing.Bitmap]::new(1536,1024)
$mg=[System.Drawing.Graphics]::FromImage($mask)
$mg.Clear([System.Drawing.Color]::Black)
$mg.FillRegion([System.Drawing.Brushes]::White,$allowed)
$mg.Dispose();$allowed.Dispose()
for($y=776;$y -lt 853;$y++){
 for($x=1419;$x -lt 1435;$x++){
  $color=$original.GetPixel($x,$y)
  if(($color.R -gt 170)-and($color.G -gt 100)-and($color.B -lt 120)){
   $menu.SetPixel($x,$y,$color)
   $mask.SetPixel($x,$y,[System.Drawing.Color]::Black)
  }
 }
}
$menu.Save($finalPath,[System.Drawing.Imaging.ImageFormat]::Png)
$mask.Save((Join-Path $dir 'kola-v11-degisim-maskesi.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$closeup=$menu.Clone([System.Drawing.Rectangle]::new(1185,675,335,294),$menu.PixelFormat)
$closeup.Save((Join-Path $dir 'kola-v11-son-kontrol.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$closeup.Dispose();$menu.Dispose();$original.Dispose();$generated.Dispose();$patch.Dispose();$mask.Dispose()
Add-Type -TypeDefinition @'
public static class ColaOnlyAudit {
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
function Read-ColaBytes($path){
 $bitmap=[System.Drawing.Bitmap]::new($path)
 $data=$bitmap.LockBits([System.Drawing.Rectangle]::new(0,0,1536,1024),[System.Drawing.Imaging.ImageLockMode]::ReadOnly,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $bytes=[byte[]]::new(1536*1024*4)
 for($y=0;$y -lt 1024;$y++){[System.Runtime.InteropServices.Marshal]::Copy([IntPtr]::Add($data.Scan0,$y*$data.Stride),$bytes,$y*1536*4,1536*4)}
 $bitmap.UnlockBits($data);$bitmap.Dispose();return ,$bytes
}
$before=Read-ColaBytes $basePath
$after=Read-ColaBytes $finalPath
$maskBytes=Read-ColaBytes (Join-Path $dir 'kola-v11-degisim-maskesi.png')
$counts=[ColaOnlyAudit]::Check($before,$after,$maskBytes)
$report=@{changed_cola_pixels=$counts[0];changed_pixels_outside_cola=$counts[1];source='Corner-Cafe-sadece-hamburger-patates-v10.png';output='Corner-Cafe-sadece-kola-duzeltildi-v11.png'}
$report | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $dir 'kola-v11-kontrol.json') -Encoding utf8
if($counts[0] -eq 0 -or $counts[1] -ne 0){throw 'Kola disinda fark saptandi'}
$report | ConvertTo-Json -Compress
