# General
This python script downloads from the internet Path of Exile Highwind filter files.

There is a script to make the script as executable, information how to make the script as executable is instructed below.

There is also a command line version of the downloader script available its called Downloader.py.

## Command line python script Downloader.py

In order to use the script one needs to give command line parameters, which are:

* old_file (optional parameter, which tells the script where is the already downloaded file located)
* new_file mandatory parameter which will tell the script where to save the downloaded file
* download_url the url in the internet where to download the file (if the address doesn't give the content-length in the headers, there will be no progress shown during the download. Pastebin is one of such servers which doesn't give this information out even in the raw address).

# How to make executable of the downloader?

In order to convert the **DLer3.py** to executable you first need to:

1. Download and Install python 3.4 (preferably) from https://www.python.org/downloads/release/python-344/
1. Download and Install cx_freeze from https://pypi.python.org/pypi/cx_Freeze/4.3.4
1. Fix tk paths in setup.py script
1. In the directory where you cloned this repository run in command prompt command: **python setup.py dist**

If everything worked out without problems the executable should be now in the dist directory.

# Troubleshooting Downloader.exe errors

In case you keep getting an error: "Failed to execute script DLer", run the DLer.py script (in the directory where you cloned this repository) by using the command: **python.exe DLer.py**

**(Again make sure the scripts directory in virtual environment is in system path that the python.exe can be found)**

And see what python reports as an error (most likely the requests module is not installed).

# Questions and answers

**Q**: Wasn't there already updaters for the filters such as FilterNova?

**A**: I actually learned about that yesterday. I didn't know such existed. I have made these scripts to learn python coding, and my scripts are very basic ones, and the UI version is meant to only update Highwind filter (at the time of writing this, I have no plans to extend the support for other filters).

**Q**: The <antivirus program's name> quarantined the Downloader, why?

**A**: The binary version of the downloader is not codesigned. As the downloader downloads file from the internet the Antivirus sees this as a possible malware program. You can make the executable version of the downloader by running the makeExecutable.bat batch file - you need python2.7 (make sure you have python.exe in system path) and pyinstaller installed (install pyinstaller with pip). There is also modules which the script uses, which are required to be installed (with pip again) in order to be able to make the executable version of the downloader (modules such as logging, requests, etc).

**Q**: I cannot get the makeExecutable.bat work, the binary is generated in dist but when I start it, I get an error

**A**: Make sure that all the required modules are installed. See with pip which modules are installed, and install all the modules what the script uses (see the import section in the script). The executable might also suddenly get closed without any apparent reason - this might be due Antivirus blocking the executable thinking it as a malware (seen it happen in my own computer). Only fix for such is to have the directory/executable be exluded in the Antivirus program.

**Q**: I'm confused what is DL2.py script?
**A**: Its Python 2.7 version of the GUI based downloader, which is bound to be removed later. Only the Python 3 version of the script (DLer3.py) will remain (along with command line version (for ppl who don't like GUI based programs and rather use command line programs)).

**Q**: When I close the Downloader from title bar's X button the Downloader is still running the task manager
**A**: This is a bug in the downloader, it'll be fixed shortly. Just for the time being use File->Exit instead.
