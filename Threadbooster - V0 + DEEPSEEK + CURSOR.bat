@echo off
:: Batch file to install Python 3.13 and game development tools

:: Define variables
set PYTHON_VERSION=3.13.5
set INSTALLER_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe    
set INSTALLER=python-installer.exe

echo Downloading Python %PYTHON_VERSION% installer...
powershell -Command "Invoke-WebRequest -Uri '%INSTALLER_URL%' -OutFile '%INSTALLER%'"

echo Installing Python %PYTHON_VERSION% silently...
start /wait %INSTALLER% /quiet Include_freethreaded=1 PrependPath=1 TargetDir=C:\Python313

if exist "%INSTALLER%" del "%INSTALLER%"

echo Installing game development libraries...
pip install pygame panda3d pyglet ursina arcade kivy pymunk

echo Setup complete!
pause