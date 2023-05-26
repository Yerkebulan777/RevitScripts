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
from System.IO import Path

# from System.Collections.Generic import List
# from Microsoft.Win32 import Registry, RegistryValueKind


clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import ElementId, BuiltInParameter, ParameterValueProvider, FilterStringRule
from Autodesk.Revit.DB import IFamilyLoadOptions, FamilySource, BuiltInCategory, FilterStringEquals
from Autodesk.Revit.DB import FilteredElementCollector, SaveAsOptions, FamilySymbol, Family
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
        overwriteParameterValues = False
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


def get_families_paths(directory):
    backup = re.compile(r".*(\S\d\d\d+)$")
    paths = (glob.iglob(os.path.join(directory, '*.rfa')))
    for path in paths:
        family_name = Path.GetFileNameWithoutExtension(path)
        if backup.match(family_name): continue
    # paths = [path for path in paths if ]
    return paths


########################################################################################################################
source_path, directory = os.path.realpath(IN[0]), os.path.realpath(IN[1])
########################################################################################################################
source_doc = app.OpenDocumentFile(source_path)
source_name = source_doc.Title.ToString().Replace(".rfa", "")
family = source_doc.LoadFamily(doc, FamilyOption())
########################################################################################################################
# core data processing
parents = []
category, result = IN[2], []
result.append("{} family has been loaded into project".format(family.Name))
parent_paths = get_families_paths(directory, category)
for path in parent_paths:
    parent_doc = app.OpenDocumentFile(path)
    family = parent_doc.LoadFamily(doc, FamilyOption())
    parent_name = family.Name
    parents.append(parent_name)
    for nested in FilteredElementCollector(parent_doc).OfClass(Family).ToElements():
        if source_name == nested.Name and nested.IsEditable:
            try:
                family = source_doc.LoadFamily(parent_doc, FamilyOption())
                message = "{} family has been loaded into {} family file".format(family.Name, parent_name)
                save_option = SaveAsOptions()
                save_option.OverwriteExistingFile = True
                save_option.MaximumBackups = 3
                parent_doc.SaveAs(path, save_option)
                parent_doc.Close(False)
                result.append(message)
                break
            except Exception as error:
                result.append(error)
                break

########################################################################################################################
source_doc.Close(False)
########################################################################################################################

OUT = source_name, parents, result
