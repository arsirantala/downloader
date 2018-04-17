@echo off

if exist "%ProgramFiles%\InstallMate 7\BinX64\Tin.exe" (
    "%ProgramFiles%\InstallMate 7\BinX64\Tin.exe" "%cd%\installer\Highwind POE filters downloader.im7" /build
) else (
    echo "Tin.exe could not be found"
    goto end
)

Tools\fnr.exe --cl --dir "%cd%\installer\Highwind POE filters downloader\InstallMate" --fileMask "Highwind POE filters downloader-Setup.txt" --find "InstallerPath=Highwind POE filters downloader-Setup.exe" --replace "InstallerPath=https://github.com/arsirantala/downloader/blob/master/installer/Highwind%20POE%20filters%20downloader/InstallMate/Highwind%20POE%20filters%20downloader-Setup.exe"

:end