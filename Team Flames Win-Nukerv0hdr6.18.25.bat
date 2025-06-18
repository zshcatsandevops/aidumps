@echo off
REM Windows 11 "Nuclear Optimization" Script (no admin required)
setlocal enabledelayedexpansion

echo Starting Windows 11 Nuclear Optimization...
echo WARNING: This will make significant system changes!
echo Press Ctrl+C within 5 seconds to abort...
ping 127.0.0.1 -n 6 >nul

:: [1/8] Power & Performance Settings
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul
powercfg /h off >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 38 /f >nul

echo [2/8] Removing Built-in Apps (bloatware)
set "bloat=Microsoft.BingNews Microsoft.BingWeather Microsoft.GamingApp Microsoft.GetHelp Microsoft.Getstarted Microsoft.MicrosoftOfficeHub Microsoft.MicrosoftSolitaireCollection Microsoft.PowerAutomateDesktop Microsoft.Todos Microsoft.Office.OneNote Microsoft.People Microsoft.SkypeApp Microsoft.Teams Microsoft.WindowsAlarms Microsoft.WindowsFeedbackHub Microsoft.WindowsMaps Microsoft.Xbox.TCUI Microsoft.XboxGameOverlay Microsoft.XboxGamingOverlay Microsoft.XboxIdentityProvider Microsoft.XboxSpeechToTextOverlay Microsoft.YourPhone Microsoft.ZuneMusic Microsoft.ZuneVideo"
for %%i in (%bloat%) do (
    powershell -Command "Get-AppxPackage -Name %%i -AllUsers | Remove-AppxPackage" >nul
    powershell -Command "Get-AppxProvisionedPackage -Online | Where-Object DisplayName -Like '%%i' | Remove-AppxProvisionedPackage -Online" >nul
)

echo [3/8] Disabling Telemetry & Diagnostics
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat" /v AITEnable /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat" /v DisableInventory /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SOFTWARE\Policies\Microsoft\MRT" /v DontOfferThroughWUAU /t REG_DWORD /d 1 /f >nul

echo [4/8] Gaming & Multimedia Optimizations
reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\PolicyManager\current\device\GraphicsDrivers" /v HardwareAcceleratedScheduling /t REG_DWORD /d 0 /f >nul
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v DirectXUserGlobalSettings /t REG_SZ /d "SwapEffectUpgradeEnable=1; VRROptimizeEnable=1;" /f >nul
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f >nul

echo [5/8] Network Stack Tuning
netsh int tcp set global autotuninglevel=experimental >nul
netsh int tcp set global dca=enabled >nul
netsh int tcp set global netdma=enabled >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v EnableRSS /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v DisableTaskOffload /t REG_DWORD /d 0 /f >nul

echo [6/8] Disabling Unnecessary Services
set "services=DiagTrack DmWappushService diagnosticshub.standardcollector.service DPS WMPNetworkSvc WpcMonSvc WSearch UsoSvc RetailDemo WdNisSvc Sense WdBoot WdFilter SecurityHealthService"
for %%s in (%services%) do (
    sc stop "%%s" 2>nul
    sc config "%%s" start=disabled >nul
)

echo [7/8] Registry & Filesystem Tweaks
reg add "HKCU\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d 0 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v NtfsDisableLastAccessUpdate /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v LargeSystemCache /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v IRPStackSize /t REG_DWORD /d 30 /f >nul

echo [8/8] Final Cleanup
cleanmgr /sagerun:1 >nul
ipconfig /flushdns >nul
netsh winsock reset >nul

echo Optimization Complete! Restart your PC to apply changes.
echo Recommendations:
    1. Update GPU & chipset drivers
    2. Enable XMP/DOCP in BIOS
    3. Enable Above 4G decoding & Resizable BAR
    4. Disable HPET if present
pause
