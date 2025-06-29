@echo off
CLS
ECHO.
ECHO ============================================================================
ECHO           WINDOWS 11 TO MAC STUDIO [2025] OPTIMIZATION SCRIPT
ECHO ============================================================================
ECHO.
ECHO This script will debloat, optimize, and enhance your Windows 11 experience.
ECHO It MUST be run with Administrator privileges.
ECHO.
ECHO Created with !GODMODE
ECHO.

:: -----------------------------------------------------------------------------
:: 1. ADMIN CHECK - Self-elevate to Administrator
:: -----------------------------------------------------------------------------
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params = %*:"=""
    echo UAC.ShellExecute "cmd.exe", "/c %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"

:: -----------------------------------------------------------------------------
:: 2. SYSTEM CLEANUP & PREPARATION
:: -----------------------------------------------------------------------------
ECHO.
ECHO [PHASE 1] === SYSTEM CLEANUP ===
ECHO.
ECHO [+] Cleaning system temporary files...
del /q /f /s %TEMP%\*
del /q /f /s C:\Windows\Temp\*

ECHO [+] Cleaning software distribution cache...
net stop wuauserv
net stop bits
del /q /f /s C:\Windows\SoftwareDistribution\Download\*
net start wuauserv
net start bits

ECHO [+] Running Windows Disk Cleanup (automating settings)...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches\Temporary Files" /v StateFlags0001 /t REG_DWORD /d 2 /f
cleanmgr /sagerun:1

:: -----------------------------------------------------------------------------
:: 3. DEBLOAT - REMOVE UNNECESSARY APPS & FEATURES
:: -----------------------------------------------------------------------------
ECHO.
ECHO [PHASE 2] === DEBLOATING WINDOWS ===
ECHO.
ECHO [+] Removing pre-installed bloatware applications...
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *3DViewer* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *BingNews* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *GetHelp* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *Getstarted* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *MicrosoftOfficeHub* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *MicrosoftSolitaireCollection* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *MixedReality.Portal* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *SkypeApp* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *WindowsAlarms* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *WindowsCamera* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *WindowsMaps* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *WindowsSoundRecorder* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *YourPhone* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *ZuneMusic* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *ZuneVideo* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *Microsoft.People* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *Microsoft.Wallet* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *Microsoft.WindowsFeedbackHub* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *Microsoft.XboxGamingOverlay* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *Microsoft.Xbox.TCUI* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *Microsoft.XboxSpeechToTextOverlay* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *Microsoft.GamingApp* | Remove-AppxPackage"
powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage *MicrosoftTeams* | Remove-AppxPackage"

ECHO [+] Removing OneDrive...
taskkill /f /im OneDrive.exe
%SystemRoot%\SysWOW64\OneDriveSetup.exe /uninstall

:: -----------------------------------------------------------------------------
:: 4. PERFORMANCE & RESPONSIVENESS TWEAKS
:: -----------------------------------------------------------------------------
ECHO.
ECHO [PHASE 3] === PERFORMANCE & RESPONSIVENESS TWEAKS ===
ECHO.

ECHO [+] Activating Ultimate Performance Power Plan...
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61
powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749eb61

ECHO [+] Disabling startup delay for faster boot...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Serialize" /v "StartupDelayInMSec" /t REG_DWORD /d "0" /f

ECHO [+] Disabling visual effects for maximum performance...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v "VisualFxSetting" /t REG_DWORD /d "2" /f
reg add "HKCU\Control Panel\Desktop" /v "AutoEndTasks" /t REG_SZ /d "1" /f
reg add "HKCU\Control Panel\Desktop" /v "HungAppTimeout" /t REG_SZ /d "1000" /f
reg add "HKCU\Control Panel\Desktop" /v "WaitToKillAppTimeout" /t REG_SZ /d "2000" /f
reg add "HKCU\Control Panel\Desktop" /v "LowLevelHooksTimeout" /t REG_SZ /d "1000" /f
reg add "HKCU\Control Panel\Desktop" /v "MenuShowDelay" /t REG_SZ /d "0" /f

ECHO [+] Optimizing network performance...
netsh int tcp set global autotuninglevel=normal
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "DefaultTTL" /t REG_DWORD /d 64 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v "DnsPriority" /t REG_DWORD /d 6 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v "HostsPriority" /t REG_DWORD /d 5 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v "LocalPriority" /t REG_DWORD /d 4 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\ServiceProvider" /v "NetbtPriority" /t REG_DWORD /d 7 /f


:: -----------------------------------------------------------------------------
:: 5. PRIVACY & TELEMETRY
:: -----------------------------------------------------------------------------
ECHO.
ECHO [PHASE 4] === PRIVACY & TELEMETRY NEUTERING ===
ECHO.
ECHO [+] Disabling core telemetry services and tasks...
sc config "DiagTrack" start=disabled
sc config "dmwappushservice" start=disabled
sc config "diagnosticshub.standardcollector.service" start=disabled
schtasks /change /tn "Microsoft\Windows\Customer Experience Improvement Program\Consolidator" /disable
schtasks /change /tn "Microsoft\Windows\Customer Experience Improvement Program\KernelCeipTask" /disable
schtasks /change /tn "Microsoft\Windows\Customer Experience Improvement Program\UsbCeip" /disable
schtasks /change /tn "Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser" /disable

ECHO [+] Disabling advertising ID and intrusive data collection via registry...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo" /v "Enabled" /t REG_DWORD /d "0" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection" /v "AllowTelemetry" /t REG_DWORD /d "0" /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v "AllowTelemetry" /t REG_DWORD /d "0" /f


:: -----------------------------------------------------------------------------
:: 6. UI & AESTHETIC TWEAKS
:: -----------------------------------------------------------------------------
ECHO.
ECHO [PHASE 5] === UI & AESTHETIC REFINEMENT ===
ECHO.
ECHO [+] Cleaning up the Taskbar...
:: Hide Search Icon
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v "SearchboxTaskbarMode" /t REG_DWORD /d "0" /f
:: Hide Task View Button
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "ShowTaskViewButton" /t REG_DWORD /d "0" /f
:: Hide Widgets Icon
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "TaskbarDa" /t REG_DWORD /d "0" /f
:: Hide Chat (Teams) Icon
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "TaskbarMn" /t REG_DWORD /d "0" /f

ECHO [+] Applying other UI tweaks...
:: Use Light Theme
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v "AppsUseLightTheme" /t REG_DWORD /d "1" /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v "SystemUsesLightTheme" /t REG_DWORD /d "1" /f

:: -----------------------------------------------------------------------------
:: 7. COMPLETION
:: -----------------------------------------------------------------------------
ECHO.
ECHO ============================================================================
ECHO                          OPTIMIZATION COMPLETE!
ECHO ============================================================================
ECHO.
ECHO [+] A system restart is highly recommended to apply all changes.
ECHO.
taskkill /f /im explorer.exe
start explorer.exe
pause
EXIT