Add-Type -AssemblyName System.Drawing
$workDir = 'C:\Users\USER\Documents\Codex\2026-10-17\outputs'
$source = [System.Drawing.Bitmap]::new((Join-Path $workDir 'Corner-Cafe-adres-kampanya-v7.png'))
$foods = @(
  @{name='burger';x=321;y=260;w=384;h=244},
  @{name='pizza';x=807;y=131;w=209;h=223},
  @{name='manti';x=1298;y=128;w=216;h=169},
  @{name='chicken_plate';x=825;y=465;w=410;h=210},
  @{name='chicken_salad';x=291;y=543;w=231;h=165},
  @{name='tuna_salad';x=526;y=537;w=225;h=171},
  @{name='bolognese';x=255;y=784;w=157;h=121},
  @{name='pesto';x=414;y=784;w=169;h=121},
  @{name='napolitan';x=585;y=784;w=166;h=121}
)
$sheet = [System.Drawing.Bitmap]::new(2304,2304)
$g = [System.Drawing.Graphics]::FromImage($sheet)
$g.Clear([System.Drawing.Color]::FromArgb(28,28,28))
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
for($i=0;$i -lt $foods.Count;$i++){
  $f=$foods[$i]
  $scale=[Math]::Min(736.0/$f.w,736.0/$f.h)
  $f.tw=[int][Math]::Round($f.w*$scale)
  $f.th=[int][Math]::Round($f.h*$scale)
  $f.tx=([int]($i%3)*768)+[int][Math]::Floor((768-$f.tw)/2)
  $f.ty=([int][Math]::Floor($i/3)*768)+[int][Math]::Floor((768-$f.th)/2)
  $g.DrawImage($source,[System.Drawing.Rectangle]::new($f.tx,$f.ty,$f.tw,$f.th),[System.Drawing.Rectangle]::new($f.x,$f.y,$f.w,$f.h),[System.Drawing.GraphicsUnit]::Pixel)
}
$g.Dispose()
$sheet.Save((Join-Path $workDir 'urunler-toplu-duzenleme-v8.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$foods | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $workDir 'urunler-v8-konumlar.json') -Encoding utf8
$sheet.Dispose(); $source.Dispose()
