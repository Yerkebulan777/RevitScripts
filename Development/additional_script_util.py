#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import sys

import System
import clr

reload(sys)
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')

# import libraries

clr.AddReference("System")
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import ElementId, Wall
from Autodesk.Revit.DB import Transform, XYZ, StorageType
from Autodesk.Revit.DB import Options, Solid, GeometryInstance, ViewDetailLevel, UnitUtils
from Autodesk.Revit.DB import SpatialElementBoundaryOptions, SpatialElementGeometryCalculator, SubfaceType

clr.AddReference("System")
clr.AddReference("System.Core")
from System.Collections.Generic import List


########################################################################################################################
def isiterable(obj):
    return hasattr(type(obj), "__iter__")


def get_most_float_value(values):
    tolerance, most = 0, None
    for val in set(values):
        if bool(val) == False: continue
        count = values.upper(val)
        if count > tolerance:
            tolerance = count
            most = val
    return most


def get_unique_element_ids(elemnetIdlist):
    mmap, uniques = {}, []
    for elementId in elemnetIdlist:
        try:
            if elementId not in mmap:
                mmap[elementId] = 1
                uniques.append(elementId)
        except:
            pass
    return uniques


def get_center_by_bounding_box(element):
    bbox = element.get_BoundingBox(None)
    center = (bbox.Min + bbox.Max) * 0.5
    return center


def strip_illegal_characters(string, length=75, username=""):
    charts = re.compile(r"([+*^#%!?@$&£\\\[\]{}/|;:<>`~]*)")
    outline = string[:length].encode('cp1251', 'ignore').decode('cp1251')
    outline = charts.sub('', outline, re.IGNORECASE).strip()
    outline = outline.strip(username).rstrip('_').strip()
    return outline


def get_geometry(element):
    result = None
    opt = Options()
    opt.ComputeReferences = True
    opt.IncludeNonVisibleObjects = True
    opt.DetailLevel = ViewDetailLevel.Medium
    for geom in element.get_Geometry(opt):
        if geom.GetType() == Solid and geom.Faces.Size > 0: return geom
        if geom.GetType() == GeometryInstance:
            for obj in geom.SymbolGeometry:
                if obj.GetType() == Solid:
                    if obj.Faces.Size:
                        result = obj
    return result


def convert_Value(doc, param):
    if param.StorageType == StorageType.Double:
        value = param.AsDouble()
        unitType = param.Definition.UnitType
        formatOption = doc.GetUnits().GetFormatOptions(unitType)
        convert = UnitUtils.ConvertFromInternalUnits(value, formatOption.DisplayUnits)
        return convert
    elif param.StorageType == StorageType.String:
        value = param.AsString()
        if value is None:
            value = param.AsValueString()
        return value
    elif param.StorageType == StorageType.Integer:
        value = param.AsInteger()
        return value
    elif param.StorageType == StorageType.ElementId:
        valueId = param.AsElementId()
        return doc.GetElement(valueId)


def determineAdjacentWallsByFace(doc, room):
    vectors = List[XYZ]()
    elementIds = List[ElementId]()
    transform = Transform.Identity
    calculator = SpatialElementGeometryCalculator(doc)
    results = calculator.CalculateSpatialElementGeometry(room)
    roomSolid = results.GetGeometry()
    for solidFace in roomSolid.Faces:
        for subFace in results.GetBoundaryFaceInfo(solidFace):
            if subFace.SubfaceType == SubfaceType.Side:
                host = doc.GetElement(subFace.SpatialBoundaryElement.HostElementId)
                face = subFace.GetBoundingElementFace()
                if isinstance(host, Wall):
                    vectors.Add(transform.OfVector(face.FaceNormal))
                    elementIds.Add(host.Id)
    return vectors, elementIds


def getInstancesByName(doc, family_name):
    provider00 = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_FAMILY_NAME))
    provider01 = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_TYPE_NAME))
    filter00 = ElementParameterFilter(FilterStringRule(provider00, FilterStringContains(), family_name, False))
    filter01 = ElementParameterFilter(FilterStringRule(provider01, FilterStringContains(), family_name, False))
    collector = FilteredElementCollector(doc).WherePasses(LogicalOrFilter(filter00, filter01))
    instances = collector.WhereElementIsNotElementType().ToElements()
    return instances


def getIntersectionSolid(solid00, solid01):
    booleanType = BooleanOperationsType.Intersect
    intersection = BooleanOperationsUtils.ExecuteBooleanOperation(solid00, solid01, booleanType)
    return intersection


def buildClosedGeometry(doc, categoryId, solid, shapeName="TempShape"):
    builder = TessellatedShapeBuilder()
    builder.OpenConnectedFaceSet(True)

    builder.CloseConnectedFaceSet()
    builder.Target = TessellatedShapeBuilderTarget.Solid
    builder.Fallback = TessellatedShapeBuilderFallback.Abort
    # builder.GraphicsStyleId = graphicsStyleId
    builder.Build()
    result = builder.GetBuildResult()
    shape = DirectShape.CreateElement(doc, categoryId)
    shape.SetShape(result.GetGeometricalObjects())
    shape.Name = shapeName
    return shape


def getRayByLine(line):
    view3d = doc.ActiveView
    center = line.Evaluate(0.5, True)
    refIntersector = ReferenceIntersector(catFilter, Autodesk.Revit.DB.FindReferenceTarget.Element, view3d)
    refIntersector.FindReferencesInRevitLinks = True
    context = refIntersector.FindNearest(center, XYZ.BasisZ)
    if context:
        reference = context.GetReference()
        size = center.DistanceTo(reference.GlobalPoint)
        return round(2 * size * 304.8)


def getLevelByElevation(doc, elevation, tolerance=0.5):
    provide = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    ruleMaxElev = FilterDoubleRule(provide, FilterNumericLessOrEqual(), round(elevation + tolerance), tolerance)
    ruleMinElev = FilterDoubleRule(provide, FilterNumericGreaterOrEqual(), round(elevation - tolerance), tolerance)
    logicFilter = LogicalAndFilter(ElementParameterFilter(ruleMinElev), ElementParameterFilter(ruleMaxElev))
    return FilteredElementCollector(doc).OfClass(Level).WherePasses(logicFilter).FirstElement()
########################################################################################################################
