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
**A**: The binary version of the downloader is not codesigned. As the downloader downloads file from the internet the Antivirus sees this a possible malware program.
