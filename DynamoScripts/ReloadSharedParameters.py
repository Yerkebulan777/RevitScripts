# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r'D:\TEMP')
sys.setdefaultencoding('utf-8')

import os
import clr

clr.AddReference("System")
clr.AddReference("System.Core")
clr.AddReference("System.Drawing")
clr.AddReference("System.Management")

import System

clr.ImportExtensions(System.Linq)

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, CategoryType
from Autodesk.Revit.DB import ElementParameterFilter, SharedParameterApplicableRule
from Autodesk.Revit.DB import SharedParameterElement, BuiltInParameterGroup
from Autodesk.Revit.DB import InstanceBinding, TypeBinding
from Autodesk.Revit.DB import ViewSchedule
from Autodesk.Revit.DB import FamilySymbol

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

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


def load_shared_parameter_file(doc, path):
    app = doc.Application
    app.SharedParametersFilename = path
    return app.OpenSharedParameterFile()


def get_schedule_shared_parameters(doc):
    spr_params, spr_names = [], []
    view_schedules = FilteredElementCollector(doc).OfClass(ViewSchedule).ToElements()
    for schedule in view_schedules:
        parameters = schedule.GetOrderedParameters()
        for param in parameters:
            spr_element = doc.GetElement(param.Id)
            if isinstance(spr_element, SharedParameterElement):
                spr_names.append(spr_element.Name)
                spr_params.append(spr_element)
    return spr_params, spr_names


def get_symbols_by_shared_parameter(doc, parameter_name):
    shared_filter = ElementParameterFilter(SharedParameterApplicableRule(parameter_name))
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).WherePasses(shared_filter)
    symbols = collector.WhereElementIsElementType().ToElements()
    return symbols


def get_external_definition(doc, parameter_name):
    app = doc.Application
    defile = app.OpenSharedParameterFile()
    for group in defile.Groups:
        if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
            definition = group.Definitions.Item[parameter_name]
            return definition


def get_bip_group(parameter_group='PG_GENERAL'):
    group = System.Enum.Parse(BuiltInParameterGroup, parameter_group)
    return group


def create_category_set(doc, category_ids=None):
    results = []
    app = doc.Application
    categories = doc.Settings.Categories
    category_set = app.Create.NewCategorySet()
    for category in categories:
        if category.AllowsBoundParameters:
            category_id = category.Id.IntegerValue
            category_name = category.Name
            if category_ids is None:
                if category.CategoryType.Equals(CategoryType.Model) and category.SubCategories.Size > 0:
                    if category_name.endswith('dwg'): continue
                    try:
                        builtIn_category = System.Enum.ToObject(BuiltInCategory, category_id)
                        category_set.Insert(doc.Settings.Categories.get_Item(builtIn_category))
                    except:
                        pass
                    else:
                        message = "{} (ID = {}) add to category set".format(category_name, category_id)
                        results.append(message)

            elif str(category_id) in category_ids:
                try:
                    builtIn_category = System.Enum.ToObject(BuiltInCategory, category_id)
                    category_set.Insert(doc.Settings.Categories.get_Item(builtIn_category))
                except Exception as e:
                    message = category_name + " : Failed category with exception: " + str(e)
                    results.append(message)
                else:
                    message = "{} (ID = {}) add to category set".format(category_name, category_id)
                    results.append(message)

    return category_set, results


def reinsert_shared_parameter(doc, definition, category_set, parameter_group, is_instance=True):
    if (is_instance):
        binding_cats = doc.Application.Create.NewInstanceBinding(category_set)
    else:
        binding_cats = doc.Application.Create.NewTypeBinding(category_set)
    parameter_name = definition.Name
    try:
        if (doc.ParameterBindings.Insert(definition, binding_cats, parameter_group)):
            message = parameter_name + " : parameter successfully bound"
            return message
        else:
            if (doc.ParameterBindings.ReInsert(definition, binding_cats, parameter_group)):
                message = parameter_name + " : parameter successfully bound"
                return message
            else:
                message = parameter_name + " : failed to bind parameter!"
    except Exception as e:
        message = parameter_name + " : Failed to bind parameter with exception: " + str(e)
    return message


def remove_parameter_binding(doc, parameter_name):
    map = doc.ParameterBindings
    iterator = map.ForwardIterator()
    iterator.Reset()
    while iterator.MoveNext():
        if iterator.Key.Name == parameter_name:
            definition = iterator.Key
            map.Remove(definition)
            message = "Success"
            return message


def reset_shared_parameter(doc, parameter_name, category_ids=None, parameter_group='PG_GENERAL', instance=True):
    category_set, category_names = create_category_set(doc, category_ids)
    definition = get_external_definition(doc, parameter_name)
    bip_group = get_bip_group(parameter_group)
    message = reinsert_shared_parameter(definition, category_set, bip_group, instance)
    return message


def reload_similar_shared_parameter(doc, parameter_name):
    source_definition = get_external_definition(doc, parameter_name)
    binding_map = doc.ParameterBindings
    iterator = binding_map.ForwardIterator()
    iterator.Reset()
    parameter_name.lower()
    while iterator.MoveNext():
        instance = None
        definition = iterator.Key
        if (definition.IsValidObject):
            name = definition.Name.lower()
            if (parameter_name == name):
                bind = iterator.Current
                group = definition.ParameterGroup
                categories = binding_map.Item[definition].Categories
                if isinstance(bind, InstanceBinding): instance = True
                if isinstance(bind, TypeBinding): instance = False
                return reinsert_shared_parameter(doc, source_definition, categories, group, instance)


########################################################################################################################
if os.path.exists(IN[0]): defile = load_shared_parameter_file(doc, os.path.realpath(IN[0]))
########################################################################################################################
########################################################################################################################
results = []
categories = []
########################################################################################################################
category_set, category_names = create_category_set(doc)
definition = get_external_definition(doc, "BI_обозначение")
bip_group = get_bip_group("PG_IDENTITY_DATA")
instance = True
result = reinsert_shared_parameter(doc, definition, category_set, bip_group, instance)
categories.append(category_names)
results.append(result)
########################################################################################################################
category_set, category_names = create_category_set(doc)
definition = get_external_definition(doc, "BI_наименование")
bip_group = get_bip_group("PG_IDENTITY_DATA")
instance = True
result = reinsert_shared_parameter(doc, definition, category_set, bip_group, instance)
categories.append(category_names)
results.append(result)
########################################################################################################################
category_set, category_names = create_category_set(doc)
definition = get_external_definition(doc, "BI_этаж")
bip_group = get_bip_group("PG_GENERAL")
instance = True
result = reinsert_shared_parameter(doc, definition, category_set, bip_group, instance)
categories.append(category_names)
results.append(result)
########################################################################################################################
category_set, category_names = create_category_set(doc, ['-2009000'])
definition = get_external_definition(doc, "BI_диаметр_арматуры")
bip_group = get_bip_group("PG_GEOMETRY")
instance = False
result = reinsert_shared_parameter(doc, definition, category_set, bip_group, instance)
categories.append(category_names)
results.append(result)
########################################################################################################################
category_set, category_names = create_category_set(doc, ['-2009000', '-2001320'])
definition = get_external_definition(doc, "BI_длина")
bip_group = get_bip_group("PG_GEOMETRY")
instance = True
result = reinsert_shared_parameter(doc, definition, category_set, bip_group, instance)
categories.append(category_names)
results.append(result)
########################################################################################################################
########################################################################################################################
OUT = result, category_names
########################################################################################################################
