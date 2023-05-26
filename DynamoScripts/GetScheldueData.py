#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')
reload(sys)

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import FilteredElementCollector, Transaction, SubTransaction
from Autodesk.Revit.DB import SectionType, ViewType

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

TransactionManager.Instance.ForceCloseTransaction()

doc = DocumentManager.Instance.CurrentDBDocument


# app = DocumentManager.Instance.CurrentUIApplication.Application
# uiapp = DocumentManager.Instance.CurrentUIApplication
# uidoc = uiapp.ActiveUIDocument
# revit_file_path = doc.PathName


def get_field(schedule, name):
    field = None
    definition = schedule.Definition
    count = definition.GetFieldCount()
    for i in range(0, count, 1):
        if definition.GetField(i).GetName() == name:
            field = definition.GetField(i)
    return field


########################################################################################################################
head_name = str(IN[0]).strip()
########################################################################################################################

result = []
schedule_data = []
schedule = doc.ActiveView
if schedule.ViewType == ViewType.Schedule:
    definition = schedule.Definition
    table = schedule.GetTableData()
    section = table.GetSectionData(SectionType.Body)
    headings = [definition.GetField(id).GetName() for id in definition.GetFieldOrder()]
    num_rows, num_columns = section.NumberOfRows, section.NumberOfColumns
    if bool(head_name) and head_name in headings:
        if (num_rows > 1):
            for row in range(num_rows):
                row_data = [schedule.GetCellText(SectionType.Body, row, column) for column in range(num_columns)]
                schedule_data.append(row_data)
            schedule_data.pop(0)  # remove headings in data values
        idx = headings.index(head_name)
        result = [data[idx] for data in schedule_data if bool(data[idx])]
    else:
        element_ids = FilteredElementCollector(doc, schedule.Id).ToElementIds()
        for row_analyse in range(num_rows):
            with Transaction(doc, "dummy") as trans:
                trans.Start()
                with  SubTransaction(doc) as subtr:
                    subtr.Start()
                    if section.CanRemoveRow(row_analyse):
                        section.RemoveRow(row_analyse)
                        section.RefreshData()
                    subtr.Commit()
                remaining = FilteredElementCollector(doc, schedule.Id).ToElementIds()
                trans.RollBack()
            group = [doc.GetElement(id) for id in element_ids if id not in remaining]
            if any(group): result.append(group)

########################################################################################################################
OUT = result
########################################################################################################################
