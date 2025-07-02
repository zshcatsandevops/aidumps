@echo off
echo == STOP AND DISABLE WINDOWS UPDATE SERVICES ==
net stop wuauserv
sc config wuauserv start= disabled

net stop UsoSvc
sc config UsoSvc start= disabled

net stop DoSvc
sc config DoSvc start= disabled

REM === DELETE WINDOWS UPDATE FOLDERS ===
echo == TAKING OWNERSHIP AND DELETING UPDATE FOLDERS ==
takeown /f "%windir%\SoftwareDistribution" /r /d y
icacls "%windir%\SoftwareDistribution" /grant %username%:F /t
rd /s /q "%windir%\SoftwareDistribution"

takeown /f "%windir%\System32\catroot2" /r /d y
icacls "%windir%\System32\catroot2" /grant %username%:F /t
rd /s /q "%windir%\System32\catroot2"

REM === (OPTIONAL) DELETE CORE DLL (DANGEROUS) ===
:: takeown /f "%windir%\System32\wuaueng.dll"
:: icacls "%windir%\System32\wuaueng.dll" /grant %username%:F
:: del /f /q "%windir%\System32\wuaueng.dll"

REM === REMOVE SCHEDULED TASKS RELATED TO WINDOWS UPDATE ===
echo == DELETING WINDOWS UPDATE SCHEDULED TASKS ==
schtasks /delete /tn "\Microsoft\Windows\WindowsUpdate\*" /f
schtasks /delete /tn "\Microsoft\Windows\UpdateOrchestrator\*" /f

echo.
echo == WINDOWS UPDATE PURGED! ==
pause
