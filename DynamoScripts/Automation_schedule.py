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
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import SharedParameterElement
from Autodesk.Revit.DB import FilteredElementCollector, Transaction
from Autodesk.Revit.DB import Element, ElementId, BuiltInCategory, BuiltInParameter
from Autodesk.Revit.DB import ViewSchedule, ScheduleSortGroupField, ScheduleFilter
from Autodesk.Revit.DB import ScheduleSortOrder, ScheduleFilterType, SectionType
from Autodesk.Revit.DB import ViewSheet, ScheduleSheetInstance, ScheduleFieldType
from Autodesk.Revit.DB import SchedulableField, UnitType
from Autodesk.Revit.DB import DisplayUnitType, UnitUtils

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

TransactionManager.Instance.ForceCloseTransaction()

doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument


# app = DocumentManager.Instance.CurrentUIApplication.Application
# uiapp = DocumentManager.Instance.CurrentUIApplication
# uidoc = uiapp.ActiveUIDocument
# revit_file_path = doc.PathName


def get_field(schedule, name):
    field = None
    definition = schedule.Definition
    count = definition.GetFieldCount()
    for idx in range(0, count, 1):
        if definition.GetField(idx).GetName() == name:
            field = definition.GetField(idx)
            count = idx
    return field, count


########################################################################################################################
def create_schedule(doc, categoryId, schedule_name, field_names, sorted_names=None, hidden_names=None):
    if isinstance(field_names, list) and len(field_names):
        with Transaction(doc, schedule_name) as trans:
            trans.Start()
            count = int(0)
            schedules = FilteredElementCollector(doc).OfClass(ViewSchedule).ToElements()
            schedule = List[Element](filter(lambda x: x.Name == schedule_name, schedules)).FirstOrDefault()
            schedule = schedule if bool(schedule) else ViewSchedule.CreateSchedule(doc, categoryId)
            definition = schedule.Definition
            width = float(50 / 304.8)
            definition.ClearFields()
            for idx, fieldName in enumerate(field_names):
                for schedulable in definition.GetSchedulableFields():
                    if (schedulable.GetName(doc) == fieldName):
                        definition.InsertField(schedulable, count)
                        field = definition.GetField(count)
                        if field and field.IsValidObject:
                            field.SheetColumnWidth = width
                            count += 1
                            break

            if isinstance(sorted_names, list) and len(sorted_names):
                for idx, fieldName in enumerate(sorted_names):
                    for fieldId in definition.GetFieldOrder():
                        field = definition.GetField(fieldId)
                        if (field.GetName() == fieldName):
                            sortingField = ScheduleSortGroupField(field.FieldId)
                            sortingField.SortOrder = ScheduleSortOrder.Ascending
                            definition.AddSortGroupField(sortingField)
                            break

            if isinstance(hidden_names, list) and len(hidden_names):
                for idx, fieldName in enumerate(hidden_names):
                    for fieldId in definition.GetFieldOrder():
                        field = definition.GetField(fieldId)
                        if (field.GetName() == fieldName):
                            field.IsHidden = True
                            break

            schedule.Definition.IsItemized = False
            schedule.Definition.ShowTitle = True
            schedule.Name = schedule_name
            trans.Commit()
            return schedule


def set_schedule_filters(schedule, filter_names, filter_values):
    if isinstance(filter_names, list) and len(filter_names):
        with Transaction(doc, "ScheduleFilter") as trans:
            trans.Start()
            definition = schedule.Definition
            filters = definition.GetFilters()
            filterType = ScheduleFilterType.Equal
            if len(filters): definition.ClearFilters()
            for idx, fieldName in enumerate(filter_names):
                for fieldId in definition.GetFieldOrder():
                    scheduleField = definition.GetField(fieldId)
                    if (definition.CanFilter() and fieldName.Equals(scheduleField.GetName())):
                        value = filter_values[idx]
                        if definition.CanFilterByParameterExistence(fieldId):
                            sdf = ScheduleFilter(fieldId, filterType)
                            sdf.SetValue(scheduleField.ParameterId)
                            definition.AddFilter(sdf)
                            break
                        elif definition.CanFilterBySubstring(fieldId):
                            value = value if isinstance(value, str) else str(value)
                            sdf = ScheduleFilter(fieldId, filterType)
                            sdf.SetValue(value)
                            definition.AddFilter(sdf)
                            break
                        elif definition.CanFilterByValue(fieldId):
                            value = value if isinstance(value, int) else int(value)
                            sdf = ScheduleFilter(fieldId, filterType)
                            sdf.SetValue(value)
                            definition.AddFilter(sdf)
                            break
            trans.Commit()
            return schedule


def get_schedule_parameters(doc, schedule):
    result = []
    definition = schedule.Definition
    for sch in definition.GetSchedulableFields():
        shared = doc.GetElement(sch.ParameterId)
        if isinstance(shared, SharedParameterElement):
            result.append(shared)
    return result


def delete_unplaced_schedules(doc):
    category = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Rooms)
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


def get_schedule_by_name(doc, schedule_name, tolerance=0.5, result=None):
    schedules = FilteredElementCollector(doc).OfClass(ViewSchedule).ToElements()
    pattern = re.compile(schedule_name)
    for sequence in schedules:
        search = sequence.Name.encode('cp1251', 'ignore').decode('cp1251').strip()
        weight = difflib.SequenceMatcher(None, schedule_name, search).ratio()
        if pattern.findall(search, re.IGNORECASE): weight += 0.5
        if (weight > tolerance):
            tolerance = weight
            result = sequence
    return result


########################################################################################################################
categoryId = ElementId(BuiltInCategory.OST_Rooms)
field_names = ['Уровень', 'Назначение', 'Имя', 'Площадь']
field_names += ['BI_тип_помещения', 'BI_коэффициент_площади', 'BI_индекс_помещения', 'BI_площадь_с_коэффициентом']
sorted_names = ['Назначение', 'Имя', 'BI_тип_помещения']
hidden_names = ['Уровень']
########################################################################################################################
# schedule = create_schedule(doc, categoryId, "TestName", field_names, sorted_names, hidden_names)
# schedule = set_schedule_filters(schedule, ['Назначение'], ["МОП"])
########################################################################################################################
OUT = delete_unplaced_schedules(doc)
########################################################################################################################
