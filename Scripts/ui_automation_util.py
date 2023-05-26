#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Revit Batch Processor

import re

import win32_user32

DIALOG_WINDOW_CLASS_NAME = "#32770"


class WindowInfo:
    def __init__(self, hwnd):
        self.Hwnd = hwnd
        self.IsWindowEnabled = win32_user32.IsWindowEnabled(hwnd)
        self.OwnerWindow = win32_user32.GetOwnerWindow(hwnd)
        self.ParentWindow = win32_user32.GetParentWindow(hwnd)
        self.DialogControlId = win32_user32.GetDialogControlId(hwnd)
        self.WindowClassName = win32_user32.GetWindowClassName(hwnd)
        self.WindowText = win32_user32.GetWindowText(hwnd)
        return


def GetEnabledDialogsInfo(processId):
    return list(
        WindowInfo(hwnd)
        for hwnd in win32_user32.GetTopLevelWindows(DIALOG_WINDOW_CLASS_NAME, None, processId)
        if win32_user32.IsWindowEnabled(hwnd))


def StripIllegalCharacters(string):
    string = re.sub(r'(\W+)', ' ', string)
    string = re.sub(r'(\s+)', ' ', string)
    return string.strip()


def TextWithoutAmpersands(text):
    return text.replace("&", '').replace(u"&", '')
    # return text.Replace("&", str.Empty).Replace(u"&", str.Empty)


def GetButtonText(buttonInfo):
    button_text = buttonInfo.WindowText
    button_text = StripIllegalCharacters(button_text)
    return TextWithoutAmpersands(button_text)


def FilterControlsByText(controls, controlText):
    targetControls = list()
    controlText = controlText.strip().lower()
    for control in controls:
        buttonText = GetButtonText(control).strip().lower()
        if buttonText == controlText or controlText in buttonText:
            targetControls.append(control)
    return targetControls
