#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')
reload(sys)

import clr
import System

clr.AddReference("System")
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)
from System.Collections.Generic import List

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import FilteredElementCollector, SharedParameterElement
from Autodesk.Revit.DB import Element, ElementId, BuiltInCategory, Transaction
from Autodesk.Revit.DB import ViewSchedule, ScheduleSortGroupField, ScheduleFilter
from Autodesk.Revit.DB import ScheduleSortOrder, ScheduleFilterType, SectionType
from Autodesk.Revit.DB import ViewSheet, ScheduleSheetInstance
from Autodesk.Revit.DB import DisplayUnitType, UnitUtils

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

TransactionManager.Instance.ForceCloseTransaction()

doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName


########################################################################################################################

def get_field(schedule, name):
    field = None
    definition = schedule.Definition
    count = definition.GetFieldCount()
    for idx in range(0, count, 1):
        if definition.GetField(idx).GetName() == name:
            field = definition.GetField(idx)
            count = idx
    return field, count


def get_schedule_parameters(doc, schedule):
    result = []
    definition = schedule.Definition
    for sch in definition.GetSchedulableFields():
        shared = doc.GetElement(sch.ParameterId)
        if isinstance(shared, SharedParameterElement):
            result.append(shared)
    return result


########################################################################################################################
categoryId = ElementId(BuiltInCategory.OST_Rooms)
########################################################################################################################
schedule_name = "ТЕХНИКО-ЭКОНОМИЧЕСКИЕ ПОКАЗАТЕЛИ(TEST)"
field_names = ['Позиция', 'Наименование', 'Ед.изм', 'Кол-во']
field_width = ['15', '120', '20', '30']
schedules = FilteredElementCollector(doc).OfClass(ViewSchedule).ToElements()
with Transaction(doc, "Create schedule") as trans:
    trans.Start()
    feet = DisplayUnitType.DUT_DECIMAL_FEET
    millimeter = DisplayUnitType.DUT_MILLIMETERS
    schedule = List[Element](filter(lambda x: x.Name == schedule_name, schedules)).FirstOrDefault()
    flag = (True if schedule and doc.Delete(schedule.Id) or schedule is None else False)
    schedule = ViewSchedule.CreateSchedule(doc, categoryId)
    schedule.Definition.ShowTitle = False
    schedule.Definition.ClearFields()
    schedule.Name = schedule_name
    trans.Commit()

with Transaction(doc, "Fill schedule") as trans:
    trans.Start()
    tableData = schedule.GetTableData()
    section = tableData.GetSectionData(SectionType.Header)
    rows, columns = section.NumberOfRows, section.NumberOfColumns
    section.ClearCell(section.FirstRowNumber, section.FirstColumnNumber)
    section.SetCellText(section.FirstRowNumber, section.FirstColumnNumber, schedule_name)
    section.SetRowHeight(section.FirstRowNumber, UnitUtils.Convert(15, millimeter, feet))
    [section.RemoveRow(row) for row in range(15) if 0 < row and section.CanRemoveRow(row)]
    [section.RemoveColumn(col) for col in range(15) if 0 < col and section.CanRemoveColumn(col)]
    rowHeader = section.FirstRowNumber + 1
    height = UnitUtils.Convert(15, millimeter, feet)
    if section.RefreshData(): section.InsertRow(rowHeader)
    if section.RefreshData(): section.SetRowHeight(rowHeader, height)
    for row, text in enumerate(field_names):
        if section.RefreshData():
            section.InsertColumn(row)
            section.SetCellText(rowHeader, row, text)
    for row, width in enumerate(field_width):
        if section.RefreshData():
            digit = UnitUtils.Convert(int(width), millimeter, feet)
            section.SetColumnWidth(row, digit)
    dataText, numDataRow = [], int(0)
    height = UnitUtils.Convert(8, millimeter, feet)
    dataText.append(['1', 'Класс жилья', 'Класс', ''])
    dataText.append(['1', 'Класс жилья', 'Класс', ''])
    dataText.append(['1', 'Класс жилья', 'Класс', ''])
    dataText.append(['1', 'Класс жилья', 'Класс', ''])
    dataText.append(['1', 'Класс жилья', 'Класс', ''])
    for row in range(len(dataText)):
        rowData = dataText[numDataRow]
        row += section.LastRowNumber
        if section.RefreshData():
            if section.CanInsertRow(row):
                section.InsertRow(row)
                section.SetRowHeight(row, height)
                numDataRow += 1
        for col, text in enumerate(rowData):
            if section.RefreshData():
                if section.CanRemoveRow(row):
                    if section.CanRemoveColumn(col):
                        section.SetCellText(row, col, text)
    section.RemoveColumn(section.LastColumnNumber)
    trans.Commit()
########################################################################################################################
OUT = schedule
########################################################################################################################
