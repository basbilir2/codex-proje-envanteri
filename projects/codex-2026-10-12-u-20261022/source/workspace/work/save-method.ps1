$ErrorActionPreference='Stop'
$corel=New-Object -ComObject 'CorelDRAW.Application.17'
$doc=$corel.ActiveDocument
$doc | Get-Member -Name SaveAs
$corel | Get-Member -Name CreateStructSaveAsOptions
$opt=$corel.CreateStructSaveAsOptions()
$opt | Get-Member -MemberType Properties | Select-Object Name,Definition
