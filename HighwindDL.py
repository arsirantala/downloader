import atexit
import datetime
import hashlib
import httplib
import logging
import os
import sys
import tempfile
import threading
import time
import urllib2
from _socket import timeout
from sys import platform
from shutil import copyfile


class Utility:
    # From http://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
    def __init__(self):
        pass

    @staticmethod
    def get_human_readable(size, precision=2):
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        suffix_index = 0
        while size > 1024 and suffix_index < 4:
            suffix_index += 1  # increment the index of the suffix
            size /= 1024.0  # apply the division
        return "%.*f%s" % (precision, size, suffixes[suffix_index])


class Downloader:
    def __init__(self):
        self.stop_down = False
        self.thread = None

    def download(self, url, dest, sha1):

        self.thread = threading.Thread(target=self.__down, args=(url, dest, sha1))
        self.thread.start()

    def __down(self, url, dest, sha1):
        util = Utility()
        logging.info("Starting downloading...")

        _continue = True
        try:
            handler = urllib2.urlopen(url, timeout=240)
        except urllib2.HTTPError, e:
            util.writeError("Error: %s occured during download" % str(e))
            self._continue = False
            self.stop_down = True
            return

        was_found = False
        if "Content-Length" not in handler.headers:
            print "Content-Length can't be found in the headers!"
            logging.error("Content-Length can't be found in the headers!")
        else:
            was_found = True
            size = long(handler.headers['content-length'])

        filepath = dest + ".new"

        util = Utility()

        print "Downloading to: " + filepath + "..."

        self.fp = open(filepath, "wb+")

        file_size_dl = 0
        block_sz = 8192

        startTime = datetime.datetime.now().replace(microsecond=0)

        while not self.stop_down and _continue:
            try:
                data = handler.read(block_sz)
            except (urllib2.HTTPError, urllib2.URLError) as error:
                util.writeError("Error occured while downloading the file: " + error)
                return
            except timeout:
                util.writeError("Timeout error occured while downloading the file")
                return
            except Exception, e:
                util.writeError("Exception occured while downloading the file. Exception was:" + str(e))
                return

            file_size_dl += len(data)

            if was_found:
                percent = file_size_dl * 100. / size

                p1 = util.get_human_readable(file_size_dl)
                p2 = util.get_human_readable(size)

                now = datetime.datetime.now().replace(microsecond=0)
                difference = now - startTime

                if difference.total_seconds() > 0:
                    kbs = file_size_dl / difference.total_seconds()
                    bytesLeft = size - file_size_dl
                    timeLeft = bytesLeft / kbs
                    estimateLeft = str(datetime.timedelta(seconds=timeLeft)).split(".")[0]
                    logging.info(str("{0:.2f}".format(percent)) + "% Downloaded " \
                    + p1 + " bytes of " + p2 + " [" + estimateLeft + " time left. Speed: " + \
                    str(util.get_human_readable(kbs)) + "/s]")
                else:
                    logging.info(str("{0:.2f}".format(percent)) + "% Downloaded " + p1 + " bytes of " + p2)

            self.fp.write(data)
            _continue = data

        handler.close()  # if download is stopped the handler should be closed
        self.fp.close()  # if download is stopped the file should be closed

        if os.path.exists(filepath) and os.path.exists(dest):
            sha1_new = hashlib.sha1(filepath).hexdigest()
            if sha1 != sha1_new:
                print "The sha1 values differ, the downloaded file is different than the other"
                copyfile(filepath, dest)
            else:
                print "Sha1 values are the same - files are the same"
        else:
            copyfile(filepath, dest)

        if os.path.exists(filepath):
            # Remove downloaded file
            os.remove(filepath)

        if not self.stop_down:
            logging.info("File was downloaded")
        else:
            logging.info("Download was stopped by user")

    def cancel(self):
        self.stop_down = True


dest = "highwind.filter"
tmpdir = os.path.dirname(os.path.realpath(sys.argv[0]))
filepath = tmpdir + '/' + dest
sha1_value = None

if os.path.exists(filepath):
    # calculate sha1
    sha1_value = hashlib.sha1(filepath).hexdigest()
    print sha1_value

down = Downloader()
down.download("https://pastebin.com/raw/k5q2b570", filepath, sha1_value)
