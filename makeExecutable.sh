rm -rf build &>/dev/null
rm -rf dist &>/dev/null
~/PycharmProjects/AnalyticTools/venv_2.7highsierra/bin/pyinstaller --onefile --hidden-import Tkinter -w DLer.py --version-file=version.txt
