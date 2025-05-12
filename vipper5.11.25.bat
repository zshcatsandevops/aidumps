@echo off
CLS

REM -----------------------------------------------------------------------------
REM Request Admin Privileges to ensure we have the necessary permissions.
REM -----------------------------------------------------------------------------
:checkPrivileges
echo Checking for admin rights...
NET FILE 1>NUL 2>NUL
IF '%errorlevel%' == '0' (
    echo Admin rights acquired! Let's proceed!
    GOTO gotPrivileges
) ELSE (
    echo No admin rights detected. Requesting elevation...
    GOTO requestPrivileges
)

:requestPrivileges
ECHO SET UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
ECHO UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
"%temp%\getadmin.vbs"
EXIT /B

:gotPrivileges
IF EXIST "%temp%\getadmin.vbs" ( DEL "%temp%\getadmin.vbs" )
pushd "%CD%"
CD /D "%~dp0"
echo Admin rights secured, ready to optimize!
echo -----------------------------------------------------------------------------
echo.
echo :: CATSEEK R1. WINDOWS 11 SPEED & ANTI-SPY SCRIPT ::
echo :: This script will boost your PC's performance! ::
echo :: Hold on tight, here we go! ::
echo -----------------------------------------------------------------------------
echo.
pause

REM -----------------------------------------------------------------------------
REM SECTION 1: DISABLING MICROSOFT TELEMETRY SERVICES
REM -----------------------------------------------------------------------------
echo [+] Disabling Telemetry Services...
sc stop DiagTrack >nul 2>&1
sc config DiagTrack start=disabled >nul 2>&1
echo     DiagTrack service disabled!
sc stop dmwappushservice >nul 2>&1
sc config dmwappushservice start=disabled >nul 2>&1
echo     dmwappushservice disabled!
sc stop WerSvc >nul 2>&1
sc config WerSvc start=disabled >nul 2>&1
echo     Windows Error Reporting disabled!
sc stop PcaSvc >nul 2>&1
sc config PcaSvc start=disabled >nul 2>&1
echo     Program Compatibility Assistant disabled!

echo [+] Modifying Telemetry Registry Settings...
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting" /v Disabled /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Privacy" /v TailoredExperiencesWithDiagnosticDataEnabled /t REG_DWORD /d 0 /f >nul 2>&1
echo     Telemetry registry settings updated!

echo [+] Disabling Telemetry Scheduled Tasks...
schtasks /Change /TN "Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\Application Experience\ProgramDataUpdater" /DISABLE >nul 2>&1


schtasks /Change /TN "Microsoft\Windows\Customer Experience Improvement Program\Consolidator" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\Customer Experience Improvement Program\UsbCeip" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\Autochk\Proxy" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\Feedback\Siuf\DmClient" /DISABLE >nul 2>&1
echo     Scheduled tasks disabled successfully!

REM -----------------------------------------------------------------------------
REM SECTION 2: OPTIMIZING WINDOWS 11 PERFORMANCE
REM -----------------------------------------------------------------------------
echo [+] Optimizing Visual Effects for performance...
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f >nul 2>&1
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v DragFullWindows /t REG_SZ /d "0" /f >nul 2>&1
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v FontSmoothing /t REG_SZ /d "2" /f >nul 2>&1
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9012038010000000 /f >nul 2>&1
echo     Visual effects optimized for speed!

echo [+] Speeding up Menu Response...
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v MenuShowDelay /t REG_SZ /d "0" /f >nul 2>&1
echo     Menus will now respond instantly!

echo [+] Setting Power Plan to High Performance...
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1
echo     High performance power plan activated!

echo [+] Disabling Unnecessary Services for Performance...
sc stop "SysMain" >nul 2>&1
sc config "SysMain" start=disabled >nul 2>&1
echo     SysMain (Superfetch) disabled!
sc stop "RemoteRegistry" >nul 2>&1
sc config "RemoteRegistry" start=disabled >nul 2>&1
echo     Remote Registry service disabled!
REM Uncomment these if you don't need them, but proceed with caution.
REM sc stop "Fax" >nul 2>&1
REM sc config "Fax" start=disabled >nul 2>&1
REM echo     Fax service disabled!
REM sc stop "TabletInputService" >nul 2>&1
REM sc config "TabletInputService" start=disabled >nul 2>&1
REM echo     Touch Keyboard and Handwriting service disabled!

echo [+] Disabling Cortana...
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search" /v "AllowCortana" /t REG_DWORD /d 0 /f >nul 2>&1
echo     Cortana disabled!

echo [+] Disabling Xbox Game Bar (can be re-enabled if needed)...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR" /v "AppCaptureEnabled" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\GameDVR" /v "AllowGameDVR" /t REG_DWORD /d 0 /f >nul 2>&1
echo     Xbox Game Bar disabled!

REM -----------------------------------------------------------------------------
REM SECTION 3: CLEANING TEMPORARY FILES
REM -----------------------------------------------------------------------------
echo [+] Cleaning temporary files and caches...
del /s /f /q "%windir%\temp\*.*" >nul 2>&1
del /s /f /q "%temp%\*.*" >nul 2>&1
del /s /f /q "%windir%\Prefetch\*.*" >nul 2>&1
ipconfig /flushdns >nul 2>&1
echo     Temporary files cleared and DNS cache flushed!

REM -----------------------------------------------------------------------------
REM COMPLETION MESSAGE
REM -----------------------------------------------------------------------------
echo.
echo -----------------------------------------------------------------------------
echo :: CATSEEK R1. OPTIMIZATION COMPLETE! ::
echo :: Your Windows 11 should now be running at peak performance! ::
echo :: Telemetry has been disabled, and performance is optimized! ::
echo :: Restart your computer to apply all changes fully! ::
echo :: Enjoy your enhanced system! ::
echo -----------------------------------------------------------------------------
echo.
pause
EXIT
