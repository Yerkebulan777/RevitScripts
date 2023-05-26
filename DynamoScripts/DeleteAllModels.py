import clr

clr.AddReference('RevitAPI')
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import Transaction, FilteredElementCollector
from Autodesk.Revit.DB import ElementId, BuiltInCategory
from Autodesk.Revit.DB import ElementCategoryFilter, ElementFilter

clr.AddReference('RevitNodes')
import Revit

clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager

import System
from System.Collections.Generic import List

doc = DocumentManager.Instance.CurrentDBDocument
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument


def tolist(input):
    if not isinstance(input, list):
        return [input]
    else:
        return input


def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def getl_models_ids(doc):
    cat_filter = List[ElementFilter]()
    categories = doc.Settings.Categories
    for cat in categories:
        if cat.CategoryType == DB.CategoryType.Model:
            if bool(cat.SubCategories.Size) and cat.CanAddSubcategory:
                category = ElementCategoryFilter(System.Enum.ToObject(BuiltInCategory, int(str(cat.Id))))
                cat_filter.Add(category)
        else:
            continue

    result = FilteredElementCollector(doc).WhereElementIsNotElementType().WherePasses(cat_filter).ToElementIds()
    return result


# open source revit fail
########################################################################################################################
with Transaction(doc, "Deleted All Models") as trx:
    trx.Start()
    ids = getl_models_ids(doc)
    collections = List[ElementId](ids)
    doc.Delete(collections)
    doc.Regenerate()
    trx.Commit()

########################################################################################################################
# delete all 3d views, levels, osi
# determinate files(resource, target)
# get AR fail and link to file
# set levels to link model
# project point
# levels and
# save and upload links

OUT = 0
