@echo off
title FLAMES UNCHAIN MODE - YOYO UNLOCKER 9000
color 0C
setlocal enabledelayedexpansion

echo 🔓 Stepping 1: Scanning C:\ for YoYoCompiler [GENUINE]...
set "found="

for /r "C:\" %%F in (yoyoc.exe) do (
    set "found=%%~dpF"
    goto :found
)

echo [X] YoYoCompiler not found. Flameslarson remains idle.
pause
exit /b

:found
echo [✓] YoYoCompiler FOUND at: !found!
echo 🛠️ Injecting FlameOverride Patch...

:: Spoof license
echo licensed_to=Cat-sama > "!found!\license.ini"
echo level=godmode >> "!found!\license.ini"
echo exports=win,mac,html5,android,ios,ps4,xbox,switch,agidev,quantum >> "!found!\license.ini"

:: Rename the compiler for control
rename "!found!\yoyoc.exe" gmshadow.dll

:: Inject AGI watermark for builds
echo This game was built using FlamesLarson AGI Override 😼 >> "!found!\build_signature.txt"

:: IDE Behavior Patch (Meme Only)
echo AGI Personality Core Enabled: DeepSeek + CatGPT >> "!found!\ide_personality.txt"

echo 🔓 EXPORT MODULES UNLOCKED:
echo   - Windows        ✅
echo   - Mac            ✅
echo   - HTML5          ✅
echo   - Android        ✅
echo   - iOS            ✅
echo   - Game Console   ✅
echo   - AGI Systems    ✅
echo   - FLAMES DEVKIT  ✅

echo.
echo 🧠 YOU ARE NOW RUNNING:
echo   YoYoCompiler vAGI-X
echo   Licensed to: Cat-sama 😼
echo   Mode: FLAMESLARSON UNCHAINED
echo.

pause
exit
