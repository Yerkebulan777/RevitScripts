#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
pyt_path = r'C:\Program Files (x86)\IronPython 2.7\Lib'
sys.path.append(pyt_path)
import math

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


def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def GetIntersection(Curve1, Curve2):
    p1 = Curve1.GetEndPoint(0)
    q1 = Curve1.GetEndPoint(1)
    p2 = Curve2.GetEndPoint(0)
    q2 = Curve2.GetEndPoint(1)
    v1 = q1 - p1; v2 = q2 - p2; w = p2 - p1
    c = (v2.X * w.Y - v2.Y * w.X) / (v2.X * v1.Y - v2.Y * v1.X)
    intersect = None
    if not float.IsInfinity(c):
        x = p1.X + c * v1.X
        y = p1.Y + c * v1.Y
        intersect  = XYZ(x, y, 0)
    return intersect


def get_intersection(line1, line2):
    from Autodesk.Revit.DB import SetComparisonResult, IntersectionResultArray
    results = clr.Reference[IntersectionResultArray]()
    result = line1.Intersect(line2, results)
    if result != SetComparisonResult.Overlap: pass
    intersection = results.Item[0]
    return intersection.XYZPoint


"""
def OffsetRoomBoundary(room, distance):
    offsetloop = None
    options = Autodesk.Revit.DB.SpatialElementBoundaryOptions()
    options.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Center
    segments = room.GetBoundarySegments(options)
    curves = flatten([i.GetCurve() for i in segments[0] if i])
    curves = List[Curve](curves)
    loop = CurveLoop.Create(curves)
    planeloop = loop.GetPlane().Normal
    if loop.IsCounterclockwise(planeloop): sourceloop.Flip()
    if loop.IsOpen(): loop = CurveLoop.CreateViaThicken(loop, distance*2, planeloop)
    try:
        offsetloop = CurveLoop.CreateViaOffset(loop, distance, planeloop)
    except:
        pass
    return offsetloop
"""


def CreateNewLineStyle( NewLineStyleName ):
    line_pattern  = [lp for lp in FilteredElementCollector(doc).OfClass(LinePatternElement) if lp.Name == "dash"]
    categories = doc.Settings.Categories
    line_cat = categories.get_Item( BuiltInCategory.OST_Lines )
    newlinestyle = categories.NewSubcategory(line_cat, str(NewLineStyleName))
    newlinestyle.SetLineWeight( 5, GraphicsStyleType.Projection )
    newlinestyle.LineColor = Color( 0xFF, 0x00, 0x00 )
    newlinestyle.SetLinePatternId( line_pattern.Id, GraphicsStyleType.Projection )
    doc.Regenerate()
    return


def WallEqualizer(self):
    wallist = FilteredElementCollector(doc, doc.ActiveView.Id).OfCategory(BuiltInCategory.OST_Walls).ToElements()
    return wallist


def BustEquiizer90(self, el, line, angleR):
    angle = self.RadiansToDegrees(angleR)
    if Math.Abs(angle - 90) > 0.0000001 and Math.Abs(angle - 90) < 1.2:
        self.Equalizer(el, -(self.DegreesToRadians(90) - angleR))
        wLine = self.GetLine(el)
        wcos = (line.Direction.X * wLine.Direction.X + line.Direction.Y * wLine.Direction.Y)
        angleR = Math.Acos(wcos)
        angle = self.RadiansToDegrees(angleR)
        if Math.Abs(angle - 90) > 0.0000001 and Math.Abs(angle - 90) < 2.4:
            self.Equalizer(el, (self.DegreesToRadians(90) - angleR))


def BustEquiizer0(self, el, line, angleR):
    angle = self.RadiansToDegrees(angleR)
    if (Math.Abs(angle) > 0.0000001 and Math.Abs(angle) < 1.2) or Math.Abs(angle - 180) > 0.0000001 and Math.Abs(angle - 180) < 2.4:
        self.Equalizer(el, -angleR)
        wLine = self.GetLine(el)
        wcos = (line.Direction.X * wLine.Direction.X + line.Direction.Y * wLine.Direction.Y)
        angleR = Math.Acos(wcos)
        angle = self.RadiansToDegrees(angleR)
        if Math.Abs(angle) > 0.0000001 and Math.Abs(angle) < 2.4 or Math.Abs(angle - 180) > 0.0000001 and Math.Abs(angle - 180) < 2.4:
            self.Equalizer(el, -angleR)
            wLine = self.GetLine(el)
            wcos = (line.Direction.X * wLine.Direction.X + line.Direction.Y * wLine.Direction.Y)
            angleR = Math.Acos(wcos)
            angle = self.RadiansToDegrees(angleR)
            if Math.Abs(angle) > 0.0000001 and Math.Abs(angle) < 5 or Math.Abs(angle - 180) > 0.0000001 and Math.Abs(angle - 180) < 5:
                self.Equalizer(el, angleR)


def Equalized(item, angle):
    line = item.Location
    mid = Midpoint(line.Curve)
    axis = Line.CreateBound(mid, XYZ(mid.X, mid.Y, mid.Z + 3.0))
    ElementTransformUtils.RotateElement(doc, item.Id, axis, angle)


def GetLine(item):
    selCurve = (item.Location).Curve
    if selCurve:
        p0 = XYZ(selCurve.GetEndPoint(0).X, selCurve.GetEndPoint(0).Y, 0)
        p1 = XYZ(selCurve.GetEndPoint(1).X, selCurve.GetEndPoint(1).Y, 0)
        line = Line.CreateBound(p0, p1)
        return line


def RadiansToDegrees(angle):
    return (angle * 180 / Math.PI)


def DegreesToRadians(angle):
    return (angle * Math.PI / 180)


def Midpoint(curve):
    return 0.5 * (curve.GetEndPoint(0) + curve.GetEndPoint(1))


Midpoint = staticmethod(Midpoint)

def InternalStartup(self):
    self._Startup += self.Module_Startup
    self._Shutdown += self.Module_Shutdown


def AllowElement(elem):
    enumerator = SelCats.GetEnumerator()
    while enumerator.MoveNext():
        cat = enumerator.Current
        if elem.Category.Id.IntegerValue == cat:
            return True
    return False


# Element.Name.GetValue(item)
###################################################################################################
#path = ModelPathUtils.ConvertModelPathToUserVisiblePath(cadLinkType.GetExternalFileReference().GetAbsolutePath())
cad_links = [i for i in FilteredElementCollector(doc).OfClass(CADLinkType).ToElements() ]

OUT = cad_links