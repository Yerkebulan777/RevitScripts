import clr

import System
from System import Guid, DateTime, Type, Text, IO
from System.IO import StreamReader, File, Directory, FileStream
from System.Collections.Generic import List
from System.Diagnostics import Stopwatch

clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.Creation import *

clr.AddReference('RevitAPIUI')
from Autodesk.Revit.UI import *

# from Autodesk.Revit.UI.Events import *
# from Autodesk.Revit.DB.Events import *

clr.AddReference("RevitNodes")
clr.AddReference("RevitServices")

import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager


class TimeCounter:
    def __init__(self):
        self.time = Stopwatch.StartNew()
        self.time.Start()

    def stop(self):
        self.time.Stop()
        time = self.time.Elapsed
        return ":".join([str(i) for i in [time.Minutes, time.Seconds, time.Milliseconds]])


# region -----------------------IFailuresProcessor----------------------
def FailureResolutionTypes():
    fail_res_types = []
    fail_res_types.append(FailureResolutionType.Invalid)
    fail_res_types.append(FailureResolutionType.Default)
    fail_res_types.append(FailureResolutionType.CreateElements)
    fail_res_types.append(FailureResolutionType.DeleteElements)
    fail_res_types.append(FailureResolutionType.SkipElements)
    fail_res_types.append(FailureResolutionType.MoveElements)
    fail_res_types.append(FailureResolutionType.FixElements)
    fail_res_types.append(FailureResolutionType.DetachElements)
    fail_res_types.append(FailureResolutionType.QuitEditMode)
    fail_res_types.append(FailureResolutionType.UnlockConstraints)
    fail_res_types.append(FailureResolutionType.SetValue)
    fail_res_types.append(FailureResolutionType.SaveDocument)
    fail_res_types.append(FailureResolutionType.ShowElements)
    fail_res_types.append(FailureResolutionType.Others)
    return fail_res_types


def FailListDict():
    clr_binf_type = clr.GetClrType(BuiltInFailures)  # BINGO
    clr_list_of_binf_fails = clr_binf_type.GetNestedTypes()
    dict_binf_and_id = {
        "{0}.{1}".format(binf.FullName.replace("+", "."), binfprop.Name): binfprop.GetGetMethod().Invoke(binf, None) for
        binf in clr_list_of_binf_fails for binfprop in binf.GetProperties()}
    return dict_binf_and_id


def fail_stat(fail_m):
    result = []
    ad_ids = [eid.IntegerValue for eid in fail_m.GetAdditionalElementIds()]
    fail_ids = [eid.IntegerValue for eid in fail_m.GetFailingElementIds()]
    has_res_of_type = ["{0} = {1}".format(str(res_type), str(fail_m.HasResolutionOfType(res_type))) for res_type in
                       FailureResolutionTypes() if fail_m.HasResolutionOfType(res_type)]
    result.append("***")
    result.append(fail_m.HasResolutions())  # 0
    result.append("FailureType = {0}".format(fail_m.GetSeverity()))  # 1
    result.append(fail_m.GetDescriptionText())  # 2
    result.append(fail_m.GetDefaultResolutionCaption())  # 3
    if fail_m.HasResolutions():
        result.append("CurrentResolutionType = {}".format(fail_m.GetCurrentResolutionType()))  # 4
    else:
        result.append("CurrentResolutionType = {}".format("does not have any resolutions"))
    result.append(fail_m.GetNumberOfResolutions())  # 5
    result.append(fail_m.GetFailureDefinitionId().Guid)
    # result.append(fail_def_reg.FindFailureDefinition(fail_m.GetFailureDefinitionId()))# 6
    result.append("AdditionalElementIds: {}".format(ad_ids))  # 7
    result.append("FailingElementIds: {}".format(fail_ids))  # 8
    result.append(has_res_of_type)  # 9
    result.append([(item[0], str(item[1].Guid.ToString())) for item in FailListDict().items() if
                   item[1] == fail_m.GetFailureDefinitionId()])
    result.append("***")
    string_list = [str(r) for r in result]
    return string_list


class WarningSwallower_BC(IFailuresProcessor):
    def ProcessFailures(self, failuresAccessor):
        fail_messages = failuresAccessor.GetFailureMessages()  # IList<FailureMessageAccessor>
        try:
            for fail_m in fail_messages:
                info = fail_stat(fail_m)
                if fail_m.GetSeverity() == FailureSeverity.Warning:
                    failuresAccessor.DeleteWarning(fail_m)
                    LogSave(info)
                    return FailureProcessingResult.Continue
                else:
                    failuresAccessor.ResolveFailure(fail_m)
                    LogSave(info)
                    return FailureProcessingResult.ProceedWithCommit
        except Exception as e:
            tb2 = sys.exc_info()[2]
            line = tb2.tb_lineno
            LogSave(["IFailuresProcessor: Code error on line {0} Has failure {1}".format(str(line), str(e))])

    def Dismiss(self, current_doc):
        pass


# endregion -----------------------IFailuresProcessor----------------------


current_doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
# uiapp.DialogBoxShowing += UiAppOnDialogBoxShowing
app.RegisterFailuresProcessor(WarningSwallower_BC())

path_to_folder_file = 'C:/RS_logs/'
log_file_name = 'Rooms_recover_info.log'
path_to_log_file = "{}{}".format(path_to_folder_file, log_file_name)
test = []

if not Directory.Exists(path_to_folder_file):
    Directory.CreateDirectory(path_to_folder_file)


def LogSave(info):
    if info:
        string_list_info = []
        string_list_info.append("")
        string_list_info.append(DateTime.Now.ToLocalTime().ToString())
        string_list_info.extend(info)
        IO.File.AppendAllLines(path_to_log_file, string_list_info, Text.Encoding.Unicode)


# def dialog(sender_uiapp, args):
# 	td = TaskDialog("любое событие")
# 	td.MainInstruction = "ещё какойто текст"
# 	td.Id = "наш собственный ID таск диалога"
# 	td.Show()


opn_opt = OpenOptions()
opn_opt.Audit = True
opn_opt.DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets
workset_config = WorksetConfiguration(WorksetConfigurationOption.CloseAllWorksets)
opn_opt.SetOpenWorksetsConfiguration(workset_config)

wrksh_svas_opt = WorksharingSaveAsOptions()
wrksh_svas_opt.SaveAsCentral = True
# sv_as_opt = SaveAsOptions()
# sv_as_opt.Compact = True
# sv_as_opt.OverwriteExistingFile = True
# sv_as_opt.SetWorksharingOptions(wrksh_svas_opt)

# transOpts = TransactWithCentralOptions()

# syncOpts = SynchronizeWithCentralOptions()
# relinquishOpts = RelinquishOptions(True)
# syncOpts.SetRelinquishOptions(relinquishOpts)
# syncOpts.SaveLocalAfter = False


# test = []

# rooms_in_current_doc = FilteredElementCollector(current_doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType().ToElementIds()
current_doc_rooms_placed_id_int = [room.Id.IntegerValue for room in FilteredElementCollector(current_doc).OfCategory(
    BuiltInCategory.OST_Rooms).WhereElementIsNotElementType() if room.Location is not None]
# current_doc_rooms_tag = FilteredElementCollector(current_doc).OfCategory(BuiltInCategory.OST_RoomTags).WhereElementIsNotElementType().ToElements()

backup_path = IN[0]  # noqa
backup_mpath = ModelPathUtils.ConvertUserVisiblePathToModelPath(backup_path)
backup_doc = app.OpenDocumentFile(backup_mpath, opn_opt)

# rooms_in_backup_doc = FilteredElementCollector(backup_doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType().ToElementIds()
backup_doc_rooms_placed_id_int = [room.Id.IntegerValue for room in FilteredElementCollector(backup_doc).OfCategory(
    BuiltInCategory.OST_Rooms).WhereElementIsNotElementType() if room.Location is not None]
backup_doc_rooms_tag = FilteredElementCollector(backup_doc).OfCategory(
    BuiltInCategory.OST_RoomTags).WhereElementIsNotElementType().ToElements()

recovered_counter = TimeCounter()
elems_id_to_recover = List[ElementId]()

backup_tags_room_id = [tag.TaggedLocalRoomId.IntegerValue for tag in backup_doc_rooms_tag if
                       tag.GetType() == Autodesk.Revit.DB.Architecture.RoomTag]
# test2 = [tag.OwnerViewId.IntegerValue for tag in backup_doc_rooms_tag]
missing_rooms_ids_int = []
missing_rooms_ids = List[ElementId]()
room_counter = 0

for backup_room_id in backup_doc_rooms_placed_id_int:
    if backup_room_id in current_doc_rooms_placed_id_int:
        pass
    else:
        missing_rooms_ids.Add(ElementId(backup_room_id))
        missing_rooms_ids_int.append(backup_room_id)
if not IN[1]:  # noqa
    TransactionManager.Instance.EnsureInTransaction(current_doc)
    new_rooms_ids = ElementTransformUtils.CopyElements(backup_doc, missing_rooms_ids, current_doc, None, None)
    room_counter = len(new_rooms_ids)
    TransactionManager.Instance.ForceCloseTransaction()

tags_views_dict = {}

# tags_views = set()

# new_rooms_tags = []
# new_recovered_rooms_ids = []

# fail_log = []

tag_counter = 0

# if IN[1]:
# test3 = []

created_elems = {}

if IN[1]:  # noqa
    for tag in backup_doc_rooms_tag:
        if tag.GetType() == Autodesk.Revit.DB.Architecture.RoomTag:
            if tag.TaggedLocalRoomId.IntegerValue in missing_rooms_ids_int:
                tag_view_id = tag.OwnerViewId.IntegerValue
                if tag_view_id in tags_views_dict:
                    tags_views_dict[tag_view_id].append(
                        [tag.TaggedLocalRoomId.IntegerValue, tag.Location.Point, tag.RoomTagType,
                         backup_doc.GetElement(tag.TaggedLocalRoomId).Number])
                else:
                    tags_views_dict[tag_view_id] = [
                        [tag.TaggedLocalRoomId.IntegerValue, tag.Location.Point, tag.RoomTagType,
                         backup_doc.GetElement(tag.TaggedLocalRoomId).Number]]
    TransactionManager.Instance.ForceCloseTransaction()
    transaction_group = TransactionGroup(current_doc, 'Rooms and Tags recovery')
    test5 = transaction_group.Start()
    # try:
    for view_id, tags_tasks in tags_views_dict.items():
        for old_room_id_int in tags_tasks:
            # try:
            if old_room_id_int[0] not in created_elems:
                test4 = List[ElementId]()
                test4.Add(ElementId(old_room_id_int[0]))
                transaction = Transaction(current_doc, "local1")
                transaction.Start()
                new_rooms_ids = ElementTransformUtils.CopyElements(backup_doc, test4, current_doc, None, None)
                transaction.Commit()
                transaction = Transaction(current_doc, "local1.1")
                transaction.Start()
                current_doc.GetElement(new_rooms_ids[0]).Number = old_room_id_int[3]
                transaction.Commit()
                created_elems[old_room_id_int[0]] = new_rooms_ids[0]
                transaction = Transaction(current_doc, "local2")
                transaction.Start()
                if old_room_id_int[2].GetType() == Autodesk.Revit.DB.Architecture.RoomTagType:
                    new_tag = current_doc.Create.NewRoomTag(LinkElementId(new_rooms_ids[0]),
                                                            UV(old_room_id_int[1].X, old_room_id_int[1].Y),
                                                            ElementId(view_id))
                    new_tag.RoomTagType = old_room_id_int[2]
                    tag_counter += 1
                transaction.Commit()
                room_counter += 1
            else:
                transaction = Transaction(current_doc, "local3")
                transaction.Start()
                if old_room_id_int[2].GetType() == Autodesk.Revit.DB.Architecture.RoomTagType:
                    new_tag = current_doc.Create.NewRoomTag(LinkElementId(created_elems[old_room_id_int[0]]),
                                                            UV(old_room_id_int[1].X, old_room_id_int[1].Y),
                                                            ElementId(view_id))
                    new_tag.RoomTagType = old_room_id_int[2]
                    tag_counter += 1
                transaction.Commit()
    # except: # noqa
    # 	transaction.RollBack()
    # 	pass
    transaction_group.Assimilate()

# transaction_group.Commit()
# TransactionManager.Instance.ForceCloseTransaction()
# uiapp.DialogBoxShowing -= UiAppOnDialogBoxShowing
recovered_time = recovered_counter.stop()
# TransactionManager.Instance.EnsureInTransaction(current_doc)
# current_doc.Regenerate()
# TransactionManager.Instance.ForceCloseTransaction()

backup_doc.Close(False)
OUT = ["recovered_time", recovered_time], ["room_counter", room_counter], ["tag_counter", tag_counter]
