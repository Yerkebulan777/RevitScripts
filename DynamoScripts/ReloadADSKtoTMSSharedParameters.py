#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.append(r"C:\Program Files (x86)\IronPython 2.7\Lib")
sys.path.append(r"D:\YandexDisk\RevitExportConfig\Library")

import os
import re
import clr

import parameter_script_util as ParamUtil

clr.AddReference('RevitAPI')

from Autodesk.Revit.DB import InstanceBinding, TypeBinding, Transaction

clr.AddReference("System")
clr.AddReference("System.Core")

from System.IO import Path

########################################################################################################################
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

clr.AddReference("RevitAPIUI")

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

doc = DocumentManager.Instance.CurrentDBDocument
app = DocumentManager.Instance.CurrentUIApplication.Application
uiapp = DocumentManager.Instance.CurrentUIApplication
uidoc = uiapp.ActiveUIDocument
revit_file_path = doc.PathName
revit_file_name = Path.GetFileNameWithoutExtension(revit_file_path)
TransactionManager.Instance.ForceCloseTransaction()


def Output(output):
    if isinstance(output, basestring):
        # TaskDialog.Show("OUTPUT", output)
        return


########################################################################################################################
foPath = os.path.realpath(r"K:\02_Библиотека\BIM\TMS_FOP.txt")
defile = ParamUtil.load_shared_parameter_file(doc, foPath) if os.path.exists(foPath) else None


########################################################################################################################

def get_all_external_definitions(doc):
    defile = doc.Application.OpenSharedParameterFile()
    def_grp = [g.Definitions for g in defile.Groups]
    ext_params = [x for l in def_grp for x in l]
    ext_names = [x.Name for x in ext_params]
    ext_guids = [x.GUID for x in ext_params]
    return ext_params, ext_names, ext_guids


def remove_parameter_binding(doc, parameter_name):
    map = doc.ParameterBindings
    iterator = map.ForwardIterator()
    iterator.Reset()
    message = "Deleted shared parameter {}".format(parameter_name)
    while iterator.MoveNext():
        if iterator.Key != None and iterator.Key.Name == parameter_name:
            definition = iterator.Key
            sip_parameter = doc.GetElement(definition.Id)
            if (0 == doc.Delete(sip_parameter.Id).Count):
                map.Remove(definition)
                return message


def reinsert_shared_parameter(doc, definition, category_set, parameter_group, is_instance=True):
    if (is_instance):
        binding_cats = doc.Application.Create.NewInstanceBinding(category_set)
    else:
        binding_cats = doc.Application.Create.NewTypeBinding(category_set)
    parameter_name = definition.Name
    message = " Failed to bind parameter "
    try:
        if (doc.ParameterBindings.Insert(definition, binding_cats, parameter_group)):
            message = parameter_name + " : parameter successfully bound"
            return message
        else:
            if (doc.ParameterBindings.ReInsert(definition, binding_cats, parameter_group)):
                message = parameter_name + " : parameter successfully bound"
                return message
            else:
                remove_parameter_binding(doc, parameter_name)
                if (doc.ParameterBindings.Insert(definition, binding_cats, parameter_group)):
                    message = parameter_name + " : parameter successfully bound"
    except Exception as e:
        message = parameter_name + " : Failed to bind parameter with exception: " + str(e)
    return message


def get_external_definition(doc, parameter_name):
    app = doc.Application
    defile = app.OpenSharedParameterFile()
    for group in defile.Groups:
        if group.Definitions.Contains(group.Definitions.Item[parameter_name]):
            definition = group.Definitions.Item[parameter_name]
            return definition


def reload_similar_shared_parameter(doc, parameter_name, prefix_source, prefix_target):
    if prefix_source and not parameter_name.startswith(prefix_source.strip()): return
    source_definition = get_external_definition(doc, parameter_name)
    source_name = re.sub(prefix_source, '', parameter_name).strip()
    source_name = re.sub('_', ' ', source_name).strip()
    if not bool(source_definition): return
    binding_map = doc.ParameterBindings
    iterator = binding_map.ForwardIterator()
    iterator.Reset()
    while iterator.MoveNext():
        instance = None
        definition = iterator.Key
        element_bind = iterator.Current
        if (definition.IsValidObject and prefix_target):
            if (definition.Name.startswith(prefix_target)):
                target_name = re.sub('_', ' ', definition.Name).strip()
                target_name = re.sub(prefix_target, '', target_name).strip()
                if source_name == target_name:
                    group = definition.ParameterGroup
                    categories = binding_map.Item[definition].Categories
                    if isinstance(element_bind, InstanceBinding): instance = True
                    if isinstance(element_bind, TypeBinding): instance = False
                    remove = True if doc.Delete(definition.Id) else binding_map.Remove(definition)
                    if remove: return reinsert_shared_parameter(doc, source_definition, categories, group, instance)


ext_params, ext_names, ext_guids = get_all_external_definitions(doc)
# parameters = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToElements()
# prm_names = [prm.Name for prm in parameters]
########################################################################################################################
output = []
prefix_source = "TMS"
prefix_target = "ADSK"
with Transaction(doc, "Reload Shared Parameters") as trans:
    trans.Start()
    for ext_name in ext_names:
        result = reload_similar_shared_parameter(doc, ext_name, prefix_source, prefix_target)
        if result: output.append(ext_name)
    trans.Commit()
########################################################################################################################
OUT = output
