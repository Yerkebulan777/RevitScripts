# -*- coding: UTF-8 -*-
# This section is common to all Python task scripts.

import os
import time

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import TransactWithCentralOptions, SynchronizeWithCentralOptions
from Autodesk.Revit.DB import SaveAsOptions, WorksharingSaveAsOptions, BasicFileInfo
from Autodesk.Revit.DB import RelinquishOptions, WorksharingUtils, ModelPathUtils

# from Autodesk.Revit.DB.Structure import *
# from Autodesk.Revit.ApplicationServices import *
# from Autodesk.Revit.Attributes import *
# from Autodesk.Revit.UI import *
# from Autodesk.Revit.UI.Selection import *
# from Autodesk.Revit.Exceptions import *

import System

clr.ImportExtensions(System.Linq)
from System.IO import *
from System.Linq import *


########################################################################################################################
def is_new_file(filename, days=7):
    source = os.path.realpath(filename)
    creation_time = os.stat(source).st_ctime
    seconds = time.time() - (days * 24 * 60 * 60)
    if seconds > creation_time: return True


def is_local_model(filepath):
    isLocalModel = False
    basicFileInfo = BasicFileInfo.Extract(filepath)
    if basicFileInfo is not None:
        isWorkshared = basicFileInfo.IsWorkshared
        if isWorkshared:
            isLocalModel = (basicFileInfo.IsCreatedLocal or basicFileInfo.IsLocal)
    return isLocalModel


def save_as_central_file(doc, filepath):
    saveAsOptions = SaveAsOptions()
    saveAsOptions.Compact = False
    saveAsOptions.MaximumBackups = 3
    saveAsOptions.OverwriteExistingFile = True
    worksharingSaveAsOptions = WorksharingSaveAsOptions()
    worksharingSaveAsOptions.SaveAsCentral = True
    worksharingSaveAsOptions.ClearTransmitted = False
    saveAsOptions.SetWorksharingOptions(worksharingSaveAsOptions)
    modelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(filepath)
    doc.SaveAs(modelPath, saveAsOptions)
    return filepath


def synchronization(doc):
    message = "Is not shared file"
    if doc.IsWorkshared:
        opt = RelinquishOptions(False)
        opt.CheckedOutElements = True
        opt.StandardWorksets = True
        opt.FamilyWorksets = True
        opt.ViewWorksets = True
        opt.UserWorksets = True
        transOpts = TransactWithCentralOptions()
        syncopt = SynchronizeWithCentralOptions()
        syncopt.Comment = "Synchronised by RBP"
        syncopt.SaveLocalBefore = False
        syncopt.SaveLocalAfter = False
        syncopt.Compact = False
        syncopt.SetRelinquishOptions(opt)
        try:
            WorksharingUtils.RelinquishOwnership(doc, opt, transOpts)
            doc.SynchronizeWithCentral(transOpts, syncopt)
            message = "Successfully synchronised file"
        except Exception as e:
            message = "Failed with exception: " + str(e)
    return message

########################################################################################################################
