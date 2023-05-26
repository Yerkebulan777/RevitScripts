# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")

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


def load_shared_parameter_file(doc, filepath):
    if os.path.exists(filepath):
        doc.Application.SharedParametersFilename = filepath
        filepath = doc.Application.SharedParametersFilename
        return filepath


def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    for group in defile.Groups:
        if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
            definition = group.Definitions.Item[parameter_name]
            return definition


def remove_parameter(doc, definition):
    with Transaction(doc, "Remove Parameter") as trans:
        try:
            trans.Start()
            parameter_name = definition.Name
            message = "\n\t{}: deleted successfully".format(parameter_name)
            if not doc.ParameterBindings.Remove(definition):
                if definition and definition.IsValidObject:
                    doc.Delete(definition.Id)
            trans.Commit()
        except Exception as e:
            message = "\n\t{}: failed delete {}".format(parameter_name, e)
            trans.RollBack()
        return message


def remove_similar_shared_parameters(doc, parameter_name):
    message, filepath, tolerance = '', None, 0.85
    parameters = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToElements()
    if parameter_name.startswith("BI"): filepath = r"D:\YandexDisk\RevitExportConfig\DataBase\BI_FOP.txt"
    if parameter_name.startswith("TMS"): filepath = r"D:\YandexDisk\RevitExportConfig\DataBase\TMS_FOP.txt"
    if filepath and load_shared_parameter_file(doc, filepath):
        definition = get_external_definition(doc, parameter_name)
        guid = definition.GUID if definition else None
        for param in sorted(parameters, key=lambda param: param.Name):
            weight = difflib.SequenceMatcher(None, parameter_name, param.Name).ratio()
            if bool(weight > tolerance):
                if guid != param.GuidValue:
                    message += remove_parameter(doc, param.GetDefinition())
    return message


def get_internal_parameter(doc, parameter_name):
    external = get_external_definition(doc, parameter_name)
    parameter = SharedParameterElement.Lookup(doc, external.GUID)
    return parameter


def get_parameter_group(parameter_group='PG_GENERAL'):
    group = System.Enum.Parse(BuiltInParameterGroup, parameter_group)
    return group


def get_parameter_by_name(element, param_name, tolerance=0, result=None):
    for param in element.GetParameters(param_name):
        weight = difflib.SequenceMatcher(None, param_name, param.Name).ratio()
        if (weight > tolerance):
            tolerance = weight
            result = param
    return result


def create_category_set(doc, categoryIds=None):
    categorySet = doc.Application.Create.NewCategorySet()
    for cid in ParameterFilterUtilities.GetAllFilterableCategories():
        category = Category.GetCategory(doc, ElementId(cid.IntegerValue))
        if category and category.CategoryType == CategoryType.Model:
            if category.AllowsBoundParameters and category.CanAddSubcategory:
                categoryIdint = category.Id.IntegerValue
                if categoryIds and str(categoryIdint) in categoryIds:
                    builtInCategory = System.Enum.ToObject(BuiltInCategory, categoryIdint)
                    categorySet.Insert(doc.Settings.Categories.get_Item(builtInCategory))
                if not categoryIds and bool(category.HasMaterialQuantities or category.IsCuttable):
                    builtInCategory = System.Enum.ToObject(BuiltInCategory, categoryIdint)
                    categorySet.Insert(doc.Settings.Categories.get_Item(builtInCategory))
    return categorySet


def reinsert_shared_parameter(doc, definition, parameter_group, category_set, is_instance=True):
    binding_cats = doc.Application.Create.NewInstanceBinding(category_set)
    if not is_instance: binding_cats = doc.Application.Create.NewTypeBinding(category_set)
    with Transaction(doc, "Reset Parameter") as trans:
        parameter_name = definition.Name
        map = doc.ParameterBindings
        try:
            trans.Start()
            if map.Contains(definition):
                if map.ReInsert(definition, binding_cats, parameter_group):
                    message = "\n\t{}: successfully reinsert".format(parameter_name)
            if not map.Contains(definition):
                if map.Insert(definition, binding_cats, parameter_group):
                    message = "\n\t{}: successfully insert".format(parameter_name)
            trans.Commit()
        except Exception as e:
            message = "\n\t{}: failed to bind {}".format(parameter_name, e)
            trans.RollBack()
    return message


########################################################################################################################
# filepath = "D:\YandexDisk\RevitExportConfig\DataBase\BI_FOP.txt"
########################################################################################################################
def change_shared_parameter_type(doc, filepath, parameter_name, instance=True):
    message = "Not defined {}".format(parameter_name)
    if load_shared_parameter_file(doc, filepath):
        external = get_external_definition(doc, parameter_name)
        if isinstance(external, ExternalDefinition):
            parameter = SharedParameterElement.Lookup(doc, external.GUID)
            if isinstance(parameter, SharedParameterElement):
                definition = parameter.GetDefinition()
                map = doc.ParameterBindings
                bind = map.Item[definition]
                param_group = definition.ParameterGroup
                if (instance and isinstance(bind, TypeBinding)):
                    binding = doc.Application.Create.NewInstanceBinding(bind.Categories)
                    if map.ReInsert(definition, binding, param_group):
                        message = "\n\t{}: successfully change to instance parameter"
                elif (not instance and isinstance(bind, InstanceBinding)):
                    binding = doc.Application.Create.NewTypeBinding(bind.Categories)
                    if map.ReInsert(definition, binding, param_group):
                        message = "\n\t{}: successfully change to type parameter"
    return parameter_name, message


def reset_shared_parameter(doc, filepath, parameter_name, param_group='PG_GENERAL', categoryIds=None, instance=True):
    message = "Not defined {}".format(parameter_name)
    if load_shared_parameter_file(doc, filepath):
        external = get_external_definition(doc, parameter_name)
        if isinstance(external, ExternalDefinition):
            bip_group = get_parameter_group(param_group)
            cat_set = create_category_set(doc, categoryIds)
            message = reinsert_shared_parameter(doc, external, bip_group, cat_set, instance)
    return message


def get_shared_parameter(doc, filepath, parameter_name, param_group='PG_GENERAL', categoryIds=None, instance=True):
    message = reset_shared_parameter(doc, filepath, parameter_name, param_group, categoryIds, instance)
    message += remove_similar_shared_parameters(doc, parameter_name)
    parameter = get_internal_parameter(doc, parameter_name)
    return parameter, message

########################################################################################################################
