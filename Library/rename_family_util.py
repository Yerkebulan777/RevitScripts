#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

reload(sys)
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")

import re
import clr

clr.AddReference("System")
clr.AddReference("System.Core")

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import ElementId, ElementType, ParameterFilterUtilities
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Category
from Autodesk.Revit.DB import ElementParameterFilter, ParameterValueProvider, FilterStringRule, FilterStringEquals


########################################################################################################################

def get_name_with_prefix(string, prefix=""):
    regex = re.compile(r"^(\(.*\))|^(\w*\s*\(.*\))")
    charts = re.compile(r"([+*^#%!?@$&£\\\[\]{}/|;:<>`~]*)")
    outline = string[:50].encode('cp1251', 'ignore').decode('cp1251')
    outline = re.sub(prefix, '', outline, re.VERBOSE | re.IGNORECASE)
    outline = charts.sub('', outline, re.IGNORECASE).rstrip('_')
    outline = regex.sub('', outline, re.IGNORECASE).strip()
    outline = "{}{}".format(prefix, outline)
    return outline


def rename_element_type(doc, item, name):
    if item.GetType().ToString() == "Autodesk.Revit.DB.FamilyParameter":
        try:
            doc.FamilyManager.RenameParameter(item, name)
            return name
        except:
            return
    elif item.GetType().ToString() == "Autodesk.Revit.DB.Workset":
        try:
            doc.GetWorksetTable().RenameWorkset(doc, item.Id, name)
            return name
        except:
            return


def rename_prefix_family_type(doc, element_type, prefix):
    if element_type and isinstance(element_type, ElementType):
        source_name = element_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        target_name = get_name_with_prefix(source_name, prefix)
        return rename_element_type(doc, element_type, target_name)


def set_model_group_name_by_category(doc, element_type, category_name, group_name):
    if element_type and isinstance(element_type, ElementType):
        if re.search(element_type.Category.Name, category_name, re.IGNORECASE):
            element = doc.GetElement(ElementId(element_type.Id.IntegerValue))
            param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MODEL)
            if param and not param.IsReadOnly: return param.Set(group_name)


def get_builtInCategory_by_category_name(doc, category_name):
    for catId in ParameterFilterUtilities.GetAllFilterableCategories():
        cat_name = Category.GetCategory(doc, catId).Name
        if re.search(cat_name, category_name, re.IGNORECASE):
            return BuiltInCategory.Enum.Parse(BuiltInCategory, catId)


def get_instances_by_type_name(doc, type_name):
    provider = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_TYPE_NAME))
    filter00 = ElementParameterFilter(FilterStringRule(provider, FilterStringEquals(), type_name, False))
    collector = FilteredElementCollector(doc).WherePasses(filter00).WhereElementIsViewIndependent()
    return collector.WhereElementIsNotElementType().ToElements()


########################################################################################################################
def rename_family_types_by_category(doc, category_name, group_name, prefix):
    builtInCat = get_builtInCategory_by_category_name(doc, category_name)
    for element_type in FilteredElementCollector(doc).OfCategory(builtInCat).WhereElementIsElementType().ToElements():
        result = set_model_group_name_by_category(doc, element_type, category_name, group_name)
        element_type_name = rename_prefix_family_type(doc, element_type, prefix)
        if result and element_type_name: return element_type_name
########################################################################################################################
