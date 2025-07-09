@echo off
:: # TEAM FLAMES CO 1.0 HQRIPPER CATRNN [C] 20XX
:: SCRIPT: BLOCK-FL-ACCESS.BAT
:: PURPOSE: Blocks FL Studio from accessing the internet using Windows Firewall.
:: NOTE: This script will automatically request Administrator privileges.

::--------------------------------------------------------------------------------
:: This script creates outbound firewall rules to block the main FL Studio
:: executables. This will prevent the application from "phoning home" or
:: connecting to any online services.
::--------------------------------------------------------------------------------

::--------------------------------------------------------------------------------
:: Auto-elevate to Administrator
::--------------------------------------------------------------------------------
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges to manage firewall rules...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: --- Main Script Body ---

echo.
echo =================================================================
echo           FL Studio Internet Access Blocker
echo =================================================================
echo.
echo This script will add rules to the Windows Firewall to block
echo FL Studio's internet access.
echo.
echo Administrator privileges granted.
echo.
pause
echo.

:: --- Define Paths to FL Studio Executables ---
:: The script will add rules for both 32-bit and 64-bit versions.
:: It checks the most common installation directories.
SET "FL_PATH_64=%ProgramFiles%\Image-Line\FL Studio 21\FL64.exe"
SET "FL_PATH_32=%ProgramFiles(x86)%\Image-Line\FL Studio 21\FL.exe"
SET "FL_PATH_ALT_64=%ProgramFiles%\Image-Line\FL Studio 20\FL64.exe"
SET "FL_PATH_ALT_32=%ProgramFiles(x86)%\Image-Line\FL Studio 20\FL.exe"


echo Adding firewall rules...
echo.

:: --- Create Firewall Rules ---

:: Rule for 64-bit FL Studio
if exist "%FL_PATH_64%" (
    echo Blocking: %FL_PATH_64%
    netsh advfirewall firewall add rule name="Block FL Studio (64-bit)" dir=out action=block program="%FL_PATH_64%" enable=yes >nul
    if %errorlevel%==0 (
      echo   SUCCESS: Rule 'Block FL Studio (64-bit)' added.
    ) else (
      echo   ERROR: Failed to add rule for 64-bit FL Studio.
    )
) else (
    echo   INFO: 64-bit FL Studio (v21) not found at default path. Skipping.
)

:: Rule for 32-bit FL Studio
if exist "%FL_PATH_32%" (
    echo Blocking: %FL_PATH_32%
    netsh advfirewall firewall add rule name="Block FL Studio (32-bit)" dir=out action=block program="%FL_PATH_32%" enable=yes >nul
    if %errorlevel%==0 (
      echo   SUCCESS: Rule 'Block FL Studio (32-bit)' added.
    ) else (
      echo   ERROR: Failed to add rule for 32-bit FL Studio.
    )
) else (
    echo   INFO: 32-bit FL Studio (v21) not found at default path. Skipping.
)

:: Rule for alternate 64-bit FL Studio (v20)
if exist "%FL_PATH_ALT_64%" (
    echo Blocking: %FL_PATH_ALT_64%
    netsh advfirewall firewall add rule name="Block FL Studio 20 (64-bit)" dir=out action=block program="%FL_PATH_ALT_64%" enable=yes >nul
    if %errorlevel%==0 (
      echo   SUCCESS: Rule 'Block FL Studio 20 (64-bit)' added.
    ) else (
      echo   ERROR: Failed to add rule for 64-bit FL Studio 20.
    )
) else (
    echo   INFO: 64-bit FL Studio (v20) not found at default path. Skipping.
)

:: Rule for alternate 32-bit FL Studio (v20)
if exist "%FL_PATH_ALT_32%" (
    echo Blocking: %FL_PATH_ALT_32%
    netsh advfirewall firewall add rule name="Block FL Studio 20 (32-bit)" dir=out action=block program="%FL_PATH_ALT_32%" enable=yes >nul
     if %errorlevel%==0 (
      echo   SUCCESS: Rule 'Block FL Studio 20 (32-bit)' added.
    ) else (
      echo   ERROR: Failed to add rule for 32-bit FL Studio 20.
    )
) else (
    echo   INFO: 32-bit FL Studio (v20) not found at default path. Skipping.
)


echo.
echo =================================================================
echo                      PROCESS COMPLETE
echo =================================================================
echo.
echo Firewall rules to block FL Studio have been created.
echo If FL Studio was installed in a custom directory, you may
echo need to edit this script and update the paths.
echo.
pause
