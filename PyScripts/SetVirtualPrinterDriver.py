#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-

import sys
import sysconfig
import time

libpaths = sysconfig.get_paths()
for key, path in libpaths.items():
    sys.path.append(path)

import win32print


def SetVirtualPrinterDriver(printer_name):
    device_name = win32print.GetDefaultPrinter()
    if printer_name != device_name:
        win32print.SetDefaultPrinter(printer_name)
        PRINTER_DEFAULTS = {'DesiredAccess': win32print.PRINTER_ALL_ACCESS}
        hprinter = win32print.OpenPrinter(printer_name, PRINTER_DEFAULTS)
        if bool(hprinter):
            level = 2
            attributes = win32print.GetPrinter(hprinter, level)
            try:
                win32print.SetPrinter(hprinter, level, attributes, 0)
            except Exception as error:
                return str(error)
            finally:
                win32print.ClosePrinter(hprinter)
                device_name = win32print.GetDefaultPrinter()

    return device_name


printer = "PDF24"
output = SetVirtualPrinterDriver(printer)
print("\n\t" + '*' * 125 + "\n")
print("\t\t\tDefault virtual printer driver: " + output)
print("\n\t" + '*' * 125 + "\n")
time.sleep(5)
