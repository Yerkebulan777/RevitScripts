# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys
import time

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import re
import clr
import difflib
from functools import wraps
from collections import defaultdict

clr.AddReference("System")
clr.AddReference("System.Core")
import System
from System import EventHandler

clr.ImportExtensions(System.Linq)
from System.Collections.Generic import List

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector, Level, XYZ
from Autodesk.Revit.DB import SharedParameterElement, ExternalDefinition
from Autodesk.Revit.DB import ElementId, BuiltInCategory, BuiltInParameter, SpatialElement
from Autodesk.Revit.DB import ViewFamilyType, ViewFamily, ViewPlan, ViewDiscipline, ViewDetailLevel, DisplayStyle
from Autodesk.Revit.DB import ParameterValueProvider, FilterDoubleRule, FilterNumericGreater
from Autodesk.Revit.DB import ElementLevelFilter, ElementParameterFilter, LogicalAndFilter
from Autodesk.Revit.DB import Transaction, UnitUtils, DisplayUnitType
from Autodesk.Revit.Exceptions import InvalidOperationException
from Autodesk.Revit.DB.Architecture import Room

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.UI.Events import IdlingEventArgs
from Autodesk.Revit.UI.Events import ViewActivatedEventArgs

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName

TransactionManager.Instance.ForceCloseTransaction()


########################################################################################################################


def Output(output):
    if isinstance(output, basestring):
        TaskDialog.Show("OUTPUT", output)
        return


########################################################################################################################


def get_rooms_by_level(level):
    double_pvp = ParameterValueProvider(ElementId(BuiltInParameter.ROOM_AREA))
    double_rul = FilterDoubleRule(double_pvp, FilterNumericGreater(), 0.5, 0.005)
    level_filter, param_filter = ElementLevelFilter(level.Id), ElementParameterFilter(double_rul)
    collector = FilteredElementCollector(doc).OfClass(SpatialElement).OfCategory(BuiltInCategory.OST_Rooms)
    rooms = collector.WherePasses(LogicalAndFilter(level_filter, param_filter)).ToElements()
    rooms = sorted(rooms, key=lambda x: x.Area)
    return rooms


def activate_view(view):
    if uidoc.ActiveView.Id != view.Id:
        uidoc.RequestViewChange(view)
        uidoc.RefreshActiveView()
    view = uidoc.ActiveView
    return view


def close_views(view):
    viewId = view.Id
    for uvw in uidoc.GetOpenUIViews():
        if (uvw.ViewId != viewId):
            try:
                uvw.Close()
            except:
                pass
    return


def select_elements(elementIds):
    uidoc.Selection.SetElementIds(elementIds)
    return


def get_plan_by_level(doc, level):
    view_name = "{} (координация)".format(level.Name).strip()
    view_name = view_name.encode('cp1251', 'ignore').decode('cp1251', 'ignore')
    view = FilteredElementCollector(doc).OfClass(ViewPlan).Where(lambda x: x.Name == view_name).FirstOrDefault()
    for viewType in FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements():
        if (view and isinstance(view, ViewPlan)): break
        if (viewType.ViewFamily == ViewFamily.FloorPlan):
            with Transaction(doc, view_name) as trans:
                trans.Start()
                view = ViewPlan.Create(doc, viewType.Id, level.Id)
                view.get_Parameter(BuiltInParameter.VIEWER_CROP_REGION).Set(0)
                if view.CanModifyViewDiscipline():
                    view.get_Parameter(BuiltInParameter.VIEW_DISCIPLINE).Set(4095)
                if view.CanModifyDetailLevel():
                    view.get_Parameter(BuiltInParameter.VIEW_DETAIL_LEVEL).Set(3)
                if view.CanModifyDisplayStyle():
                    view.get_Parameter(BuiltInParameter.MODEL_GRAPHICS_STYLE).Set(3)
                view.CropBoxVisible = False
                view.ShowActiveWorkPlane()
                view.ViewName = view_name
                doc.Regenerate()
                trans.Commit()
                break
    activate_view(view)
    close_views(view)
    return view


########################################################################################################################
message = "Undefined rooms:\n"
########################################################################################################################
levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
levels = sorted(levels, key=lambda x: x.Elevation)
for level in levels:
    view = get_plan_by_level(doc, level)
    message += "\nLevel: {}\n".format(view.Name)
    rooms = get_rooms_by_level(level)
    time.sleep(0.5)
    for room in rooms:
        select_elements(List[ElementId]([room.Id]))

########################################################################################################################
OUT = message
########################################################################################################################
