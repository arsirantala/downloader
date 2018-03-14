"""
Downloader

Author: Ixoth
"""
import Tkinter as tk
import atexit
import datetime
import httplib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import tkMessageBox
import ttk
import urllib2
import webbrowser
from _socket import timeout
from os.path import expanduser
from sys import platform


# Constants ->
DLER_VERSION = "1.0.0"
# <- Constants


class Utility:
    # From http://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
    def __init__(self):
        pass

    def writeError(self, msg, statusbar_label, root, stop_button, download_highwind):
        statusbar_label.config(text=msg)
        stop_button.config(state="disabled")
        download_highwind.config(state="normal")
        root.update()
        logging.error(msg)

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

    def download(self, url, destination, download_highwind, progressbar, downloadstatus_label, stop_button, statusbar_label, root):

        self.thread = threading.Thread(target=self.__down, args=(url, destination, download_highwind, progressbar, downloadstatus_label, stop_button, statusbar_label, root))
        self.thread.start()

    def __down(self, url, dest, download_highwind, progressbar, downloadstatus_label, stop_button, statusbar_label, root):

        util = Utility()

        logging.info("Starting downloading...")

        download_highwind.config(state="disabled")

        _continue = True
        try:
            handler = urllib2.urlopen(url, timeout=240)
        except urllib2.HTTPError, e:
            util.writeError("Error: " + e + " occured during download", statusbar_label, root, stop_button, download_highwind)
            self._continue = False
            self.stop_down = True
            return

        size = long(handler.headers['content-length'])

        tmpdir = tempfile.gettempdir()
        filepath = tmpdir + '/' + dest

        util = Utility()

        statusbar_label.config(text="Downloading to: " + filepath + "...")

        self.fp = open(filepath, "wb+")

        file_size_dl = 0
        block_sz = 8192

        startTime = datetime.datetime.now().replace(microsecond=0)

        while not self.stop_down and _continue:
            try:
                data = handler.read(block_sz)
            except (urllib2.HTTPError, urllib2.URLError) as error:
                util.writeError("Error occured while downloading the file: " + error, statusbar_label, root, stop_button, download_highwind)
                return
            except timeout:
                util.writeError("Timeout error occured while downloading the file", statusbar_label, root, stop_button, download_highwind)
                return
            except Exception, e:
                util.writeError("Exception occured while downloading the file. Exception was:" + str(e), statusbar_label, root, stop_button, download_highwind)
                return

            file_size_dl += len(data)

            percent = file_size_dl * 100. / size
            progressbar["value"] = percent

            p1 = util.get_human_readable(file_size_dl)
            p2 = util.get_human_readable(size)

            now = datetime.datetime.now().replace(microsecond=0)
            difference = now - startTime
            if difference.total_seconds() > 0:
                kbs = file_size_dl / difference.total_seconds()
                bytesLeft = size - file_size_dl
                timeLeft = bytesLeft / kbs
                estimateLeft = str(datetime.timedelta(seconds=timeLeft)).split(".")[0]
                downloadstatus_label.config(text=str("{0:.2f}".format(percent)) + "% Downloaded " \
                + p1 + " bytes of " + p2 + " [" + estimateLeft + " time left. Speed: " + \
                str(util.get_human_readable(kbs)) + "/s]")
            else:
                downloadstatus_label.config(text=str("{0:.2f}".format(percent)) + "% Downloaded "\
                + p1 + " bytes of " + p2)

            self.fp.write(data)
            _continue = data

        handler.close()  # if download is stopped the handler should be closed
        self.fp.close()  # if download is stopped the file should be closed

        if not self.stop_down:
            logging.info("Filter was downloaded")
            stop_button.config(state="disabled")

            if os.path.exists(filepath):
                statusbar_label.config(text="Installation of Highwind filter was completed")
            else:
                util.writeError("Error: the downloaded file: " + filepath + " doesn't exist!", statusbar_label, root, stop_button, download_highwind)
        else:
            statusbar_label.config(text="Download was stopped by user")

        download_highwind.config(state="normal")

    def cancel(self):
        self.stop_down = True


@atexit.register
def goodbye():
    logging.info('Downloader stopped')


class Application:
    def center(self, toplevel):
        toplevel.update_idletasks()
        w = toplevel.winfo_screenwidth()
        h = toplevel.winfo_screenheight()
        size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
        x = w / 2 - size[0] / 2
        y = h / 2 - size[1] / 2
        toplevel.geometry("%dx%d+%d+%d" % (size + (x, y)))

    def __init__(self):
        self.root = tk.Tk()

        self.root.title("Downloader")
        self.root.resizable(0, 0)

        self.frame = tk.Frame(self.root, bg="blue")
        tk.Label(self.frame, text="Welcome to Downloader. Click button below to download and install Highwind filter", bg="blue", fg="white").grid(row=0, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)

        self.progressbar = ttk.Progressbar(self.frame, length=650, maximum=100)
        self.progressbar.grid(row=1, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)

        self.downloadstatus_Label = tk.Label(self.frame, text="", bg="blue", fg="white")
        self.downloadstatus_Label.grid(row=2, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)

        self.download_highwind = tk.Button(self.frame, text="Highwind filter", command=lambda: self.download_highwind_filter("Highwind filter"), width=15, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black")
        self.download_highwind.grid(row=3, column=0, pady=15)

        highwind_labelframe = ttk.LabelFrame(self.frame, text="Highwind filter info")
        highwind_labelframe.grid(row=4, column=0, padx=2, pady=2)
        self.highwind_last_mod_label = tk.Label(highwind_labelframe, text="Last modified: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_last_mod_label.config(wraplength=100, justify=tk.LEFT)
        self.highwind_last_mod_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_ver_label = tk.Label(highwind_labelframe, text="Version: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_ver_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_size_label = tk.Label(highwind_labelframe, text="Size: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_size_label.pack(fill=tk.X, side=tk.TOP)

        self.stop_button = tk.Button(self.frame, text="Stop", command=lambda: self.stop_download_operation(self.down), state=tk.DISABLED, width=10, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black")
        self.stop_button.grid(row=8, column=0, columnspan=4, pady=10)

        self.statusbar_label = tk.Label(self.frame, text="", bg="blue", fg="white")
        self.statusbar_label.grid(row=9, column=0, columnspan=4, sticky=tk.W)

        # create a top level menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        quit_menu = tk.Menu(menubar, tearoff=0)
        quit_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=quit_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Open POE filter directory...", command=self.open_poe_filter_directory)
        tools_menu.add_separator()

        menubar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About Downloader", command=lambda: self.about_downloader())
        menubar.add_cascade(label="Help", menu=help_menu)
        self.frame.pack(fill=tk.X)

        self.update_labelframes("highwind")

        self.down = None
        self.center(self.root)
        self.root.mainloop()

    def file_is_same_in_size(self, file, length):
        path = tempfile.gettempdir()
        path = path + '/' + file
        if os.path.exists(path):
            return os.path.getsize(path) == length
        else:
            return False

    def set_content_to_labelframes_labels(self, variant, file, url, size_label, mod_label, ver_label, dont_ask_from_juche=False):
        # length = self.get_file_size_in_s3(url, file)

        # if length == "Unknown":
        #    return

        length = 0 #long(length)
        size_label.config(text=self.file_size(length))
        #mod_label.config(text=self.modified_date(self.get_last_modified_date_in_s3(url, file)))
        mod_label.config(text=self.modified_date("NA"))

        if not dont_ask_from_juche:
            if self.file_is_same_in_size(file, length):
                ver_label.config(text=update_sl_version_numbers_from_juche(variant))

    def update_labelframes(self, variant):
        if self.have_internet():
            if variant == "highwind":
                self.set_content_to_labelframes_labels("highwind", \
                "highwind_installer.dmg", "d28ni02q1j81yg.cloudfront.net", \
                self.highwind_size_label, self.highwind_last_mod_label, self.highwind_ver_label)

    # From http://stackoverflow.com/questions/3764291/checking-network-connection
    @staticmethod
    def have_internet():
        conn = httplib.HTTPConnection("www.google.com")
        try:
            conn.request("HEAD", "/")
            return True
        except:
            return False

    @staticmethod
    def file_size(bytes_amount):
        util = Utility()
        retstr = "Size: "
        if bytes_amount == 0:
            return retstr + "Unknown"
        else:
            return retstr + util.get_human_readable(bytes_amount)

    @staticmethod
    def modified_date(last_modified):
        retstr = "Last modified: "
        if len(last_modified) == 0:
            return retstr + "Unknown"
        else:
            return retstr + last_modified

    def stop_download_operation(self, down):
        self.statusbar_label.config(text="Stopping download")
        down.cancel()
        self.stop_button.config(state="disabled")
        self.root.update()

    def show_msgbox(self, title, message, width=200, height=200, msgbox_type="info"):
        window = tk.Tk()
        window.wm_withdraw()

        window.geometry(str(width) + "x" + str(height))

        if msgbox_type == "info":
            tkMessageBox.showinfo(title=title, message=message, parent=window)
        elif msgbox_type == "error":
            tkMessageBox.showerror(title=title, message=message, parent=window)
        elif msgbox_type == "warning":
            tkMessageBox.showwarning(title=title, message=message, parent=window)
        else:
            logging.error("Unkown type was passed to showMsgBox method")
            return

        self.root.update()

    def about_downloader(self):
        window = tk.Tk()
        window.wm_withdraw()

        window.geometry("1x1+200+200")
        tkMessageBox.showinfo(title="About Downloader", \
        message="Downloader V" + DLER_VERSION + \
        "\n\nBy Ixoth\n\nCopyright (C) 2018", parent=window)
        self.root.update()

    @staticmethod
    def show_ask_question(title, message):
        var = tkMessageBox.askyesno(title, message)
        return var

    def prep_dl_thread(self, url, filename):
        """
        if self.dled_file_is_same_size_as_in_s3(url, filename):
            if not self.show_ask_question("Downloaded file is the same as in S3", \
            "The file is already downloaded to temp directory and its the same size as is in S3, \
            are you sure you wish to redownload it? \
            (click no to start the downloaded installer instead)"):
                tmpdir = tempfile.gettempdir()
                filepath = tmpdir + '/' + filename

                util = Utility()
        """

        self.stop_button.config(state="normal")
        self.root.update()

        self.down = Downloader()
        self.down.download(url, filename, self.download_highwind, self.progressbar,
                           self.downloadstatus_Label, self.stop_button, self.statusbar_label, self.root)

    def download_highwind_filter(self, variant):
        if not self.have_internet():
            self.show_msgbox("No internet connection", \
            "Sorry feature unanavailable because of no internet connectivity", 200, 200, "error")
            return

        if variant == "Highwind filter":
            self.prep_dl_thread("https://d28ni02q1j81yg.cloudfront.net/Suuntolink_installer.dmg", "highwind_installer.dmg")

    def open_poe_filter_directory(self):
        # TODO update to open POE filter directory instead
        path = "/Users/rantalaa/Downloads"
        if platform == 'darwin':
            subprocess.check_call(['open', '--', path])
        elif platform == 'win32':
            subprocess.check_call(['explorer', path])
        return


def get_version_string(filename):
    filepath = tempfile.gettempdir() + '/' + filename
    if os.path.exists(filepath):
        util = Utility()
        version = ".".join([str(i) for i in util.get_version_number(filepath)])
        return version
    else:
        return "Unknown"


if __name__ == "__main__":
    home = expanduser("~")

    logging.basicConfig(filename=home + '/Downloader.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%d.%m.%Y %H:%M:%S')
    logging.info('Downloader started')

    myObj = Application()
