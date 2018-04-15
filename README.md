# General
This python script downloads from the internet Path of Exile Highwind filter files.

There is a script to make the script as executable, information how to make the script as executable is instructed below.

# How to make executable of the downloader?

In order to convert the **DLer3.py** to executable you first need to:

1. Download and Install python 3.4 (preferably) from https://www.python.org/downloads/release/python-344/
1. Download and Install cx_freeze from https://pypi.python.org/pypi/cx_Freeze/4.3.4
1. Fix tk paths in setup.py script
1. In the directory where you cloned this repository run in command prompt command: **python setup.py dist**

If everything worked out without problems the executable should be now in the dist directory.

In order to convert the **DLer.py** to executable, run makeExecutable.bat in commmand prompt.

You need to have pyinstaller in the system path. You also need to have required modules installed with pip in the python 2.7 installation path.

# Troubleshooting Downloader.exe errors

In case you keep getting an error: "Failed to execute script DLer", run the DLer.py script (in the directory where you cloned this repository) by using the command: **python.exe DLer.py**

**(Again make sure the scripts directory in virtual environment is in system path that the python.exe can be found)**

And see what python reports as an error (most likely the requests module is not installed).

# Questions and answers

**Q**: The <antivirus program's name> quarantined the Downloader, why?

**A**: The binary version of the downloader is not codesigned. As the downloader downloads file from the internet the Antivirus sees this as a possible malware program. You can make the executable version of the downloader by running the makeExecutable.bat batch file - you need python2.7 (make sure you have python.exe in system path) and pyinstaller installed (install pyinstaller with pip). There is also modules which the script uses, which are required to be installed (with pip again) in order to be able to make the executable version of the downloader (modules such as logging, requests, etc).

**Q**: I cannot get the makeExecutable.bat work, the binary is generated in dist but when I start it, I get an error

**A**: Make sure that all the required modules are installed. See with pip which modules are installed, and install all the modules what the script uses (see the import section in the script). The executable might also suddenly get closed without any apparent reason - this might be due Antivirus blocking the executable thinking it as a malware (seen it happen in my own computer). Only fix for such is to have the directory/executable be exluded in the Antivirus program.

**Q**: What is DL2.py script?

**A**: Its Python 2.7 version of the GUI based downloader, which is bound to be removed later. Only the Python 3 version of the script (DLer3.py) will remain (along with command line version (for ppl who don't like GUI based programs and rather use command line programs)).

**Q**: What is makeExecutable.bat file?

**A**: Old way to convert the DL2.py to executable by using pyinstaller. During the transition to use cx_freeze instead of the pyinstaller I've left the said batch file still to the repository - but its bound to removed.
