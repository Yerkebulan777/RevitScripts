#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
import difflib
import glob
import os
import re

import clr

clr.AddReference("System")
clr.AddReference("System.Core")

from System.IO import Path
from System.Collections.Generic import List

clr.AddReference('RevitAPI')
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import View3D
from Autodesk.Revit.DB import Element
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB import ModelPathUtils
from Autodesk.Revit.DB import XYZ, Transform
from Autodesk.Revit.DB import BuiltInFailures
from Autodesk.Revit.DB import ElementId, Level
from Autodesk.Revit.DB import FilterNumericLessOrEqual
from Autodesk.Revit.DB import LocationPoint, LocationCurve
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter
from Autodesk.Revit.DB import RevitLinkOptions, RevitLinkType, RevitLinkInstance
from Autodesk.Revit.DB import BoundingBoxIsInsideFilter, Outline, ExclusionFilter
from Autodesk.Revit.DB import IFailuresPreprocessor, FailureProcessingResult, FailureSeverity, FailureResolutionType
from Autodesk.Revit.DB import ParameterValueProvider, ElementParameterFilter
from Autodesk.Revit.DB import ElementMulticategoryFilter, BuiltInCategory
from Autodesk.Revit.DB import ViewFamily, ViewFamilyType, ViewType
from Autodesk.Revit.DB import FilterDoubleRule

########################################################################################################################

import revit_file_util
import revit_script_util
from revit_script_util import Output

filepath = revit_script_util.GetRevitFilePath()
sessionId = revit_script_util.GetSessionId()
doc = revit_script_util.GetScriptDocument()
uiapp = revit_script_util.GetUIApplication()
uidoc = uiapp.ActiveUIDocument

########################################################################################################################

filename = doc.Title
identity = Transform.Identity
filename = filename.rstrip("_detached")
filename = filename.rstrip("_отсоединено")


########################################################################################################################

class WarningDismiss(IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):

        for failure in failuresAccessor.GetFailureMessages():

            time.sleep(0.5)
            fas = failure.GetSeverity()
            id = failure.GetFailureDefinitionId()

            if (fas == FailureSeverity.Error):
                Output("Error: {}".format(failure.GetDescriptionText()))
                failure.SetCurrentResolutionType(FailureResolutionType.Default)
                failuresAccessor.GetFailureHandlingOptions().SetClearAfterRollback(True)
                failuresAccessor.ResolveFailure(failure)
                return FailureProcessingResult.ProceedWithRollBack

            if (fas == FailureSeverity.Warning):
                Output("\nStarting check for a warning failure...")
                Output("Warning: {}".format(failure.GetDescriptionText()))
                Output("Warning definitionId: {}\n".format(failure.GetFailureDefinitionId()))

                if failuresAccessor.IsFailureResolutionPermitted(failure, FailureResolutionType.UnlockConstraints):
                    failure.SetCurrentResolutionType(FailureResolutionType.UnlockConstraints)
                    failuresAccessor.DeleteElements(failure.GetFailingElementIds())
                    failuresAccessor.ResolveFailure(failure)

                if failuresAccessor.IsFailureResolutionPermitted(failure, FailureResolutionType.DetachElements):
                    failure.SetCurrentResolutionType(FailureResolutionType.DetachElements)
                    failuresAccessor.DeleteElements(failure.GetFailingElementIds())
                    failuresAccessor.ResolveFailure(failure)

                if failuresAccessor.IsFailureResolutionPermitted(FailureResolutionType.DeleteElements):
                    failure.SetCurrentResolutionType(FailureResolutionType.DeleteElements)
                    failuresAccessor.DeleteElements(failure.GetFailingElementIds())
                    failuresAccessor.ResolveFailure(failure)

            if (BuiltInFailures.GeneralFailures.DuplicateValue == id):
                Output("GeneralFailure duplicateValue: {}".format(failure.GetDescriptionText()))

            failuresAccessor.DeleteWarning(failure)
            return FailureProcessingResult.ProceedWithCommit

        return FailureProcessingResult.Continue


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
    if not os.path.isdir(result):
        os.makedirs(result)
    return result


def getValidLevels(doc):
    provider = ParameterValueProvider(ElementId(BuiltInParameter.LEVEL_ELEV))
    rule = FilterDoubleRule(provider, FilterNumericLessOrEqual(), float(250), 0.0005)
    levels = FilteredElementCollector(doc).OfClass(Level).WherePasses(ElementParameterFilter(rule)).ToElements()
    return sorted(levels, key=lambda x: x.Elevation)


def retrieveArchModelPath(filepath, filename, extension='.rvt', tolerance=0.75, result=None):
    Output("Start search AR for {} ... ".format(filename))
    directory = getSubdirectory(filepath, 'PROJECT')
    directory = os.path.dirname(directory)
    regex = re.compile(r'#')
    for folder in os.listdir(directory):
        if (folder.endswith('AR') or folder.endswith('AS')):
            path = os.path.join(directory, folder)
            if os.path.isdir(path) and extension:
                paths = glob.glob(path + '/*' + extension)
                paths.extend(glob.glob(path + '/**/*' + extension))
                paths.extend(glob.glob(path + '/***/**/*' + extension))
                for idx, path in enumerate(paths):
                    if regex.search(path): continue
                    name, extension = os.path.splitext(os.path.basename(path))
                    matchValue = difflib.SequenceMatcher(None, filename, name).ratio()
                    if matchValue > tolerance:
                        Output("Match name {}".format(name))
                        tolerance = matchValue
                        result = path

    return result


def setRevitLink(doc, filepath, linkDoc=None):
    if os.path.isfile(filepath):
        with Transaction(doc, "SetRevitLink") as trx:
            try:
                trx.Start()
                filename = os.path.basename(filepath)
                modelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(filepath)
                rvtLinkType = RevitLinkType.Create(doc, modelPath, RevitLinkOptions(False))
                instance = RevitLinkInstance.Create(doc, rvtLinkType.ElementId)
                Output("\nLoaded revit link: {}".format(filename))
                linkDoc = instance.GetLinkDocument()
                instance.Pinned = True
                trx.Commit()
            except Exception as e:
                Output("\n{0}\n".format(e.args))
                trx.RollBack()
                time.sleep(5)

    return linkDoc


def configureAndCleanAllLinks(doc, filename):
    collector = FilteredElementCollector(doc).OfClass(RevitLinkType)
    with Transaction(doc, "AdjustAllLinks") as trx:
        try:
            trx.Start()
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
            Output("\n{0}\n".format(e.args))
            trx.RollBack()
            time.sleep(5)


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


def create3dView(doc):
    viewFamilyTypes = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
    viewFamilyType3D = [vft for vft in viewFamilyTypes if vft.ViewFamily == ViewFamily.ThreeDimensional][0]
    with Transaction(doc, "3dView") as trx:
        trx.Start()
        view3d = View3D.CreateIsometric(doc, viewFamilyType3D.Id)
        Output("Creation 3D view is done: {}".format(view3d.Name))
        if view3d.ViewTemplateId != ElementId.InvalidElementId:
            view3d.ViewTemplateId = ElementId.InvalidElementId
        if view3d.CanModifyDisplayStyle():
            view3d.get_Parameter(BuiltInParameter.MODEL_GRAPHICS_STYLE).Set(3)
        if view3d.CanModifyViewDiscipline():
            view3d.get_Parameter(BuiltInParameter.VIEW_DISCIPLINE).Set(4095)
        if view3d.CanModifyDetailLevel():
            view3d.get_Parameter(BuiltInParameter.VIEW_DETAIL_LEVEL).Set(1)
        trx.Commit()
    return view3d


def deletedFlyingObjects(doc, view, minPnt, maxPnt):
    ids = List[ElementId]()
    filter = BoundingBoxIsInsideFilter(Outline(minPnt, maxPnt))
    ids.AddRange(FilteredElementCollector(doc).OfClass(Level).ToElementIds())
    ids.AddRange(FilteredElementCollector(doc).WherePasses(filter).ToElementIds())
    with Transaction(doc, "DeletedFlyingObjects") as trx:
        if view.ViewType == ViewType.ThreeD:
            Output("Start search flying objects...")
            collector = FilteredElementCollector(doc, view.Id)
            collector = collector.WherePasses(ExclusionFilter(ids))
            elements = collector.ToElements()
            trx.Start()

            Output("Found: {}".format(len(elements)))
            options = trx.GetFailureHandlingOptions()
            options.SetFailuresPreprocessor(WarningDismiss())
            trx.SetFailureHandlingOptions(options)
            bip = BuiltInParameter.ALL_MODEL_MARK
            for idx, elem in enumerate(elements):
                if elem.IsValidObject:
                    Element.Pinned.SetValue(elem, False)
                    param = elem.get_Parameter(bip)
                    if bool(param): param.Set('')
                    doc.Delete(elem.Id)

            trx.Commit()


def saveAsRevitOutFile(doc, root, filename, extension='.rvt'):
    filename = filename.rstrip(extension) + extension
    saveRevitFilePath = Path.Combine(root, filename)
    Output("\nSaved: {}".format(saveRevitFilePath))
    if doc.IsWorkshared:
        saveRevitModelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(saveRevitFilePath)
        revit_file_util.SaveAsNewCentral(doc, saveRevitModelPath, True)
        revit_file_util.RelinquishAll(doc)
    else:
        revit_file_util.SaveAs(doc, saveRevitFilePath, True)

    return os.startfile(root)


########################################################################################################################

minPnt = maxPnt = XYZ.Zero
view3D = create3dView(doc)
configureAndCleanAllLinks(doc, filename)
directory = determineDirectory(filepath, "07_BIM")
linkpath = retrieveArchModelPath(filepath, filename)
if linkpath is None:
    Output("WARNING: Not found link path")
if filepath == linkpath:
    minPnt, maxPnt = getOutline(doc, identity)
if linkpath and os.path.exists(linkpath):
    linkDoc = setRevitLink(doc, linkpath)
    if linkDoc: minPnt, maxPnt = getOutline(linkDoc, identity)

########################################################################################################################

time.sleep(30)
midPnt = (minPnt + maxPnt) * 0.5
if False == midPnt.IsZeroLength():
    Output('\n' + '<>' * 100 + '\n')
    deletedFlyingObjects(doc, view3D, minPnt, maxPnt)
    saveAsRevitOutFile(doc, directory, filename)
    Output('\n' + '<>' * 100 + '\n')

########################################################################################################################

Output("\nScript completed successfully without errors")

########################################################################################################################
