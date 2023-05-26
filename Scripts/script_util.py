#
# Revit Batch Processor
#
# Copyright (c) 2020  Dan Rumery, BVN
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

from System.IO import Path

import path_util

PYTHON_SCRIPT_FILE_EXTENSION = ".py"
DYNAMO_SCRIPT_FILE_EXTENSION = ".dyn"

SESSION_ID_CONTAINER = [None]
TASK_DATA_CONTAINER = [None]
EXPORT_FOLDER_PATH_CONTAINER = [None]
SESSION_DATA_FOLDER_PATH_CONTAINER = [None]
REVIT_FILE_LIST_FILE_PATH_CONTAINER = [None]


def SetSessionId(batchRvtConfig):
    SESSION_ID_CONTAINER[0] = batchRvtConfig.SessionId
    return


def SetTaskData(batchRvtConfig):
    TASK_DATA_CONTAINER[0] = batchRvtConfig.TaskData
    return


def SetExportFolderPath(batchRvtConfig):
    EXPORT_FOLDER_PATH_CONTAINER[0] = batchRvtConfig.DataExportFolderPath
    return


def SetSessionDataFolderPath(batchRvtConfig):
    SESSION_DATA_FOLDER_PATH_CONTAINER[0] = batchRvtConfig.SessionDataFolderPath
    return


def SetRevitFileListFilePath(batchRvtConfig):
    REVIT_FILE_LIST_FILE_PATH_CONTAINER[0] = batchRvtConfig.RevitFileListFilePath
    return


def GetSessionId():
    sessionId = SESSION_ID_CONTAINER[0]
    return sessionId


def GetTaskData():
    taskData = TASK_DATA_CONTAINER[0]
    return taskData


def GetExportFolderPath():
    exportFolderPath = EXPORT_FOLDER_PATH_CONTAINER[0]
    return exportFolderPath


def GetSessionDataFolderPath():
    sessionDataFolderPath = SESSION_DATA_FOLDER_PATH_CONTAINER[0]
    return sessionDataFolderPath


def GetRevitFileListFilePath():
    revitFileListFilePath = REVIT_FILE_LIST_FILE_PATH_CONTAINER[0]
    return revitFileListFilePath


def ExecuteScript(scriptFilePath):
    path_util.AddSearchPath(Path.GetDirectoryName(scriptFilePath))
    try:
        scriptGlobals = {}
        execfile(scriptFilePath, scriptGlobals)
    except Exception as e:
        return e
    return
