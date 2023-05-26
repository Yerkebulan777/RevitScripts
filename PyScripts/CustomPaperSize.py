#!/usr/bin/env python 3.9
# -*- coding: utf-8 -*-

import sys
import sysconfig
import time

LibPaths = sysconfig.get_paths()
for path in LibPaths.values():
    sys.path.append(path)

import win32print


def AddCustomPaperSize(str_width_mm, str_height_mm, printer_name='PDF24', level=2):
    width_mm = int(str_width_mm if isinstance(str_width_mm, str) and str_width_mm.isdigit() else 0)
    height_mm = int(str_height_mm if isinstance(str_height_mm, str) and str_height_mm.isdigit() else 0)
    if (width_mm > height_mm): width_mm, height_mm = height_mm, width_mm
    if (width_mm and height_mm):
        # Get a handle for the default printer
        device_name = win32print.GetDefaultPrinter()
        print("Default printer name: " + device_name)

        format_name = f'CustomSize {width_mm} x {height_mm}'
        width, height = int(width_mm * 1000), int(height_mm * 1000)
        custom_form = ({'Flags': 0, 'Name': format_name, 'Size': {'cx': width, 'cy': height},
                        'ImageableArea': {'left': 0, 'topValue': 0, 'right': width, 'botValue': height}})

        if printer_name != device_name: win32print.SetDefaultPrinter(printer_name)
        PRINTER_DEFAULTS = {'DesiredAccess': win32print.PRINTER_ALL_ACCESS}
        hprinter = win32print.OpenPrinter(device_name, PRINTER_DEFAULTS)
        
        if bool(hprinter):
            try:
                win32print.GetForm(hprinter, format_name)
                win32print.DeleteForm(hprinter, format_name)
            except:
                pass
            try:
                win32print.AddForm(hprinter, custom_form)
                attributes = win32print.GetPrinter(hprinter, level)
                win32print.SetPrinter(hprinter, level, attributes, 0)
                print("... Script Add custom paper size successfully")
                print("Set paper size: " + format_name)
                win32print.ClosePrinter(hprinter)
                time.sleep(0.25)
            except Exception as error:
                print(error)


width_mm, height_mm, printer_name = sys.argv[1], sys.argv[2], sys.argv[3]
print("Start set custom format: {} x {}".format(width_mm, height_mm))
AddCustomPaperSize(width_mm, height_mm, printer_name)

# str_width_mm, str_height_mm, printer_name = '250', '250', 'PDF24'
# AddCustomPaperSize(str_width_mm, str_height_mm, printer_name)
