import clr

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

# Import DocumentManager and TransactionManager
clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
from System.Collections.Generic import *

# Import RevitAPI
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Analysis import *

# Import ToDSType(bool) extension method
clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
# Import geometry conversion extension methods
clr.ImportExtensions(Revit.GeometryConversion)
# Import DocumentManager and TransactionManager
clr.AddReference("RevitServices")


def NameParam(arg):
    return arg.LookupParameter("Имя типа").AsString()


# Выбор связей
doc = DocumentManager.Instance.CurrentDBDocument
opt = Options()
collector = Autodesk.Revit.DB.FilteredElementCollector(doc)
linkInstances = collector.OfClass(Autodesk.Revit.DB.RevitLinkInstance)
# настройка фильтра
filter = ElementCategoryFilter(BuiltInCategory.OST_Walls)
Walls = FilteredElementCollector(doc).WherePasses(filter).WhereElementIsElementType().ToElements()

for i in linkInstances:
    if IN[0].ToLower() in i.Name.ToLower():
        linkDoc = i.GetLinkDocument()
        # Выбор типов стен
        collector = FilteredElementCollector(linkDoc)
        linkWalls = collector.WherePasses(filter).WhereElementIsElementType().ToElements()
        LinkWallNames = [NameParam(lw) for lw in linkWalls]
a = []
TransactionManager.Instance.EnsureInTransaction(doc)
for w in Walls:
    TypeName = NameParam(w)
    if TypeName in LinkWallNames:
        ind = LinkWallNames.IndexOf(TypeName)
        LinkTypeMark = linkWalls[ind].LookupParameter("Маркировка типоразмера").AsString()
        a.append(LinkTypeMark)
        if LinkTypeMark:
            w.LookupParameter("Маркировка типоразмера").Set(LinkTypeMark)
    else:
        OUT = "Совпадений типов не найдено"
b = []
TransactionManager.Instance.TransactionTaskDone()
for w in Walls:
    TypeName = NameParam(w)
    if TypeName in LinkWallNames:
        ind = LinkWallNames.IndexOf(TypeName)
        LinkTypeMark = linkWalls[ind].LookupParameter("Комментарии к типоразмеру").AsString()
        a.append(LinkTypeMark)
        if LinkTypeMark:
            w.LookupParameter("Комментарии к типоразмеру").Set(LinkTypeMark)
    else:
        OUT = "Совпадений типов не найдено"
TransactionManager.Instance.TransactionTaskDone()

с = []
TransactionManager.Instance.TransactionTaskDone()
for w in Walls:
    TypeName = NameParam(w)
    if TypeName in LinkWallNames:
        ind = LinkWallNames.IndexOf(TypeName)
        LinkTypeMark = linkWalls[ind].LookupParameter("Группа модели").AsString()
        с.append(LinkTypeMark)
        if LinkTypeMark:
            w.LookupParameter("Группа модели").Set(LinkTypeMark)
    else:
        OUT = "Совпадений типов не найдено"
TransactionManager.Instance.TransactionTaskDone()

OUT = a, b, c
