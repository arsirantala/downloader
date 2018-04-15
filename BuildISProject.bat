@echo off

PATH=%PATH%;"%programfiles(x86)%\InstallShield\2015 SAB\System"

if exist "Downloader" rd /S /Q "Downloader"

IF [%1] EQU [] Iscmdbld.exe -p "Downloader.ism" -a "PROJECT_ASSISTANT" -r "SINGLE_EXE_IMAGE"
IF [%1] NEQ [] Iscmdbld.exe -p "Downloader.ism" -a "PROJECT_ASSISTANT" -r "SINGLE_EXE_IMAGE" -y "%~1"

If ERRORLEVEL 1 goto errorHandler

Echo success
goto end

:errorHandler
Echo failure

:end
