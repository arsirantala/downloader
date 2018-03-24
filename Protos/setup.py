import os
from cx_Freeze import setup, Executable

os.environ['TCL_LIBRARY'] = 'c:/python36/tcl/tcl8.6'
os.environ['TK_LIBRARY'] = 'c:/python36/tcl/tk8.6'


# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(
    packages = [],
    excludes = [],
    include_files=['c:/python36/DLLs/tcl86t.dll', 'c:/python36/DLLs/tk86t.dll']
)

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('DLer3.py', base=base)
]

setup(name = "Downloader" ,
      version = "1.0.7" ,
      description = "Highwind Path of Exile filter downloader" ,
      options = dict(build_exe = buildOptions),
      executables = executables)
