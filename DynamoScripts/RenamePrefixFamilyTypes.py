#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")

import re
import clr

# import calculate_script_util as CalculateUtil
# import synchronization_script_util as SynchUtil

clr.AddReference("System")
clr.AddReference("System.Core")
import System

clr.AddReference('RevitAPI')
# from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter
from Autodesk.Revit.DB import ElementId, BuiltInCategory, FamilySymbol, ParameterValueProvider
from Autodesk.Revit.DB import ElementParameterFilter, FilterStringRule, FilterStringContains

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


def set_model_parameter(doc, elem_type, value=""):
    if elem_type and isinstance(value, basestring):
        elem_type = doc.GetElement(ElementId(elem_type.Id.IntegerValue))
        param = elem_type.get_Parameter(BuiltInParameter.ALL_MODEL_MODEL)
        if param and not param.IsReadOnly: return param.Set(value)


def get_symbols_by_category(doc, category, model_group):
    bic = System.Enum.ToObject(BuiltInCategory, category.Id)
    pvp = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_MODEL))
    flt = ElementParameterFilter(FilterStringRule(pvp, FilterStringContains(), model_group, False))
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).WhereElementIsViewIndependent()
    symbols = collector.OfCategory(bic).WherePasses(flt).WhereElementIsElementType().ToElements()
    return symbols


########################################################################################################################
prefix, category, model_group = IN[0], IN[1], IN[2]
########################################################################################################################
rename = re.compile(r"^(\(\w*\s*\w*\)\s*)")
rematch = re.compile(r"^(\({0}\)).*".format(prefix))
recharts = re.compile(r"([+*^#%!?@$&£\\\[\]{}/|;:<>`~]*)")
symbols = get_symbols_by_category(doc, category, model_group)
########################################################################################################################
TransactionManager.Instance.EnsureInTransaction(doc)

result = set()
if all([prefix, category]):
    for symbol in symbols:
        old_name = symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        if rematch.match(old_name): continue
        new_name = old_name.encode('cp1251', 'ignore').decode('cp1251').strip()
        if recharts.match(new_name): new_name = re.sub(recharts, '', new_name)
        if rename.match(new_name): new_name = re.sub(rename, prefix, new_name)
        # new_name = TransUtil.set_element_name(doc, symbol, "{}{}".format(prefix, new_name))
        result.add(new_name)

TransactionManager.Instance.TransactionTaskDone()
########################################################################################################################
OUT = result
########################################################################################################################
