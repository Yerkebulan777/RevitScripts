#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import os
import re
import clr
import System

clr.AddReference("System")
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)

clr.AddReference("RevitAPI")

from Autodesk.Revit.DB import TransactionGroup, Transaction
from Autodesk.Revit.DB import ElementId, BuiltInParameter, ParameterValueProvider, FilterStringRule
from Autodesk.Revit.DB import IFamilyLoadOptions, FamilySource, BuiltInCategory
from Autodesk.Revit.DB import FilteredElementCollector, Family, Category

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

project_doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application

TransactionManager.Instance.ForceCloseTransaction()


########################################################################################################################

class FamilyOption(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues = True
        return True

    def OnSharedFamilyFound(self, sharedFamily, familyInUse, source, overwriteParameterValues):
        source = FamilySource.Family
        overwriteParameterValues = True
        return True


backup = re.compile(r".*(\S\d\d\d+)$")


########################################################################################################################
def get_basename(file_path):
    fullname = os.path.basename(file_path)
    filename, ext = os.path.splitext(fullname)
    return filename


def getFamiliesByCategory(doc, category):
    bic = System.Enum.ToObject(BuiltInCategory, category.Id)
    collector = FilteredElementCollector(doc).OfClass(Family)
    collector = collector.Where(lambda x: x.FamilyCategory.Id == ElementId(bic))
    families = collector.Where(lambda x: x.IsEditable == True).ToList()
    return families


def getFamiliesByBuiltInCategory(doc, buildCat):
    category = Category.GetCategory(doc, ElementId(buildCat))
    collector = FilteredElementCollector(doc).OfClass(Family)
    collector = collector.Where(lambda x: x.FamilyCategory.Id == category.Id)
    families = collector.Where(lambda x: x.IsEditable == True).ToList()
    return families


def loadFamily(source_doc, target_doc):
    source_family = source_doc.LoadFamily(target_doc, FamilyOption())
    with Transaction(target_doc, "Activate FamilySymbols") as trans:
        trans.Start()
        for symbolId in source_family.GetFamilySymbolIds():
            symbol = target_doc.GetElement(symbolId)
            symbol.Activate()
        trans.Commit()
    return source_family


########################################################################################################################
result = []
source_path, category = os.path.realpath(IN[0]), IN[1]
########################################################################################################################
source_type_names = []
source_doc = app.OpenDocumentFile(source_path)
source_family = loadFamily(source_doc, project_doc)
source_name = source_doc.Title.ToString().Replace(".rfa", "")
result.append("{} family has been loaded into project\n".format(source_name))
for fid in source_family.GetFamilySymbolIds():
    symbol = project_doc.GetElement(fid)
    source_type_names.append(symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString())
########################################################################################################################
families = getFamiliesByCategory(project_doc, category)
result.append("Defined opening families count {}".format(len(families)))
with TransactionGroup(project_doc, "Transaction Group") as transGroup:
    transGroup.Start()
    for parent_family in families:
        parent_doc = project_doc.EditFamily(parent_family)
        nestedFamilies = FilteredElementCollector(parent_doc).OfClass(Family).ToElements()
        for nested in nestedFamilies:
            if (source_name == nested.Name):
                if nested.IsEditable:
                    message = "Nested loaded into {}".format(parent_family.Name)
                    source_family = loadFamily(source_doc, parent_doc)
                    parent_family = loadFamily(parent_doc, project_doc)
                    parent_doc.Close(False)
                    result.append(message)
                    break
    transGroup.Assimilate()
########################################################################################################################
source_doc.Close(False)
OUT = result
########################################################################################################################
