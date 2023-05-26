# -*- coding: UTF-8 -*-
# This section is common to all Python task scripts.
import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import os
import clr

clr.AddReference("System")
clr.AddReference("System.Core")

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import Transaction, Element
from Autodesk.Revit.DB import SharedParameterElement
from Autodesk.Revit.DB import ExternalDefinition, InternalDefinition
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter, BuiltInCategory
from Autodesk.Revit.DB import FilterNumericEquals, ParameterValueProvider, FilterDoubleRule
from Autodesk.Revit.DB import ElementId, ElementParameterFilter
from Autodesk.Revit.DB.Structure import RebarBarType

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName

TransactionManager.Instance.ForceCloseTransaction()


########################################################################################################################


def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    for group in defile.Groups:
        if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
            definition = group.Definitions.Item[parameter_name]
            return definition


def load_shared_parameter_file(doc, filepath):
    if os.path.exists(filepath):
        doc.Application.SharedParametersFilename = filepath
        filepath = doc.Application.SharedParametersFilename
        return filepath


def get_shared_parameter(doc, parameter_name):
    external = get_external_definition(doc, parameter_name)
    if external and external.IsValidObject:
        parameter = SharedParameterElement.Lookup(doc, external.GUID)
        if isinstance(parameter, SharedParameterElement): return parameter


def create_categorySet(doc, builtInCat):
    categories = doc.Application.Create.NewCategorySet()
    category = doc.Settings.Categories.get_Item(builtInCat)
    categories.Insert(category)
    return categories


def change_shared_parameter_type(doc, filepath, parameter_name, categories, instance=True):
    message = "Not defined {}".format(parameter_name)
    if load_shared_parameter_file(doc, filepath):
        external = get_external_definition(doc, parameter_name)
        if isinstance(external, ExternalDefinition):
            parameter = SharedParameterElement.Lookup(doc, external.GUID)
            if isinstance(parameter, SharedParameterElement):
                with Transaction(doc, "Set rebar quotient") as trans:
                    trans.Start()
                    bindMap = doc.ParameterBindings
                    definition = parameter.GetDefinition()
                    if isinstance(definition, InternalDefinition):
                        param_name = definition.Name
                        param_group = definition.ParameterGroup
                        message = "\nFailed change type {}".format(param_name)
                        if (instance == True and categories.Size):
                            binding = doc.Application.Create.NewInstanceBinding(categories)
                            if bindMap.ReInsert(external, binding, param_group):
                                message = "\nSuccessfully change to instance parameter"
                        if (instance == False and categories.Size):
                            binding = doc.Application.Create.NewTypeBinding(categories)
                            if bindMap.ReInsert(external, binding, param_group):
                                message = "\nSuccessfully change to type parameter"
                    trans.Commit()
    return message


def get_rebar_type_by_diameter(doc, diameter):
    provider_diameter = ParameterValueProvider(ElementId(BuiltInParameter.REBAR_BAR_DIAMETER))
    diameter_rule = FilterDoubleRule(provider_diameter, FilterNumericEquals(), float(diameter / 304.8), 0.005)
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rebar).OfClass(RebarBarType)
    rebar_types = collector.WherePasses(ElementParameterFilter(diameter_rule)).ToElements()
    return rebar_types


def get_value_by_diameter(diameter, quotient=None):
    if diameter == 6:
        quotient = 1.06

    elif diameter == 8:
        quotient = 1.07

    elif diameter == 10:
        quotient = 1.08

    elif diameter == 12:
        quotient = 1.1

    elif diameter == 14:
        quotient = 1.12

    elif diameter == 16:
        quotient = 1.14

    elif diameter == 18:
        quotient = 1.15

    elif diameter == 20:
        quotient = 1.17

    elif diameter == 22:
        quotient = 1.19

    elif diameter == 25:
        quotient = 1.21

    elif diameter == 28:
        quotient = 1.24

    elif diameter == 32:
        quotient = 1.27

    return quotient


def set_rebar_quotient(doc, parameter_name):
    message = "\nNot defined {}".format(parameter_name)
    spr_quotient = get_shared_parameter(doc, parameter_name)
    flag = bool(isinstance(spr_quotient, SharedParameterElement))
    message = ("\nDefined {}\n".format(parameter_name) if flag else message)
    guid_quotient = (spr_quotient.GuidValue if flag else None)
    with Transaction(doc, "Set rebar quotient") as trans:
        trans.Start()
        for diameter in range(2, 36, 2):
            quotient = None
            diameter = (diameter if diameter != 24 else 25)
            rebar_types = get_rebar_type_by_diameter(doc, diameter)
            if len(rebar_types): quotient = get_value_by_diameter(diameter)
            if len(rebar_types) and not quotient:
                message += "\nQuotient not defined for {} diameter".format(diameter)
            for idx, rbt in enumerate(rebar_types):
                param_quotient = rbt.get_Parameter(guid_quotient)
                if quotient and param_quotient:
                    symbol_name = Element.Name.GetValue(rbt)
                    if param_quotient.IsReadOnly:
                        message += "\nParameter read only for {}".format(symbol_name)
                    elif not param_quotient.IsReadOnly and param_quotient.Set(quotient):
                        message += "\nSet Value {} in {}".format(quotient, symbol_name)
                    elif not param_quotient.IsReadOnly and not param_quotient.Set(quotient):
                        message += "\nFailed set value to {}".format(symbol_name)
        trans.Commit()
    return message


########################################################################################################################
categories = create_categorySet(doc, BuiltInCategory.OST_Rebar)
parameter_name, filepath, instance = "BI_коэф_нахлеста_арматуры", IN[0], False
message = change_shared_parameter_type(doc, filepath, parameter_name, categories, instance)
message += "\n{}".format(set_rebar_quotient(doc, parameter_name))
OUT = message
########################################################################################################################
