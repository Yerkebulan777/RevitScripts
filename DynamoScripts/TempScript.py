#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
import difflib
import glob
import os
import re

import clr

clr.AddReference("System")
clr.AddReference("System.Core")
from System.Collections.Generic import List

clr.AddReference('RevitAPI')
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import View3D
from Autodesk.Revit.DB import Options
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB import ModelPathUtils
from Autodesk.Revit.DB import ViewDetailLevel
from Autodesk.Revit.DB import ElementId, Level
from Autodesk.Revit.DB import XYZ, Grid, Transform
from Autodesk.Revit.DB import FilterNumericLessOrEqual
from Autodesk.Revit.DB import LocationPoint, LocationCurve
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter
from Autodesk.Revit.DB import RevitLinkOptions, RevitLinkType, RevitLinkInstance
from Autodesk.Revit.DB import BoundingBoxIsInsideFilter, Outline, ExclusionFilter
from Autodesk.Revit.DB import ParameterValueProvider, ElementParameterFilter
from Autodesk.Revit.DB import ElementMulticategoryFilter, BuiltInCategory
from Autodesk.Revit.DB import FilterDoubleRule

########################################################################################################################
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

TransactionManager.Instance.ForceCloseTransaction()
########################################################################################################################

options = Options()
options.IncludeNonVisibleObjects = True
options.DetailLevel = ViewDetailLevel.Medium

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
identityTransform = Transform.Identity
uidoc = uiapp.ActiveUIDocument
output = "Result: \n"


########################################################################################################################

def getSubdirectory(ipath, directory):
    folder = os.path.basename(os.path.dirname(ipath))
    drive, tail = os.path.splitdrive(ipath)
    ipath = os.path.realpath(ipath)
    while os.path.exists(ipath):
        if folder == '': return drive
        result = os.path.join(ipath, folder)
        ipath, folder = os.path.split(ipath)
        if folder.endswith(directory):
            return result


def determineDirectory(ipath, directory, folder=None):
    result = os.path.join(getSubdirectory(ipath, 'PROJECT'), directory)
    if bool(os.path.exists(result) and folder):
        result = os.path.join(result, folder)
    if not os.path.exists(result):
        os.makedirs(result)
    return result


def retrieveArchModelPath(filepath, filename, extension, tolerance=0.75):
    directory = getSubdirectory(filepath, 'PROJECT')
    directory = os.path.dirname(directory)
    result, regex = None, re.compile(r'#')
    for folder in os.listdir(directory):
        if (folder.endswith('AR') or folder.endswith('AS')):
            path = os.path.join(directory, folder)
            if os.path.isdir(path):
                paths = glob.glob(path + '/*' + extension)
                paths.extend(glob.glob(path + '/**/*' + extension))
                paths.extend(glob.glob(path + '/***/**/*' + extension))
                for idx, path in enumerate(paths):
                    if regex.search(path): continue
                    name, extension = os.path.splitext(os.path.basename(path))
                    matchValue = difflib.SequenceMatcher(None, filename, name).ratio()
                    if matchValue > tolerance:
                        tolerance = matchValue
                        result = path
    return result


def setRevitLink(doc, filepath):
    if os.path.isfile(filepath):
        with Transaction(doc, "SetRevitLink") as trx:
            try:
                trx.Start()
                global output
                modelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(filepath)
                rvtLinkType = RevitLinkType.Create(doc, modelPath, RevitLinkOptions(False))
                instance = RevitLinkInstance.Create(doc, rvtLinkType.ElementId)
                instance.Pinned = True
                trx.Commit()
            except Exception as e:
                output += "Error: {0}".format(e.message)
                trx.RollBack()
        return instance


def configureAndCleanAllLinks(doc, filename):
    collector = FilteredElementCollector(doc).OfClass(RevitLinkType)
    with Transaction(doc, "AdjustAllLinks") as trx:
        try:
            trx.Start()
            global output
            for idx, rvtLinkType in enumerate(collector.ToElements()):
                aTypeName = rvtLinkType.AttachmentType.ToString()
                if RevitLinkType.IsLoaded(doc, rvtLinkType.Id) and aTypeName == 'Attachment':
                    name = rvtLinkType.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
                    contains = any([segment for segment in re.findall(r'_(\w\w)_', filename) if segment in name])
                    if not contains: rvtLinkType.Unload(None)
                else:
                    doc.Delete(rvtLinkType.Id)
            trx.Commit()
        except Exception as e:
            output += "Error: {0}".format(e.message)
            trx.RollBack()


def getValidLevels(doc):
    provider = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    rule = FilterDoubleRule(provider, FilterNumericLessOrEqual(), float(250), 0.0005)
    levels = FilteredElementCollector(doc).OfClass(Level).WherePasses(ElementParameterFilter(rule)).ToElements()
    return sorted(levels, key=lambda x: x.Elevation)


def getStructuralElements(doc):
    builtInCats = List[BuiltInCategory]()
    builtInCats.Add(BuiltInCategory.OST_Grids)
    builtInCats.Add(BuiltInCategory.OST_Roofs)
    builtInCats.Add(BuiltInCategory.OST_Walls)
    builtInCats.Add(BuiltInCategory.OST_Ramps)
    builtInCats.Add(BuiltInCategory.OST_Floors)
    filter = ElementMulticategoryFilter(builtInCats)
    collector = FilteredElementCollector(doc).WherePasses(filter)
    return collector.WhereElementIsNotElementType().ToElements()


def getOutline(doc, transform, offset=5):
    minX = minY = minZ = maxX = maxY = maxZ = 0
    for instance in getStructuralElements(doc):
        if (instance.IsValidObject):
            location = instance.Location
            if isinstance(location, LocationCurve):
                pnt0 = location.Curve.GetEndPoint(0)
                pnt1 = location.Curve.GetEndPoint(1)
                minX = round(min(minX, pnt0.X, pnt1.X))
                minY = round(min(minY, pnt0.Y, pnt1.Y))
                minZ = round(min(minZ, pnt0.Z, pnt1.Z))
                maxX = round(max(maxX, pnt0.X, pnt1.X))
                maxY = round(max(maxY, pnt0.Y, pnt1.Y))
                maxZ = round(max(maxZ, pnt0.Z, pnt1.Z))
            if isinstance(location, LocationPoint):
                bbox = instance.get_BoundingBox(None)
                pnt0, pnt1 = bbox.Min, bbox.Max
                minX = round(min(minX, pnt0.X, pnt1.X))
                minY = round(min(minY, pnt0.Y, pnt1.Y))
                minZ = round(min(minZ, pnt0.Z, pnt1.Z))
                maxX = round(max(maxX, pnt0.X, pnt1.X))
                maxY = round(max(maxY, pnt0.Y, pnt1.Y))
                maxZ = round(max(maxZ, pnt0.Z, pnt1.Z))

    minPnt = transform.OfPoint(XYZ(minX - offset, minY - offset, minZ - offset * 3))
    maxPnt = transform.OfPoint(XYZ(maxX + offset, maxY + offset, maxZ + offset * 3))

    return minPnt, maxPnt


def deletedFlyingObjects(doc, view, minPnt, maxPnt):
    filter = BoundingBoxIsInsideFilter(Outline(minPnt, maxPnt))
    ids = FilteredElementCollector(doc).WherePasses(filter).ToElementIds()
    with Transaction(doc, "AdjustAllLinks") as trx:
        if instance(view, View3D):
            try:
                trx.Start()
                global output
                collector = FilteredElementCollector(doc, view.Id)
                collector = collector.WherePasses(ExclusionFilter(ids))
                doc.Delete(collector.ToElementIds())
                output = "Flying objects deleted!"
                trx.Commit()
            except Exception as e:
                output = e.message
                trx.RollBack()


########################################################################################################################

filepath = doc.PathName
identity = Transform.Identity
filename = os.path.basename(filepath)
configureAndCleanAllLinks(doc, filename)
filename, extension = os.path.splitext(filename)
linkpath = retrieveArchModelPath(filepath, filename, extension)
if bool(linkpath) and os.path.exists(linkpath):
    instance = setRevitLink(doc, linkpath)
    linkDoc = instance.GetLinkDocument()
    minPnt, maxPnt = getOutline(linkDoc, identity)
    deletedFlyingObjects(doc, doc.ActiveView, minPnt, maxPnt)

########################################################################################################################
OUT = output
########################################################################################################################
