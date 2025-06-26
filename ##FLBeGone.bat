@echo off
:: Block common FL Studio 21 activation and telemetry domains
:: Run this script as administrator!

setlocal

REM --- List of known FL Studio/Imageline domains to block ---
set DOMAINS= 
set DOMAINS=%DOMAINS% www.image-line.com
set DOMAINS=%DOMAINS% support.image-line.com
set DOMAINS=%DOMAINS% license.image-line.com
set DOMAINS=%DOMAINS% auth.image-line.com
set DOMAINS=%DOMAINS% accounts.image-line.com

REM --- Backup hosts file first ---
copy %SystemRoot%\System32\drivers\etc\hosts %SystemRoot%\System32\drivers\etc\hosts.bak

REM --- Loop through and block each domain ---
for %%D in (%DOMAINS%) do (
    echo 127.0.0.1 %%D>> %SystemRoot%\System32\drivers\etc\hosts
)

echo All done! The following domains are now blocked:
for %%D in (%DOMAINS%) do (
    echo     %%D
)

pause
