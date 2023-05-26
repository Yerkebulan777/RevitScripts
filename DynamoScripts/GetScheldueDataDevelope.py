#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')

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


# def get_elements(active_view, value):
#     provider = ParameterValueProvider(ElementId(param))
#     filter_rule = FilterStringRule(provider, FilterStringEquals(), value, True)
#     filter = ElementParameterFilter(filter_rule)
#     elements = FilteredElementCollector(doc, active_view.Id).WherePasses(filter).ToElements()
#     return elements


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
            with Transaction(doc, "dummy") as t:
                t.Start()
                with  SubTransaction(doc) as st:
                    st.Start()
                    if section.CanRemoveRow(row_analyse):
                        section.RemoveRow(row_analyse)
                        section.RefreshData()
                    st.Commit()
                remaining = FilteredElementCollector(doc, schedule.Id).ToElementIds()
                t.RollBack()
            group = [doc.GetElement(id) for id in element_ids if id not in remaining]
            if any(group): result.append(group)

        # element = FilteredElementCollector(doc, schedule.Id).FirstElement()
        # collector = FilteredElementCollector(doc, schedule.Id)
        # for sort_group in definition.GetSortGroupFields():
        #     field = definition.GetField(sort_group.FieldId)
        #     param = element.LookupParameter(field.GetName())
        #     # if field.ParameterId < -1: param = element.get_Parameter(BuiltInParameter(field.ParameterId.IntegerValue))
        #     # if field.ParameterId > 0:  param = doc.GetElement(field.ParameterId)
        #     column = definition.GetFieldIndex(sort_group.FieldId)
        #     values = [schedule.GetCellText(SectionType.Body, row, column) for row in range(num_rows) if row != 0]
        #     for value in values:
        #         if (param.StorageType == StorageType.Integer):
        #             filter_rule = ParameterFilterRuleFactory.CreateEqualsRule(param.AsElementId(), int(value))
        #             collector = collector.WherePasses(ElementParameterFilter(filter_rule))
        #         elif (param.StorageType == StorageType.Double):
        #             filter_rule = ParameterFilterRuleFactory.CreateEqualsRule(param.AsElementId(), float(value), 1e-5)
        #             collector = collector.WherePasses(ElementParameterFilter(filter_rule))
        #         elif (param.StorageType == StorageType.String):
        #             filter_rule = ParameterFilterRuleFactory.CreateEqualsRule(param.AsElementId(), value, True)
        #             collector = collector.WherePasses(ElementParameterFilter(filter_rule))
        #         elif (param.StorageType == StorageType.ElementId):
        #             elements = [elem for elem in param][0]
        #     elements = collector.ToElements()
        #     result.append(elements)

########################################################################################################################
OUT = result
########################################################################################################################
