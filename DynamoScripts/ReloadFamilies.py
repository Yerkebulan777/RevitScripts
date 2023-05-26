#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
reload(sys)
import glob
import os
import re
import clr

clr.AddReference("System")
clr.AddReference("System.Core")
import System

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
import Autodesk
from Autodesk.Revit.DB import ElementId, BuiltInParameter, ParameterValueProvider, FilterStringRule
from Autodesk.Revit.DB import IFamilyLoadOptions, FamilySource, BuiltInCategory, FilterStringEquals
from Autodesk.Revit.DB import FilteredElementCollector, FamilySymbol, TransactionGroup, Transaction
from Autodesk.Revit.DB import ElementParameterFilter, ElementCategoryFilter

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application

TransactionManager.Instance.ForceCloseTransaction()


########################################################################################################################

class FamilyOption(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues = False
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source = FamilySource.Family
        overwriteParameterValues = True
        return True


########################################################################################################################


def get_basename(file_path):
    fullname = os.path.basename(file_path)
    filename, ext = os.path.splitext(fullname)
    return filename


def find_symbolByCategoryAndName(doc, category, path):
    backup = re.compile(r".*(\S\d\d\d+)$")
    name = get_basename(path)
    if backup.match(name): return
    bic = System.Enum.ToObject(BuiltInCategory, category.Id)
    paramId = ElementId(BuiltInParameter.ALL_MODEL_FAMILY_NAME)
    rule = FilterStringRule(ParameterValueProvider(paramId), FilterStringEquals(), name, True)
    cat_filter, str_filter = ElementCategoryFilter(bic), ElementParameterFilter(rule)
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(bic)
    fid = collector.WhereElementIsElementType().WherePasses(cat_filter).WherePasses(str_filter).FirstElementId()
    return bool(fid.IntegerValue > 0)


def get_family_paths(directory, category):
    include_folders = ["AR", "AS", "KJ", "KR", "KG", "OV", "VK", "EOM", "PS", "SS"]
    roots = [os.path.join(directory, fld) for fld in os.listdir(directory) if fld in include_folders]
    roots.append(directory)
    families = []
    for root in roots:
        families.extend(glob.iglob(os.path.join(root, '*.rfa')))
        families.extend(glob.iglob(os.path.join(root, '*', '*.rfa')))
        families.extend(glob.iglob(os.path.join(root, '*', '*', '*.rfa')))
    families = [path for path in families if find_symbolByCategoryAndName(doc, category, path)]
    return families


def get_unfounded_familySymbols(category, family_names):
    bic = System.Enum.ToObject(BuiltInCategory, category.Id)
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(bic)
    families = collector.WhereElementIsElementType().ToElements()
    unfounded = [fsm for fsm in families if fsm.Family.Name not in family_names]
    return unfounded


def delete_notUsed_types(family, valid_type_names):
    for fid in family.GetFamilySymbolIds():
        symbol = family.Document.GetElement(fid)
        type_name = symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        typeId = symbol.get_Parameter(BuiltInParameter.ELEM_TYPE_PARAM).AsElementId()
        if type_name not in valid_type_names: family.Document.Delete(typeId)


########################################################################################################################
directory, category = os.path.realpath(IN[0]), IN[1]
########################################################################################################################
# core data processing
result = []
found_names = []
find_paths = get_family_paths(directory, category)
with TransactionGroup(doc, "Transaction Group") as transGroup:
    transGroup.Start()
    for parent_path in find_paths:
        family_doc = app.OpenDocumentFile(parent_path)
        try:
            family = family_doc.LoadFamily(doc, FamilyOption())
        except Exception as e:
            family_name = get_basename(parent_path)
            result.append("Error {} : {} ".format(family_name, e))
            continue
        with Transaction(doc, "Activate FamilySymbols") as trans:
            try:
                trans.Start()
                for symbolId in family.GetFamilySymbolIds():
                    symbol = doc.GetElement(symbolId)
                    symbol.Activate()
                trans.Commit()
                found_names.append(family.Name)
            except Exception as e:
                trans.RollBack()
    transGroup.Assimilate()
########################################################################################################################
result.extend(get_unfounded_familySymbols(category, found_names))
########################################################################################################################
message = "Unfounded families: "
OUT = message, result
