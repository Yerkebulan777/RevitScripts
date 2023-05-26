#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')
reload(sys)

import re
import clr
import difflib
import System

clr.AddReference("System")
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)
from System.Collections.Generic import List

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector, Transaction, XYZ
from Autodesk.Revit.DB import ElementId, SharedParameterElement, Transform
from Autodesk.Revit.DB import ViewSchedule, ScheduleSheetInstance, ViewSheet

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

TransactionManager.Instance.ForceCloseTransaction()

doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName

########################################################################################################################
regex = re.compile(r"([+*^#%!?@$&£\\\[\]{}|/;:<>`~]|\d*)")


########################################################################################################################
def select_elements(elementIds):
    uidoc.Selection.SetElementIds(elementIds)
    uidoc.ShowElements(elementIds)
    uidoc.RefreshActiveView()
    return elementIds


def get_schedule_parameters(doc, schedule):
    result = []
    definition = schedule.Definition
    for sch in definition.GetSchedulableFields():
        shared = doc.GetElement(sch.ParameterId)
        if isinstance(shared, SharedParameterElement):
            result.append(shared)
    return result


def delete_unplaced_schedules(doc):
    # category = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Rooms)
    schedules = FilteredElementCollector(doc).OfClass(ScheduleSheetInstance).ToElements()
    viewScheduleIds = FilteredElementCollector(doc).OfClass(ViewSchedule).ToElementIds()
    unplacedIds = set(viewScheduleIds).difference(inst.ScheduleId for inst in schedules)
    with Transaction(doc, "Delete unplaced schedules") as trans:
        trans.Start()
        for vid in unplacedIds: pass
        # try:
        #     doc.Delete(sch.Id)
        # except:
        #     pass
        trans.Commit()
    return len(viewScheduleIds), len(unplacedIds)


def get_field(schedule, name):
    field = None
    definition = schedule.Definition
    count = definition.GetFieldCount()
    for idx in range(0, count, 1):
        if definition.GetField(idx).GetName() == name:
            field = definition.GetField(idx)
            count = idx
    return field, count


def get_schedule_by_name(doc, schedule_name, tolerance=0.5, result=None):
    schedules = FilteredElementCollector(doc).OfClass(ViewSchedule).ToElements()
    schedule_name = regex.sub('', schedule_name, re.IGNORECASE)
    pattern = re.compile(schedule_name)
    for sequence in schedules:
        if tolerance > 1: break
        search = sequence.Name.strip()
        weight = difflib.SequenceMatcher(None, schedule_name, search).ratio()
        if pattern.findall(search, re.IGNORECASE): weight += 0.25
        if pattern.search(search, re.IGNORECASE): weight += 0.25
        if (weight > tolerance):
            tolerance = weight
            result = sequence
    return result


def get_schedules_by_category(doc, categoryId):
    schedules = FilteredElementCollector(doc).OfClass(ScheduleSheetInstance).ToElements()
    schedules = set(sch for sch in schedules if categoryId == doc.GetElement(sch.ScheduleId).Definition.CategoryId)
    # schedules = sorted(schedules lambda x: x.)
    return schedules


########################################################################################################################
# target = (seq for seq in doc.Application.Documents if (doc.Title != seq.Title))
# target = (target.next() if target.next() else IN[0])
########################################################################################################################
result = []
transform = Transform.Identity
schedule_name = "*NEW BIM Спецификация арматуры"
source = get_schedule_by_name(doc, schedule_name)
schedules = get_schedules_by_category(doc, source.Definition.CategoryId)
for schedule in schedules:
    viewId = schedule.OwnerViewId
    view = doc.GetElement(viewId)
    if isinstance(view, ViewSheet):
        with Transaction(doc, "Create instances") as trans:
            trans.Start()
            name = schedule.Name
            box = schedule.get_BoundingBox(view)
            point = transform.OfPoint(schedule.Point)
            u = (view.Outline.Max.U - view.Outline.Min.U) * 0.5
            v = (view.Outline.Max.V - view.Outline.Min.V) * 0.5
            instance = ScheduleSheetInstance.Create(doc, viewId, source.Id, XYZ(u, v, 0))
            if instance: result.append("Create SheetInstance overwrite by {} ".format(name))
            if instance and instance.Location.Move(point): select_elements(List[ElementId]([instance.Id]))
            trans.Commit()
            break
########################################################################################################################
OUT = result
########################################################################################################################
