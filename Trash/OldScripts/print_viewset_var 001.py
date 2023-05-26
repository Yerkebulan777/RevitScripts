#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
pyt_path = r'C:\Program Files (x86)\IronPython 2.7\Lib'
sys.path.append(pyt_path)
import difflib
import os.path
import pprint
import math
import re
"""
import operator
from itertools import count
"""

import clr
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import *

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import *

clr.AddReference('System')
import System
from System.Collections.Generic import *

clr.AddReference('RevitNodes')
import Revit
clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

#uiapp = DocumentManager.Instance.CurrentUIApplication
#app = uiapp.Application
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
doc = DocumentManager.Instance.CurrentDBDocument


def SetPaperFormat(sformat, orientation):
    printmanager = doc.PrintManager
    printsizes = printmanager.PaperSizes
    pprm = printmanager.PrintSetup.CurrentPrintSetting.PrintParameters
    pprm.PaperSize = [size for size in printsizes if sformat == size.Name]
    if orientation == "Landscape":
        pprm.PageOrientation = PageOrientationType.Landscape
    if orientation == "Portrait":
        pprm.PageOrientation = PageOrientationType.Portrait
    return pprm


def GetPaperSizeParameter(swidth, sheight):
    for pformat in FilteredElementCollector(doc).OfClass(Autodesk.Revit.DB.PrintSetting):
        pps = pformat.PrintParameters
        try:
            if 290 < int(swidth) < 310 and 200 < int(sheight) < 220:
                if pps.PaperSize.Name == "A4" and str(pps.PageOrientation) == "Landscape":
                    return pformat
                else:
                    return SetPaperFormat("A4", "Landscape")

            if 200 < int(swidth) < 220 and 290 < int(sheight) < 310:
                if pps.PaperSize.Name == "A4" and str(pps.PageOrientation) == "Portrait":
                    return pformat
                else:
                    return SetPaperFormat("A4", "Portrait")

            if 400 < int(swidth) < 450 and 290 < int(sheight) < 310:
                if pps.PaperSize.Name == "A3" and str(pps.PageOrientation) == "Landscape":
                    return pformat
                else:
                    return SetPaperFormat("A3", "Landscape")

            if 290 < int(swidth) < 310 and 400 < int(sheight) < 450:
                if pps.PaperSize.Name == "A3" and str(pps.PageOrientation) == "Portrait":
                    return pformat
                else:
                    return SetPaperFormat("A3", "Portrait")

            if 580 < int(swidth) < 600 and 400 < int(sheight) < 450:
                if pps.PaperSize.Name == "A2" and str(pps.PageOrientation) == "Landscape":
                    return pformat
                else:
                    return SetPaperFormat("A2", "Landscape")

            if 400 < int(swidth) < 450 and 580 < int(sheight) < 600:
                if pps.PaperSize.Name == "A2" and str(pps.PageOrientation) == "Portrait":
                    return pformat
                else:
                    return SetPaperFormat("A2", "Portrait")

            if 800 < int(swidth) < 900 and 580 < int(sheight) < 600:
                if pps.PaperSize.Name == "A1" and str(pps.PageOrientation) == "Landscape":
                    return pformat
                else:
                    return SetPaperFormat("A1", "Landscape")

            if 580 < int(swidth) < 600 and 800 < int(sheight) < 900:
                if pps.PaperSize.Name == "A1" and str(pps.PageOrientation) == "Portrait":
                    return pformat
                else:
                    return SetPaperFormat("A1", "Portrait")
        except:
            pass


def Print(printset_name, printset):
    printManager = doc.PrintManager
    printManager.SelectNewPrintDriver("PDF24 PDF")
    printManager.PrintRange = Autodesk.Revit.DB.PrintRange.Select
    printManager.CombinedFile = False
    printManager.PrintToFile = True
    printManager.PrintSetup.CurrentPrintSetting = printset
    pprm = printManager.PrintSetup.CurrentPrintSetting.PrintParameters
    pprm.HiddenLineViews = HiddenLineViewsType.RasterProcessing
    pprm.RasterQuality = RasterQualityType.High
    pprm.ColorDepth = ColorDepthType.GrayScale
    pprm.HideUnreferencedViewTags = False
    pprm.HideCropBoundaries = True
    pprm.HideReforWorkPlanes = True
    pprm.HideScopeBoxes = True
    pprm.PaperPlacement = PaperPlacementType.Margins
    pprm.MarginType = MarginType.NoMargin
    pprm.ZoomType = ZoomType.Zoom
    pprm.Zoom = 100
    TransactionManager.Instance.EnsureInTransaction(doc)
    printManager.Apply()
    printManager.PrintSetup.SaveAs(printset_name)
    uidoc.RefreshActiveView()
    doc.Regenerate()
    printManager.SubmitPrint()
    TransactionManager.Instance.TransactionTaskDone()
    return


def SetVeiwset():
    sheetdict = {}
    for i in FilteredElementCollector(doc).OfClass(Autodesk.Revit.DB.ViewSheet):
        viewcnt = i.GetAllPlacedViews().Count
        collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks)
        titleblock = collector.OwnedByView(i.Id).WhereElementIsNotElementType().FirstElement()
        if viewcnt >= 1 and titleblock:
            sn = titleblock.Name
            sw = titleblock.get_Parameter(BuiltInParameter.SHEET_WIDTH).AsValueString()
            sh = titleblock.get_Parameter(BuiltInParameter.SHEET_HEIGHT).AsValueString()
            sformat = sn + "(" + sw + "x" + sh + ")"
            if sheetdict.has_key(sformat):
                sheetdict[sformat].append(i)
            else:
                sheetdict.update({sformat: [i]})

    #############      Set Viewset      ############

    viewsetnames = ""
    printManager = doc.PrintManager
    printManager.PrintRange = PrintRange.Select
    TransactionManager.Instance.EnsureInTransaction(doc)
    try:
        printManager.ViewSheetSetting.SaveAs("tempSheetSetName")
        printManager.Apply()
    except:
        pass
    TransactionManager.Instance.TransactionTaskDone()
    for key in sorted(sheetdict.iterkeys()):
        for sheets in sheetdict.get(key):
            viewsetnames = []
            myViewSet = ViewSet()
            myViewSet.Insert(sheets)
            for viewset in FilteredElementCollector(doc).OfClass(ViewSheetSet).ToElements():
                if not viewset.IsValidObject:
                    continue
                TransactionManager.Instance.EnsureInTransaction(doc)
                viewSheetSetting = printManager.ViewSheetSetting
                viewsetname = viewset.Name
                if viewsetname == "tempSheetSetName":
                    viewSheetSetting.CurrentViewSheetSet = viewset
                    viewSheetSetting.Delete()
                    doc.Regenerate()
                if viewsetname == key and viewset.IsValidObject:
                    try:
                        viewsetnames.append(viewsetname)
                        viewSheetSetting.CurrentViewSheetSet.Views = myViewSet
                        viewSheetSetting.Save()
                        viewsetnames.append(key)
                        printManager.Apply()
                    except:
                        viewSheetSetting.CurrentViewSheetSet = viewset
                        viewSheetSetting.Delete()
                        viewsetnames.append("Deleted" + key)
                        doc.Regenerate()
                TransactionManager.Instance.ForceCloseTransaction()
            if not viewsetnames or key not in viewsetnames:
                TransactionManager.Instance.EnsureInTransaction(doc)
                viewSheetSetting = printManager.ViewSheetSetting
                viewSheetSetting.CurrentViewSheetSet.Views = myViewSet
                viewSheetSetting.SaveAs(key)
                printManager.Apply()
                viewsetnames.append(key)
                TransactionManager.Instance.ForceCloseTransaction()
    return viewsetnames

###########################################################################
###########################################################################
viewsets = SetVeiwset()
OUT = viewsets

