# -*- coding: utf-8 -*-
# !/usr/bin/python

import os
import sys

server_path = sys.argv[1]
# server_path = "I:"

if "I:" in server_path:
    server_path = server_path.replace("I:", r"\\Iaspserv\iasp")

revit_files = []
exclude_folder_names = ("BI STANDART", "BIM коллизии", "Titul-Stamp", "SMETA", "GOSEXPERTIZA",
                        "OPZ", "POS", "OVOS", "DWG", "INcoming", "OUTgoing", "URNA", "Urna",
                        "#", "Revit_temp", "X_BIM", "Z_Titul-Stamp")

projectsToResave = []
new_names = ["00_NAME_1"]
for new_name in new_names:
    for proj in os.listdir(server_path):
        if new_name == proj:
            projectsToResave.append(proj)
    print(new_name)

project_paths = []
for project in projectsToResave:
    project_paths.append(server_path + "\\" + project + "\\" + "01_PROJECT")
# print(project)

for project_path in project_paths:
    for dirpath, dirnames, filenames in os.walk(project_path):
        for name in filenames:
            if name.endswith((".rvt")) and "#" not in name:
                if any([x in dirpath for x in exclude_folder_names]) == False:
                    full_path = dirpath + "\\" + name
                    revit_files.append(full_path)

output_path = r"\\iasp-dc2\Documents\05_Soft\Revit Batch Processor\RevitExportConfig\revit_file_list_resave.txt"
with open(output_path, 'w', encoding='utf-8') as f:
    for item in revit_files:
        f.write(item + "\n")
