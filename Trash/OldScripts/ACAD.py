#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
pyt_path = r'C:\Program Files (x86)\IronPython 2.7\Lib'
sys.path.append(pyt_path)
import System
from System import *
import clr
clr.AddReferenceToFileAndPath('C:/Program Files/Autodesk/AutoCAD 2020/Autodesk.AutoCAD.Interop.Common')
from Autodesk.AutoCAD.Interop.Common import *
from Autodesk.AutoCAD.ApplicationServices import *
from  Autodesk.AutoCAD.DatabaseServices import *
from Autodesk.AutoCAD.EditorInput import *
from  Autodesk.AutoCAD.Runtime import *
from  Autodesk.AutoCAD.Windows import *

marsh = System.Runtime.InteropServices.Marshal
app = marsh.GetActiveObject("Autocad.Application")
doc = app.ActiveDocument
msp = doc.ModelSpace
sel = doc.PickfirstSelectionSet
dicts = doc.Database.dictionaries


test = []
for obj in msp:
    name = obj.ObjectName
    if name == "AcDbBlockReference":
        test.append(name)


"""
for x in ThisDrawing.ModelSpace:
    if x.type is AcadHatch:
    #if x.ObjectName = "AcDbBlockReference":
        name = x.Name.upper()
        test.append(name)

#ts = dicts.Item("acad_tablestyle")
#.GetObjectIdString(AcadHatch, True)


#vrb = doc.GetVariable()
#grp = doc.Groups

#doc.Layouts.Item()
"""


OUT = test
