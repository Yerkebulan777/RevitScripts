#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

pyt_path = r'C:\Program Files (x86)\IronPython 2.7\Lib'
sys.path.append(pyt_path)
import difflib
import re
import os

import clr

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument


def PurgeLineList(search, line_list):
    outlist = []
    for line in sorted(list(set(line_list))):
        line = " ".join(line.split(" - "))
        line = " ".join(line.split("Лист"))
        line = " ".join(line.split(".pdf"))
        line = re.sub('[\s!?]+', " ", line)
        line = line.strip()
        wrds = line.split()
        result = []
        for w in list(wrds):
            ratio = round(float(difflib.SequenceMatcher(None, search, w).ratio()), 2)
            if ratio < 0.85:
                result.append(w)
        result = " ".join(result)
        if result == " ":
            outlist.append(None)
        else:
            outlist.append(result)
    return outlist


def reformat(oldname, newname):
    fsearch = os.path.splitext(oldname)[1]
    fchange = os.path.splitext(newname)[1]
    pattern = r'(^|[^\w]){}([^\w]|$)'.format(fsearch)
    pattern = re.compile(pattern, re.UNICODE)
    match = re.search(pattern, newname)
    if not bool(match) and len(fsearch) < 5:
        newname = re.sub(fchange, fsearch, newname)
    return newname


def IdentifyAndRename(identify_path, replaced_path):
    search = doc.Title
    if not replaced_path: pass
    identify_names = os.listdir(identify_path)
    replaced_names = os.listdir(replaced_path)
    identify_names = sorted(i for i in identify_names if i)
    replaced_names = sorted(i for i in replaced_names if i)
    identify = (PurgeLineList(search, identify_names))
    replaced = (PurgeLineList(search, replaced_names))
    final = []
    for sindx, search in enumerate(replaced):
        search = search[1:]
        result = None
        count = findx = float(0)

        def cleanLine(text):
            text = re.sub('[\s!?:;.,]+', " ", text)
            text = text.replace("-", "")
            return text

        search = cleanLine(search)
        if search == "": continue
        for idx, line in enumerate(identify):
            line = cleanLine(line)
            if line == "": continue
            ratio = difflib.SequenceMatcher(None, search, line).ratio()
            if ratio > 0.85 and ratio > count:
                result = True
                count = ratio
                findx = idx
        if result:
            try:
                oldname = replaced_names[sindx]
                newname = identify_names[findx]
                newname = reformat(oldname, newname)
                oldname = replaced_path + "\\" + oldname
                newname = replaced_path + "\\" + newname
                os.rename(oldname, newname)
                final.append(newname + "заменен")
            except:
                import traceback
                error = traceback.format_exc()
                final.append(error)
        else:
            try:
                newname = replaced[sindx]
                oldname = replaced_names[sindx]
                newname = reformat(oldname, newname)
                oldname = replaced_path + "\\" + oldname
                newname = replaced_path + "\\" + newname
                os.rename(oldname, newname)
                final.append(newname + "переименован")
            except:
                import traceback
                error = traceback.format_exc()
                final.append(error)
    return final


###################################################
identify_path = str(IN[0])
replaced_path = str(IN[1])
###################################################
result = IdentifyAndRename(identify_path, replaced_path)
###################################################
OUT = result
