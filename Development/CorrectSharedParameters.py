#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

import System
import clr

sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

# import libraries
import parameters_script_util as ParamUtil
import synchronization_script_util as SynchUtil

clr.AddReference("System")
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

clr.AddReference("System")
clr.AddReference("RevitAPI")

from Autodesk.Revit.DB import Transaction

import revit_script_util
from revit_script_util import Output

sessionId = revit_script_util.GetSessionId()
doc = revit_script_util.GetScriptDocument()

uiapp = revit_script_util.GetUIApplication()
uidoc = uiapp.ActiveUIDocument
app = uiapp.Application

revit_file_path = revit_script_util.GetRevitFilePath()
########################################################################################################################
foPath = os.path.realpath(r"K:\02_Библиотека\BIM\BID-BIM-CRT-004-RU_Файл общих параметров от 27.07.2021.txt")
if os.path.exists(foPath):
    defile = ParamUtil.load_shared_parameter_file(doc, foPath)
elif IN[0] and isinstance(IN[0], basestring) and os.path.exists(IN[0]):
    defile = ParamUtil.load_shared_parameter_file(doc, os.path.realpath(IN[0]))
else:
    Output("Please set general parameter file...")
########################################################################################################################
Output("\n\n\n  Start reinsert shared parameters... \n\n\n")
########################################################################################################################


with Transaction(doc, "Reinsert shared parameter") as trans:
    trans.Start()

    Output("\nStart reinsert BI_обозначение shared parameter ...\n")
    parameter_name, category_ids, parameter_group, instance = "BI_обозначение", None, "PG_IDENTITY_DATA", True
    result = ParamUtil.reset_shared_parameter(doc, parameter_name, category_ids, parameter_group, instance)
    Output(result)

    Output("\nStart reinsert BI_наименование shared parameter ...\n")
    parameter_name, category_ids, parameter_group, instance = "BI_наименование", None, "PG_IDENTITY_DATA", True
    result = ParamUtil.reset_shared_parameter(doc, parameter_name, category_ids, parameter_group, instance)
    Output(result)

    Output("\nStart reinsert BI_масса shared parameter ...\n")
    parameter_name, category_ids, parameter_group, instance = "BI_масса", None, "PG_GENERAL", True
    result = ParamUtil.reset_shared_parameter(doc, parameter_name, category_ids, parameter_group, instance)
    Output(result)

    Output("\nStart reinsert BI_масса_1_пм shared parameter ...\n")
    category_ids = ['-2009000', '-2001320']
    parameter_name, parameter_group, instance = "BI_масса_1_пм", "PG_GENERAL", True
    result = ParamUtil.reset_shared_parameter(doc, parameter_name, category_ids, parameter_group, instance)
    Output(result)

    Output("\nStart reinsert BI_длина shared parameter ...\n")
    category_ids = ['-2009000', '-2001320']
    parameter_name, parameter_group, instance = "BI_длина", "PG_GEOMETRY", True
    result = ParamUtil.reset_shared_parameter(doc, parameter_name, category_ids, parameter_group, instance)
    Output(result)

    Output("\nStart reinsert BI_диаметр_арматуры shared parameter ...\n")
    category_ids = ['-2009000']
    parameter_name, parameter_group, instance = "BI_диаметр_арматуры", "PG_GEOMETRY", False
    result = ParamUtil.reset_shared_parameter(doc, parameter_name, category_ids, parameter_group, instance)
    Output(result)

    doc.Regenerate()
    Output("\nStart check all shared parameters ...\n")
    result = ParamUtil.check_all_parameters(doc)
    Output(result)

    trans.Commit()

########################################################################################################################
Output('\n' + 100 * "#" + '\n')
Output("\nRevit file path is {}".format(revit_file_path))
result = SynchUtil.re_synchronization_file(doc, revit_file_path)
Output("\nSaving and synchronizing the document...")
Output(result)
########################################################################################################################
