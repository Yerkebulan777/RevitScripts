# -*- coding: UTF-8 -*-
# This section is common to all Python task scripts.

import sys

import clr

sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import FilteredElementCollector, Transaction, SubTransaction
from Autodesk.Revit.DB import SectionType, ViewSchedule
from Autodesk.Revit.DB import SharedParameterElement

from System.IO import *
from System.Linq import *

#########################################################################################
#########################################################################################

def get_schedule_data(doc, schedule):
    result = []
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
        if any(items): result.append(items)

    return result

#########################################################################################
