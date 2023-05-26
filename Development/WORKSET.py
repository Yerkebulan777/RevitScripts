# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r'D:\TEMP')
sys.setdefaultencoding('utf-8')

import clr

clr.AddReference("System")
clr.AddReference("System.Core")
clr.AddReference("System.Drawing")
clr.AddReference("System.Management")

import System

clr.ImportExtensions(System.Linq)
from System.Collections.Generic import List

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import FilteredWorksetCollector, WorksetKind
from Autodesk.Revit.DB import ElementId, BuiltInParameter, Transaction, SubTransaction
from Autodesk.Revit.DB import FilterRule, ParameterFilterUtilities, ParameterFilterRuleFactory, ParameterFilterElement

# clr.AddReference('RevitAPIIFC')

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI import TaskDialog

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName

TransactionManager.Instance.ForceCloseTransaction()


def Output(output):
    if isinstance(output, basestring):
        TaskDialog.Show("OUTPUT", output)
        return


def get_field(schedule, name):
    field = None
    definition = schedule.Definition
    count = definition.GetFieldCount()
    for i in range(0, count, 1):
        if definition.GetField(i).GetName() == name:
            field = definition.GetField(i)
    return field


########################################################################################################################

def viewfilter_by_workset(view, filter_name, value):
    rules, value = List[FilterRule](), value.lower()
    wsparamId = ElementId(BuiltInParameter.ELEM_PARTITION_PARAM)
    categories = ParameterFilterUtilities.GetAllFilterableCategories()
    worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets()
    for count, workset in enumerate(worksets):
        if value in workset.Name.lower():
            rules.Add(ParameterFilterRuleFactory.CreateContainsRule(wsparamId, workset.Name, False))
            with Transaction(doc, "CreateViewFilter") as trans:
                trans.Start()
                filter = ParameterFilterElement.Create(doc, filter_name, categories, rules)
                with SubTransaction(doc) as sut:
                    sut.Start()
                    view.AddFilter(filter.Id)
                    sut.Commit()
                with SubTransaction(doc) as sut:
                    sut.Start()
                    view.SetFilterVisibility(filter.Id, False)
                    sut.Commit()
                trans.Commit()
            return value


########################################################################################################################
view = doc.ActiveView
result = viewfilter_by_workset(view, "Test", "KR")
#######################################################################################################################
OUT = result
#######################################################################################################################
