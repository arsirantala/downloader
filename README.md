# General
This repository contains two python scripts (essentially they do the same, but the other one is console app while the other is with UI). The python scripts are: Downloader.py and DLer.py (latter is with UI, former is console app).

Purpose of the scripts are to download specified file from the internet. The scripts support checking the old file (previously downloaded) sha1 value and compare that to the downloaded one's sha1 value. If they are different, script will replace the old file with the downloaded one.

The script with UI (for time being) only supports downloading Path of Exile's Highwind filter file (support for mapping version will be added later) - but its customizable, support for other filters can be added quite easily.

The script which runs only in console mode, does take parameters in order to work. Parameters are:

* old_file (optional parameter, which tells the script where is the already downloaded file located)
* new_file mandatory parameter which will tell the script where to save the downloaded file
* download_url the url in the internet where to download the file (if the address doesn't give the content-length in the headers, there will be no progress shown during the download. Pastebin is one of such servers which doesn't give this information out even in the raw address).

# Plans for the future with the scripts

I am focusing in the near future to further develop the UI version of the script (DLer.py) - the console version of the script (Downloader.py) is now mature enough, so won't be doing much to that script anymore (how the script works with servers which give the content-length in headers needs to be checked, and adjustments how the progress is shown in the console probably will need to be modified - essentially the code is the same what comes to the showing the progress as in the UI version).

# Questions and answers

**Q**: Wasn't there already updaters for the filters such as FilterNova?

**A**: I actually learned about that yesterday. I didn't know such existed. I have made these scripts to learn python coding, and my scripts are very basic ones, and the UI version is meant to only update Highwind filter (at the time of writing this, I have no plans to extend the support for other filters).

**Q**: The <antivirus program's name> quarantined the Downloader, why?

**A**: The binary version of the downloader is not codesigned. As the downloader downloads file from the internet the Antivirus sees this as a possible malware program. You can make the executable version of the downloader by running the makeExecutable.bat batch file - you need python2.7 (make sure you have python.exe in system path) and pyinstaller installed (install pyinstaller with pip). There is also modules which the script uses, which are required to be installed (with pip again) in order to be able to make the executable version of the downloader (modules such as logging, requests, etc).

**Q**: I cannot get the makeExecutable.bat work, the binary is generated in dist but when I start it, I get an error

**A**: Make sure that all the required modules are installed. See with pip which modules are installed, and install all the modules what the script uses (see the import section in the script). The executable might also suddenly get closed without any apparent reason - this might be due Antivirus blocking the executable thinking it as a malware (seen it happen in my own computer). Only fix for such is to have the directory/executable be exluded in the Antivirus program.

# Comprehensive guide for makeExecutable.bat

Here is good guide how to first install python and virtual environment for it: http://pymote.readthedocs.io/en/latest/install/windows_virtualenv.html

Essentially once you've installed python, start command prompt and enter command: **pip install virtualenv**

After that goto Documents directory and enter following command to install python to virtual environment: **virtualenv pymote_env**

Now install pyinstaller to the virtual environment by entering command in pymote directory: **Scripts\pip.exe install pyinstaller**

Install requests module: **Scripts\pip.exe install requests**

**Now make sure the scripts directory in virtual environment is in system path that the pyinstaller can be found by the makeExecutable.bat file.**

Run the makeExecutable.bat file, and once its completed the Downloader.exe is found in dist directory.

If you now start the Downloader.exe in dist directory, AntiVirus software most likely will block it - you need to exlude the dist directory in the AntiVirus settings!

# Troubleshooting Downloader.exe errors

In case you keep getting an error: "Failed to execute script DLer", run the DLer.py script (in the directory where you cloned this repository) by using the command: **python.exe DLer.py**

**(Again make sure the scripts directory in virtual environment is in system path that the pyinstaller can be found by the makeExecutable.bat file)**

And see what python reports as an error (most likely the requests module is not installed).
