#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import os
# import clr
# import System
# from System import *
# app = System.Runtime.InteropServices.Marshal.GetActiveObject("Autocad.Application")

import win32com.client

app = win32com.client.dynamic.Dispatch("AutoCAD.Application")
app.Visible = True

suffix = '.dwg'
output = r"D:\OUTPUT"
directory = r"D:\ACADFILES"
if not os.path.exists(output): os.makedirs(output)
for filename in os.listdir(directory):
    if filename.endswith(suffix):
        filepath = os.path.join(directory, filename)
        outfile = os.path.join(output, filename)
        doc = app.Documents.Open(filepath)
        if not os.path.exists(outfile):
            print("\tSave file: {}".format(filename))
            doc.SaveAs(outfile)
            doc.Close()

print("All files successfully completed!!!")
