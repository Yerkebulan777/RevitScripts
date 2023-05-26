# -*- coding: utf-8 -*-
# !/usr/bin/python

import sys

reload(sys)
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.setdefaultencoding('utf-8')

# import parameters_script_util as ParamUtil
# import calculate_script_util as CalculateUtil
# import synchronization_script_util as SynchUtil
# import get_elements_script_util as GetElementsUtil
# import transaction_script_util as TransactionUtil

import clr

import System

clr.AddReference("System")
clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)

# from System.Collections.Generic import List
from System.Collections.Generic import *

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

########################################################################################################################
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI import TaskDialog

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName

TransactionManager.Instance.ForceCloseTransaction()
# = System.Enum.GetValues(BuiltInParameterGroup)

def Output(output):
    if isinstance(output, basestring):
        TaskDialog.Show("OUTPUT", output)
        return
########################################################################################################################
def transaction(action):
    from Library_develop import transaction_script_util as TransactionUtil
    wrapped = TransactionUtil.transaction(doc, action)
    return wrapped
########################################################################################################################

# clr.AddReference('ProtoGeometry')
# from Autodesk.DesignScript.Geometry import *
#
# clr.AddReference('RevitServices')
# from RevitServices.Persistence import DocumentManager
# from RevitServices.Transactions import TransactionManager
#
# clr.AddReference("RevitAPIUI")
# from Autodesk.Revit.UI import TaskDialog
#
# doc = DocumentManager.Instance.CurrentDBDocument
# app = DocumentManager.Instance.CurrentUIApplication.Application
# uiapp = DocumentManager.Instance.CurrentUIApplication
# uidoc = uiapp.ActiveUIDocument
# revit_file_path = doc.PathName
#
# TransactionManager.Instance.ForceCloseTransaction()

########################################################################################################################
OUT =  revit_file_path
########################################################################################################################
