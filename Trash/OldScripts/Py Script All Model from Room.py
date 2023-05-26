import clr

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Structure import *

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import *

clr.AddReference('RevitNodes')
import Revit

clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

import System
from System.Collections.Generic import *

import clr

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

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


def GetAllModels():
    categories = doc.Settings.Categories
    catfilter = []
    for cat in categories:
        if cat.CategoryType == CategoryType.Model:
            if cat.SubCategories.Size > 0 or cat.CanAddSubcategory:
                catfilter.Add(ElementCategoryFilter(System.Enum.ToObject(BuiltInCategory, int(str(cat.Id)))))
        else:
            continue
    filter_list = List[ElementFilter](catfilter)
    result = FilteredElementCollector(doc).WhereElementIsNotElementType().WherePasses(filter_list).ToElements()
    return result


def JoinElements(elist1, elist2):
    for elm1 in elist1:
        for elm2 in elist2:
            if Autodesk.Revit.DB.JoinGeometryUtils.AreElementsJoined(doc, elm1, elm2): continue
            geo1 = elm1.Geometry()
            geo2 = elm2.Geometry()
            if Geometry.DoesIntersect(geo1, geo2):
                try:
                    JoinGeometryUtils.JoinGeometry(doc, elm1, elm2)
                except:
                    continue
    return


def GetSolidsOfElement(item):
    opt = Options()
    opt.ComputeReferences = True
    geo_elem = item.get_Geometry(opt)
    solids = []
    for geoObj in geo_elem:
        if geoObj.ToString() == 'Autodesk.Revit.DB.GeometryInstance':
            geomIns = geoObj
            instGeoElement = geomIns.GetSymbolGeometry()
            for i in instGeoElement:
                if i.ToString() == 'Autodesk.Revit.DB.Solid':
                    if i.Volume == 0:
                        pass
                    else:
                        solids.append(i)
        else:
            if geoObj.ToString() == 'Autodesk.Revit.DB.Solid':
                solids.append(geoObj)
    return solids


def get_intersection(line1, line2):
    results = clr.Reference[IntersectionResultArray]()
    result = line1.Intersect(line2, results)
    if result != SetComparisonResult.Overlap: pass
    intersection = results.Item[0]
    return intersection.XYZPoint


######################## INPUT ##############################
#############################################################

TransactionManager.Instance.EnsureInTransaction(doc)

TransactionManager.Instance.TransactionTaskDone()

OUT = 0
