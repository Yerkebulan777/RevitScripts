#!/usr/bin/python
# -*- coding: utf-8 -*-
import clr
import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
# import os, os.path, math, difflib
# from collections import defaultdict
clr.AddReference("System")
clr.AddReference("System.Core")
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference('RevitAPIIFC')
clr.AddReference('RevitNodes')
clr.AddReference('RevitServices')
import Autodesk
import System
import Revit
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
# from Autodesk.Revit.DB.Structure import *
# from Autodesk.Revit.DB.IFC import ExporterIFCUtils
# from Autodesk.Revit.UI.Selection import ObjectType
# from Autodesk.Revit.ApplicationServices import *
# from Autodesk.Revit.Attributes import *
# from Autodesk.Revit.UI import *
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument

TransactionManager.Instance.ForceCloseTransaction()


def lines_by_points(points):
    lines = []
    for idx, point in enumerate(points):
        if idx == 0:
            lines.append(Line.CreateBound(points[- 1], point))
        else:
            lines.append(Line.CreateBound(points[idx - 1], point))
    return lines


def simpfly_curves(curves, clearance=0.5):
    simpfly_lines, points = [], []
    idx, current = 0, curves[0]
    qoint = current.GetEndPoint(1)
    while True:
        find = reverse = None
        tolerance = clearance
        for count, line in enumerate(curves):
            p = line.GetEndPoint(0)
            q = line.GetEndPoint(1)
            distance1 = p.DistanceTo(qoint)
            distance2 = q.DistanceTo(qoint)
            if tolerance > distance1 and clearance < distance2:
                tolerance = distance1
                reverse = False
                find = True
                idx = count

            if tolerance > distance2 and clearance < distance1:
                tolerance = distance2
                reverse = True
                find = True
                idx = count

        if find:
            match = curves.pop(idx)
            point, qoint = current.GetEndPoint(0), current.GetEndPoint(1)
            line = Line.CreateUnbound(point, (qoint - point).Normalize())
            if reverse == False:
                result = line.Project(match.GetEndPoint(0))
                point, qoint = match.GetEndPoint(0), match.GetEndPoint(1)
                line = Line.CreateUnbound(qoint, (point - qoint).Normalize())
                point = line.Project(result.XYZPoint).XYZPoint
                current = Line.CreateBound(point, qoint)
                points.append(point)
            elif reverse == True:
                result = line.Project(match.GetEndPoint(1))
                point, qoint = match.GetEndPoint(1), match.GetEndPoint(0)
                line = Line.CreateUnbound(qoint, (point - qoint).Normalize())
                point = line.Project(result.XYZPoint).XYZPoint
                current = Line.CreateBound(point, qoint)
                points.append(point)
        else:
            lines = lines_by_points(points)
            simpfly_lines.extend(lines)
            points = []
            try:
                curves = curves[:]
                current = curves[0]
                qoint = current.GetEndPoint(1)
            except:
                break

    return simpfly_lines


with Transaction(doc, "WallFinishing") as tra:
    tra.Start()
    lines = []
    collector = FilteredElementCollector(doc, doc.ActiveView.Id)
    for detail_curve in collector.OfCategory(BuiltInCategory.OST_Lines).WhereElementIsNotElementType().ToElements():
        line = detail_curve.GeometryCurve
        direction = line.Direction.Normalize()
        vector = direction.CrossProduct(XYZ.BasisZ)
        tf = Transform.CreateTranslation(0.5 * vector)
        line = line.CreateTransformed(tf)
        lines.append(line)
    outlist = []
    lines = simpfly_curves(lines, 3.0)
    for line in lines:
        newline = doc.Create.NewDetailCurve(doc.ActiveView, line)
        newline.LineStyle.GraphicsStyleCategory.LineColor = Autodesk.Revit.DB.Color(0, 75, 150)
        outlist.append(newline)
    doc.Regenerate()
    tra.Commit()

OUT = outlist
