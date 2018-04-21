#!/usr/bin/env python
"""
date: 21.4.2018
username: Ixoth
description: Highwind POE filter Downloader
TODO:
-
"""

import Tkinter as tk
import atexit
import ctypes.wintypes
import datetime
import hashlib
import httplib
import logging.handlers
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import tkMessageBox
import ttk
import urllib2
from _socket import timeout
from shutil import copyfile
from sys import platform

import configparser
import requests

# Constants ->
DLER_VERSION = "1.0.17"
CSIDL_PERSONAL = 5       # My Documents
SHGFP_TYPE_CURRENT = 0
SMALL_REGULAR_FILTER = "S1_Regular_Highwind"
SMALL_MAPPING_FILTER = "S2_Mapping_Highwind"
SMALL_STRICT_FILTER = "S3_Strict_Highwind"
SMALL_VERY_STRICT_FILTER = "S4_Very_Strict_Highwind"
CONFIG_URL_ADDRESS = "https://raw.githubusercontent.com/ffhighwind/PoE-Price-Lister/master/Resources/filterblast_config.txt"
#  <- Constants

# Globals ->
filters = []
# <- Globals


class Filter:
    name = ""
    filename = ""
    url = ""

    def __init__(self, name, filename, url):
        self.name = name
        self.filename = filename
        self.url = url


class Utility:
    # From http://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
    def __init__(self):
        pass

    @staticmethod
    def write_error(msg, statusbar_label, root, stop_button, download_highwind, download_highwind_mapper, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters):
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
    def get_last_modified_date_in_file(filepath):
        return os.path.getmtime(filepath)

    @staticmethod
    def get_info_from_url(base_url):
        info = {}
        response = requests.get(base_url, stream=True)
        info["etag"] = response.headers["ETag"]
        info["date"] = response.headers["Date"]
        info["size"] = response.headers["Content-length"]

        return info

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

    @staticmethod
    def poe_filter_directory():
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf)
        path = buf.value + "\My Games\Path of Exile"
        if os.path.exists(path):
            return path
        else:
            return ""

    @staticmethod
    def update_ini_file(section, key, value, add_section_if_missing=False):
        if not add_section_if_missing:
            if section == "" or section is None:
                raise Exception("Section called %s value is empty or None" % section)

        if key == "" or key is None:
            raise Exception("Key called %s value is empty or None" % key)

        if value == "" or value is None:
            raise Exception("Value called %s value is empty or None" % value)

        cfg_filename = os.path.basename(sys.argv[0]).replace(".py", ".ini").replace(".exe", ".ini")
        cfgfile_write = open(cfg_filename, "w")
        Config.read(cfg_filename)

        if add_section_if_missing:
            if not Config.has_section(section):
                Config.add_section(section)

        if not Config.has_section(section):
            raise Exception("No section called %s was found in the ini file: %s!" % (section, cfg_filename))
        else:
            Config.set(section, key, str(value))

        Config.write(cfgfile_write)
        cfgfile_write.close()

    @staticmethod
    def read_from_ini(section, key):
        cfg_filename_read = os.path.basename(sys.argv[0]).replace(".py", ".ini").replace(".exe", ".ini")
        cfgfile_read = open(cfg_filename_read, "r")
        Config.read(cfg_filename_read)
        try:
            value = Config.get(section, key)
        except:
            my_logger.error("No key '%s' were found in section: '%s' from ini file: %s" % (key, section, cfg_filename_read))
            value = None
        cfgfile_read.close()
        return value

    @staticmethod
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    @staticmethod
    def file_is_same_in_size(file_name, length):
        path = tempfile.gettempdir()
        path = path + '/' + file_name
        if os.path.exists(path):
            return os.path.getsize(path) == length
        else:
            return False

    @staticmethod
    def show_ask_question(title, message):
        var = tkMessageBox.askyesno(title, message)
        return var

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
        retstr = "Size: "
        if bytes_amount == 0:
            return retstr + "Unknown"
        else:
            return retstr + Utility.get_human_readable(bytes_amount)

    @staticmethod
    def modified_date(last_modified):
        retstr = "Last modified: "
        if len(last_modified) == 0:
            return retstr + "Unknown"
        else:
            return retstr + last_modified

    @staticmethod
    def downloader_homepage():
        url = "https://github.com/arsirantala/downloader"
        os.startfile(url)

    @staticmethod
    def highwind_filter_poe_forums():
        url = "https://www.pathofexile.com/forum/view-thread/1490867"
        os.startfile(url)


class Downloader:
    def write_error(self, e, statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters):
        Utility.write_error("Error: " + e + " occurred during download", statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters)
        self.stop_down = True

    def __init__(self):
        self._continue = False
        self.stop_down = False
        self.thread = None

    def download(self, url, destination, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters, progressbar, downloadstatus_label, stop_button, statusbar_label, root):

        self.thread = threading.Thread(target=self.__down, args=(url, destination, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters, progressbar, downloadstatus_label, stop_button, statusbar_label, root))
        self.thread.start()

    def __down(self, url, dest, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters, progressbar, downloadstatus_label, stop_button, statusbar_label, root):

        my_logger.info("Starting downloading...")

        download_highwind.config(state="disabled")
        download_highwind_mapping.config(state="disabled")
        download_highwind_strict.config(state="disabled")
        download_highwind_very_strict.config(state="disabled")
        check_updates.config(state="disabled")
        update_all_filters.config(state="disabled")

        _continue = True
        try:
            handler_dl = urllib2.urlopen(url, timeout=240)
        except urllib2.HTTPError, e:
            self.write_error(e, statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters)
            return

        no_content_length = False
        size = 0
        if "content-length" in handler_dl.headers:
            size = long(handler_dl.headers['content-length'])
        else:
            no_content_length = True
            my_logger.info("content-length was not found from headers! Can't show download progress")

        temp_dir = tempfile.gettempdir()
        file_path = temp_dir + '/' + dest

        statusbar_label.config(text="Downloading to: " + file_path + "...")

        try:
            self.fp = open(file_path, "wb+")
        except:
            self.write_error("Was not able to open temporary file for writing the filter file at " + file_path, statusbar_label, root, stop_button, download_highwind, download_highwind_mapping,
                             download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters)
            return

        file_size_dl = 0
        block_sz = 8192

        start_time = datetime.datetime.now().replace(microsecond=0)

        while not self.stop_down and _continue:
            try:
                data = handler_dl.read(block_sz)
            except (urllib2.HTTPError, urllib2.URLError) as error:
                self.write_error("Error occurred while downloading the file: " + error, statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters)
                return
            except timeout:
                self.write_error("Timeout error occurred while downloading the file", statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters)
                return
            except Exception, e:
                self.write_error("Exception occurred while downloading the file. Exception was:" + str(e), statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters)
                return

            file_size_dl += len(data)

            if not no_content_length:
                percent = file_size_dl * 100. / size
            else:
                percent = 100

            progressbar["value"] = percent

            p1 = Utility.get_human_readable(file_size_dl)
            if not no_content_length:
                p2 = Utility.get_human_readable(size)
            else:
                p2 = "Unknown"

            now = datetime.datetime.now().replace(microsecond=0)
            difference = now - start_time
            if difference.total_seconds() > 0:
                kbs = file_size_dl / difference.total_seconds()
                if not no_content_length:
                    bytes_left = size - file_size_dl
                    time_left = bytes_left / kbs
                    estimate_left = str(datetime.timedelta(seconds=time_left)).split(".")[0]
                    downloadstatus_label.config(text=str("{0:.2f}".format(percent)) + "% Downloaded " + p1 + " bytes of " + p2 + " [" + estimate_left + " time left. Speed: " + str(Utility.get_human_readable(kbs)) + "/s]")
                else:
                    downloadstatus_label.config(text=str("{0:.2f}".format(percent)) + "% Downloaded " + p1 + " bytes of Unknown [??? time left. Speed: " + str(Utility.get_human_readable(kbs)) + "/s]")

            else:
                if not no_content_length:
                    downloadstatus_label.config(text=str("{0:.2f}".format(percent)) + "% Downloaded " + p1 + " bytes of " + p2)
                else:
                    downloadstatus_label.config(text=str("{0:.2f}".format(percent)) + "% Downloaded " + p1 + " bytes of Unknown")

            self.fp.write(data)
            _continue = data

        handler_dl.close()  # if download is stopped the handler should be closed
        self.fp.close()  # if download is stopped the file should be closed

        if not self.stop_down:
            my_logger.info(file_path + " was downloaded")
            stop_button.config(state="disabled")

            if os.path.exists(file_path):
                dled_file_sha1_value = Utility.calculate_sha1(file_path)
                path = Utility.poe_filter_directory()
                if os.path.exists(path):
                    installed_file_path = path + "\\" + dest
                    installed_file_sha1_value = None
                    if os.path.exists(installed_file_path):
                        installed_file_sha1_value = Utility.calculate_sha1(installed_file_path)
                        Utility.update_ini_file(dest.replace(".filter", ""), "DownloadedFileSha1", str(dled_file_sha1_value), True)

                    if dled_file_sha1_value != installed_file_sha1_value:
                        try:
                            copyfile(file_path, installed_file_path.encode("utf-8"))
                        except Exception, e:
                            statusbar_label.config(text="An exception occurred while attempting to copy file: {}".format(
                                e))

                        statusbar_label.config(text="Installation of " + dest + " filter was completed")
                    else:
                        statusbar_label.config(text="The filter is the same as the older one")
                else:
                    Utility.write_error("Error: POE filter directory doesn't exist!", statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters)
            else:
                Utility.write_error("Error: the downloaded file: " + file_path + " doesn't exist!", statusbar_label, root, stop_button, download_highwind, download_highwind_mapping, download_highwind_strict, download_highwind_very_strict, check_updates, update_all_filters)
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
    @staticmethod
    def center(toplevel):
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
        tk.Label(self.frame, text="Welcome to Downloader. Click button below to download filter(s) and have them copied to POE filters folder", bg="blue", fg="white", font="Helvetica 12 bold").grid(row=0, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)

        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("black.Horizontal.TProgressbar", background="blue")
        self.progressbar = ttk.Progressbar(self.frame, length=650, maximum=100, style="black.Horizontal.TProgressbar")
        self.progressbar.grid(row=1, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)

        self.downloadstatus_Label = tk.Label(self.frame, text="", bg="blue", fg="white")
        self.downloadstatus_Label.grid(row=2, column=0, columnspan=4, sticky=tk.N+tk.E+tk.W)

        self.download_highwind = tk.Button(self.frame, text="Highwind filter", command=lambda: self.download_highwind_filter(SMALL_REGULAR_FILTER), state=tk.DISABLED, width=15, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black", padx=5, pady=5)
        self.download_highwind.grid(row=3, column=0, pady=15)
        self.download_highwind_mapping = tk.Button(self.frame, text="Highwind mapping filter", command=lambda: self.download_highwind_filter(SMALL_MAPPING_FILTER), state=tk.DISABLED, width=20, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black", padx=5, pady=5)
        self.download_highwind_mapping.grid(row=3, column=1, pady=15)
        self.download_highwind_strict = tk.Button(self.frame, text="Highwind strict filter", command=lambda: self.download_highwind_filter(SMALL_STRICT_FILTER), state=tk.DISABLED, width=17, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black", padx=5, pady=5)
        self.download_highwind_strict.grid(row=3, column=2, pady=15)
        self.download_highwind_very_strict = tk.Button(self.frame, text="Highwind very strict filter", command=lambda: self.download_highwind_filter(SMALL_VERY_STRICT_FILTER), state=tk.DISABLED, width=20, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black", padx=5, pady=5)
        self.download_highwind_very_strict.grid(row=3, column=3, pady=15)

        self.style.configure("Red.TLabelframe", background="blue", foreground="black")
        self.style.configure("TLabelframe.Label", background="blue", foreground="white")
        highwind_labelframe = ttk.LabelFrame(self.frame, text="Filter info", style="Red.TLabelframe")
        highwind_labelframe.grid(row=4, column=0, padx=4, pady=15, sticky=tk.N+tk.E+tk.W)
        self.highwind_last_mod_label = tk.Label(highwind_labelframe, text="Last modified: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_last_mod_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_last_mod_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_size_label = tk.Label(highwind_labelframe, text="Size: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_size_label.config(wraplength=100, justify=tk.LEFT, height=2)
        self.highwind_size_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_update_available_label = tk.Label(highwind_labelframe, text="Update available: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_update_available_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_update_available_label.pack(fill=tk.X, side=tk.TOP)
        highwind_labelframe.grid_propagate(False)
        highwind_mapping_labelframe = ttk.LabelFrame(self.frame, text="Filter info", style="Red.TLabelframe")
        highwind_mapping_labelframe.grid(row=4, column=1, padx=4, pady=15, sticky=tk.N+tk.E+tk.W)
        self.highwind_mapping_last_mod_label = tk.Label(highwind_mapping_labelframe, text="Last modified: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_mapping_last_mod_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_mapping_last_mod_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_mapping_size_label = tk.Label(highwind_mapping_labelframe, text="Size: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_mapping_size_label.config(wraplength=100, justify=tk.LEFT, height=2)
        self.highwind_mapping_size_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_mapping_update_available_label = tk.Label(highwind_mapping_labelframe, text="Update available: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_mapping_update_available_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_mapping_update_available_label.pack(fill=tk.X, side=tk.TOP)
        highwind_mapping_labelframe.grid_propagate(False)
        highwind_strict_labelframe = ttk.LabelFrame(self.frame, text="Filter info", style="Red.TLabelframe")
        highwind_strict_labelframe.grid(row=4, column=2, padx=4, pady=15, sticky=tk.N+tk.E+tk.W)
        self.highwind_strict_last_mod_label = tk.Label(highwind_strict_labelframe, text="Last modified: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_strict_last_mod_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_strict_last_mod_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_strict_size_label = tk.Label(highwind_strict_labelframe, text="Size: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_strict_size_label.config(wraplength=100, justify=tk.LEFT, height=2)
        self.highwind_strict_size_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_strict_update_available_label = tk.Label(highwind_strict_labelframe, text="Update available: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_strict_update_available_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_strict_update_available_label.pack(fill=tk.X, side=tk.TOP)
        highwind_strict_labelframe.grid_propagate(False)
        highwind_very_strict_labelframe = ttk.LabelFrame(self.frame, text="Filter info", style="Red.TLabelframe")
        highwind_very_strict_labelframe.grid(row=4, column=3, padx=4, pady=15, sticky=tk.N+tk.E+tk.W)
        self.highwind_very_strict_last_mod_label = tk.Label(highwind_very_strict_labelframe, text="Last modified: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_very_strict_last_mod_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_very_strict_last_mod_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_very_strict_size_label = tk.Label(highwind_very_strict_labelframe, text="Size: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_very_strict_size_label.config(wraplength=100, justify=tk.LEFT, height=2)
        self.highwind_very_strict_size_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_very_strict_update_available_label = tk.Label(highwind_very_strict_labelframe, text="Update available: Unknown", anchor="w", bg="blue", fg="white")
        self.highwind_very_strict_update_available_label.config(wraplength=100, justify=tk.LEFT, height=4)
        self.highwind_very_strict_update_available_label.pack(fill=tk.X, side=tk.TOP)
        highwind_very_strict_labelframe.grid_propagate(False)

        local_filter_files_labelframe = ttk.LabelFrame(self.frame, text="Local Highwind filter files", style="Red.TLabelframe")
        local_filter_files_labelframe.grid(row=5, column=0, columnspan=4, padx=4, pady=5, sticky=tk.N+tk.E+tk.W)
        self.highwind_last_modified_label = tk.Label(local_filter_files_labelframe, text="Your Highwind filter: Not found", bg="blue", fg="white")
        self.highwind_last_modified_label.config(justify=tk.LEFT)
        self.highwind_last_modified_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_mapping_last_modified_label = tk.Label(local_filter_files_labelframe, text="Your Highwind mapping filter: Not found", bg="blue", fg="white")
        self.highwind_mapping_last_modified_label.config(wraplength=500, justify=tk.LEFT)
        self.highwind_mapping_last_modified_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_strict_last_modified_label = tk.Label(local_filter_files_labelframe, text="Your Highwind strict filter: Not found", bg="blue", fg="white")
        self.highwind_strict_last_modified_label.config(wraplength=500, justify=tk.LEFT)
        self.highwind_strict_last_modified_label.pack(fill=tk.X, side=tk.TOP)
        self.highwind_very_strict_last_modified_label = tk.Label(local_filter_files_labelframe, text="Your Highwind very strict filter: Not found", bg="blue", fg="white")
        self.highwind_very_strict_last_modified_label.config(wraplength=500, justify=tk.LEFT)
        self.highwind_very_strict_last_modified_label.pack(fill=tk.X, side=tk.TOP)
        local_filter_files_labelframe.grid_propagate(False)

        self.check_updates = tk.Button(self.frame, text="Check for updates", command=lambda: self.check_filter_updates(), state=tk.DISABLED, width=15, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black", padx=5, pady=5)
        self.check_updates.grid(row=6, column=0, columnspan=2, pady=5)
        self.update_all_filters = tk.Button(self.frame, text="Update all old filters", command=lambda: self.update_all_filters_files(), state=tk.DISABLED, width=15, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black", padx=5, pady=5)
        self.update_all_filters.grid(row=6, column=2, columnspan=2, pady=5)

        self.stop_button = tk.Button(self.frame, text="Stop", command=lambda: self.stop_download_operation(self.down), state=tk.DISABLED, width=10, bg="blue", fg="white", activebackground="blue", highlightbackground="blue", disabledforeground="black", padx=5, pady=5)
        self.stop_button.grid(row=7, column=0, columnspan=4, pady=5)

        self.statusbar_label = tk.Label(self.root, text="", bg="blue", fg="white", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar_label.pack(side=tk.BOTTOM, fill=tk.X)

        # create a top level menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        quit_menu = tk.Menu(menubar, tearoff=0)
        quit_menu.add_command(label="Exit", command=self.exit_app)
        menubar.add_cascade(label="File", menu=quit_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Open POE filter directory...", command=self.open_poe_filter_directory)
        tools_menu.add_separator()
        view_menu = tk.Menu(tools_menu, tearoff=0)
        self.choices = ["No transparency", "90%", "80%", "70%"]
        self.transparency = tk.IntVar()
        index = 1
        for l in self.choices:
            view_menu.add_radiobutton(label=l, value=index, variable=self.transparency, command=self.set_transparency)
            index += 1

        background_menu = tk.Menu(tools_menu, tearoff=0)
        self.choices = ["Blue", "Red", "Green", "Black"]
        self.background_color = tk.IntVar()
        index = 1
        for l in self.choices:
            background_menu.add_radiobutton(label=l, value=index, variable=self.background_color, command=self.set_background_color)
            index += 1

        tools_menu.add_cascade(label="Background color", menu=background_menu)

        value = Utility.read_from_ini("General", "background_color")

        if value == "" or value is None or value == "blue":
            self.background_color.set(1)
            Utility.update_ini_file("General", "background_color", 1, True)
            self.change_color_in_frame("blue")
        elif value == "red":
            self.background_color.set(2)
            self.change_color_in_frame("red")
        elif value == "green":
            self.background_color.set(3)
            self.change_color_in_frame("green")
        elif value == "black":
            self.background_color.set(4)
            self.change_color_in_frame("black")

        value = Utility.read_from_ini("General", "uitransparency")

        if value == "" or value is None or value == "1.0":
            if value == "" or value is None:
                value = "1.0"
            self.transparency.set(1)
            Utility.update_ini_file("General", "uitransparency", 1.0, True)
        elif value == "0.7":
            self.transparency.set(4)
        elif value == "0.8":
            self.transparency.set(3)
        elif value == "0.9":
            self.transparency.set(2)

        self.root.attributes('-alpha', value)

        tools_menu.add_cascade(label="Window transparency", menu=view_menu)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Show Downloader's home page at github", command=lambda: Utility.downloader_homepage())
        help_menu.add_command(label="Show Highwind filter thread at Path of Exile's forums", command=lambda: Utility.highwind_filter_poe_forums())
        help_menu.add_separator()
        help_menu.add_command(label="About Downloader", command=lambda: self.about_downloader())
        menubar.add_cascade(label="Help", menu=help_menu)
        self.frame.pack(fill=tk.X)

        self.update_labels()

        t = threading.Timer(2.0, self.update_labelframes_timer_tick)
        t.start()

        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self.down = None
        self.center(self.root)

        self.root.lift()
        self.root.iconbitmap(default=Utility.resource_path("Highwind.ico"))

        self.root.mainloop()

    def exit_app(self):
        self.root.quit()

    def set_transparency(self):
        value = self.transparency.get()

        if value == 1:
            self.root.attributes('-alpha', 1.0)
            Utility.update_ini_file("General", "uitransparency", 1.0, True)
        elif value == 2:
            self.root.attributes('-alpha', 0.9)
            Utility.update_ini_file("General", "uitransparency", 0.9, True)
        elif value == 3:
            self.root.attributes('-alpha', 0.8)
            Utility.update_ini_file("General", "uitransparency", 0.8, True)
        elif value == 4:
            self.root.attributes('-alpha', 0.7)
            Utility.update_ini_file("General", "uitransparency", 0.7, True)

    def change_color_in_frame(self, color):
        self.frame.configure(bg=color)
        self.statusbar_label.configure(bg=color, fg="white")

        for wid in self.frame.winfo_children():
            if wid.widgetName != "ttk::progressbar" and wid.widgetName != "ttk::labelframe":
                wid.configure(bg=color)
            else:
                if wid.widgetName == "ttk::labelframe":
                    try:
                        self.style = ttk.Style()
                        self.style.theme_use("default")
                        self.style.configure("TLabelframe.Label", background=color, foreground="white")
                        self.style.configure("Red.TLabelframe", background=color)
                    except:
                        my_logger.error("Error occurred setting style to labelframe")
                        sys.exit()

                    for lwid in wid.winfo_children():
                        lwid.configure(bg=color)
                elif wid.widgetName == "ttk::progressbar":
                    try:
                        self.style = ttk.Style()
                        self.style.theme_use("default")
                        self.style.configure("black.Horizontal.TProgressbar", background=color)
                    except:
                        my_logger.error("Error occurred setting style to progressbar")
                        sys.exit()

    def set_background_color(self):
        value = self.background_color.get()

        if value == 1:
            self.change_color_in_frame("blue")
            Utility.update_ini_file("General", "background_color", "blue", True)
        elif value == 2:
            self.change_color_in_frame("red")
            Utility.update_ini_file("General", "background_color", "red", True)
        elif value == 3:
            self.change_color_in_frame("green")
            Utility.update_ini_file("General", "background_color", "green", True)
        elif value == 4:
            self.change_color_in_frame("black")
            Utility.update_ini_file("General", "background_color", "black", True)

    @staticmethod
    def update_sha1_for_local_filter_file_to_ini(filename, variant):
        if os.path.exists(filename):
            sha1 = Utility.calculate_sha1(filename)
            Utility.update_ini_file(variant, "LocalFileSha1", str(sha1), True)

    def update_labelframes_timer_tick(self):
        self.statusbar_label.config(text="Checking for updates...")

        poe_dir = Utility.poe_filter_directory()
        self.update_sha1_for_local_filter_file_to_ini(poe_dir + "\\" + SMALL_REGULAR_FILTER + ".filter", SMALL_REGULAR_FILTER)
        self.update_sha1_for_local_filter_file_to_ini(poe_dir + "\\" + SMALL_MAPPING_FILTER + ".filter", SMALL_MAPPING_FILTER)
        self.update_sha1_for_local_filter_file_to_ini(poe_dir + "\\" + SMALL_STRICT_FILTER + ".filter", SMALL_STRICT_FILTER)
        self.update_sha1_for_local_filter_file_to_ini(poe_dir + "\\" + SMALL_VERY_STRICT_FILTER + ".filter", SMALL_VERY_STRICT_FILTER)

        if Utility.have_internet():
            config_etag_from_ini = Utility.read_from_ini("ConfigFile", "etag")
            config_date_from_ini = Utility.read_from_ini("ConfigFile", "date")
            config_size_from_ini = Utility.read_from_ini("ConfigFile", "gzip_size")

            info_from_url = Utility.get_info_from_url(CONFIG_URL_ADDRESS)
            config_etag = info_from_url["etag"]
            config_size = info_from_url["size"]
            config_date = info_from_url["date"]

            if config_etag_from_ini != config_etag and config_date_from_ini != config_date and config_size_from_ini != config_size:
                Utility.update_ini_file("ConfigFile", "etag", config_etag, True)
                Utility.update_ini_file("ConfigFile", "date", config_date, True)
                Utility.update_ini_file("ConfigFile", "gzip_size", config_size, True)

                try:
                    txt = urllib2.urlopen(CONFIG_URL_ADDRESS, timeout=240).read()

                    regex = "\tPreset\s\"(?P<name>[\w\s]+)\"(\sDEFAULT){0,1}\s\[(?P<filename>[\w]+)\]\s\[(?P<url>[\w:/.-]+)\]"
                    matches = re.finditer(regex, txt, re.MULTILINE)

                    for matchNum, match in enumerate(matches):
                        name = ""
                        filename = ""
                        url = ""

                        for groupNum in range(0, len(match.groups())):
                            groupNum = groupNum + 1

                            if groupNum == 1:
                                name = match.group(groupNum)
                            elif groupNum == 3:
                                filename = match.group(groupNum)
                            elif groupNum == 4:
                                url = match.group(groupNum)

                            if name != "" and filename != "" and url != "":
                                filters.append(Filter(name, filename, url))

                            for f in filters:
                                if "S1_" in f.filename or "S2_" in f.filename or "S3_" in f.filename or "S4_" in f.filename:
                                    # Utility will only handle small font filter files - support for large versions will be added at some point
                                    Utility.update_ini_file(f.filename, "name", f.name, True)
                                    Utility.update_ini_file(f.filename, "url", f.url, True)
                except urllib2.HTTPError, e:
                    my_logger.error("While downloading the config file an exception: '%s' occurred", str(e))
            else:
                my_logger.info("Config file has not changed. Not going to process it again")
        else:
            self.show_msgbox("No internet connection", "Sorry feature unavailable because of no internet connectivity", "error")

        self.update_labelframes(SMALL_REGULAR_FILTER)
        self.update_labelframes(SMALL_MAPPING_FILTER)
        self.update_labelframes(SMALL_STRICT_FILTER)
        self.update_labelframes(SMALL_VERY_STRICT_FILTER)

        self.download_highwind.config(state="normal")
        self.download_highwind_mapping.config(state="normal")
        self.download_highwind_strict.config(state="normal")
        self.download_highwind_very_strict.config(state="normal")

        self.check_updates.config(state="normal")
        self.update_all_filters.config(state="normal")

        self.statusbar_label.config(text="Updates were checked")

    def update_all_filters_files(self):
        self.update_all_filters.config(state="disabled")

        if not Utility.have_internet():
            self.statusbar_label.config(text="There is no internet connection available!")
            return

        if "MODIFIED" not in self.highwind_update_available_label.cget("text"):
            self.download_highwind_filter(SMALL_REGULAR_FILTER, True)
            self.root.update()

        if "MODIFIED" not in self.highwind_mapping_update_available_label.cget("text"):
            self.download_highwind_filter(SMALL_MAPPING_FILTER, True)
            self.root.update()

        if "MODIFIED" not in self.highwind_strict_update_available_label.cget("text"):
            self.download_highwind_filter(SMALL_STRICT_FILTER, True)
            self.root.update()

        if "MODIFIED" not in self.highwind_very_strict_update_available_label.cget("text"):
            self.download_highwind_filter(SMALL_VERY_STRICT_FILTER, True)
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

    @staticmethod
    def set_content_to_labelframes_labels(variant, url, size_label, mod_label, updated_available_label):
        info_from_url = Utility.get_info_from_url(url)

        size_label.config(text=Utility.get_human_readable(long(info_from_url["size"])) + " (gziped)")
        mod_time = info_from_url["date"]
        mod_label.config(text=Utility.modified_date(mod_time))
        etag = info_from_url["etag"]

        old_etag = Utility.read_from_ini(variant, "etag")
        old_date = Utility.read_from_ini(variant, "date")
        old_size = Utility.read_from_ini(variant, "gzip_size")

        if old_etag is not None and old_date is not None and old_size is not None:
            if len(old_etag) > 0 and len(old_date) > 0 and len(old_size) > 0:
                local_sha1 = Utility.read_from_ini(variant, "localfilesha1")
                dled_sha1 = Utility.read_from_ini(variant, "downloadedfilesha1")

                if old_etag != etag and old_date != mod_time and old_size != length:
                    if len(local_sha1) > 0 and len(dled_sha1):
                        if local_sha1 != dled_sha1:
                            updated_available_label.config(text="Update available: MODIFIED")
                        else:
                            updated_available_label.config(text="Update available: YES")
                else:
                    path = Utility.poe_filter_directory() + "\\" + variant + ".filter"
                    if not os.path.exists(path):
                        updated_available_label.config(text="Update available: YES")
                    else:
                        if len(local_sha1) > 0 and len(dled_sha1):
                            if local_sha1 != dled_sha1:
                                updated_available_label.config(text="Update available: MODIFIED")
                            else:
                                updated_available_label.config(text="Update available: NO")
            else:
                updated_available_label.config(text="Update available: Unknown")
        else:
            updated_available_label.config(text="Update available: Unknown")

        Utility.update_ini_file(variant, "etag", etag, True)
        Utility.update_ini_file(variant, "date", str(mod_time), True)
        Utility.update_ini_file(variant, "gzip_size", str(length), True)

    @staticmethod
    def set_content_to_label(variant, label):
        path = Utility.poe_filter_directory() + "\\" + variant + ".filter"
        if os.path.exists(path):
            mod_time = Utility.get_last_modified_date_in_file(path)
            label.config(text="Your " + variant + " filter file last modified time: %s" % time.ctime(mod_time))
        else:
            label.config(text="Your " + variant + " filter file is not found")

    def update_labelframes(self, variant):
        if Utility.have_internet():
            if variant == SMALL_REGULAR_FILTER:
                self.set_content_to_labelframes_labels(SMALL_REGULAR_FILTER, Utility.read_from_ini(SMALL_REGULAR_FILTER, "url"), self.highwind_size_label, self.highwind_last_mod_label, self.highwind_update_available_label)
            elif variant == SMALL_MAPPING_FILTER:
                self.set_content_to_labelframes_labels(SMALL_MAPPING_FILTER, Utility.read_from_ini(SMALL_MAPPING_FILTER, "url"), self.highwind_mapping_size_label, self.highwind_mapping_last_mod_label, self.highwind_mapping_update_available_label)
            elif variant == SMALL_STRICT_FILTER:
                self.set_content_to_labelframes_labels(SMALL_STRICT_FILTER, Utility.read_from_ini(SMALL_STRICT_FILTER, "url"), self.highwind_strict_size_label, self.highwind_strict_last_mod_label, self.highwind_strict_update_available_label)
            elif variant == SMALL_VERY_STRICT_FILTER:
                self.set_content_to_labelframes_labels(SMALL_VERY_STRICT_FILTER, Utility.read_from_ini(SMALL_VERY_STRICT_FILTER, "url"), self.highwind_very_strict_size_label, self.highwind_very_strict_last_mod_label, self.highwind_very_strict_update_available_label)
            else:
                my_logger.error("update_labelframes method. Unknown variant: " + variant)

    def update_labels(self):
        self.set_content_to_label(SMALL_REGULAR_FILTER, self.highwind_last_modified_label)
        self.set_content_to_label(SMALL_MAPPING_FILTER, self.highwind_mapping_last_modified_label)
        self.set_content_to_label(SMALL_STRICT_FILTER, self.highwind_strict_last_modified_label)
        self.set_content_to_label(SMALL_VERY_STRICT_FILTER, self.highwind_very_strict_last_modified_label)

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

    def show_msgbox(self, title, message, msgbox_type="info"):

        if msgbox_type == "info":
            tkMessageBox.showinfo(title=title, message=message)
        elif msgbox_type == "error":
            tkMessageBox.showerror(title=title, message=message)
        elif msgbox_type == "warning":
            tkMessageBox.showwarning(title=title, message=message)
        else:
            my_logger.error("Unknown type was passed to showMsgBox method")
            return

        self.root.update()

    def about_downloader(self):
        tkMessageBox.showinfo(title="About Highwind POE filters downloader...", message=u"Highwind POE filters downloader V%s\n\nBy Ixoth\n\nCopyright %s 2018" % (DLER_VERSION, u"\N{COPYRIGHT SIGN}"))
        self.root.update()

    def prep_dl_thread(self, url, filename):
        self.stop_button.config(state="normal")
        self.root.update()

        self.down = Downloader()
        self.down.download(url, filename, self.download_highwind, self.download_highwind_mapping, self.download_highwind_strict, self.download_highwind_very_strict, self.check_updates, self.update_all_filters, self.progressbar, self.downloadstatus_Label, self.stop_button, self.statusbar_label, self.root)

    def download_highwind_filter(self, variant, no_msgbox=False):
        if not no_msgbox:
            if not Utility.have_internet():
                self.show_msgbox("No internet connection", "Sorry feature unavailable because of no internet connectivity", "error")
                return

        if not os.path.exists(Utility.poe_filter_directory()):
            self.show_msgbox("POE filter directory doesn't exist!", "Make sure the \"Path of Exile\" directory exists in \"My Documents\"\\\"My Games\"!", "error")
            return

        if variant == SMALL_REGULAR_FILTER:
            self.prep_dl_thread(Utility.read_from_ini(SMALL_REGULAR_FILTER, "url"), SMALL_REGULAR_FILTER + ".filter")
        elif variant == SMALL_MAPPING_FILTER:
            self.prep_dl_thread(Utility.read_from_ini(SMALL_MAPPING_FILTER, "url"), SMALL_MAPPING_FILTER + ".filter")
        elif variant == SMALL_STRICT_FILTER:
            self.prep_dl_thread(Utility.read_from_ini(SMALL_STRICT_FILTER, "url"), SMALL_STRICT_FILTER + ".filter")
        elif variant == SMALL_VERY_STRICT_FILTER:
            self.prep_dl_thread(Utility.read_from_ini(SMALL_VERY_STRICT_FILTER, "url"), SMALL_VERY_STRICT_FILTER + ".filter")
        else:
            my_logger.error("download_highwind_filter. Unknown variant: " + variant)

    def open_poe_filter_directory(self):
        path = Utility.poe_filter_directory()
        if os.path.exists(path):
            subprocess.call(['explorer', path])
        else:
            self.show_msgbox("Can't find POE filter directory", "The default POE filter directory doesn't exist!", "error")


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

    # Attempt to read the configuration file. If it doesn't exist, it'll be created (and default values are used)
    Config = configparser.ConfigParser()
    Config._interpolation = configparser.ExtendedInterpolation()

    config_filename = os.path.basename(sys.argv[0]).replace(".py", ".ini").replace(".exe", ".ini")

    if not os.path.exists(config_filename):
        my_logger.info("Config file %s was not found. Creating it (using default values)" % config_filename)
        cfgfile = open(config_filename, "w")

        Config.add_section("General")
        Config.set("General", "UITransparency", "1.0")

        try:
            Config.write(cfgfile)
        except:
            my_logger.error("Error occurred while trying to write file %s" % config_filename)

        cfgfile.close()

    if platform != 'win32':
        my_logger.error("Unsupported OS")
        sys.exit()

    myObj = Application()
