if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
pyinstaller --noupx --onefile --hidden-import Tkinter -w DLer.py --version-file=version.txt
