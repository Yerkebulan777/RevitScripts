#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")

import re
import clr

clr.AddReference('RevitAPI')
# from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import ElementId, SharedParameterElement, ElementType, StorageType
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter, UnitUtils, DisplayUnitType
from Autodesk.Revit.DB import SharedParameterApplicableRule, ElementParameterFilter, LogicalOrFilter
from Autodesk.Revit.DB import ParameterValueProvider, FilterStringRule, FilterStringEquals

clr.AddReference("System")
clr.AddReference("System.Core")

########################################################################################################################
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

TransactionManager.Instance.ForceCloseTransaction()

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName


########################################################################################################################
def get_external_definition(doc, parameter_name):
    defile = doc.Application.OpenSharedParameterFile()
    for group in defile.Groups:
        if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
            definition = group.Definitions.Item[parameter_name]
            return definition


def get_internal_guid_by_name(doc, parameter_name):
    external = get_external_definition(doc, parameter_name)
    if bool(external and SharedParameterElement.Lookup(doc, external.GUID)):
        return external.GUID


def strip_illegal_characters(string, length=75, username=""):
    charts = re.compile(r"([+*^#%!?@$&£\\\[\]{}/|;:<>`~]*)")
    outline = string[:length].encode('cp1251', 'ignore').decode('cp1251')
    outline = charts.sub('', outline, re.IGNORECASE).strip()
    outline = outline.strip(username).rstrip('_').strip()
    return outline


def get_element_type_by_name(doc, type_name):
    pvp01 = ParameterValueProvider(ElementId(BuiltInParameter.ELEM_TYPE_PARAM))
    pvp02 = ParameterValueProvider(ElementId(BuiltInParameter.SYMBOL_NAME_PARAM))
    pvp03 = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_FAMILY_NAME))
    filter01 = ElementParameterFilter(FilterStringRule(pvp01, FilterStringEquals(), type_name, False))
    filter02 = ElementParameterFilter(FilterStringRule(pvp02, FilterStringEquals(), type_name, False))
    filter03 = ElementParameterFilter(FilterStringRule(pvp03, FilterStringEquals(), type_name, False))
    logic_filter = LogicalOrFilter(LogicalOrFilter(filter01, filter02), filter03)
    collector = FilteredElementCollector(doc).WherePasses(logic_filter)
    result = collector.WhereElementIsElementType().FirstElement()
    return result


def set_parameter_value_by_guid(doc, guid, item, value):
    if guid and item is not None:
        if isinstance(item, ElementId): item = doc.GetElement(item)
        if item.GroupId.Equals(ElementId.InvalidElementId):
            param, result = item.get_Parameter(guid), None
            if param is None: return "Parameter not defined"
            if param.IsReadOnly: return "Parameter read only"
            if param.StorageType == StorageType.String:
                value = (value if isinstance(value, basestring) else str(value))
                result = param.Set(value)
            elif param.StorageType == StorageType.Double:
                value = (value if isinstance(value, float) else float(value))
                result = param.Set(value)
            elif param.StorageType == StorageType.Integer:
                value = (value if isinstance(value, int) else int(value))
                result = param.Set(value)
            return result


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


def get_instances_by_type_name(doc, type_name):
    provider = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_TYPE_NAME))
    filter00 = ElementParameterFilter(FilterStringRule(provider, FilterStringEquals(), type_name, False))
    collector = FilteredElementCollector(doc).WherePasses(filter00).WhereElementIsViewIndependent()
    return collector.WhereElementIsNotElementType().ToElements()


def set_model_group(doc, element_type, name=""):
    if isinstance(element_type, ElementType) and isinstance(name, basestring):
        element = doc.GetElement(ElementId(element_type.Id.IntegerValue))
        param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MODEL)
        if param and not param.IsReadOnly: return param.Set(name)


def rename_model_group_by_category(element_type):
    category_name = element_type.Category.Name
    if isinstance(category_name, basestring):
        if re.search("Трубы для прокладки кабеля", category_name, re.IGNORECASE):
            return set_model_group(doc, element_type, "Трубы для прокладки кабеля")
        if re.search("Осветительные приборы", category_name, re.IGNORECASE):
            return set_model_group(doc, element_type, "Осветительные приборы")
        if re.search("Электрооборудование", category_name, re.IGNORECASE):
            return set_model_group(doc, element_type, "Оборудование")
        if re.search("Оборудование", category_name, re.IGNORECASE):
            return set_model_group(doc, element_type, "Оборудование")
        if re.search("Выключатели", category_name, re.IGNORECASE):
            return set_model_group(doc, element_type, "Выключатели")
        if re.search("Розетки", category_name, re.IGNORECASE):
            return set_model_group(doc, element_type, "Розетки")
        if re.search("Кабели", category_name, re.IGNORECASE):
            return set_model_group(doc, element_type, "Кабели")
        if re.search("Лотки", category_name, re.IGNORECASE):
            return set_model_group(doc, element_type, "Лотки")
        if re.search("Щит", category_name, re.IGNORECASE):
            return set_model_group(doc, element_type, "Щиты")
        return category_name


########################################################################################################################
lost, start = [], 0
input = list(IN[0]) if bool(IN[0]) else []
source_names, target_names, volt_values, watt_values = [], [], [], []
if len(input) >= 1: source_names = [input[0][i] if input[0][i] else "null" for i in range(len(input[0]))]
if len(input) >= 2: target_names = [input[1][i] if input[1][i] else "null" for i in range(len(input[0]))]
if len(input) >= 3: volt_values = [input[2][i] if input[2][i] else "null" for i in range(len(input[0]))]
if len(input) >= 4: watt_values = [input[3][i] if input[3][i] else "null" for i in range(len(input[0]))]
if len(input) >= 5: watt_values = [input[4][i] if input[4][i] else "null" for i in range(len(input[0]))]
if len(input) == 1: target_names = ["null" for i in range(len(input[0])) if input]
if len(input) == 2: volt_values = ["null" for i in range(len(input[0])) if input]
if len(input) == 3: watt_values = ["null" for i in range(len(input[0])) if input]
########################################################################################################################
volt_guid = get_internal_guid_by_name(doc, "BI_напряжение")
watt_guid = get_internal_guid_by_name(doc, "BI_номинальная_мощность")
########################################################################################################################
########################################################################################################################
TransactionManager.Instance.EnsureInTransaction(doc)

excluded = set()
if len([source_names]):
    for idx, source_name in enumerate(source_names):
        start += 1
        new_type_name = target_names[idx]
        if (new_type_name == "null"): continue
        element_type = get_element_type_by_name(doc, source_name)
        if element_type:
            volt, watt = volt_values[idx], watt_values[idx]
            elements = get_instances_by_type_name(doc, source_name)
            if (volt and volt != "null" and len(elements)):
                volt = UnitUtils.ConvertToInternalUnits(float(volt), DisplayUnitType.DUT_VOLTS)
                [set_parameter_value_by_guid(doc, watt_guid, elem, volt) for elem in elements]
            if (watt and watt != "null" and len(elements)):
                watt = UnitUtils.ConvertToInternalUnits(float(watt), DisplayUnitType.DUT_WATTS)
                [set_parameter_value_by_guid(doc, watt_guid, elem, watt) for elem in elements]
            if rename_element_type(doc, element_type, new_type_name): excluded.add(new_type_name)
        else:
            lost.append(source_name)

TransactionManager.Instance.TransactionTaskDone()
########################################################################################################################
defined = []
########################################################################################################################

bracket = re.compile(r"^(\(.*\)).*")
filename = doc.Title.strip("_detached").strip("_отсоединено")
filename = strip_illegal_characters(filename, 30, app.Username)
collector = FilteredElementCollector(doc).WhereElementIsViewIndependent()
filter01 = ElementParameterFilter(SharedParameterApplicableRule("BI_напряжение"))
filter02 = ElementParameterFilter(SharedParameterApplicableRule("BI_номинальная_мощность"))
element_types = collector.WherePasses(LogicalOrFilter(filter01, filter02)).WhereElementIsElementType().ToElements()
element_types = sorted(element_types, key=lambda x: x.Category)

TransactionManager.Instance.EnsureInTransaction(doc)

for element_type in element_types:
    res = rename_model_group_by_category(element_type)
    name = element_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
    if name not in source_names:
        if name not in excluded:
            if not bracket.match(name):
                defined.append(name)

TransactionManager.Instance.TransactionTaskDone()
########################################################################################################################
OUT = filename, defined
########################################################################################################################
