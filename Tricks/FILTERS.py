#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import clr

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
import difflib

clr.AddReference("System")
clr.AddReference("System.Core")
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference('RevitAPIIFC')

from Autodesk.Revit.DB import *
# from Autodesk.Revit.DB.Structure import *
# from Autodesk.Revit.DB.IFC import ExporterIFCUtils
# from Autodesk.Revit.UI.Selection import ObjectType
# from Autodesk.Revit.ApplicationServices import *
# from Autodesk.Revit.Attributes import *
# from Autodesk.Revit.UI import *
from System.Collections.Generic import List

"""
import revit_script_util
from revit_script_util import Output

sessionId = revit_script_util.GetSessionId()
uiapp = revit_script_util.GetUIApplication()

doc = revit_script_util.GetScriptDocument()
revitFilePath = revit_script_util.GetRevitFilePath()
"""

clr.AddReference('RevitNodes')
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument

TransactionManager.Instance.ForceCloseTransaction()

toList = lambda x: x if hasattr(x, "__iter__") else [x]

# viewsSchedule = toList(UnwrapElement(IN[0]))

def parameter_by_name(element, mark_name):
    mark_name = mark_name.lower()
    parameter = tolerance = None
    for param in element.Parameters:
        param_name = param.Definition.Name
        param_name = param_name.lower()
        matcher = difflib.SequenceMatcher(None, mark_name, param_name).ratio()
        if tolerance < matcher:
            tolerance = matcher
            parameter = param
    return parameter


def set_workset(workset_name, elements):
    workset_table = doc.GetWorksetTable()
    if workset_table:
        if workset_table.IsWorksetNameUnique(doc, workset_name):
            workset = Workset.Create(doc, workset_name)
            doc.Regenerate()
        for workset in FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets():
            name = workset.Name
            if workset.IsEditable and name == workset_name:
                workset_id = workset.Id.IntegerValue
                for element in elements:
                    wsparam = element.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM)
                    wsparam.Set(workset_id)
                return


def delete_elements(elements):
    elementIds = List[ElementId]([elem.Id for elem in elements])
    return doc.Delete(elementIds)


def SetVisibleWorksetInView(view):
    defaultVisibility = WorksetDefaultVisibilitySettings.GetWorksetDefaultVisibilitySettings(doc)
    worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets()
    for workset in worksets:
        worksid = WorksetId(workset.Id.IntegerValue)
        visibility = view.GetWorksetVisibility(worksid)
        if not defaultVisibility.IsWorksetVisible(worksid):
            defaultVisibility.SetWorksetVisibility(worksid, True)
        if (visibility == WorksetVisibility.Hidden):
            view.SetWorksetVisibility(worksid, WorksetVisibility.Visible)
    return



def add_schedule_filter(scheduleObj, schedule_field, filter_value):
    scheduleFilterType = DB.ScheduleFilterType.NotContains
    with Transaction(doc, "AddFilter") as trx:
        trx.Start()
        definition = scheduleObj.Definition
        scheduleField = None
        ids = definition.GetFieldOrder()
        for id in ids:
            param = definition.GetField(id)
            if param.GetName() == schedule_field:
                scheduleField = param.FieldId
        filter = DB.ScheduleFilter(scheduleField, scheduleFilterType, filter_value)
        definition.AddFilter(filter)
        trx.Commit()
    return


def create_ViewFilter_by_workset(view, filter_name, filter_value):
    rules = List[FilterRule]()
    wsparamId = ElementId(BuiltInParameter.ELEM_PARTITION_PARAM)
    categories = ParameterFilterUtilities.GetAllFilterableCategories()
    rules.Add(ParameterFilterRuleFactory.CreateEqualsRule(wsparamId, filter_value))
    filter = ParameterFilterElement.Create(doc, filter_name, categories, rules)
    with Transaction(doc, "CreateFilter") as trans:
        trans.Start()
        view.AddFilter(filter.Id)
        trans.Commit()
    with Transaction(doc, "SetVisibility") as trans:
        trans.Start()
        view.SetFilterVisibility(filter.Id, False)
        trans.Commit()
    return


view = doc.ActiveView
with Transaction(doc, "SetVisibleWorksetInView") as trx:
    trx.Start()
    SetVisibleWorksetInView(view)
    doc.Regenerate()
    trx.Commit()
OUT = 0

if doc.IsWorkshared:
    all_worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksetIds()
    edt_worksets = WorksharingUtils.CheckoutWorksets(doc, all_worksets)
    borrowers = set(all_worksets).difference(edt_worksets)
    if len(borrowers):
        Output("Not owner worksets counts = {}".format(len(borrowers)))
        Output("\t\n\t{} workset is borrower".format(doc.GetElement(id).Name) for id in borrowers)