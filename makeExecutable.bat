if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
pyinstaller --noupx --onefile -w --hidden-import=Tkinter --hidden-import=configparser --hidden-import=requests --hidden-import=pkgutil DLer.py --icon=Highwind.ico --version-file=version.txt -n Downloader
if not exist binaries mkdir binaries
copy dist\*.exe binaries
copy Highwind.ico binaries
copy Highwind.ico dist

