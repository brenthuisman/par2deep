;Get NSIS. Get winpython (zero). Install par2deep into Winpython. Compile par2deep.nsi.

!define AppName "par2deep"
!define AppAbb "par2deep"
SetCompressor LZMA

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General

  ;Name and file
  Name "${AppName}"
  BrandingText "${AppName}"
  OutFile "${AppAbb}.exe"

  ;Default installation folder
  InstallDir "$PROGRAMFILES\${AppAbb}"

  ;Get installation folder from registry if available
  ;InstallDirRegKey HKCU "Software\${AppAbb}" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel admin

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

  !define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install.ico"
  !define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall.ico"
   
  ; MUI Settings / Header
  !define MUI_HEADERIMAGE
  !define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\orange.bmp"
  !define MUI_HEADERIMAGE_UNBITMAP "${NSISDIR}\Contrib\Graphics\Header\orange-uninstall.bmp"
   
  ; MUI Settings / Wizard
  !define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\orange.bmp"
  !define MUI_UNWELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\orange-uninstall.bmp"

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !define MUI_FINISHPAGE_RUN "$INSTDIR\pythonw.exe"
  !define MUI_FINISHPAGE_RUN_PARAMETERS "$\"$INSTDIR\Scripts\par2deep-script.py$\""
  !insertmacro MUI_PAGE_FINISH
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  
;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "Dutch"
  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "Dummy Section" SecDummy

  SetOutPath "$INSTDIR"
  
  ;ADD YOUR OWN FILES HERE...
  File /r d:\par2deep\*.*

  ;Create shortcuts
  CreateDirectory "$SMPROGRAMS"
  CreateShortCut "$SMPROGRAMS\${AppName}.lnk" "$INSTDIR\pythonw.exe" "$\"$INSTDIR\Scripts\par2deep-script.py$\""
  CreateShortCut "$DESKTOP\${AppName}.lnk" "$INSTDIR\pythonw.exe" "$\"$INSTDIR\Scripts\par2deep-script.py$\""

  ;Store installation folder
  WriteRegStr HKCU "Software\${AppAbb}" "" $INSTDIR
  
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${AppAbb}" "DisplayName" "${AppName}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${AppAbb}" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${AppAbb}" "InstallLocation" "$\"$INSTDIR$\""

SectionEnd

;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ;ADD YOUR OWN FILES HERE...

  Delete "$INSTDIR\Uninstall.exe"

  RMDir /r "$INSTDIR"

  delete "$SMPROGRAMS\${AppName}.lnk"
  delete "$DESKTOP\${AppName}.lnk"

  DeleteRegKey /ifempty HKCU "Software\${AppAbb}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${AppAbb}"

SectionEnd
