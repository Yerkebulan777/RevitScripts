# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import os
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
from Autodesk.Revit.DB import InstanceBinding, TypeBinding
from Autodesk.Revit.DB import BuiltInParameterGroup, ElementId, ExternalDefinition
from Autodesk.Revit.DB import BuiltInCategory, Category, CategoryType, Transaction
from Autodesk.Revit.DB import ParameterFilterUtilities, SharedParameterElement


def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    if defile and defile.Groups:
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


def remove_similar_shared_parameters(doc, parameter_name):
    message, tolerance = '', 0.85
    parameters = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToElements()
    definition = get_external_definition(doc, parameter_name)
    guid = definition.GUID if definition else None
    for param in sorted(parameters, key=lambda param: param.Name):
        weight = difflib.SequenceMatcher(None, parameter_name, param.Name).ratio()
        if bool(weight > tolerance):
            if guid != param.GuidValue:
                message += remove_parameter(doc, param.GetDefinition())
    return message
