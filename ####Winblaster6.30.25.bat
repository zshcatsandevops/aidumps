@echo off
:: zero_shot_test.bat  —  Windows 11 performance tune‑up
:: Author: Cat‑sama’s AI assistant  |  Rev: 01‑Jul‑2025

:: 0. Safety net
echo Creating system restore point...
powershell -NoLogo -NoProfile -Command ^
  "Checkpoint-Computer -Description 'Pre‑Optimize' -RestorePointType 'MODIFY_SETTINGS'"

:: 1. Ultimate Performance power plan
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 >nul
powercfg -setactive   e9a42b02-d5df-448d-aa00-03f14749eb61

:: 2. Turn off transparency (requires logoff to fully apply)
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f

:: 3. Visual effects = Best Performance
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f

:: 4. Kill OneDrive and disable future auto‑start
taskkill /f /im OneDrive.exe 2>nul
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\OneDrive" /v DisableFileSyncNGSC /t REG_DWORD /d 1 /f

:: 5. Disable background apps for current user
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" /v GlobalUserDisabled /t REG_DWORD /d 1 /f

:: 6. Storage clean‑up (Temp, old updates, etc.)
cleanmgr /verylowdisk
cleanmgr /sagerun:1

:: 7. Component Store cleanup (quiet, may take time)
dism /online /cleanup-image /startcomponentcleanup /quiet

:: 8. Restart Explorer to pick up UI changes
taskkill /f /im explorer.exe & start explorer.exe

echo.
echo All tasks queued. Reboot for full effect.
pause
