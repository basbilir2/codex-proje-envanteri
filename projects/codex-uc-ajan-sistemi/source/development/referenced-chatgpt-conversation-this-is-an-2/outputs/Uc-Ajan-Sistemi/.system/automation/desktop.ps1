$env:PSModulePath = $PSHOME + '\Modules'
$ErrorActionPreference='Stop'
[Console]::InputEncoding=New-Object Text.UTF8Encoding
[Console]::OutputEncoding=New-Object Text.UTF8Encoding
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes,System.Drawing,System.Windows.Forms
Add-Type @'
using System; using System.Runtime.InteropServices;
public class StudioWindow {
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out Rect r);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 public struct Rect { public int Left,Top,Right,Bottom; }
}
'@
$request=([Console]::ReadLine() | ConvertFrom-Json)
$checks=New-Object Collections.Generic.List[object]
$errors=New-Object Collections.Generic.List[string]
$window=$null
$handle=[IntPtr]::Zero
function Find-OwnedWindow {
 $owned=New-Object 'Collections.Generic.HashSet[int]'
 [void]$owned.Add([int]$request.pid)
 for($level=0;$level -lt 4;$level++) {
  $before=$owned.Count
  foreach($parent in @($owned)){foreach($child in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$parent" -ErrorAction SilentlyContinue)){[void]$owned.Add([int]$child.ProcessId)}}
  if($before -eq $owned.Count){break}
 }
 $candidates=@(foreach($ownedId in $owned){$p=Get-Process -Id $ownedId -ErrorAction SilentlyContinue;if($p -and $p.MainWindowHandle -ne 0){$p}})
 if($request.window_title){$candidates=@($candidates | Where-Object MainWindowTitle -eq $request.window_title)}
 if($candidates.Count -gt 1){throw 'Birden fazla proje penceresi açık; window_title belirt.'}
 if($candidates.Count -eq 1){return $candidates[0]}
 return $null
}
function Find-Control($step) {
 if($step.automation_id){$condition=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::AutomationIdProperty,[string]$step.automation_id)}
 elseif($step.name -or $step.text){$wanted=if($step.name){$step.name}else{$step.text};$condition=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::NameProperty,[string]$wanted)}
 else{throw 'name, text veya automation_id gerekiyor.'}
 for($attempt=0;$attempt -lt 20;$attempt++) {
  $found=$window.FindAll([Windows.Automation.TreeScope]::Descendants,$condition)
  if($found.Count -eq 1){return $found[0]}
  if($found.Count -gt 1){throw 'Birden fazla denetim eşleşiyor; benzersiz automation_id kullan.'}
  Start-Sleep -Milliseconds 150
 }
 throw 'Pencerede denetim bulunamadı.'
}
try {
 for($attempt=0;$attempt -lt 45;$attempt++){$p=Find-OwnedWindow;if($p){break};Start-Sleep -Milliseconds 200}
 if(-not $p){throw 'Oluşturulan EXE görünür bir masaüstü penceresi açmadı.'}
 $handle=$p.MainWindowHandle
 $window=[Windows.Automation.AutomationElement]::FromHandle($handle)
 foreach($step in @($request.steps)) {
  try {
   if($step.action -eq 'wait'){Start-Sleep -Milliseconds ([Math]::Min(3000,[Math]::Max(0,[int]$step.ms)))}
   elseif($step.action -eq 'press') {
    $keyMap=@{Enter='{ENTER}';Tab='{TAB}';Escape='{ESC}';Space=' ';ArrowLeft='{LEFT}';ArrowRight='{RIGHT}';ArrowUp='{UP}';ArrowDown='{DOWN}'}
    if(-not $keyMap.ContainsKey([string]$step.key)){throw 'Bu masaüstü tuşu desteklenmiyor.'}
    [void][StudioWindow]::SetForegroundWindow($handle)
    if([StudioWindow]::GetForegroundWindow() -ne $handle){throw 'Proje penceresi odakta değil; başka pencereye tuş gönderilmedi.'}
    [Windows.Forms.SendKeys]::SendWait($keyMap[[string]$step.key])
   } else {
    $target=Find-Control $step
    if($target.Current.IsOffscreen){throw 'Beklenen denetim görünür değil.'}
    switch($step.action) {
     'click' {$target.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke()}
     'fill' {$target.GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern).SetValue([string]$step.value)}
     'expect_text' {}
     'expect_visible' {}
     default {throw 'Desteklenmeyen masaüstü adımı.'}
    }
   }
   $checks.Add(@{action=$step.action;target=$step.name;passed=$true})
  } catch {$checks.Add(@{action=$step.action;passed=$false;error=$_.Exception.Message});break}
 }
} catch {$errors.Add($_.Exception.Message)}
$controls=@()
if($window){
 try{$elements=$window.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition);$controls=@(for($i=0;$i -lt [Math]::Min(140,$elements.Count);$i++){$c=$elements[$i].Current;if(-not $c.IsOffscreen){@{name=if($c.IsPassword){'[gizli]'}else{$c.Name};automation_id=$c.AutomationId;type=$c.ControlType.ProgrammaticName}}})}catch{}
 try{
  $rect=New-Object StudioWindow+Rect
  if(-not [StudioWindow]::GetWindowRect($handle,[ref]$rect)){throw 'Pencere ölçüleri alınamadı.'}
  $width=$rect.Right-$rect.Left;$height=$rect.Bottom-$rect.Top
  if($width -lt 10 -or $height -lt 10 -or $width -gt 2560 -or $height -gt 1800){throw 'Pencere görüntüsü ölçüsü desteklenmiyor.'}
  $bitmap=New-Object Drawing.Bitmap($width,$height)
  $graphics=[Drawing.Graphics]::FromImage($bitmap);$dc=$graphics.GetHdc()
  try{$captured=[StudioWindow]::PrintWindow($handle,$dc,2)}finally{$graphics.ReleaseHdc($dc)}
  if(-not $captured){throw 'Uygulama penceresi görüntülenemedi.'}
  $bitmap.Save([string]$request.screenshot,[Drawing.Imaging.ImageFormat]::Png)
 }catch{$errors.Add($_.Exception.Message)}finally{if($graphics){$graphics.Dispose()};if($bitmap){$bitmap.Dispose()}}
}
$failed=@($checks | Where-Object {-not $_.passed})
@{passed=($errors.Count -eq 0 -and $failed.Count -eq 0);errors=$errors.ToArray();assertions=$checks.ToArray();controls=$controls;screenshot=$request.screenshot;owned_process_only=$true} | ConvertTo-Json -Depth 8 -Compress | ForEach-Object {[Console]::WriteLine($_)}
