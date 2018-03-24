if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
pyinstaller --noupx --onefile Downloader.py --version-file=versionDownloader.txt -n DownloaderConsole
if not exist binaries mkdir binaries
copy dist\*.exe binaries
