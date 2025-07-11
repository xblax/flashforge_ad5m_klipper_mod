# Hash checking of gcode files
#
# See https://github.com/Klipper3d/klipper/commit/ba2b3909cdc51e4d00521510788a3bf95de273a7
#
# Copyright (C) 2025  minicx <minicx@disroot.org>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import os
import hashlib
import logging

class Md5Check:
    def __init__(self, config):
        self.name = config.get_name().split()[-1]
        self.printer = config.get_printer()
        self.logger = logging.getLogger('klippy')
        self.gcode = self.printer.lookup_object("gcode")
        try:
            self.vc = self.printer.lookup_object("virtual_sdcard")
        except Exception:
            self.printer.register_event_handler("virtual_sdcard:load_file", lambda _: self._respond_warn("MD5 check disabled!") )
            self.logger.error("md5_check: virtual_sdcard not found; MD5 check disabled.")
            return
        self.md5_prefix = config.get('md5_prefix', " MD5:")
        self.checked = False
        
        self.printer.register_event_handler("virtual_sdcard:reset_file", self.on_file_reset)
        self.printer.register_event_handler("virtual_sdcard:load_file", self.on_load_file)

    def on_file_reset(self):
        self.checked = False

    def on_load_file(self):
        if not self.vc or self.checked:
            return
        try:
            path = self.vc.file_path()
        except Exception as e:
            self.logger.error(f"md5_check: error obtaining file_path(): {e}")
            self.checked = True
            return
        if not path or not os.path.isfile(path):
            self.checked = True
            return
        self.checked = True
        try:
            with open(path, "rb") as f:
                first_line = f.readline()
                try:
                    first_line_str = first_line.decode("utf-8", errors="ignore").strip()
                except Exception:
                    first_line_str = ""
                prefix = f";{self.md5_prefix}"
                if not first_line_str.startswith(prefix):
                    self._respond_warn("MD5 comment not found at file start; skipping MD5 check.")
                    return
                expected_hash = first_line_str[len(prefix):].strip()
                md5 = hashlib.md5()
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    md5.update(chunk)
                actual_hash = md5.hexdigest()
                if actual_hash.lower() != expected_hash.lower():
                    self._respond_error(f"MD5 mismatch: expected {expected_hash}, but computed {actual_hash}. Canceling print.")
                    self.vc.do_cancel()
                else:
                    self._respond_info(f"MD5 match: {actual_hash}. Ready to print.")
        except Exception as e:
            self.logger.error(f"md5_check: error during MD5 verification: {e}")
            self._respond_error(f"Error during MD5 verification: {e}")

    def _respond_info(self, text):
        self.gcode.respond_info(f"md5_check: {text}")

    def _respond_error(self, text):
        self.gcode._respond_error(text)

    def _respond_warn(self, text):
        self.gcode.respond_info(f"md5_check WARNING: {text}")

def load_config(config):
    return Md5Check(config)
