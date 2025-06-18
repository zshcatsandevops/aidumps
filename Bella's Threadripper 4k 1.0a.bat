@echo off
REM Windows 11 “PS5 PRO Speed” Optimization Script
REM Aggressive low‑latency & gaming‑centric tweaks – USE AT YOUR OWN RISK!
REM Some commands require Administrator rights. Back‑up & create a restore point first.

setlocal enabledelayedexpansion
chcp 65001 >nul

echo ----------------------------------------------------------
echo   Windows 11 – “PS5 PRO Speed” Optimization Routine
echo   Goal: Minimize latency & maximize sustained FPS
echo ----------------------------------------------------------
echo Press Ctrl+C within 8 seconds to cancel...
ping 127.0.0.1 -n 9 >nul

:: [1/10] Power Plan – Ultimate Performance if present, otherwise High Performance
for /f "tokens=2 delims==" %%g in ('powercfg /list ^| find /i "Ultimate Performance"') do (
    powercfg /setactive %%g >nul
)
if errorlevel 1 (
    powercfg /setactive scheme_min >nul
)
powercfg /h off >nul

:: Disable CPU parking & throttling
powercfg -setacvalueindex scheme_current sub_processor CPMINCORES 100 >nul
powercfg -setacvalueindex scheme_current sub_processor PROCTHROTTLEMIN 100 >nul
powercfg -setactive scheme_current >nul

:: [2/10] GPU Scheduling & Game Mode
reg add "HKLM\SOFTWARE\Microsoft\PolicyManager\current\device\GraphicsDrivers" /v HardwareAcceleratedScheduling /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\GameBar" /v AutoGameModeEnabled /t REG_DWORD /d 1 /f >nul
reg add "HKCU\SOFTWARE\Microsoft\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 1 /f >nul

:: Disable Game DVR & background recording
reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f >nul
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f >nul

:: [3/10] Memory & Cache tweaks
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v LargeSystemCache /t REG_DWORD /d 1 /f >nul

:: [4/10] Remove selected built‑in apps (light bloat list)
set "bloat=Microsoft.BingNews Microsoft.GamingApp Microsoft.GetHelp Microsoft.MicrosoftSolitaireCollection Microsoft.SkypeApp Microsoft.Teams Microsoft.YourPhone Microsoft.People"
for %%i in (%bloat%) do (
    powershell -Command "Get-AppxPackage -Name %%i -AllUsers ^| Remove-AppxPackage" >nul
    powershell -Command "Get-AppxProvisionedPackage -Online ^| Where-Object DisplayName -Like '%%i' ^| Remove-AppxProvisionedPackage -Online" >nul
)

:: [5/10] Telemetry & Diagnostics
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat" /v DisableInventory /t REG_DWORD /d 1 /f >nul

:: [6/10] Multimedia & system responsiveness
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f >nul

:: [7/10] Network Stack tuning (safe)
netsh int tcp set global autotuninglevel=normal >nul
netsh int tcp set global rss=enabled >nul

:: [8/10] Optional Windows Features OFF
dism /online /Disable-Feature /FeatureName:"Printing-PDFServices-Features" /NoRestart >nul

:: [9/10] Stop heavy services (run‑time only)
set "services=DiagTrack WMPNetworkSvc WSearch RetailDemo"
for %%s in (%services%) do (
    sc stop "%%s" >nul 2>&1
)

:: [10/10] Cleanup & Restart Prompt
ipconfig /flushdns >nul

echo.
echo ----------------------------------------------------------
echo  Optimization routine completed!
echo  PLEASE RESTART your PC to apply all changes.
echo ----------------------------------------------------------

:: Pause at the very end to view summary
pause

endlocal
