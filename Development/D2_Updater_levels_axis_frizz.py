import clr
import sys

sys.path.append("D:/code/py_libs")

# clr.AddReference('Win32Api')
# from Win32Api import Win32Api

import System
from System import Guid, DateTime, Type, Text, IO
from System.IO import StreamReader, File, Directory, FileStream
from System.Collections.Generic import List

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Events import *
from Autodesk.Revit.DB.Events import *

clr.AddReference("RevitNodes")
clr.AddReference("RevitServices")

import RevitServices
from RevitServices.Persistence import DocumentManager

# from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument
ui_app = DocumentManager.Instance.CurrentUIApplication
app = ui_app.Application
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
user_name = app.Username

path_to_folder_file = 'C:/RS_logs/'
log_file_name = 'D2_Updater_info.log'
path_to_log_file = "{}{}".format(path_to_folder_file, log_file_name)
test = []

if not Directory.Exists(path_to_folder_file):
    Directory.CreateDirectory(path_to_folder_file)


def LogSave(info):
    if info:
        string_list_info = []
        string_list_info.append("")
        string_list_info.append(DateTime.Now.ToLocalTime().ToString())
        # string_list_info.append(python_file_name)
        string_list_info.extend(info)
        IO.File.AppendAllLines(path_to_log_file, string_list_info, Text.Encoding.Unicode)


class ParamAutoWrite(IUpdater):
    def Execute(self, data):
        try:
            updater_doc = data.GetDocument()
            new_elems = data.GetAddedElementIds()
            del_elems = data.GetDeletedElementIds()
            modif_elems = data.GetModifiedElementIds()

            test.append(len(del_elems))

            if (del_elems.Count > 0):
                for elementId in del_elems:
                    self.UpdateParamsForElem(updater_doc, elementId, "del")

            if (new_elems.Count > 0):
                for elementId in new_elems:
                    self.UpdateParamsForElem(updater_doc, elementId, "new")

            if (modif_elems.Count > 0):
                for elementId in modif_elems:
                    self.UpdateParamsForElem(updater_doc, elementId, "modif")
        except Exception as e:
            tb2 = sys.exc_info()[2]
            line = tb2.tb_lineno
            LogSave(["ParamAutoWrite: Code error on line {0} Has failure {1}".format(str(line), str(e))])

    def GetAdditionalInformation(self):
        info = "ParamAutoWrite info"
        return info

    def GetChangePriority(self):
        return ChangePriority.FreeStandingComponents

    def GetUpdaterId(self):
        dynamo_id = AddInId(ui_app.ActiveAddInId.GetGUID())
        return UpdaterId(dynamo_id, Guid("0ef61eac-d4a0-4cb2-89ba-4b636fab1a14"))

    def GetUpdaterName(self):
        return "ID-ParamAutoWrite"

    def UpdateParamsForElem(self, updater_doc, elementId, change_name):
        td = TaskDialog("Brain don't")
        td.MainContent = "Изменение уровней и осей запрещено"
        td.MainIcon = TaskDialogIcon.TaskDialogIconShield
        td.Show()
        ui_app.PostCommand(RevitCommandId.LookupPostableCommandId(PostableCommand.Undo))
        LogSave([updater_doc.Title, '{} {} {} {}'.format("Change type:", change_name, "try by:", user_name)])
    # elem = updater_doc.GetElement(elementId)
    # coord_param = elem.LookupParameter("Комментарии")
    # if coord_param:
    # 	coord_param.Set("Привет")


def dialog(sender_uiapp, args):
    td = TaskDialog("любое событие")
    td.MainInstruction = "ещё какойто текст"
    td.Id = "наш собственный ID таск диалога"
    td.Show()


if IN[0]:  # noqa
    r_updater = ParamAutoWrite()
    ilst_of_build_cat = List[BuiltInCategory]([BuiltInCategory.OST_Levels, BuiltInCategory.OST_Grids])
    multi_cat_filter = ElementMulticategoryFilter(ilst_of_build_cat)
    if not UpdaterRegistry.IsUpdaterRegistered(r_updater.GetUpdaterId()):
        TaskDialog("Updater ON").Show()
        UpdaterRegistry.RegisterUpdater(r_updater, True)
        # UpdaterRegistry.SetIsUpdaterOptional(r_updater.GetUpdaterId(), False)
        UpdaterRegistry.AddTrigger(r_updater.GetUpdaterId(), multi_cat_filter, Element.GetChangeTypeAny())
        UpdaterRegistry.AddTrigger(r_updater.GetUpdaterId(), multi_cat_filter, Element.GetChangeTypeElementAddition())
        UpdaterRegistry.AddTrigger(r_updater.GetUpdaterId(), multi_cat_filter, Element.GetChangeTypeElementDeletion())
        UpdaterRegistry.EnableUpdater(r_updater.GetUpdaterId())
    else:
        TaskDialog("Updater Off").Show()
        UpdaterRegistry.UnregisterUpdater(r_updater.GetUpdaterId())
    OUT = test, "GO"
else:
    OUT = test, "not go"
