@echo off
::##################################################################################
::#                                                                                #
::#    --== TEAM FLAMES CO 1.0 HQRIPPER CATRNN [C] 20XX ==--                       #
::#                --< Windows Update Obliteration Script >--                      #
::#                                                                                #
::#      This script will aggressively disable Windows Update. Run as Admin.       #
::#                                                                                #
::##################################################################################

echo [INFO] This script must be run with administrative privileges.
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system" || (
    echo [ERROR] Administrator privileges are required. Please re-run this script as an Administrator.
    pause
    exit /b
)

echo.
echo [STAGE 1] Stopping and Disabling Windows Update Services...
echo -----------------------------------------------------------
net stop wuauserv
sc config wuauserv start= disabled

net stop BITS
sc config BITS start= disabled

net stop DoSvc
sc config DoSvc start= disabled

net stop UsoSvc
sc config UsoSvc start= disabled

net stop WaaSMedicSvc
sc config WaaSMedicSvc start= disabled

echo [SUCCESS] Services have been stopped and disabled.

echo.
echo [STAGE 2] Applying Registry Modifications to Neuter Windows Update...
echo --------------------------------------------------------------------
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v "DoNotConnectToWindowsUpdateInternetLocations" /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v "ExcludeWUDriversInQualityUpdate" /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "NoAutoUpdate" /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "AUOptions" /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "UseWUServer" /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "DetectionFrequencyEnabled" /t REG_DWORD /d 0 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "AutoInstallMinorUpdates" /t REG_DWORD /d 0 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "AllowAutoUpdate" /t REG_DWORD /d 0 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "ScheduledInstallDay" /t REG_DWORD /d 0 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v "ScheduledInstallTime" /t REG_DWORD /d 3 /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" /v "NoWindowsUpdate" /t REG_DWORD /d 1 /f

echo [SUCCESS] Registry has been modified.

echo.
echo [STAGE 3] Seizing Control and Renaming Update Components...
echo ------------------------------------------------------------
takeown /f "%windir%\System32\UsoClient.exe" /a >nul 2>&1
icacls "%windir%\System32\UsoClient.exe" /grant administrators:F >nul 2>&1
if exist "%windir%\System32\UsoClient.exe" (
    rename "%windir%\System32\UsoClient.exe" "UsoClient.exe.FLAMES"
    echo [SUCCESS] UsoClient.exe has been renamed.
) else (
    echo [INFO] UsoClient.exe not found or already renamed.
)

echo.
echo [STAGE 4] Disabling Scheduled Tasks for Updates...
echo --------------------------------------------------
schtasks /Change /TN "Microsoft\Windows\WindowsUpdate\Automatic App Update" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\WindowsUpdate\Scheduled Start" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\WindowsUpdate\sih" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\WindowsUpdate\sihboot" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\UpdateOrchestrator\Schedule Scan" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\UpdateOrchestrator\Schedule Wake To Work" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\UpdateOrchestrator\UpdateAssistant" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\UpdateOrchestrator\UpdateAssistantCalendarRun" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\UpdateOrchestrator\USO_Broker_Display" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\UpdateOrchestrator\USO_Broker_Ready" /DISABLE >nul 2>&1
schtasks /Change /TN "Microsoft\Windows\UpdateOrchestrator\USO_Broker_Request" /DISABLE >nul 2>&1

echo [SUCCESS] Scheduled tasks have been disabled.

echo.
echo [STAGE 5] Blocking Microsoft Update Servers via Hosts File...
echo -------------------------------------------------------------
set HOSTS_PATH=%windir%\System32\drivers\etc\hosts
echo 127.0.0.1 windowsupdate.microsoft.com >> %HOSTS_PATH%
echo 127.0.0.1 *.windowsupdate.microsoft.com >> %HOSTS_PATH%
echo 127.0.0.1 download.windowsupdate.com >> %HOSTS_PATH%
echo 127.0.0.1 *.download.windowsupdate.com >> %HOSTS_PATH%
echo 127.0.0.1 download.microsoft.com >> %HOSTS_PATH%
echo 127.0.0.1 *.download.microsoft.com >> %HOSTS_PATH%
echo 127.0.0.1 wustat.windows.com >> %HOSTS_PATH%
echo 127.0.0.1 ntservicepack.microsoft.com >> %HOSTS_PATH%
echo 127.0.0.1 stats.microsoft.com >> %HOSTS_PATH%

echo [SUCCESS] Update servers blocked in hosts file.

echo.
echo ###########################################################
echo ##                                                       ##
echo ##  TEAM FLAMES CO - Windows Update has been OBLITERATED ##
echo ##                                                       ##
echo ###########################################################
echo.
echo A system restart is recommended to ensure all changes take full effect.
pause
