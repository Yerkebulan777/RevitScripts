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

import System

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


def LinkDWG_LayersInImportInstance(obj):
    clr.AddReference("DSCoreNodes")
    import DSCore
    rtn = []
    cat = obj.Category.SubCategories.GetEnumerator()
    while cat.MoveNext():
        rtn.append(cat.Current.Name)
    return DSCore.List.Sort(rtn)


def _ConvertRevitCurves(xcrv):
    if str(xcrv.GetType()) != "Autodesk.Revit.DB.PolyLine":
        rtn = xcrv.ToProtoType()
    else:
        pt = []
        for abc in xcrv.GetCoordinates():
            pt.append(abc.ToPoint())
        rtn = PolyCurve.ByPoints(pt)
    return rtn


def _Mesh2PolySurface(topo):
    vp = topo.VertexPositions
    fi = topo.FaceIndices
    xr1 = xrange(len(fi))
    ind = [(fi[i].A, fi[i].B, fi[i].C) for i in xr1]
    ptslist = [map(vp.__getitem__, ind[i]) for i in xr1]
    surf = []
    for i in ptslist:
        surf.append(Autodesk.DesignScript.Geometry.Surface.ByPerimeterPoints(i))
    return Autodesk.DesignScript.Geometry.PolySurface.ByJoinedSurfaces(surf)


# if  str(xcrv.GetType()) != "Autodesk.Revit.DB.PolyLine":
instances = flatten(FilteredElementCollector(doc).OfClass(ImportInstance))
plans = FilteredElementCollector(doc).OfClass(ViewPlan)


"""
name_dict = {}
for item in FilteredElementCollector(doc).OfClass(FilledRegion).WhereElementIsNotElementType():
    util = Autodesk.Revit.DB.UnitUtils
    view = [ v.Name for v in plans if item.Id in FilteredElementCollector(doc).OfClass(FilledRegion).OwnedByView(v.Id).ToElementIds() ]
    name = item.get_Parameter(BuiltInParameter.ELEM_TYPE_PARAM).AsValueString() + " " + view[0]
    prmr = item.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
    area = util.ConvertFromInternalUnits(prmr.AsDouble(), Autodesk.Revit.DB.DisplayUnitType.DUT_SQUARE_METERS)
    if name in name_dict.keys(): val = name_dict.get(name) + round(area, 3)
    else: val = round(area, 3)
    name_dict.update({name: val})
"""
"""
DWG = instances
CRV = []
CRX = []
LAY = []
CLR = []

for abc in DWG.Geometry[Options()]:
    for crv in abc.GetInstanceGeometry():
        try:
            lay = doc.GetElement(crv.GraphicsStyleId).GraphicsStyleCategory.Name
            ccc = doc.GetElement(crv.GraphicsStyleId).GraphicsStyleCategory.LineColor
            clr = [ccc.Red, ccc.Green, ccc.Blue]
            CRX.append(_ConvertRevitCurves(crv))
            CRV.append(crv)
            LAY.append(lay)
            CLR.append(clr)
        except:
            try:
                lay = "0"
                clr = [0, 0, 0]
                ccc = crv.ToProtoType()
                ccc = _Mesh2PolySurface(ccc)
                if ccc != None or ccc != []:
                    CRX.append(ccc)
                    CRV.append(crv)
                    LAY.append(lay)
                    CLR.append(clr)
            except:
                pass
"""
tpc = []
for instance in instances:
    for abc in instance.Geometry[Options()]:
        for crv in abc.GetInstanceGeometry():
            if "Autodesk.Revit.DB.PolyLine" == str(crv.GetType()):
                tpc.append(crv.ToProtoType())

OUT = tpc
