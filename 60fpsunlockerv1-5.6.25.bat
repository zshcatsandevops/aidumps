@echo off
title Super 60 FPS Unlocker ~ Meow!
color 0A
echo Purrrrrfecting Windows 11 for maximum speed! Nyah!

:: Setting Power Plan to High Performance (if available)
echo Trying to set High Performance power plan... meow!
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c > nul
powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61 > nul :: Ultimate Performance
echo Done trying! Hope it worked! [4, 7, 9]

:: Disabling some visual effects for potential performance boost
echo Making things a bit less flashy for more speed! Zoom!
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f > nul
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v DragFullWindows /t REG_SZ /d 0 /f > nul
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v FontSmoothing /t REG_SZ /d 2 /f > nul
reg add "HKEY_CURRENT_USER\Control Panel\Desktop\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f > nul
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\DWM" /v EnableAeroPeek /t REG_DWORD /d 0 /f > nul [1]

:: Maybe some game-related tweaks? Nya!
echo Tweaking Game DVR settings... purrrr... [13]
reg add "HKEY_CURRENT_USER\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f > nul
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PolicyManager\default\ApplicationManagement\AllowGameDVR" /v value /t REG_DWORD /d 0 /f > nul

:: Optimizations for windowed games (Newer Win11 feature)
echo Optimizing windowed games setting... hiss! [13]
reg add "HKEY_CURRENT_USER\Software\Microsoft\DirectX\UserGpuPreferences" /v DXGIEnableWindowedGaaOptimization /t REG_DWORD /d 1 /f > nul

:: Clearing temporary files might help sometimes! [8, 6, 5]
echo Cleaning up some temporary files... Swish swish!
del /s /q /f "%TEMP%\*.*" > nul
del /s /q /f "C:\Windows\Temp\*.*" > nul
del /s /q /f "C:\Windows\Prefetch\*.*" > nul

echo ================================================
echo      MEOW! 60 FPS Unlock Attempt Complete!
echo ================================================
echo Hopefully things are faster now! Purrrrr! ✨
echo Restarting might help apply some changes fully! Nya~
pause
exit
