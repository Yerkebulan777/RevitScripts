#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Revit Batch Processor

import random
import re

import clr

import global_test_mode
import script_host_error
import thread_util
import ui_automation_util
import win32_user32

clr.AddReference('System')
from System import String

REVIT_DIALOG_MESSAGE_HANDLER_PREFIX = "[ REVIT DIALOG BOX HANDLER ]"

MODEL_UPGRADE_WINDOW_TITLE = "Model Upgrade"
LOAD_LINK_WINDOW_TITLE = "Load Link"
CHANGES_NOT_SAVED_TITLE = "Changes Not Saved"
CLOSE_PROJECT_WITHOUT_SAVING_TITLE = "Close Project Without Saving"
SAVE_FILE_WINDOW_TITLE = "Save File"
EDITABLE_ELEMENTS_TITLE = "Editable Elements"
AUTODESK_CUSTOMER_INVOLVEMENT_PROGRAM_TITLE = "Autodesk Customer Involvement Program"
OPENING_WORKSETS_TITLES = [
    "Worksets",
    "Opening Worksets"
]

DIRECTUI_CLASS_NAME = "DirectUIHWND"
CTRLNOTIFYSINK_CLASS_NAME = "CtrlNotifySink"
STATIC_CONTROL_CLASS_NAME = "Static"
BUTTON_CLASS_NAME = "Button"

DELETE_REFERENCE_OBJECTS_BUTTON_TEXT = "Удаление опорных объектов"
DELETE_DIMENSIONS_BUTTON_TEXT = "Удалить размер(ы)"
MOVE_IN_ROOM_BUTTON_TEXT = "Перенести в помещение"
ALWAYS_LOAD_BUTTON_TEXT = "Всегда загружать"
CANCEL_BUTTON_TEXT = "Отмена"
CLOSE_BUTTON_TEXT = "Закрыть"
SHOW_BUTTON_TEXT = "Показать"

OK_BUTTON_TEXT = "OK"
NO_BUTTON_TEXT = "Нет"
YES_BUTTON_TEXT = "Да"

SPACE_BUTTON_TEXT = " "

CANCEL_LINK_BUTTON_TEXT = "Cancel Link"
DO_NOT_SAVE_THE_PROJECT_TEXT = "Do not save the project"
RELINQUISH_ALL_ELEMENTS_TEXT = "Relinquish all elements and worksets"
RELINQUISH_ELEMENTS_TEXT = "Relinquish elements and worksets"
HAVE_REPORTED_BATCH_RVT_ERROR_WINDOW_DETECTION = [False]


class RevitDialogInfo:
    def __init__(self, dialogHwnd):
        self.Window = ui_automation_util.WindowInfo(dialogHwnd)
        self.Win32Buttons = []
        self.Buttons = []
        for win32Button in win32_user32.FindWindows(dialogHwnd, BUTTON_CLASS_NAME, None):
            buttonInfo = ui_automation_util.WindowInfo(win32Button)
            self.Win32Buttons.append(buttonInfo)
        for directUI in win32_user32.FindWindows(dialogHwnd, DIRECTUI_CLASS_NAME, None):
            for ctrlNotifySink in win32_user32.FindWindows(directUI, CTRLNOTIFYSINK_CLASS_NAME, None):
                for button in win32_user32.FindWindows(ctrlNotifySink, BUTTON_CLASS_NAME, None):
                    buttonInfo = ui_automation_util.WindowInfo(button)
                    self.Buttons.append(buttonInfo)
        return


def tolist(obj1):
    if hasattr(obj1, "__iter__"):
        return obj1
    else:
        return [obj1]


def StripIllegalCharacters(string):
    string = re.sub(r'(\W+\S+)', '', string)
    string = re.sub(r'(\s+)', ' ', string)
    return string.strip()


def IsButtonByText(control, search_text):
    button_text = ui_automation_util.GetButtonText(control)
    button_text = StripIllegalCharacters(button_text)
    search_text = StripIllegalCharacters(search_text)
    if re.match(search_text, button_text, re.UNICODE):
        return True


def SendButtonClick(buttons, output):
    output()
    buttons = tolist(buttons)
    target_button = (random.choice(buttons) if len(buttons) > 0 else None)
    display = any([x for x in buttons if IsButtonByText(x, SHOW_BUTTON_TEXT)])
    choice = random.choice([False, False, True, False, False])

    for control in buttons:

        if IsButtonByText(control, OK_BUTTON_TEXT): target_button = control

        if IsButtonByText(control, YES_BUTTON_TEXT): target_button = control

        if IsButtonByText(control, CLOSE_BUTTON_TEXT): target_button = control

        if all([display, choice]) and IsButtonByText(control, CANCEL_BUTTON_TEXT):
            target_button = control
            break

        if IsButtonByText(control, ALWAYS_LOAD_BUTTON_TEXT):
            target_button = control
            break

        if IsButtonByText(control, MOVE_IN_ROOM_BUTTON_TEXT):
            target_button = control
            break

        if IsButtonByText(control, DELETE_DIMENSIONS_BUTTON_TEXT):
            target_button = control
            break

        if IsButtonByText(control, DELETE_REFERENCE_OBJECTS_BUTTON_TEXT):
            target_button = control
            break

    output()
    if target_button is not None:
        thread_util.SleepForSeconds(5)
        target_button_text = ui_automation_util.GetButtonText(target_button)
        output("\tSending button click to '" + target_button_text + "' button...")
        win32_user32.SendButtonClickMessage(target_button.Hwnd)
        output("...sent.")
    else:
        output("WARNING: Could not find suitable button to click.")
        thread_util.SleepForSeconds(300)
    return


def DismissRevitDialogBox(title, buttons, button_text, output):
    targetButtons = ui_automation_util.FilterControlsByText(buttons, button_text)
    if len(targetButtons) == 1:
        targetButton = targetButtons[0]
    else:
        output()
        output("WARNING: Could not find suitable button to click for '" + title + "' dialog box!")
        targetButton = None
        for button in buttons:
            buttonText = ui_automation_util.GetButtonText(button)
            output()
            output("Button: '" + buttonText + "'")

    if targetButton is not None:
        button_text = ui_automation_util.GetButtonText(targetButton)
        output()
        output("Sending button click to '" + button_text + "' button...")
        win32_user32.SendButtonClickMessage(targetButton.Hwnd)
        output()
        output("...sent.")
    return


def DismissCheekyRevitDialogBoxes(revitProcessId, output_):
    output = global_test_mode.PrefixedOutputForGlobalTestMode(output_, REVIT_DIALOG_MESSAGE_HANDLER_PREFIX)
    enabledDialogs = ui_automation_util.GetEnabledDialogsInfo(revitProcessId)
    if len(enabledDialogs) > 0:
        for enabledDialog in enabledDialogs:
            revitDialog = RevitDialogInfo(enabledDialog.Hwnd)
            buttons = revitDialog.Buttons
            win32Buttons = revitDialog.Win32Buttons
            if enabledDialog.WindowText == MODEL_UPGRADE_WINDOW_TITLE and len(buttons) == 0:
                pass  # Do nothing for model upgrade dialog box. It has no buttons and will go away on its own.
            elif (
                    enabledDialog.WindowText == LOAD_LINK_WINDOW_TITLE
                    and
                    len(win32Buttons) == 1
                    and
                    ui_automation_util.GetButtonText(win32Buttons[0]) == CANCEL_LINK_BUTTON_TEXT):
                pass  # Do nothing for this dialog box. It will go away on its own.
            elif enabledDialog.WindowText == script_host_error.BATCH_RVT_ERROR_WINDOW_TITLE:
                # Report dialog detection but do nothing for BatchRvt error message windows.
                if not HAVE_REPORTED_BATCH_RVT_ERROR_WINDOW_DETECTION[0]:
                    output()
                    output("WARNING: Revit Batch Processor error window detected! Processing has halted!")
                    HAVE_REPORTED_BATCH_RVT_ERROR_WINDOW_DETECTION[0] = True
                    staticControls = list(ui_automation_util.WindowInfo(hwnd) for hwnd in
                                          win32_user32.FindWindows(enabledDialog.Hwnd, STATIC_CONTROL_CLASS_NAME, None))
                    if len(staticControls) > 0:
                        output()
                        output("Dialog has the following static control text:")
                        for staticControl in staticControls:
                            staticControlText = staticControl.WindowText
                            if not String.IsNullOrWhiteSpace(staticControlText):
                                output()
                                output(staticControlText)
            elif enabledDialog.WindowText == CHANGES_NOT_SAVED_TITLE and len(buttons) == 4:
                output()
                output("'" + enabledDialog.WindowText + "' dialog box detected.")
                DismissRevitDialogBox(enabledDialog.WindowText, buttons, DO_NOT_SAVE_THE_PROJECT_TEXT, output)
            elif enabledDialog.WindowText == CLOSE_PROJECT_WITHOUT_SAVING_TITLE and len(buttons) == 3:
                output()
                output("'" + enabledDialog.WindowText + "' dialog box detected.")
                DismissRevitDialogBox(enabledDialog.WindowText, buttons, RELINQUISH_ALL_ELEMENTS_TEXT, output)
            elif enabledDialog.WindowText == SAVE_FILE_WINDOW_TITLE and len(buttons) == 3:
                output()
                output("'" + enabledDialog.WindowText + "' dialog box detected.")
                DismissRevitDialogBox(enabledDialog.WindowText, buttons, NO_BUTTON_TEXT, output)
            elif enabledDialog.WindowText == EDITABLE_ELEMENTS_TITLE and len(buttons) == 3:
                output()
                output("'" + enabledDialog.WindowText + "' dialog box detected.")
                DismissRevitDialogBox(enabledDialog.WindowText, buttons, RELINQUISH_ELEMENTS_TEXT, output)
            elif enabledDialog.WindowText in ["Revit", ''] and len(buttons) == 0 and len(win32Buttons) > 0:
                output()
                output("'" + enabledDialog.WindowText + "' dialog box detected.")
                staticControls = list(ui_automation_util.WindowInfo(hwnd) for hwnd in
                                      win32_user32.FindWindows(enabledDialog.Hwnd, STATIC_CONTROL_CLASS_NAME, None))
                if len(staticControls) > 0:
                    output()
                    output("Dialog has the following static control text:")
                    for staticControl in staticControls:
                        staticControlText = staticControl.WindowText
                        if not String.IsNullOrWhiteSpace(staticControlText):
                            output()
                            output(staticControlText)
                SendButtonClick(win32Buttons, output)
            elif enabledDialog.WindowText == AUTODESK_CUSTOMER_INVOLVEMENT_PROGRAM_TITLE and len(buttons) == 0 and len(
                    win32Buttons) > 0:
                output()
                output("'" + enabledDialog.WindowText + "' dialog box detected.")
                output()
                output("Sending close message...")
                win32_user32.SendCloseMessage(enabledDialog.Hwnd)
                output()
                output("...sent.")
            elif enabledDialog.WindowText in OPENING_WORKSETS_TITLES and len(buttons) == 0 and len(win32Buttons) > 0:
                output()
                output("'" + enabledDialog.WindowText + "' dialog box detected.")
                output()
                SendButtonClick(win32Buttons, output)
            else:
                output()
                output("Revit dialog box detected!")
                output()
                output("\tDialog box title: '" + enabledDialog.WindowText + "'")

                buttons = buttons if len(buttons) > 0 else win32Buttons
                for button in buttons:
                    button_text = ui_automation_util.GetButtonText(button)
                    output("\tButton: '" + button_text + "'")
                SendButtonClick(buttons, output)
    return
