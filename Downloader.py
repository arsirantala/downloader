#!/usr/bin/env python

import datetime
import hashlib
import logging
import os
import threading
import urllib2
from _socket import timeout
from shutil import copyfile
import argparse


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

    @staticmethod
    def calculate_sha1(filename):
        if not os.path.exists(filename):
            raise Exception("File cannot be found")

        hasher = hashlib.sha1()
        with open(filename, "rb") as afile:
            buf = afile.read()
            hasher.update(buf)
        return hasher.hexdigest()


class Downloader:
    def __init__(self):
        self.stop_down = False
        self.thread = None

    def download(self, url, old_file_path, new_file_base_name, old_file_sha1_value):

        self.thread = threading.Thread(target=self.__down, args=(url, old_file_path, new_file_base_name, old_file_sha1_value))
        self.thread.start()

    def __down(self, url, old_file_path, new_file_base_name, old_file_sha1_value):
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
            print "\n(Content-Length can't be found in the headers. Can't show download progress)"
        else:
            was_found = True
            size = long(handler.headers['content-length'])

        downloaded_file_name = new_file_base_name + ".new"

        util = Utility()

        print "\nDownloading to: %s..." % downloaded_file_name

        self.fp = open(downloaded_file_name, "wb+")

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

        if os.path.exists(downloaded_file_name) and os.path.exists(old_file_path):
            dled_file_sha1_value = util.calculate_sha1(downloaded_file_name)
            print "\nSha1 for the downloaded file: %s" % dled_file_sha1_value
            if old_file_sha1_value != dled_file_sha1_value:
                print "\nThe content of the files differ - replacing old file with downloaded file"
                copyfile(downloaded_file_name, old_file_path)
            else:
                print "\nFiles are identical - not replacing the old file with downloaded one"
        else:
            print "\nRenaming downloaded file %s with old filename: %s" % (downloaded_file_name, old_file_path)
            copyfile(downloaded_file_name, old_file_path)

        if os.path.exists(downloaded_file_name):
            # Remove downloaded file
            os.remove(downloaded_file_name)

        if not self.stop_down:
            logging.info("File was downloaded")
        else:
            logging.info("Download was stopped by user")

        print "\nAll done."
        raw_input("Press Enter to continue...")

    def cancel(self):
        self.stop_down = True


parser = argparse.ArgumentParser(
    description="Downloads file from given url. Compares sha1 value of downloaded file to sha1 value of old file and the values differ, the new file replaces the old file.")
parser.add_argument("-old_file", "--old_file", help="Location of existing old file", required=True,
                    dest="old_file", metavar="<Location for for old file>")
parser.add_argument("-new_file", "--new_file", help="Base name of the new file", required=True,
                    dest="new_file", metavar="<Basename for new file>")
parser.add_argument("-download_url", "--download_url", help="Download url", required=True,
                    dest="download_url", metavar="<Download url>")
args = parser.parse_args()

old_file_sha1_value = None

if os.path.exists(args.old_file):
    util = Utility()
    old_file_sha1_value = util.calculate_sha1(args.old_file)
    print "\nSha1 value for old file: %s" % str(old_file_sha1_value)

down = Downloader()
down.download(args.download_url, args.old_file, args.new_file, old_file_sha1_value)
