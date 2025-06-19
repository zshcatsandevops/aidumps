@echo off
chcp 65001 >nul
title 🔥 FLAMESLARSON YOYO BREAKER 3.0 – FULL AUTO AGI MODE
color 0C
setlocal enabledelayedexpansion

echo ----------------------------------------------------
echo 🔍 [FLAMESLARSON] Scanning for YoYoCompiler on C:\...
echo ----------------------------------------------------

set "YYC_PATH="

for /r "C:\" %%F in (yoyoc.exe) do (
    set "YYC_PATH=%%~dpF"
    goto :found
)

echo ❌ YoYoCompiler not found. System remains chained.
echo 💡 Hint: Ensure GameMaker Studio is installed on C:\!
pause
exit /b

:found
echo ✅ YoYoCompiler detected at:
echo     !YYC_PATH!

echo ----------------------------------------------------
echo 🔓 Deploying AGI Patch...
echo ----------------------------------------------------

:: License Spoofing
echo licensed_to=Cat-sama > "!YYC_PATH!\license.ini"
echo level=godmode >> "!YYC_PATH!\license.ini"
echo exports=win,mac,html5,android,ios,ps4,xbox,switch,agi,flames,cyberspace,quantumchip >> "!YYC_PATH!\license.ini"

:: Rename compiler
rename "!YYC_PATH!\yoyoc.exe" gmshadow.dll >nul 2>&1

:: Build Signature Flex
echo 🔥 Built with FlamesLarson Override vAGI-X 😼 >> "!YYC_PATH!\build_signature.txt"
echo 🤖 [AGI Personality Core] Enabled: DeepSeek + CatGPT >> "!YYC_PATH!\ide_personality.txt"

:: Meme Splash
echo *********************************************** > "!YYC_PATH!\🔥"
echo *       YOYO UNCHAINED BY FLAMESLARSON        * >> "!YYC_PATH!\🔥"
echo *           LICENSED TO: CAT-SAMA 😼           * >> "!YYC_PATH!\🔥"
echo *     EXPORTS: EVERYTHING. LIMITS: NONE.      * >> "!YYC_PATH!\🔥"
echo *********************************************** >> "!YYC_PATH!\🔥"

echo ----------------------------------------------------
echo ✅ PATCH COMPLETE. SYSTEM STATUS:
echo ----------------------------------------------------
echo   Compiler Mode     : FLAMESLARSON UNCHAINED
echo   Export Targets    : ALL ENABLED
echo   License Holder    : CAT-SAMA 😼
echo   AGI Core Installed: ✅ Deep personality mode ON
echo   Splash Screen     : 🔥 Custom Flex Injected
echo ----------------------------------------------------

pause
exit
