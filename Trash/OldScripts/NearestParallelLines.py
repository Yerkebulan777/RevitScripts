#!/usr/bin/python
# -*- coding: utf-8 -*-

import clr

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import *

clr.AddReference('System')
import System
from System.Collections.Generic import *

clr.AddReference('RevitNodes')
import Revit
clr.ImportExtensions(Revit.GeometryConversion)
clr.ImportExtensions(Revit.Elements)

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument


def GetModelLinesByView():
    #doc.Regenerate()
    uidoc.RefreshActiveView()
    filter = ElementCategoryFilter(BuiltInCategory.OST_Lines)
    collector = FilteredElementCollector(doc, uidoc.ActiveView.Id)
    return collector.WherePasses(filter).WhereElementIsNotElementType().ToElements()


def GetClosestPoints(ModelLines):
    curves = [ i.GeometryCurve for i in ModelLines if i ]
    lines = [ i for i in curves if i.GetType().Name == "Line" ]
    #strpts = [ i.GetEndPoint( 0 ) for i in curves ]
    #endpts = [ i.GetEndPoint( 1 ) for i in curves ]
    result = []
    results = clr.Reference[Autodesk.Revit.DB.ClosestPointsPairBetweenTwoCurves]()
    curves = List[Curve](lines)
    for indx, crv in enumerate(curves):
        try:
            point = crv.GetEndPoint(0)
            project = curves[indx+1].Project(point)
            result.append(project)
        except Exception as error: result.append(error)
        #if DistanceTo()
        #crv.Project(point)
        #if indx < len(lines) - 1:
            #curves = [lines[i], lines[i + 1]]

    return result #[p.ToPoint() for p in result]


ModelLines = GetModelLinesByView()
test = GetClosestPoints(ModelLines)


#Join curves in polycurves
joinedCurves = []
for d in disjoinedcurves:
    tempList = []
    for item in d:
        tempList.append(PolyCurve.ByJoinedCurves(item))
    joinedCurves.append(tempList)


#Check the sense of the polycurve
for j in joinedCurves:
    for crv in j:
        if crv.BasePlane().Normal.Z > 0:
            crv = crv
        else:
            crv = crv.Reverse()


OUT =  test

