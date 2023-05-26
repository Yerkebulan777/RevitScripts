import System
import clr

clr.AddReference("System.Core")
clr.ImportExtensions(System.Linq)
import Autodesk
import script_util
import revit_script_util
from revit_script_util import Output

sessionId = script_util.GetSessionId()

# NOTE: this only make sense for batch Revit file processing mode.
revitFileListFilePath = script_util.GetRevitFileListFilePath()
uiapp = revit_script_util.GetUIApplication()
doc = revit_script_util.GetScriptDocument()
# NOTE: these only make sense for data export mode.
sessionDataFolderPath = script_util.GetSessionDataFolderPath()
dataExportFolderPath = script_util.GetExportFolderPath()

# TODO: some real work!
Output()
Output("Pre-processing script is running!")
commandId = Autodesk.Revit.UI.RevitCommandId.LookupPostableCommandId(Autodesk.Revit.UI.PostableCommand.PurgeUnused)
uiapp.PostCommand(commandId)