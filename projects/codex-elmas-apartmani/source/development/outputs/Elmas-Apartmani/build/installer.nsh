!include "LogicLib.nsh"
!include "nsDialogs.nsh"

!ifdef BUILD_UNINSTALLER
Var KeepElmasData
Var KeepElmasDataCheckbox

!macro customUnInit
  StrCpy $KeepElmasData 1
!macroend

!macro customUnInstall
  ${If} $KeepElmasData == 0
    RMDir /r "$APPDATA\Elmas Apartmanı"
  ${EndIf}
!macroend

Function un.DataChoicePage
  nsDialogs::Create 1018
  Pop $0
  ${If} $0 == error
    Abort
  ${EndIf}
  ${NSD_CreateLabel} 0 0 100% 36u "Elmas Apartmanı kaldırılacak. Apartman kayıtlarını ve yedeklerini bu bilgisayarda saklamak ister misiniz?"
  Pop $0
  ${NSD_CreateCheckbox} 0 48u 100% 14u "Verilerimi sakla (önerilir)"
  Pop $KeepElmasDataCheckbox
  ${NSD_Check} $KeepElmasDataCheckbox
  nsDialogs::Show
FunctionEnd

Function un.DataChoiceLeave
  ${NSD_GetState} $KeepElmasDataCheckbox $0
  ${If} $0 == ${BST_CHECKED}
    StrCpy $KeepElmasData 1
  ${Else}
    StrCpy $KeepElmasData 0
  ${EndIf}
FunctionEnd

!macro customUnWelcomePage
  UninstPage custom un.DataChoicePage un.DataChoiceLeave
!macroend
!endif
