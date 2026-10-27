@echo off
setlocal
set "forum_arch=amd64"
if /I "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "forum_arch=arm64"
if /I "%PROCESSOR_ARCHITEW6432%"=="ARM64" set "forum_arch=arm64"
if /I "%PROCESSOR_ARCHITECTURE%"=="x86" if "%PROCESSOR_ARCHITEW6432%"=="" (
  echo Este instalador necessita de Windows de 64 bits. Consulta INSTALAR.md.
  pause
  exit /b 1
)
"%~dp0installer\bin\forum-windows-%forum_arch%.exe" --project "%~dp0." %*
exit /b %errorlevel%
