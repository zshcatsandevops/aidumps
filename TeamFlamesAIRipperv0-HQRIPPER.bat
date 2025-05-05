@echo off
setlocal enabledelayedexpansion
title Win Nuker 1.1b - Windows Optimization Toolkit

::# Safety Check
echo Checking administrator privileges...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ########################################################
    echo # ERROR: Please run this script as Administrator!       #
    echo ########################################################
    timeout /t 5 /nobreak >nul
    exit /b 1
)

::# Configuration
set BACKUP_DIR=%SystemDrive%\WinNuker_Backup_%date:~-4%-%date:~3,2%-%date:~0,2%
set LOGFILE=%BACKUP_DIR%\optimization.log

::# Initialization
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%" >nul
    echo Backup directory created: %BACKUP_DIR% >> "%LOGFILE%"
)

::# Main Menu
:menu
cls
echo ########################################################
echo #                 WIN NUKER 1.1b                       #
echo ########################################################
echo.
echo [1] Apply Performance Optimizations
echo [2] Apply Security Hardening
echo [3] Clean System Junk Files
echo [4] Restore Default Settings
echo [5] Exit
echo.
choice /c 12345 /n /m "Select operation [1-5]: "

if errorlevel 5 exit /b
if errorlevel 4 goto restore
if errorlevel 3 goto clean
if errorlevel 2 goto security
if errorlevel 1 goto optimize

::# Performance Optimization Section
:optimize
cls
echo ########################################################
echo #              PERFORMANCE OPTIMIZATION               #
echo ########################################################
echo.
echo [1] Apply All Performance Tweaks
echo [2] Power Settings Optimization
echo [3] Visual Effects Tuning
echo [4] Startup Program Management
echo [5] Service Optimization
echo [6] Network Tweaks
echo [7] Return to Main Menu
echo.
choice /c 1234567 /n /m "Select optimization [1-7]: "

if errorlevel 7 goto menu
if errorlevel 6 goto network
if errorlevel 5 goto services
if errorlevel 4 goto startup
if errorlevel 3 goto visual
if errorlevel 2 goto power
if errorlevel 1 goto all_perf

:all_perf
call :power
call :visual
call :startup
call :services
call :network
goto menu

:power
echo.
echo Applying High Performance power plan...
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >> "%LOGFILE%" 2>&1
echo Disabling hibernation...
powercfg /hibernate off >> "%LOGFILE%" 2>&1
goto :EOF

:visual
echo.
echo Optimizing visual performance...
reg add "HKCU\Control Panel\Desktop" /v DragFullWindows /t REG_SZ /d 0 /f >> "%LOGFILE%" 2>&1
reg add "HKCU\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d 0 /f >> "%LOGFILE%" 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ListviewShadow /t REG_DWORD /d 0 /f >> "%LOGFILE%" 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f >> "%LOGFILE%" 2>&1
goto :EOF

:startup
echo.
echo Backing up startup programs...
reg export "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" "%BACKUP_DIR%\user_startup.reg" /y >> "%LOGFILE%" 2>&1
reg export "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" "%BACKUP_DIR%\system_startup.reg" /y >> "%LOGFILE%" 2>&1

echo Disabling startup programs...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /f >> "%LOGFILE%" 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /f >> "%LOGFILE%" 2>&1
del /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\*" >> "%LOGFILE%" 2>&1
del /q "%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup\*" >> "%LOGFILE%" 2>&1
goto :EOF

:services
echo.
echo Optimizing services...
set "services=DiagTrack DPS SysMain WdiServiceHost WdiSystemHost RetailDemo WMPNetworkSvc"
for %%s in (%services%) do (
    sc config "%%s" start=disabled >> "%LOGFILE%" 2>&1
    sc stop "%%s" >> "%LOGFILE%" 2>&1
)
goto :EOF

:network
echo.
echo Optimizing network settings...
netsh int tcp set global autotuninglevel=normal >> "%LOGFILE%" 2>&1
netsh winsock reset >> "%LOGFILE%" 2>&1
ipconfig /flushdns >> "%LOGFILE%" 2>&1
goto :EOF

::# Security Hardening Section
:security
cls
echo ########################################################
echo #                SECURITY HARDENING                    #
echo ########################################################
echo.
echo [1] Apply All Security Tweaks
echo [2] Disable Telemetry & Tracking
echo [3] Disable Cortana
echo [4] Disable Windows Spy Features
echo [5] Disable SMBv1 Protocol
echo [6] Return to Main Menu
echo.
choice /c 123456 /n /m "Select security measure [1-6]: "

if errorlevel 6 goto menu
if errorlevel 5 goto smb
if errorlevel 4 goto spy
if errorlevel 3 goto cortana
if errorlevel 2 goto telemetry
if errorlevel 1 goto all_sec

:all_sec
call :telemetry
call :cortana
call :spy
call :smb
goto menu

:telemetry
echo.
echo Disabling telemetry...
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f >> "%LOGFILE%" 2>&1
schtasks /change /tn "\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser" /disable >> "%LOGFILE%" 2>&1
goto :EOF

:cortana
echo.
echo Disabling Cortana...
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f >> "%LOGFILE%" 2>&1
goto :EOF

:spy
echo.
echo Disabling activity history tracking...
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v EnableActivityFeed /t REG_DWORD /d 0 /f >> "%LOGFILE%" 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v PublishUserActivities /t REG_DWORD /d 0 /f >> "%LOGFILE%" 2>&1
goto :EOF

:smb
echo.
echo Disabling SMBv1...
sc config lanmanworkstation depend= bowser/mrxsmb20/nsi >> "%LOGFILE%" 2>&1
sc config mrxsmb10 start= disabled >> "%LOGFILE%" 2>&1
goto :EOF

::# Cleanup Section
:clean
cls
echo ########################################################
echo #                  SYSTEM CLEANUP                      #
echo ########################################################
echo.
echo Cleaning temporary files...
cleanmgr /sagerun:1 >> "%LOGFILE%" 2>&1

echo Clearing DNS cache...
ipconfig /flushdns >> "%LOGFILE%" 2>&1

echo Cleaning prefetch...
del /q /f %SystemRoot%\Prefetch\* >> "%LOGFILE%" 2>&1

echo.
echo Cleanup completed!
timeout /t 3 /nobreak >nul
goto menu

::# Restoration Section
:restore
cls
echo ########################################################
echo #                RESTORE DEFAULTS                     #
echo ########################################################
echo.
echo [1] Restore Startup Programs
echo [2] Reset Power Plan
echo [3] Reset Service Configurations
echo [4] Return to Main Menu
echo.
choice /c 1234 /n /m "Select restoration option [1-4]: "

if errorlevel 4 goto menu
if errorlevel 3 goto restore_services
if errorlevel 2 goto restore_power
if errorlevel 1 goto restore_startup

:restore_startup
echo.
echo Restoring startup programs...
if exist "%BACKUP_DIR%\user_startup.reg" (
    reg import "%BACKUP_DIR%\user_startup.reg" >> "%LOGFILE%" 2>&1
)
if exist "%BACKUP_DIR%\system_startup.reg" (
    reg import "%BACKUP_DIR%\system_startup.reg" >> "%LOGFILE%" 2>&1
)
goto menu

:restore_power
echo.
echo Restoring balanced power plan...
powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e >> "%LOGFILE%" 2>&1
goto menu

:restore_services
echo.
echo Restoring default service configurations...
set "services=DiagTrack DPS SysMain WdiServiceHost WdiSystemHost RetailDemo WMPNetworkSvc"
for %%s in (%services%) do (
    sc config "%%s" start=demand >> "%LOGFILE%" 2>&1
)
goto menu

::# Exit
:exit
endlocal
exit /b 0
