Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
public static class ExactShownFoodAudit {
 public static long[] Check(byte[] before,byte[] after,byte[] expected,byte[] mask){
  long outside=0,sourceMismatch=0,inserted=0;
  for(int i=0;i<before.Length;i+=4){
   bool differsOld=false,differsSource=false;
   for(int c=0;c<4;c++){if(before[i+c]!=after[i+c])differsOld=true;if(expected[i+c]!=after[i+c])differsSource=true;}
   if(mask[i+2]>0){inserted++;if(differsSource)sourceMismatch++;}else if(differsOld)outside++;
  }
  return new long[]{outside,sourceMismatch,inserted};
 }
}
'@
$dir='C:\Users\USER\Documents\Codex\2026-10-17\outputs'
function Read-PhotoBytes($name){
 $bitmap=[System.Drawing.Bitmap]::new((Join-Path $dir $name))
 $locked=$bitmap.LockBits([System.Drawing.Rectangle]::new(0,0,$bitmap.Width,$bitmap.Height),[System.Drawing.Imaging.ImageLockMode]::ReadOnly,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $bytes=[byte[]]::new($bitmap.Width*$bitmap.Height*4)
 for($row=0;$row -lt $bitmap.Height;$row++){
  [System.Runtime.InteropServices.Marshal]::Copy([IntPtr]::Add($locked.Scan0,$row*$locked.Stride),$bytes,$row*$bitmap.Width*4,$bitmap.Width*4)
 }
 $bitmap.UnlockBits($locked);$bitmap.Dispose()
 return ,$bytes
}
$before=Read-PhotoBytes 'Corner-Cafe-tum-urunler-son-v8.png'
$after=Read-PhotoBytes 'Corner-Cafe-gosterilen-salata-makarnalar-v9.png'
$expected=Read-PhotoBytes 'gosterilen-urunler-v9-kaynak-kontrol.png'
$mask=Read-PhotoBytes 'gosterilen-urunler-v9-maskesi.png'
$counts=[ExactShownFoodAudit]::Check($before,$after,$expected,$mask)
$report=@{changed_pixels_outside_five_photos=$counts[0];pixels_different_from_shown_source_after_resize=$counts[1];inserted_source_pixels=$counts[2];products=@('chicken salad','tuna salad','spaghetti bolognese','pesto penne','napolitan penne');source_image='exec-b1426021-7479-45af-9d19-3ff95edcbb40.png'}
$report | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $dir 'gosterilen-urunler-v9-kontrol.json') -Encoding utf8
if($counts[0] -ne 0 -or $counts[1] -ne 0 -or $counts[2] -eq 0){throw 'Gosterilen gorsel veya koruma kontrolu basarisiz'}
$report | ConvertTo-Json -Compress
