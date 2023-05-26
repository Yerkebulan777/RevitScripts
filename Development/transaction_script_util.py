# -*- coding: UTF-8 -*-
# This section is common to all Python task scripts.

import sys

sys.path.append("D:\YandexDisk\RevitExportConfig\Scripts")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")
sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import Transaction, ElementId, StorageType
from Autodesk.Revit.DB import IFailuresPreprocessor, FailureProcessingResult, FailureSeverity, BuiltInFailures


class warning_dismiss(IFailuresPreprocessor):
    def PreprocessFailures(self, failuresAccessor):
        for failure in failuresAccessor.GetFailureMessages():
            fail_severity = failure.GetSeverity()
            if (fail_severity == FailureSeverity.Warning):
                failuresAccessor.DeleteWarning(failure)
        return FailureProcessingResult.Continue


def transaction(doc, action):
    def wrapped(*args, **kwargs):
        with Transaction(doc, 'Automation') as trans:
            trans.Start()
            fail_options = trans.GetFailureHandlingOptions()
            fail_options.SetFailuresPreprocessor(warning_dismiss())
            trans.SetFailureHandlingOptions(fail_options)
            try:
                result = action(*args, **kwargs)
            except:
                result = None
                trans.RollBack()
            else:
                trans.Commit()
        return result
    return wrapped


def set_value_by_parameter_name(parameter_name, element, value):
    if element.IsValidObject and element.GroupId.Equals(ElementId.InvalidElementId):
        param, result = element.LookupParameter(parameter_name), None
        if param is None: return "Parameter not defined"
        if param.IsReadOnly: return "Parameter read only"
        if param.StorageType == StorageType.String:
            value = (value if isinstance(value, basestring) else str(value))
            result = param.Set(value)
        elif param.StorageType == StorageType.Double:
            value = (value if isinstance(value, float) else float(value))
            result = param.Set(value)
        elif param.StorageType == StorageType.Integer:
            value = (value if isinstance(value, int) else int(value))
            result = param.Set(value)
        return result


def set_parameter_value_by_guid(doc, guid, item, value):
    if guid and item is not None:
        if isinstance(item, ElementId): item = doc.GetElement(item)
        if item.GroupId.Equals(ElementId.InvalidElementId):
            param, result = item.get_Parameter(guid), None
            if param is None: return "Parameter not defined"
            if param.IsReadOnly: return "Parameter read only"
            if param.StorageType == StorageType.String:
                value = (value if isinstance(value, basestring) else str(value))
                result = param.Set(value)
            elif param.StorageType == StorageType.Double:
                value = (value if isinstance(value, float) else float(value))
                result = param.Set(value)
            elif param.StorageType == StorageType.Integer:
                value = (value if isinstance(value, int) else int(value))
                result = param.Set(value)
            return result


def rename_element_type(doc, item, name):
    if item.GetType().ToString() == "Autodesk.Revit.DB.FamilyParameter":
        try:
            doc.FamilyManager.RenameParameter(item, name)
            return name
        except:
            return
    elif item.GetType().ToString() == "Autodesk.Revit.DB.Workset":
        try:
            doc.GetWorksetTable().RenameWorkset(doc, item.Id, name)
            return name
        except:
            return
