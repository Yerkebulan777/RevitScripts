# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import os
import clr
import time
import System

clr.AddReference("System")
clr.AddReference("System.Core")
from System.Collections.Generic import List

clr.ImportExtensions(System.Linq)

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import Family, Category
from Autodesk.Revit.DB import TransactionGroup, Transaction
from Autodesk.Revit.DB import BuiltInParameter, BuiltInCategory
from Autodesk.Revit.DB import IFamilyLoadOptions, FamilySource
from Autodesk.Revit.DB import PerformanceAdviser, PerformanceAdviserRuleId
from Autodesk.Revit.DB import ElementId, FilteredElementCollector, ImportInstance

########################################################################################################################
import revit_file_util

import revit_script_util
from revit_script_util import Output

sessionId = revit_script_util.GetSessionId()
uiapp = revit_script_util.GetUIApplication()
doc = revit_script_util.GetScriptDocument()
revitFilePath = revit_script_util.GetRevitFilePath()


########################################################################################################################
class FamilyOption(IFamilyLoadOptions):
    def OnFamilyFound(self, familyInUse, overwriteParameterValues):
        overwriteParameterValues = True
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


def getFamiliesByBuiltInCategory(doc, buildCat):
    category = Category.GetCategory(doc, ElementId(buildCat))
    collector = FilteredElementCollector(doc).OfClass(Family)
    collector = collector.Where(lambda x: x.FamilyCategory.Id == category.Id)
    families = collector.Where(lambda x: x.IsEditable == True).ToList()
    Output("Get families by {} category".format(category.Name))
    return families


def loadFamily(source_doc, target_doc):
    try:
        source_family = source_doc.LoadFamily(target_doc, FamilyOption())
        with Transaction(target_doc, "Activate FamilySymbols") as trans:
            trans.Start()
            for symbolId in source_family.GetFamilySymbolIds():
                symbol = target_doc.GetElement(symbolId)
                symbol.Activate()
            trans.Commit()
        return source_family
    except Exception as exc:
        Output("Warning: {}".format(exc))
        return


def synchronizeRevitFile(doc):
    comment = "Automation"
    message = "WARNING: Synchronize error!"
    if doc.IsWorkshared and not doc.IsDetached:
        message = "\r\n\t ... Synchronize revit file successfully!!!"
        revit_file_util.SynchronizeWithCentral(doc, comment)
        revit_file_util.RelinquishAll(doc)
    return message


########################################################################################################################
Output('\t\t\t')
Output('><' * 100)
Output('\n\n\n')
########################################################################################################################
source_path = r"K:\02_Библиотека\AR\01_Семейства\Каркас несущий и Перемычка\Перемычка\Металлическая перемычка.rfa"
source_path = os.path.normpath(os.path.realpath(source_path))
########################################################################################################################
source_type_names = []
sourceDoc = doc.Application.OpenDocumentFile(source_path)
sourceFamily = loadFamily(sourceDoc, doc)
source_name = sourceDoc.Title.ToString().Replace(".rfa", "")
Output("\r\n\t{} family has been loaded into project\n".format(source_name))
for fid in sourceFamily.GetFamilySymbolIds():
    symbol = doc.GetElement(fid)
    source_type_names.append(symbol.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString())
########################################################################################################################
catFamilies = []
catFamilies.extend(getFamiliesByBuiltInCategory(doc, BuiltInCategory.OST_Doors))
catFamilies.extend(getFamiliesByBuiltInCategory(doc, BuiltInCategory.OST_Windows))
Output("Defined opening families count {}".format(len(catFamilies)))
for parentFamily in catFamilies:
    parentDoc = doc.EditFamily(parentFamily)
    collector = FilteredElementCollector(parentDoc)
    nestedFamilies = collector.OfClass(Family).ToElements()
    for nested in nestedFamilies:
        if (nested.IsEditable and source_name == nested.Name):
            message = "Nested loaded into {}".format(parentFamily.Name)
            sourceFamily = loadFamily(sourceDoc, parentDoc)
            if sourceFamily and sourceFamily.IsValidObject:
                parentFamily = loadFamily(parentDoc, doc)
                parentDoc.Close(False)
                collector.Dispose()
                Output(message)
                time.sleep(0.5)
                break
Output(synchronizeRevitFile(doc))
########################################################################################################################
Output('\n\n\n')
Output('><' * 100)
Output('\t\t\t')
########################################################################################################################
