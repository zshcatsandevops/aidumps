@echo off
setlocal enabledelayedexpansion

:: ============================================================================
:: Meshnet Airlock Protocol v1.0
:: Routes all traffic through a Meshnet peer and blocks all other internet access.
:: ============================================================================

:: --- Configuration ---
:: Set the name of the firewall rule to be created.
set FIREWALL_RULE_NAME="Meshnet Airlock - Block All Except NordLynx"

:: Set the path to your NordVPN installation.
set NORDVPN_PATH="C:\Program Files\NordVPN\"

:: --- Script Body ---
cd /d %NORDVPN_PATH%

:MENU
echo.
echo -------------------------------------------------
echo  Meshnet Airlock Control
echo -------------------------------------------------
echo 1. Engage Airlock Protocol (Route via Meshnet & Lock Down)
echo 2. Disengage Airlock Protocol (Restore Internet Access)
echo 3. View Meshnet Peers
echo 4. Exit
echo.

set /p "CHOICE=Enter your choice: "

if "%CHOICE%"=="1" goto ENGAGE_AIRLOCK
if "%CHOICE%"=="2" goto DISENGAGE_AIRLOCK
if "%CHOICE%"=="3" goto VIEW_PEERS
if "%CHOICE%"=="4" goto :EOF

goto MENU

:ENGAGE_AIRLOCK
echo.
echo [INFO] Engaging Airlock Protocol...

:: Step 1: Enable Meshnet if it's not already on.
echo [ACTION] Ensuring Meshnet is enabled...
nordvpn set meshnet on
timeout /t 2 /nobreak >nul

:: Step 2: Get the target peer from the user.
echo.
echo [INFO] Available Meshnet Peers:
nordvpn meshnet peer list
echo.
set /p "TARGET_PEER=Enter the full NordName of the device to route traffic through: "
if not defined TARGET_PEER (
    echo [ERROR] No target peer specified. Aborting.
    pause
    goto MENU
)

:: Step 3: Connect to the Meshnet peer for traffic routing.
echo [ACTION] Attempting to route all traffic through %TARGET_PEER%...
nordvpn meshnet peer connect "%TARGET_PEER%"
echo.

:: Step 4: Create and enable the firewall rule.
echo [ACTION] Creating and enabling firewall rule: %FIREWALL_RULE_NAME%
echo [INFO] This will block all outbound traffic except on the NordLynx interface.

:: Delete any pre-existing rule with the same name to ensure a clean slate.
netsh advfirewall firewall delete rule name=%FIREWALL_RULE_NAME% >nul 2>&1

:: Create the rule. This is the core of the lockdown.
:: We block all outbound traffic on all profiles for any program,
:: but specify the interface alias 'nordlynx' as an exception.
netsh advfirewall firewall add rule name=%FIREWALL_RULE_NAME% dir=out action=block enable=yes profile=any interfacetype=any
netsh advfirewall firewall set rule name=%FIREWALL_RULE_NAME% new remoteip=any localip=any protocol=any action=block enable=yes dir=out profile=any interfacetype=!nordlynx

echo.
echo [SUCCESS] Airlock Protocol Engaged.
echo [STATUS] All traffic is being routed through %TARGET_PEER%.
echo [STATUS] All non-Meshnet internet connections are now blocked by the firewall.
echo [IMPORTANT] To restore normal internet, run this script and choose option 2.
pause
goto MENU

:DISENGAGE_AIRLOCK
echo.
echo [INFO] Disengaging Airlock Protocol...

:: Step 1: Disconnect from the Meshnet peer.
echo [ACTION] Disconnecting from Meshnet traffic routing...
nordvpn disconnect
timeout /t 3 /nobreak >nul

:: Step 2: Delete the firewall rule to restore internet access.
echo [ACTION] Deleting firewall rule: %FIREWALL_RULE_NAME%...
netsh advfirewall firewall delete rule name=%FIREWALL_RULE_NAME%

echo.
echo [SUCCESS] Airlock Protocol Disengaged.
echo [STATUS] Normal internet connectivity has been restored.
pause
goto MENU

:VIEW_PEERS
echo.
echo [INFO] Listing available Meshnet Peers...
nordvpn meshnet peer list
echo.
pause
goto MENU