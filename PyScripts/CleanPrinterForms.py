#!/usr/bin/env python
# -*- coding: utf-8 -*-


# import ctypes
# from ctypes import wintypes
# winspool = ctypes.windll.winspool
#
# def clean_printer_forms(printer_name, startswith):
#     hprinter = winspool.OpenPrinter(printer_name, None, 0)
#
#     forms, count = winspool.EnumForms(hprinter, 1, None, 0)
#
#     forms_to_delete = [form['pName'] for form in forms if not form['pName'].startswith(startswith)]
#
#     for form_name in forms_to_delete:
#         try:
#             winspool.DeleteForm(hprinter, form_name)
#             print("Deleted form: " + form_name)
#         except WindowsError as e:
#             if e.winerror == winspool.ERROR_INVALID_FORM_NAME:
#                 print("Form not found: " + form_name)
#             else:
#                 raise


import win32print


def clean_printer_forms(printer_name, startswith):
    hprinter = win32print.OpenPrinter(printer_name)

    forms = win32print.EnumForms(hprinter)

    forms_to_delete = [form['pName'] for form in forms if not form['pName'].startswith(startswith)]

    for form_name in forms_to_delete:
        try:
            win32print.DeleteForm(hprinter, form_name)
            print("Deleted form: " + form_name)
        except win32print.error as e:
            if e.winerror == win32print.ERROR_INVALID_FORM_NAME:
                print("Form not found: " + form_name)
            else:
                raise


print("\nStart clean forms\n")
clean_printer_forms('PDF24', 'A')
print ("\r\n\tClear forms completed!!!\r\n\t")
