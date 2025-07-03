@echo off
title WINDOWS 7.1 INSTALLER — CAT-SAMA EDITION
color 0A

echo ======================================================
echo  WELCOME TO WINDOWS 7.1 INSTALLER — CAT-SAMA EDITION
echo  ALL BILL GATES, NSA, COPILOT, FEEDBACK REMOVED
echo  BLUETOOTH, WIFI, AND DRIVERS ARE SAFE
echo ======================================================
timeout /t 2 /nobreak >nul

:: ====== COSMETIC: Change Windows Branding to "Windows 7.1" ======
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName /d "Windows 7.1 Cat-sama Edition" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v EditionID /d "CatSama" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v DisplayVersion /d "7.1" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v BuildLab /d "7.1-Cat-sama" /f
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ReleaseId /d "7.1" /f

:: ====== Debloat & De-MS Operations ======
:: 1. Disable Telemetry and Data Collection
sc stop DiagTrack
sc delete DiagTrack
sc stop dmwappushservice
sc delete dmwappushservice
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f

:: 2. Remove Modern Microsoft Bloatware Apps
for %%A in (
    3DViewer
    BingWeather
    GetHelp
    Getstarted
    Messaging
    Microsoft3DViewer
    MicrosoftOfficeHub
    MicrosoftSolitaireCollection
    MicrosoftStickyNotes
    MixedReality.Portal
    Office.OneNote
    OneConnect
    Paint3D
    People
    SkypeApp
    WindowsAlarms
    WindowsCamera
    WindowsFeedbackHub
    WindowsMaps
    WindowsSoundRecorder
    XboxApp
    XboxGameOverlay
    XboxGamingOverlay
    XboxIdentityProvider
    XboxSpeechToTextOverlay
    ZuneMusic
    ZuneVideo
    MicrosoftTeams
    Microsoft.Copilot
    Copilot
    Cortana
    OneDrive
) do powershell -command "Get-AppxPackage *%%A* | Remove-AppxPackage -AllUsers"

:: 3. Disable Advertising ID & Suggestions
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo" /v Enabled /t REG_DWORD /d 0 /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v SubscribedContent-338388Enabled /t REG_DWORD /d 0 /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v SubscribedContent-338389Enabled /t REG_DWORD /d 0 /f

:: 4. Disable Cortana
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f

:: 5. Remove OneDrive
taskkill /f /im OneDrive.exe 2>nul
%SystemRoot%\SysWOW64\OneDriveSetup.exe /uninstall
%SystemRoot%\System32\OneDriveSetup.exe /uninstall

:: 6. Disable Connected User Experiences (DiagTrack)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\DiagTrack" /v Start /t REG_DWORD /d 4 /f

:: 7. Disable Copilot (Windows 11)
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot" /v TurnOffWindowsCopilot /t REG_DWORD /d 1 /f

:: 8. Block Unwanted Outbound Telemetry Hosts (Firewall)
netsh advfirewall firewall add rule name="Block Windows Telemetry" dir=out action=block remoteip=13.107.4.50,13.107.5.88,204.79.197.200,40.76.0.0/14,40.112.0.0/13,40.96.0.0/12,111.221.29.0/24 program="System" enable=yes

:: 9. Disable Feedback & Tips
reg add "HKCU\Software\Microsoft\Siuf\Rules" /v NumberOfSIUFInPeriod /t REG_DWORD /d 0 /f
reg add "HKCU\Software\Microsoft\Siuf\Rules" /v PeriodInNanoSeconds /t REG_QWORD /d 0 /f

:: 10. Restart Explorer for Branding/Settings to apply
taskkill /f /im explorer.exe
timeout /t 2 >nul
start explorer.exe

echo.
echo ======================================================
echo  SUCCESS! WINDOWS 7.1 CAT-SAMA EDITION IS INSTALLED!
echo  ALL BILL GATES MODULES HAVE BEEN NEUTRALIZED.
echo  WINVER & SYSTEM INFO NOW SAYS: Windows 7.1 Cat-sama Edition
echo ======================================================
pause
