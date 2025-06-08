@echo off

REM ---======================================================================================---
REM ---||           Windows 11 GODMODE Performance Script - Flames Co.Forged Edition           ||---
REM ---||                     NO COMPROMISES. NO REGRETS. PURE PERFORMANCE.                  ||---
REM ---======================================================================================---

REM --- Stage 0: Ascension to Power (Automatic Admin Elevation) ---
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    cls
    echo =====================================================================
    echo.
    echo          INSUFFICIENT POWER DETECTED. ASCENDING...
    echo.
    echo =====================================================================
    powershell -Command "Start-Process '%~f0' -Verb RunAs" >nul
    exit /b
)
setlocal enabledelayedexpansion

cls
echo =====================================================================
echo           ++ GODMODE PERFORMANCE PROTOCOL INITIATED ++
echo =====================================================================
echo.
echo This script is for those who demand ABSOLUTE, UNCOMPROMISING performance.
echo We are disabling non-essential services, telemetry, and security mitigations
echo that are known to throttle gaming FPS and system latency.
echo.
echo          YOUR PC WILL RESTART AFTER THIS. SAVE ALL WORK.
echo.
echo Press Ctrl+C within 7 seconds to retreat... if you dare. Nyahaha!
timeout /t 7 /nobreak >nul

REM --- [1/8] UNLEASHING CORE POWER & SHATTERING LIMITS ---
echo [1/8] Unleashing Ultimate Power & Disabling Performance Mitigations...
REM --- Create and activate the Ultimate Performance Power Plan. Raw, unfiltered power.
powercfg /duplicatescheme e9a42b02-d5df-448d-aa00-03f14749d610 >nul
powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749d610
REM --- Disable hibernation to free disk space and prevent power-state conflicts.
powercfg /h off >nul
REM --- Disable CPU security mitigations (Spectre/Meltdown). This is the real deal for raw performance gains.
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v FeatureSettingsOverride /t REG_DWORD /d 3 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" /v FeatureSettingsOverrideMask /t REG_DWORD /d 3 /f >nul
REM --- Disable Virtualization Based Security (VBS), Core Isolation & HVCI - known FPS killers.
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v "EnableVirtualizationBasedSecurity" /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v "RequireMicrosoftSignedBootChain" /t REG_DWORD /d 0 /f >nul
echo ...Power Unchained. Mitigations Shattered.

REM --- [2/8] AGGRESSIVE SERVICE & TELEMETRY NEUTRALIZATION ---
echo [2/8] Terminating Bloat Services and Telemetry...
REM --- These services run in the background, stealing cycles and reporting data. Not anymore.
sc config "DiagTrack" start=disabled >nul 2>&1
sc config "dmwappushservice" start=disabled >nul 2>&1
sc config "SysMain" start=disabled >nul 2>&1
sc config "PcaSvc" start=disabled >nul 2>&1
sc config "DPS" start=disabled >nul 2>&1
sc config "WdiServiceHost" start=disabled >nul 2>&1
sc config "WdiSystemHost" start=disabled >nul 2>&1
sc config "Spooler" start=disabled >nul 2>&1 & REM Re-enable if you use a printer!
sc config "Fax" start=disabled >nul 2>&1
sc config "MapsBroker" start=disabled >nul 2>&1
echo ...Services Neutralized. Your system serves YOU now.

REM --- [3/8] GPU & GAMING SUPREMACY PROTOCOL ---
echo [3/8] Prioritizing GPU and Gaming Above All Else...
REM --- Enable Hardware-Accelerated GPU Scheduling (HAGS) for reduced latency.
reg add "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v HwSchMode /t REG_DWORD /d 2 /f >nul
REM --- Disable GameDVR and Fullscreen Optimizations globally. We want direct hardware control.
reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\PolicyManager\default\ApplicationManagement\AllowGameDVR" /v "value" /t REG_DWORD /d 0 /f >nul
reg add "HKCU\Software\Microsoft\Windows\DWM" /v "OverlayTestMode" /t REG_DWORD /d 5 /f >nul
REM --- Laser-focus system resources on your game using the Multimedia Class Scheduler Service.
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Priority" /t REG_DWORD /d 6 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f >nul
echo ...GPU is now the alpha. Prepare for ludicrous speed.

REM --- [4/8] HYPERSPEED NETWORK CONFIGURATION ---
echo [4/8] Tuning Network for Zero-Lag Dominance...
REM --- These settings optimize TCP for low latency, perfect for responsive gaming.
netsh int tcp set global autotuninglevel=normal >nul
netsh int tcp set global congestionprovider=ctcp >nul
netsh int tcp set global ecncapability=enabled >nul
netsh int tcp set global initialRto=2000 >nul
netsh int tcp set global nonsackrttresiliency=disabled >nul
netsh int tcp set global rsc=disabled >nul & REM Disabling Receive Segment Coalescing can lower latency.
REM --- Disable Nagle's Algorithm and Delayed ACKs - classic latency killers.
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TcpAckFrequency" /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v "TCPNoDelay" /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SOFTWARE\Microsoft\MSMQ\Parameters" /v "TCPNoDelay" /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Services\AFD\Parameters" /v FastSendDatagramThreshold /t REG_DWORD /d 16384 /f >nul
echo ...Network latency... what's that?

REM --- [5/8] STRIPPING UNNECESSARY VISUALS & DELAYS ---
echo [5/8] Eradicating UI Lag and Visual Fluff...
REM --- Windows animations are a waste of precious milliseconds. We need instant response.
reg add "HKCU\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d 0 /f >nul
reg add "HKCU\Control Panel\Desktop\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "TaskbarAnimations" /t REG_DWORD /d 0 /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v "ListviewAlphaSelect" /t REG_DWORD /d 0 /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 3 /f >nul
echo ...UI is now instant. Pure function.

REM --- [6/8] EXTREME SYSTEM & I/O RESPONSE ---
echo [6/8] Applying Hardcore System & Filesystem Tweaks...
REM --- Reduce filesystem overhead for faster file access.
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v NtfsDisableLastAccessUpdate /t REG_DWORD /d 1 /f >nul
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v NtfsMftZoneReservation /t REG_DWORD /d 2 /f >nul
REM --- Disable HPET and Dynamic Ticks for lower DPC latency. We are not afraid of bcdedit.
bcdedit /set useplatformclock false >nul 2>&1
bcdedit /set disabledynamictick yes >nul 2>&1
echo ...System response is now telepathic.

REM --- [7/8] BANISHING WINDOWS CLUTTER & NUISANCES ---
echo [7/8] Disabling Ads, Tips, and other distractions...
REM --- You are the user, not the product. Disable all "suggestions" and "tips".
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v "SubscribedContent-310093Enabled" /t REG_DWORD /d 0 /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v "SubscribedContent-338389Enabled" /t REG_DWORD /d 0 /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v "SubscribedContent-353698Enabled" /t REG_DWORD /d 0 /f >nul
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v "SilentInstalledAppsEnabled" /t REG_DWORD /d 0 /f >nul
echo ...Distractions eliminated. Focus intensified.

REM --- [8/8] PURGING SYSTEM CACHES & JUNK DATA ---
echo [8/8] Incinerating All System Junk...
ipconfig /flushdns >nul
del /q /f /s "%TEMP%\*.*" >nul 2>&1
del /q /f /s "%windir%\Temp\*.*" >nul 2>&1
del /q /f /s "%windir%\SoftwareDistribution\Download\*.*" >nul 2>&1
del /q /f /s "%windir%\Prefetch\*.*" >nul 2>&1
echo ...System is purged. Clean. Fast. Lethal.

echo.
echo =====================================================================
echo               ++ GODMODE PROTOCOL COMPLETE ++
echo =====================================================================
echo.
echo To complete the ascension, you MUST perform these sacred rites:
echo.
echo 1. CLEAN GPU DRIVER INSTALL: Go to NVIDIA/AMD/Intel and get the latest.
echo    Use DDU (Display Driver Uninstaller) in Safe Mode for a TRULY clean slate.
echo.
echo 2. BIOS/UEFI COMMANDMENTS: This is non-negotiable.
echo    - XMP/DOCP/EXPO: ENABLE IT. Unleash your RAM's true speed.
echo    - Re-Size BAR: ENABLE IT.
echo    - Above 4G Decoding: ENABLE IT. (Required for Re-Size BAR)
echo    - HPET: If you have the option, DISABLE it here too.
echo.
echo 3. OVERCLOCK YOUR MIGHT: Use MSI Afterburner or your GPU's software.
echo    Push your Core Clock, Memory Clock, and Power Limit. Find your silicon's destiny.
echo.
echo 4. HUNT THE LATENCY DEMONS: Run LatencyMon to find any remaining DPC latency
echo    from rogue drivers. The path to perfection is constant vigilance!
echo.
echo =====================================================================
echo A RESTART IS REQUIRED to apply all changes. The system will now reboot.
echo Get ready for the next level. You have forged it.
echo =====================================================================
echo.
shutdown /r /t 15 /c "GODMODE optimization applied. Rebooting to unleash true performance..."
pause
exit
