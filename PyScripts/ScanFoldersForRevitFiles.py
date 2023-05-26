#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os
import re
import sys
import time

import msvcrt



def get_file_size(path):
    size = os.path.getsize(path)
    return size


def get_basename(file_path):
    fullname = os.path.basename(file_path)
    filename, ext = os.path.splitext(fullname)
    return filename


def get_file_paths(server_path):
    rvt_dir = re.compile(r".*(RVT)\b")
    if rvt_dir.match(os.path.basename(server_path)):
        return server_path


def get_project_directories(server_path, include_folders):
    project_dirs = []
    includes = re.compile(r".*(?:" + "|".join(include_folders) + ")$")
    roots = get_file_paths(server_path)

    if roots:
        project_dirs.append(roots)
        return project_dirs

    for entry in os.listdir(server_path):
        if includes.match(entry):
            temp_path = os.path.join(server_path, entry)
            for sub in os.listdir(temp_path):
                if sub.endswith('RVT'):
                    sub_path = os.path.join(temp_path, sub)
                    project_dirs.append(sub_path)

    return project_dirs


########################################################################################################################

server_path = os.path.normpath(sys.argv[1])
if "I:" in server_path: server_path = server_path.replace("I:", r"\\tmsserv\tms")
include_folders = ["AR", "AS", "KJ", "KR", "KG", "OV", "VK", "EOM", "EM", "PS", "SS"]
directories = get_project_directories(server_path, include_folders)
print('\n\n\n\tProject directory path on the server: ' + server_path)
print('\t' + '#' * 100)
print('\t\t\t\t\t')

########################################################################################################################
suffix = '.rvt'
print("\n\tRevit files list:\t\n")
backup = re.compile(r".*(\S\d\d\d+)$")
detach = re.compile(r".*\S(отсоединено)$")
########################################################################################################################

revit_paths = []
for directory in directories:
    for filename in os.listdir(directory):
        if filename.endswith(suffix):
            firstname = filename.rstrip(suffix)
            filepath = os.path.join(directory, filename)
            if backup.match(firstname): continue
            if detach.match(firstname): continue
            if (0 < firstname.find('#')): continue
            revit_paths.append(filepath)

########################################################################################################################
revit_paths = sorted(revit_paths, key=lambda x: get_basename(x))
########################################################################################################################

for i, filepath in enumerate(revit_paths):
    print("\n\t" + str(i + 1) + ".\t" + get_basename(filepath))
    time.sleep(0.25)

########################################################################################################################
selected = []
########################################################################################################################

print('\n\n\t' + '#' * 100)

counts, interval, timeout = len(revit_paths), float(1 / 5), int(3 * 5 * 60)
print("\tPlease enter zero or enter the number by project and press enter:\t")
for _ in range(timeout):
    time.sleep(interval)
    if msvcrt.kbhit():
        press_key = input()
        if press_key.isdigit():
            num = int(press_key)
            if num <= 0:
                print("\n\tSet projects to script list")
                time.sleep(0.5)
                break
            elif num <= counts:
                filepath = revit_paths[num - 1]
                if filepath not in selected:
                    print("\n\t\tSelect project by number:   " + str(num) + ".   " + get_basename(filepath))
                    time.sleep(interval)
                    selected.append(filepath)

print('\t' + '#' * 100 + '\n\n')

########################################################################################################################

if len(selected) == 0:  selected = revit_paths
directory = os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
output_path = os.path.join(directory, 'revit_file_list.txt')
print('Revit files list located path is: ' + str(output_path) + '\n')
with codecs.open(output_path, mode='w', encoding='utf-8', errors='ignore') as f:
    [f.write(item + "\n") for item in selected]

#######################################################################################################################
