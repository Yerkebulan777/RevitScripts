#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector, Transaction, SubTransaction
from Autodesk.Revit.DB import BuiltInParameter, SectionType, ViewType
from Autodesk.Revit.DB import UnitUtils, DisplayUnitType, StorageType

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

TransactionManager.Instance.ForceCloseTransaction()


def tolist(obj1):
    if hasattr(obj1, "__iter__"):
        return obj1
    else:
        return [obj1]


def get_mark(elevations, offset):
    strvals = []
    for idx, value in enumerate(elevations):
        if not isinstance(value, float): continue
        value = value + offset if (offset > 0) else value
        string = '+' + str(format(value, '.3f')) if value > 0 else str(format(value, '.3f'))
        string = string + '*' * int(idx)
        strvals.append(string.replace('.', ','))
    mark = ' '.join(strvals).strip()
    return mark


get_parameter = IN[1]
set_parameter = IN[2]
manualOffset = IN[3]

schedule_groups = []
schedule = doc.ActiveView
if schedule.ViewType == ViewType.Schedule:
    definition = schedule.Definition
    table = schedule.GetTableData()
    section = table.GetSectionData(SectionType.Body)
    headings = [definition.GetField(id).GetName() for id in definition.GetFieldOrder()]
    num_rows, num_columns = section.NumberOfRows, section.NumberOfColumns
    element_ids = FilteredElementCollector(doc, schedule.Id).ToElementIds()
    for row_analyse in range(num_rows):
        with Transaction(doc, "RemoveROW") as trans:
            trans.Start()
            with  SubTransaction(doc) as sut:
                sut.Start()
                if section.CanRemoveRow(row_analyse):
                    section.RemoveRow(row_analyse)
                    section.RefreshData()
                sut.Commit()
            remaining = FilteredElementCollector(doc, schedule.Id).ToElementIds()
            trans.RollBack()
        items = [doc.GetElement(id) for id in element_ids if id not in remaining]
        if any(items): schedule_groups.append(items)

TransactionManager.Instance.EnsureInTransaction(doc)

output = []
metreOffset = float(manualOffset) * 0.001
output.append(metreOffset)
for item_list in schedule_groups:
    if IN[0] != True: break
    elements, elevations, levels = [], [], []
    for element in tolist(item_list):
        if not element.IsValidObject: continue
        param = element.LookupParameter(get_parameter)
        offset = element.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM).AsDouble()
        level = doc.GetElement(element.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM).AsElementId())
        elevation = UnitUtils.ConvertFromInternalUnits(offset + level.ProjectElevation, DisplayUnitType.DUT_METERS)
        value = round(elevation * 1000)
        elevations.append(value / 1000)
        elements.append(element)
        levels.append(level)
        if param.Definition.BuiltInParameter == BuiltInParameter.INVALID:  # Check and add parameter value
            if param.StorageType == StorageType.Double and value != param.AsDouble(): param.Set(value)
            if param.StorageType == StorageType.Integer and value != param.AsInteger(): param.Set(int(value))
            if param.StorageType == StorageType.String and value != float(param.AsString()): param.Set(str(value))

    outmarks = []
    for levelId in sorted(set(map(lambda lvl: lvl.Id, levels)), reverse=True):
        values = sorted(set(x for x, lvl in zip(elevations, levels) if lvl.Id == levelId), reverse=True)
        mark = get_mark(values, metreOffset)
        outmarks.append(mark)
        for element, elevation, level in zip(elements, elevations, levels):
            if level.Id != levelId: continue
            count = values.index(elevation)
            param = element.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
            param.Set('*' * count) if count > 0 else param.Set('')

    joinmark = ' '.join(outmarks).strip()
    [element.LookupParameter(set_parameter).Set(joinmark) for element in elements]
    output.append(joinmark)

    TransactionManager.Instance.TransactionTaskDone()

    if schedule.ViewType != ViewType.Schedule:
        OUT = "WARNING: PLEASE ACTIVATE SCHEDULE"
    elif IN[0] == False:
        OUT = schedule_groups
    else:
        OUT = output
