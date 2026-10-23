Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
public static class FoodPixelAudit {
 public static long[] Check(byte[] a, byte[] b, byte[] mask) {
  long changed=0,outside=0;
  for(int i=0;i<a.Length;i+=4) {
   bool diff=a[i]!=b[i]||a[i+1]!=b[i+1]||a[i+2]!=b[i+2]||a[i+3]!=b[i+3];
   if(diff){changed++;if(mask[i+2]==0)outside++;}
  }
  return new long[]{changed,outside};
 }
}
'@
$dir='C:\Users\USER\Documents\Codex\2026-10-17\outputs'
function Read-Pixels($path){
 $bitmap=[System.Drawing.Bitmap]::new($path)
 $rect=[System.Drawing.Rectangle]::new(0,0,$bitmap.Width,$bitmap.Height)
 $locked=$bitmap.LockBits($rect,[System.Drawing.Imaging.ImageLockMode]::ReadOnly,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $bytes=[byte[]]::new($bitmap.Width*$bitmap.Height*4)
 for($y=0;$y -lt $bitmap.Height;$y++){
  [System.Runtime.InteropServices.Marshal]::Copy([IntPtr]::Add($locked.Scan0,$y*$locked.Stride),$bytes,$y*$bitmap.Width*4,$bitmap.Width*4)
 }
 $bitmap.UnlockBits($locked);$bitmap.Dispose()
 return ,$bytes
}
$before=Read-Pixels (Join-Path $dir 'Corner-Cafe-adres-kampanya-v7.png')
$after=Read-Pixels (Join-Path $dir 'Corner-Cafe-tum-urunler-son-v8.png')
$allowed=Read-Pixels (Join-Path $dir 'tum-urunler-v8-degisim-maskesi.png')
$result=[FoodPixelAudit]::Check($before,$after,$allowed)
$report=@{changed_food_pixels=$result[0];changed_pixels_outside_food=$result[1];source='Corner-Cafe-adres-kampanya-v7.png';output='Corner-Cafe-tum-urunler-son-v8.png';width=1536;height=1024}
$report | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $dir 'tum-urunler-v8-kontrol.json') -Encoding utf8
if($result[0] -eq 0 -or $result[1] -ne 0){throw 'Piksel kontrolu basarisiz'}
$report | ConvertTo-Json -Compress
