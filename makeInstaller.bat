@echo off

if exist "%ProgramFiles%\InstallMate 7\BinX64\Tin.exe" (
    "%ProgramFiles%\InstallMate 7\BinX64\Tin.exe" "%cd%\installer\Highwind POE filters downloader.im7" /build
) else (
    echo "Tin.exe could not be found"
    goto end
)

Tools\fnr.exe --cl --dir "%cd%\installer" --fileMask "Downloader_Setup.txt" --find "Downloader_Setup.exe" --replace "InstallerPath=https://github.com/arsirantala/downloader/blob/master/installer/Downloader_Setup.exe"

:end