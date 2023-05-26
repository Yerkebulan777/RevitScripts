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
from System.Collections.Generic import List

clr.AddReference('RevitNodes')
import Revit

clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

def GetActive3DView():
    actiview = uidoc.ActiveView
    collector = FilteredElementCollector(doc).OfClass(View3D)
    if actiview.Id in collector.ToElementIds(): return actiview
    TransactionManager.Instance.EnsureInTransaction(doc)
    TransactionManager.Instance.ForceCloseTransaction()
    cmdname = PostableCommand.CloseHiddenWindows
    cmdid = RevitCommandId.LookupPostableCommandId(cmdname)
    for view in collector.ToElements():
        if view and not view.IsTemplate:
            try:
                uidoc.ActiveView.Dispose()
                uidoc.RequestViewChange(view)
                uidoc.RefreshActiveView()
                collector.Dispose()
                uiapp.PostCommand(cmdid)
                return view
            except:
                pass

view3d = GetActive3DView()

OUT = view3d
