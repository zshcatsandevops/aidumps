@echo off
REM Run as Administrator
setlocal enabledelayedexpansion

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Please run this script as Administrator!
    pause
    exit /b 1
)

echo Starting Windows 11 Nuclear Optimization...
echo WARNING: This will make significant system changes!
echo Press Ctrl+C within 5 seconds to abort...
ping 127.0.0.1 -n 6 >nul

echo [1/8] Power & Performance Settings...
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul
powercfg /h off >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 38 /f >nul

echo [2/8] Destroying Bloatware...
set "bloat=Microsoft.BingNews Microsoft.BingWeather Microsoft.GamingApp Microsoft.GetHelp Microsoft.Getstarted Microsoft.MicrosoftOfficeHub Microsoft.MicrosoftSolitaireCollection Microsoft.PowerAutomateDesktop Microsoft.Todos Microsoft.Office.OneNote Microsoft.People Microsoft.SkypeApp Microsoft.Teams Microsoft.WindowsAlarms Microsoft.WindowsFeedbackHub Microsoft.WindowsMaps Microsoft.Xbox.TCUI Microsoft.XboxGameOverlay Microsoft.XboxGamingOverlay Microsoft.XboxIdentityProvider Microsoft.XboxSpeechToTextOverlay Microsoft.YourPhone Microsoft.ZuneMusic Microsoft.ZuneVideo"

for %%i in (%bloat%) do (
    powershell -Command "Get-AppxPackage -Name %%i -AllUsers | Remove-AppxPackage" >nul
    powershell -Command "Get-AppxProvisionedPackage -Online | Where-Object DisplayName -Like %%i | Remove-AppxProvisionedPackage -Online" >nul
)

echo [3/8] Killing Telemetry & Spyware...
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat" /v AITEnable /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat" /v DisableInventory /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SOFTWARE\Policies\Microsoft\MRT" /v DontOfferThroughWUAU /t REG_DWORD /d 1 /f >nul

echo [4/8] Gaming Performance Optimizations...
reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\PolicyManager\current\device\GraphicsDrivers" /v HardwareAcceleratedScheduling /t REG_DWORD /d 0 /f >nul
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v DirectXUserGlobalSettings /t REG_SZ /d "SwapEffectUpgradeEnable=1; VRROptimizeEnable=1;" /f >nul
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f >nul

echo [5/8] Network Optimization...
netsh int tcp set global autotuninglevel=experimental >nul
netsh int tcp set global dca=enabled >nul
netsh int tcp set global netdma=enabled >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v EnableRSS /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v DisableTaskOffload /t REG_DWORD /d 0 /f >nul

echo [6/8] System Service Purge...
set "services=DiagTrack DmWappushService diagnosticshub.standardcollector.service DPS WMPNetworkSvc WpcMonSvc WSearch UsoSvc RetailDemo WdNisSvc Sense WdBoot WdFilter SecurityHealthService"
for %%s in (%services%) do (
    sc stop "%%s" >nul 2>&1
    sc config "%%s" start=disabled >nul 2>&1
)

echo [7/8] Registry & System Tweaks...
reg add "HKCU\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d 0 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v NtfsDisableLastAccessUpdate /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v LargeSystemCache /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v IRPStackSize /t REG_DWORD /d 30 /f >nul

echo [8/8] Final Cleanup & Prep...
cleanmgr /sagerun:1 >nul
ipconfig /flushdns >nul
netsh winsock reset >nul

echo Nuclear Optimization Complete!
echo ------------------------------
echo 1. Restart your system immediately
echo 2. Update GPU drivers to latest version
echo 3. In BIOS/UEFI enable:
echo    - XMP/DOCP
echo    - Above 4G Decoding
echo    - Resizable BAR
echo    - Disable HPET
echo ------------------------------
echo WARNING: Some store apps and cloud features may no longer work
pause