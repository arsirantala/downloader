#!/usr/bin/env python
"""
date: 16.3.2018
username: Ixoth
description: Highwind POE filter Downloader
"""

import tkinter as tk
import atexit
import ctypes.wintypes
import datetime
import hashlib
import http.client
import logging
import logging.handlers
import os
import subprocess
import sys
import tempfile
import threading
import time
import tkinter.messagebox
import tkinter.ttk
import urllib.request, urllib.error, urllib.parse
from _socket import timeout
from shutil import copyfile
from sys import platform
import threading

import requests

# Constants ->
DLER_VERSION = "1.0.6"
CSIDL_PERSONAL = 5       # My Documents
SHGFP_TYPE_CURRENT= 0   # Want current, not default value
#  <- Constants

# Globals

class Utility:
    # From http://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
    def __init__(self):
        pass

    def writeError(self, msg, statusbar_label, root, stop_button, download_highwind, download_highwind_mapper, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters):
        statusbar_label.config(text=msg)
        stop_button.config(state="disabled")
        download_highwind.config(state="normal")
        download_highwind_mapper.config(state="normal")
        download_highwind_strict.config(state="normal")
        download_highwind_very_strict.config(state="normal")
        check_updates.config(state="normal")
        update_all_filters.config(state="normal")
        root.update()
        my_logger.error(msg)

    @staticmethod
    def get_human_readable(size, precision=2):
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        suffix_index = 0
        while size > 1024 and suffix_index < 4:
            suffix_index += 1  # increment the index of the suffix
            size /= 1024.0  # apply the division
        return "%.*f%s" % (precision, size, suffixes[suffix_index])

    @staticmethod
    def get_file_size_in_url(base_url):
        return requests.get(base_url, stream=True).headers['Content-length']

    @staticmethod
    def get_last_modified_date_in_url(base_url):
        return requests.get(base_url, stream=True).headers['Date']

    @staticmethod
    def get_last_modified_date_in_file(filepath):
        return os.path.getmtime(filepath)

    @staticmethod
    def calculate_sha1(filename):
        if not os.path.exists(filename):
            raise Exception("File cannot be found")

        hasher = hashlib.sha1()
        with open(filename, "rb") as afile:
            buf = afile.read()
            hasher.update(buf)
        return hasher.hexdigest()

    @staticmethod
    def gmt_to_epoch(gmt):
        temp_time = time.strptime(gmt, "%a, %d %b %Y %H:%M:%S %Z")
        return time.mktime(temp_time)

class Downloader:
    def __init__(self):
        self.stop_down = False
        self.thread = None

    def download(self, url, destination, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters, progressbar, downloadstatus_label, stop_button, statusbar_label, root):

        self.thread = threading.Thread(target=self.__down, args=(url, destination, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters, progressbar, downloadstatus_label, stop_button, statusbar_label, root))
        self.thread.start()

    def __down(self, url, dest, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters, progressbar, downloadstatus_label, stop_button, statusbar_label, root):

        util = Utility()

        my_logger.info("Starting downloading...")

        download_highwind.config(state="disabled")
        download_highwind_mapping.config(state="disabled")
        download_highwind_strict.config(state="disabled")
        download_highwind_very_strict.config(state="disabled")
        check_updates.config(state="disabled")
        update_all_filters.config(state="disabled")

        _continue = True
        try:
            handler = urllib.request.urlopen(url, timeout=240)
        except urllib.error.HTTPError as e:
            util.writeError("Error: " + e + " occurred during download", statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict)
            self._continue = False
            self.stop_down = True
            return

        no_content_length = False
        if "content-length" in handler.headers:
            size = int(handler.headers['content-length'])
        else:
            no_content_length = True
            my_logger.info("content-length was not found from headers! Can't show download progress")

        temp_dir = tempfile.gettempdir()
        file_path = temp_dir + '/' + dest

        util = Utility()

        statusbar_label.config(text="Downloading to: " + file_path + "...")

        try:
            self.fp = open(file_path, "wb+")
        except:
            util.writeError("Was not able to open temporary file for writing the filter file at " + file_path, statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict)
            self._continue = False
            self.stop_down = True
            return

        file_size_dl = 0
        block_sz = 8192

        start_time = datetime.datetime.now().replace(microsecond=0)

        while not self.stop_down and _continue:
            try:
                data = handler.read(block_sz)
            except (urllib.error.HTTPError, urllib.error.URLError) as error:
                util.writeError("Error occured while downloading the file: " + error, statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict)
                self._continue = False
                self.stop_down = True
                return
            except timeout:
                util.writeError("Timeout error occurred while downloading the file", statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict)
                self._continue = False
                self.stop_down = True
                return
            except Exception as e:
                util.writeError("Exception occurred while downloading the file. Exception was:" + str(e), statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict)
                self._continue = False
                self.stop_down = True
                return

            file_size_dl += len(data)

            if not no_content_length:
                percent = file_size_dl * 100. / size
            else:
                percent = 100

            progressbar["value"] = percent

            p1 = util.get_human_readable(file_size_dl)
            if not no_content_length:
                p2 = util.get_human_readable(size)
            else:
                p2 = "Unknown"

            now = datetime.datetime.now().replace(microsecond=0)
            difference = now - start_time
            if difference.total_seconds() > 0:
                kbs = file_size_dl / difference.total_seconds()
                if no_content_length == False:
                    bytesLeft = size - file_size_dl
                    timeLeft = bytesLeft / kbs
                    estimateLeft = str(datetime.timedelta(seconds=timeLeft)).split(".")[0]
                    downloadstatus_label.config(text=str("{0:.2f}".format(percent)) + "% Downloaded " \
                                                     + p1 + " bytes of " + p2 + " [" + estimateLeft + " time left. Speed: " + \
                                                     str(util.get_human_readable(kbs)) + "/s]")
                else:
                    downloadstatus_label.config(text=str("{0:.2f}".format(percent)) + "% Downloaded " \
                                                     + p1 + " bytes of Unknown [??? time left. Speed: " + \
                                                     str(util.get_human_readable(kbs)) + "/s]")

            else:
                if not no_content_length:
                    downloadstatus_label.config(text=str("{0:.2f}".format(percent)) + "% Downloaded " + p1 + " bytes of " + p2)
                else:
                    downloadstatus_label.config(text=str("{0:.2f}".format(percent)) + "% Downloaded " + p1 + " bytes of Unknown")

            self.fp.write(data)
            _continue = data

        handler.close()  # if download is stopped the handler should be closed
        self.fp.close()  # if download is stopped the file should be closed

        if not self.stop_down:
            my_logger.info(file_path + " was downloaded")
            stop_button.config(state="disabled")

            if os.path.exists(file_path):
                dled_file_sha1_value = util.calculate_sha1(file_path)
                buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf)
                path = buf.value + "\My Games\Path of Exile"
                if os.path.exists(path):
                    installed_file_path = path + "\\" + dest
                    installed_file_sha1_value = None
                    if os.path.exists(installed_file_path):
                        installed_file_sha1_value = util.calculate_sha1(installed_file_path)

                    if dled_file_sha1_value != installed_file_sha1_value:
                        try:
                            copyfile(file_path, installed_file_path.encode("utf-8"))
                        except Exception as e:
                            statusbar_label.config(text="An exception occurred while attempting to copy file: {}".format(
                                e))

                        statusbar_label.config(text="Installation of " + dest + " filter was completed")
                    else:
                        statusbar_label.config(text="The filter is the same as the older one")
            else:
                util.writeError("Error: the downloaded file: " + file_path + " doesn't exist!", statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict)
        else:
            statusbar_label.config(text="Download was stopped by user")

        download_highwind.config(state="normal")
        download_highwind_mapping.config(state="normal")
        download_highwind_strict.config(state="normal")
        download_highwind_very_strict.config(state="normal")
        check_updates.config(state="normal")
        update_all_filters.config(state="normal")

    def cancel(self):
        self.stop_down = True


@atexit.register
def goodbye():
    my_logger.info('Downloader stopped')


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

        self.root.title("Path of Exile Highwind filter Downloader")
        self.root.resizable(0, 0)

        self.frame = tk.Frame(self.root, bg="blue")
        tk.Label(self.frame, text="Welcome to Downloader. Click button below to download and install Highwind filter", bg="blue", fg="white").grid(row=0, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)

        self.progressbar = tkinter.ttk.Progressbar(self.frame, length=650, maximum=100)
        self.progressbar.grid(row=1, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)

        self.downloadstatus_Label = tk.Label(self.frame, text="", bg="blue", fg="white")
        self.downloadstatus_Label.grid(row=2, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)

        self.download_highwind = tk.Button(self.frame, text="Highwind filter", command=lambda: self.download_highwind_filter("Highwind filter"), state=tk.DISABLED, width=15, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black")
        self.download_highwind.grid(row=3, column=0, pady=15)
        self.download_highwind_mapping = tk.Button(self.frame, text="Highwind mapping filter", command=lambda: self.download_highwind_filter("Highwind mapping filter"), state=tk.DISABLED, width=20, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black")
        self.download_highwind_mapping.grid(row=3, column=1, pady=15)
        self.download_highwind_strict = tk.Button(self.frame, text="Highwind strict filter", command=lambda: self.download_highwind_filter("Highwind strict filter"), state=tk.DISABLED, width=17, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black")
        self.download_highwind_strict.grid(row=3, column=2, pady=15)
        self.download_highwind_very_strict = tk.Button(self.frame, text="Highwind very strict filter", command=lambda: self.download_highwind_filter("Highwind very strict filter"), state=tk.DISABLED, width=20, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black")
        self.download_highwind_very_strict.grid(row=3, column=3, pady=15)

        highwind_labelframe = tkinter.ttk.LabelFrame(self.frame, text="Filter info")
        highwind_labelframe.grid(row=4, column=0, padx=4, pady=15, sticky=tk.N+tk.E+tk.W)
        self.highwind_last_mod_label = tk.Label(highwind_labelframe, text="Last modified: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_last_mod_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_last_mod_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_size_label = tk.Label(highwind_labelframe, text="Size: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_size_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_size_label.pack(fill=tk.X, side=tk.TOP)
        highwind_labelframe.grid_propagate(False)
        highwind_mapping_labelframe = tkinter.ttk.LabelFrame(self.frame, text="Filter info")
        highwind_mapping_labelframe.grid(row=4, column=1, padx=4, pady=15, sticky=tk.N+tk.E+tk.W)
        self.highwind_mapping_last_mod_label = tk.Label(highwind_mapping_labelframe, text="Last modified: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_mapping_last_mod_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_mapping_last_mod_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_mapping_size_label = tk.Label(highwind_mapping_labelframe, text="Size: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_mapping_size_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_mapping_size_label.pack(fill=tk.X, side=tk.TOP)
        highwind_mapping_labelframe.grid_propagate(False)
        highwind_strict_labelframe = tkinter.ttk.LabelFrame(self.frame, text="Filter info")
        highwind_strict_labelframe.grid(row=4, column=2, padx=4, pady=15, sticky=tk.N+tk.E+tk.W)
        self.highwind_strict_last_mod_label = tk.Label(highwind_strict_labelframe, text="Last modified: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_strict_last_mod_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_strict_last_mod_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_strict_size_label = tk.Label(highwind_strict_labelframe, text="Size: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_strict_size_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_strict_size_label.pack(fill=tk.X, side=tk.TOP)
        highwind_strict_labelframe.grid_propagate(False)
        highwind_very_strict_labelframe = tkinter.ttk.LabelFrame(self.frame, text="Filter info")
        highwind_very_strict_labelframe.grid(row=4, column=3, padx=4, pady=15, sticky=tk.N+tk.E+tk.W)
        self.highwind_very_strict_last_mod_label = tk.Label(highwind_very_strict_labelframe, text="Last modified: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_very_strict_last_mod_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_very_strict_last_mod_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_very_strict_size_label = tk.Label(highwind_very_strict_labelframe, text="Size: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_very_strict_size_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_very_strict_size_label.pack(fill=tk.X, side=tk.TOP)
        highwind_very_strict_labelframe.grid_propagate(False)

        self.highwind_last_modified_label = tk.Label(self.frame, text="Your Highwind filter: Not found", font="-weight bold", bg="blue", fg="white")
        self.highwind_last_modified_label.grid(row=5, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)
        self.highwind_mapping_last_modified_label = tk.Label(self.frame, text="Your Highwind mapping filter: Not found", font="-weight bold", bg="blue", fg="white")
        self.highwind_mapping_last_modified_label.grid(row=6, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)
        self.highwind_strict_last_modified_label = tk.Label(self.frame, text="Your Highwind strict filter: Not found", font="-weight bold", bg="blue", fg="white")
        self.highwind_strict_last_modified_label.grid(row=7, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)
        self.highwind_very_strict_last_modified_label = tk.Label(self.frame, text="Your Highwind very strict filter: Not found", font="-weight bold", bg="blue", fg="white")
        self.highwind_very_strict_last_modified_label.grid(row=8, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)

        self.check_updates = tk.Button(self.frame, text="Check for updates", command=lambda: self.check_filter_updates(), state=tk.DISABLED, width=15, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black")
        self.check_updates.grid(row=9, column=0, columnspan=2, pady=5)
        self.update_all_filters = tk.Button(self.frame, text="Update all old filters", command=lambda: self.update_all_filters_files(), state=tk.DISABLED, width=15, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black")
        self.update_all_filters.grid(row=9, column=2, columnspan=2, pady=5)

        self.stop_button = tk.Button(self.frame, text="Stop", command=lambda: self.stop_download_operation(self.down), state=tk.DISABLED, width=10, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black")
        self.stop_button.grid(row=10, column=0, columnspan=4, pady=10)

        self.statusbar_label = tk.Label(self.frame, text="", bg="blue", fg="white")
        self.statusbar_label.grid(row=11, column=0, columnspan=4, sticky=tk.W+tk.S, pady=15)

        # create a top level menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        quit_menu = tk.Menu(menubar, tearoff=0)
        quit_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=quit_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Open POE filter directory...", command=self.open_poe_filter_directory)

        menubar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Show Downloader's home page at github", command=lambda: self.downloader_homepage())
        help_menu.add_command(label="Show Highwind filter thread at Path of Exile's forums", command=lambda: self.highwind_filter_poe_forums())
        help_menu.add_separator()
        help_menu.add_command(label="About Downloader", command=lambda: self.about_downloader())
        menubar.add_cascade(label="Help", menu=help_menu)
        self.frame.pack(fill=tk.X)

        self.update_labels()

        t = threading.Timer(2.0, self.update_labelframes_timer_tick)
        t.start()

        self.down = None
        self.center(self.root)
        self.root.mainloop()

    def update_labelframes_timer_tick(self):
        self.statusbar_label.config(text="Checking for updates...")

        self.update_labelframes("highwind")
        self.update_labelframes("highwind_mapping")
        self.update_labelframes("highwind_strict")
        self.update_labelframes("highwind_very_strict")

        self.download_highwind.config(state="normal")
        self.download_highwind_mapping.config(state="normal")
        self.download_highwind_strict.config(state="normal")
        self.download_highwind_very_strict.config(state="normal")
        self.check_updates.config(state="normal")
        self.update_all_filters.config(state="normal")

        self.statusbar_label.config(text="Updates were checked")

    def update_all_filters_files(self):
        self.update_all_filters.config(state="disabled")

        self.download_highwind_filter("Highwind filter")
        self.root.update()
        self.download_highwind_filter("Highwind mapping filter")
        self.root.update()
        self.download_highwind_filter("Highwind strict filter")
        self.root.update()
        self.download_highwind_filter("Highwind very strict filter")
        self.root.update()

        self.update_all_filters.config(state="normal")

    def check_filter_updates(self):
        self.download_highwind.config(state="disabled")
        self.download_highwind_mapping.config(state="disabled")
        self.download_highwind_strict.config(state="disabled")
        self.download_highwind_very_strict.config(state="disabled")
        self.check_updates.config(state="disabled")
        self.update_all_filters.config(state="disabled")
        self.root.update()

        self.update_labelframes_timer_tick()

    def file_is_same_in_size(self, file, length):
        path = tempfile.gettempdir()
        path = path + '/' + file
        if os.path.exists(path):
            return os.path.getsize(path) == length
        else:
            return False

    def set_content_to_labelframes_labels(self, variant, url, size_label, mod_label):
        util = Utility()
        length = util.get_file_size_in_url(url)

        if length == "Unknown":
            return

        length = int(length)
        size_label.config(text=self.file_size(length))
        mod_time = util.get_last_modified_date_in_url(url)
        mod_label.config(text=self.modified_date(mod_time))

    def set_content_to_label(self, variant, label):
        util = Utility()

        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf)
        path = buf.value + "\My Games\Path of Exile\\" + variant + ".filter"
        if os.path.exists(path):
            mod_time = util.get_last_modified_date_in_file(path)
            label.config(text="Your " + variant + " filter file last modified time: %s" % time.ctime(mod_time))
        else:
            label.config(text="Your " + variant + " filter file is not found")

    def update_labelframes(self, variant):
        if self.have_internet():
            if variant == "highwind":
                self.set_content_to_labelframes_labels("highwind", "https://raw.githubusercontent.com/ffhighwind/PoE-Price-Lister/master/Resources/highwind's_filter.filter", self.highwind_size_label, self.highwind_last_mod_label)
            elif variant == "highwind_mapping":
                self.set_content_to_labelframes_labels("highwind_mapping", "https://raw.githubusercontent.com/ffhighwind/PoE-Price-Lister/master/Resources/highwind's_mapping_filter.filter", self.highwind_mapping_size_label, self.highwind_mapping_last_mod_label)
            elif variant == "highwind_strict":
                self.set_content_to_labelframes_labels("highwind_strict", "https://raw.githubusercontent.com/ffhighwind/PoE-Price-Lister/master/Resources/highwind's_strict_filter.filter", self.highwind_strict_size_label, self.highwind_strict_last_mod_label)
            elif variant == "highwind_very_strict":
                self.set_content_to_labelframes_labels("highwind_very_strict", "https://raw.githubusercontent.com/ffhighwind/PoE-Price-Lister/master/Resources/highwind's_very_strict_filter.filter", self.highwind_very_strict_size_label, self.highwind_very_strict_last_mod_label)

    def update_labels(self):
        self.set_content_to_label("highwind", self.highwind_last_modified_label)
        self.set_content_to_label("highwind_mapping", self.highwind_mapping_last_modified_label)
        self.set_content_to_label("highwind_strict", self.highwind_strict_last_modified_label)
        self.set_content_to_label("highwind_very_strict", self.highwind_very_strict_last_modified_label)

    # From http://stackoverflow.com/questions/3764291/checking-network-connection
    @staticmethod
    def have_internet():
        conn = http.client.HTTPConnection("www.google.com")
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
        self.download_highwind.config(state="normal")
        self.download_highwind_mapping.config(state="normal")
        self.download_highwind_strict.config(state="normal")
        self.download_highwind_very_strict.config(state="normal")
        self.check_updates.config(state="normal")
        self.update_all_filters.config(state="normal")
        self.root.update()

    def show_msgbox(self, title, message, width=200, height=200, msgbox_type="info"):
        window = tk.Tk()
        window.wm_withdraw()

        window.geometry(str(width) + "x" + str(height))

        if msgbox_type == "info":
            tkinter.messagebox.showinfo(title=title, message=message, parent=window)
        elif msgbox_type == "error":
            tkinter.messagebox.showerror(title=title, message=message, parent=window)
        elif msgbox_type == "warning":
            tkinter.messagebox.showwarning(title=title, message=message, parent=window)
        else:
            my_logger.error("Unkown type was passed to showMsgBox method")
            return

        self.root.update()

    def about_downloader(self):
        window = tk.Tk()
        window.wm_withdraw()

        window.geometry("1x1+200+200")
        tkinter.messagebox.showinfo(title="About Downloader", message="Downloader V" + DLER_VERSION + "\n\nBy Ixoth\n\nCopyright (C) 2018", parent=window)
        self.root.update()

    def downloader_homepage(self):
        url = "https://github.com/arsirantala/downloader"
        os.startfile(url)

    def highwind_filter_poe_forums(self):
        url = "https://www.pathofexile.com/forum/view-thread/1490867"
        os.startfile(url)

    @staticmethod
    def show_ask_question(title, message):
        var = tkinter.messagebox.askyesno(title, message)
        return var

    def prep_dl_thread(self, url, filename):
        self.stop_button.config(state="normal")
        self.root.update()

        self.down = Downloader()
        self.down.download(url, filename, self.download_highwind, self.download_highwind_mapping, self.download_highwind_strict, self.download_highwind_very_strict, self.check_updates, self.update_all_filters, self.progressbar,
                           self.downloadstatus_Label, self.stop_button, self.statusbar_label, self.root)

    def download_highwind_filter(self, variant):
        if not self.have_internet():
            self.show_msgbox("No internet connection", "Sorry feature unanavailable because of no internet connectivity", 200, 200, "error")
            return

        if variant == "Highwind filter":
            self.prep_dl_thread("https://raw.githubusercontent.com/ffhighwind/PoE-Price-Lister/master/Resources/highwind's_filter.filter", "highwind.filter")
        elif variant == "Highwind mapping filter":
            self.prep_dl_thread("https://raw.githubusercontent.com/ffhighwind/PoE-Price-Lister/master/Resources/highwind's_mapping_filter.filter", "highwind_mapping.filter")
        elif variant == "Highwind strict filter":
            self.prep_dl_thread("https://raw.githubusercontent.com/ffhighwind/PoE-Price-Lister/master/Resources/highwind's_strict_filter.filter", "highwind_strict.filter")
        elif variant == "Highwind very strict filter":
            self.prep_dl_thread("https://raw.githubusercontent.com/ffhighwind/PoE-Price-Lister/master/Resources/highwind's_very_strict_filter.filter", "highwind_very_strict.filter")

    def open_poe_filter_directory(self):
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf)
        path = buf.value + "\My Games\Path of Exile"
        if os.path.exists(path):
            subprocess.call(['explorer', path])
        else:
            self.show_msgbox("Can't find POE filter directory", "The default POE filter directory doesn't exist!", 200, 200, "error")

if __name__ == "__main__":
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(os.path.basename(sys.argv[0]).replace(".py", ".out").replace(".exe", ".out"), maxBytes=2000000, backupCount=10)
    my_logger = logging.getLogger(os.path.basename(sys.argv[0]).replace(".py", "").replace(".exe", ".out"))
    my_logger.setLevel(logging.INFO)

    # create a logging format
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%d.%m.%Y %I:%M:%S %p')
    handler.setFormatter(formatter)

    # add the handlers to the logger
    my_logger.addHandler(handler)

    my_logger.info('Downloader started')

    if platform != 'win32':
        my_logger.error("Unsupported OS")
        sys.exit()

    myObj = Application()
