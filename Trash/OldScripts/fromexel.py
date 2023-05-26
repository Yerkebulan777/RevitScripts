#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

pyt_path = r'C:\Program Files (x86)\IronPython 2.7\Lib'
sys.path.append(pyt_path)
from collections import defaultdict
import difflib
import os.path
import math
import os

import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import *

clr.AddReference('System')
from System import Guid
from System.Collections.Generic import List

microsoft_ref = "Microsoft.Office.Interop.Excel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=71e9bce111e9429c"
clr.AddReferenceByName(microsoft_ref)
from Microsoft.Office.Interop import Excel

clr.AddReference('RevitNodes')
import Revit

clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
uiapp = DocumentManager.Instance.CurrentUIApplication

# element = UnwrapElement(IN[0])

excl = Excel.ApplicationClass()
excl.Visible = False
excl.DisplayAlerts = False
workbk = excl.Workbooks.Open(IN[0])
worksheets = workbk.Worksheets
wsnms = [w.Name for w in worksheets]
workbk.Close()
excl.Quit()

# читаем excel-файл
# печатаем список листов


TransactionManager.Instance.EnsureInTransaction(doc)

TransactionManager.Instance.TransactionTaskDone()

OUT = 0
