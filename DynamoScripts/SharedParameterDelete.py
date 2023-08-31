# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import clr
import difflib
import System

clr.AddReference("System")
clr.AddReference("System.Core")
clr.AddReference("System.Drawing")
clr.AddReference("System.Management")
clr.ImportExtensions(System.Linq)

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import FilteredElementCollector
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB import SharedParameterElement

########################################################################################################################

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)
TransactionManager.Instance.ForceCloseTransaction()
########################################################################################################################
doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument

sharedParamName = IN[0]


def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    if defile and defile.Groups.Size > 0:
        for group in defile.Groups:
            if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
                definition = group.Definitions.Item[parameter_name]
                return definition


def remove_parameter(doc, definition):
    with Transaction(doc) as trans:
        try:
            trans.Start("Remove Parameter")
            parameter_name = definition.Name
            message = "\n\t{}: deleted successfully".format(parameter_name)
            if not doc.ParameterBindings.Remove(definition):
                if definition: doc.Delete(definition.Id)
            trans.Commit()
        except Exception as e:
            trans.RollBack()
            message = "\n\t{}: failed delete {}".format(parameter_name, e)
        return message


def remove_similar_shared_parameters(doc, sharedParamName):
    message, tolerance = '', 0.95
    definition = get_external_definition(doc, sharedParamName)
    parameters = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToElements()
    for param in sorted(parameters, key=lambda param: param.Name):
        weight = difflib.SequenceMatcher(None, sharedParamName, param.Name).ratio()
        if bool(weight > tolerance):
            if definition and definition.GUID == param.GuidValue: continue
            message += remove_parameter(doc, param.GetDefinition())
    return message


if (sharedParamName and isinstance(sharedParamName, str)):
    OUT = remove_similar_shared_parameters(doc, sharedParamName)
else:
    "Not defined parameter name"
