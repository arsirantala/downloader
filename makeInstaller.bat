@echo off

if exist "%ProgramFiles%\InstallMate 9\BinX64\Tin.exe" (
    "%ProgramFiles%\InstallMate 9\BinX64\Tin.exe" "%cd%\installer\Highwind POE filters downloader.im9" /build
) else (
    echo "Tin.exe could not be found"
    goto end
)

Tools\fnr.exe --cl --dir "%cd%\installer" --fileMask "Downloader_Setup.txt" --find "InstallerPath=Downloader_Setup.exe" --replace "InstallerPath=https://github.com/arsirantala/downloader/raw/master/installer/Downloader_Setup.exe"

:end
