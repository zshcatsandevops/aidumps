@echo off
:: PC-to-Console Optimization Script
:: Run this script as an Administrator.
:: It is designed for modern Windows 11 gaming systems.

::----------------------------------------------------------------------
:: [0/9] Administrative Privilege Check
::----------------------------------------------------------------------
openfiles >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)
cd /d "%~dp0"

::----------------------------------------------------------------------
:: Script Header & Warning
::----------------------------------------------------------------------
cls
echo =================================================================
echo        Windows 11 "PC-to-Console" Optimization Script
echo =================================================================
echo.
echo This script will apply advanced system optimizations for maximum
echo gaming performance and responsiveness.
echo.
echo It is based on modern, tested tweaks and corrects many common
echo but outdated "optimizations".
echo.
echo WARNING: This will make significant system changes!
echo          Close all other applications before continuing.
echo.
echo Press Ctrl+C within 7 seconds to abort...
ping 127.0.0.1 -n 8 >nul

::----------------------------------------------------------------------
:: [1/9] Ultimate Performance & Power Settings
::----------------------------------------------------------------------
echo [1/9] Activating Ultimate Performance & Disabling Hibernation...
:: Sets the Ultimate Performance power plan, ideal for desktops.
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul
:: Disables hibernation to free up disk space (hiberfil.sys).
powercfg /h off >nul
:: Keeps kernel in RAM. Good for systems with 16GB+ RAM.
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f >nul
:: Default workstation setting for LargeSystemCache (0 is for clients, 1 is for servers).
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v LargeSystemCache /t REG_DWORD /d 0 /f >nul

::----------------------------------------------------------------------
:: [2/9] Debloating - Removing Non-Essential UWP Apps
::----------------------------------------------------------------------
echo [2/9] Removing non-essential pre-installed applications...
set "bloat=Microsoft.BingNews Microsoft.BingWeather Microsoft.GamingApp Microsoft.GetHelp Microsoft.Getstarted Microsoft.MicrosoftOfficeHub Microsoft.MicrosoftSolitaireCollection Microsoft.PowerAutomateDesktop Microsoft.Todos Microsoft.Office.OneNote Microsoft.People Microsoft.SkypeApp Microsoft.Teams Microsoft.WindowsAlarms Microsoft.WindowsFeedbackHub Microsoft.WindowsMaps Microsoft.Xbox.TCUI Microsoft.XboxGameOverlay Microsoft.XboxGamingOverlay Microsoft.XboxIdentityProvider Microsoft.XboxSpeechToTextOverlay Microsoft.YourPhone Microsoft.ZuneMusic Microsoft.ZuneVideo"
for %%i in (%bloat%) do (
    powershell -ExecutionPolicy Bypass -Command "Get-AppxPackage -Name %%i -AllUsers | Remove-AppxPackage -ErrorAction SilentlyContinue" >nul
    powershell -ExecutionPolicy Bypass -Command "Get-AppxProvisionedPackage -Online | Where-Object DisplayName -Like '%%i' | Remove-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue" >nul
)

::----------------------------------------------------------------------
:: [3/9] Disabling Telemetry & Unnecessary Data Collection
::----------------------------------------------------------------------
echo [3/9] Hardening privacy by disabling telemetry...
:: Disables the Connected User Experiences and Telemetry service.
sc config "DiagTrack" start=disabled >nul
:: Disables the service that pushes apps.
sc config "DmWappushService" start=disabled >nul
:: Prevents Microsoft from collecting data about your system.
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f >nul
:: Disables Malicious Software Removal Tool auto-updates.
reg add "HKLM\SOFTWARE\Policies\Microsoft\MRT" /v DontOfferThroughWUAU /t REG_DWORD /d 1 /f >nul

::----------------------------------------------------------------------
:: [4/9] Core Gaming & GPU Optimizations (Modern Tweaks)
::----------------------------------------------------------------------
echo [4/9] Applying modern gaming and GPU optimizations...
:: Disables Game DVR & Game Bar features which can cause overhead.
reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\GameDVR" /v "AllowGameDVR" /t REG_DWORD /d 0 /f >nul
:: ENABLES Hardware Accelerated GPU Scheduling (HAGS). Crucial for modern GPUs.
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v HwSchMode /t REG_DWORD /d 2 /f >nul
:: Prioritizes games for CPU resources. 10 (0xA) is the default for gaming.
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 10 /f >nul
:: Optimizes games running in windowed/borderless mode.
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Priority" /t REG_DWORD /d 6 /f >nul

::----------------------------------------------------------------------
:: [5/9] Network Stack Optimization (Safe & Effective)
::----------------------------------------------------------------------
echo [5/9] Tuning network stack for lower latency...
:: Sets TCP auto-tuning to 'normal', the best balance of speed and stability.
netsh int tcp set global autotuninglevel=normal >nul
:: Enables Receive Side Scaling (RSS) to spread network load across CPU cores.
netsh int tcp set global rss=enabled >nul
:: Disables ECN capability, which can sometimes reduce throughput.
netsh int tcp set global ecncapability=disabled >nul
:: Enables TCP Fast Open for faster connections.
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TcpFastOpen" /t REG_DWORD /d 1 /f >nul
:: Disables Nagle's Algorithm, reducing latency in most online games.
reg add "HKLM\SOFTWARE\Microsoft\MSMQ\Parameters" /v "TCPNoDelay" /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces" /v "TcpAckFrequency" /t REG_DWORD /d 1 /f >nul

::----------------------------------------------------------------------
:: [6/9] Disabling Non-Essential Services (SAFE LIST)
::----------------------------------------------------------------------
echo [6/9] Disabling safe-to-remove, non-essential services...
:: This list is conservative and avoids breaking key features like Search, Updates, or Security.
set "services=RetailDemo DPS WMPNetworkSvc"
for %%s in (%services%) do (
    sc stop "%%s" 2>nul
    sc config "%%s" start=disabled >nul
)

::----------------------------------------------------------------------
:: [7/9] UI & Filesystem Responsiveness Tweaks
::----------------------------------------------------------------------
echo [7/9] Improving UI and filesystem responsiveness...
:: Removes menu animation delay for a snappier desktop experience.
reg add "HKCU\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d 0 /f >nul
:: Disables NTFS last access timestamps to reduce unnecessary disk I/O.
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v NtfsDisableLastAccessUpdate /t REG_DWORD /d 1 /f >nul
:: Disables the startup delay for programs after booting.
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Serialize" /v "StartupDelayInMSec" /t REG_DWORD /d 0 /f >nul

::----------------------------------------------------------------------
:: [8/9] System Cleanup & Cache Flush
::----------------------------------------------------------------------
echo [8/9] Performing final system cleanup...
:: Flushes the DNS resolver cache.
ipconfig /flushdns >nul
:: Resets the Winsock catalog to fix potential network issues.
netsh winsock reset >nul
:: Deletes temporary files.
if exist "%temp%" del /q /f /s "%temp%\*.*"
if exist "%windir%\temp" del /q /f /s "%windir%\temp\*.*"

::----------------------------------------------------------------------
:: [9/9] Completion & Final Recommendations
::----------------------------------------------------------------------
echo.
echo =================================================================
echo                 OPTIMIZATION COMPLETE!
echo =================================================================
echo.
echo A RESTART IS REQUIRED to apply all changes.
echo.
echo Final Manual Recommendations for True Console-like Performance:
echo.
echo 1. GPU Drivers: Use DDU (Display Driver Uninstaller) in Safe Mode
echo    to completely wipe your old drivers, then install the latest
echo    version from NVIDIA/AMD's website.
echo.
echo 2. BIOS/UEFI Settings: RESTART and enter your BIOS.
echo    - Enable XMP (Intel) or DOCP/EXPO (AMD) for your RAM.
echo    - Enable Above 4G Decoding.
echo    - Enable Resizable BAR (ReBAR).
echo    - Disable CSM (Compatibility Support Module) for a pure UEFI boot.
echo    - Consider disabling HPET (High Precision Event Timer) if you have
echo      a modern system, but test for stability afterwards.
echo.
echo 3. In-Game Settings: Always use Fullscreen Exclusive mode, not
echo    Borderless or Windowed, for the lowest input latency.
echo.
pause
exit