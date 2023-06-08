import clr
from Autodesk.Revit.DB import *
from OfficeOpenXml import *
from OfficeOpenXml.Style import *
from System import *
from System.Collections.Generic import *
from System.Data import *
from System.Linq import *
from System.Threading import *


class ScheduleExporter(object):
    def __init__(self, cancellationToken):
        """ <summary>
             Modifies the content of the cancellationToken variable
         </summary>
         <param name="cancellationToken">CancellationToken</param>
         <returns></returns>
        """
        self._ScheduleGuidColumn = 1
        self._ScheduleGuidRow = 1
        self._cancellationToken = cancellationToken

    def ExportViewScheduleBasic(self, schedule, worksheet):
        """ <summary>
             Function which allows to export the nomenclature as it is in revit
         </summary>
         <param name="schedule">Schedule information</param>
         <param name="worksheet">Excel file</param>
         <returns></returns>
        """
        dt = DataTable()
        # Definition of columns
        fieldsCount = schedule.Definition.GetFieldCount()
        fieldIndex = 0
        while fieldIndex < fieldsCount:
            field = schedule.Definition.GetField(fieldIndex)
            if field.IsHidden:
                continue
            fieldType = clr.GetClrType(str)
            columnName = field.ColumnHeading
            i = 1
            while dt.Columns.Contains(columnName):
                columnName = "{field.GetName()}({i})"
                i += 1
            dt.Columns.Add(columnName, fieldType)
            fieldIndex += 1
        # Content display
        viewSchedule = schedule
        table = viewSchedule.GetTableData()
        section = table.GetSectionData(SectionType.Body)
        nRows = section.NumberOfRows
        nColumns = section.NumberOfColumns
        if nRows > 1:
            # Starts at 1 so as not to display the header
            i = 1
            while i < nRows:
                data = dt.NewRow()
                j = 0
                while j < nColumns:
                    val = viewSchedule.GetCellText(SectionType.Body, i, j)
                    if val.ToString() != "":
                        data[j] = val
                    j += 1
                dt.Rows.Add(data)
                i += 1
        if dt.Rows.Count > 0:
            worksheet.Cells.LoadFromDataTable(dt, True)
            RevitUtilities.AutoFitAllCol(worksheet)

    def ExportViewSchedule(self, doc, schedule, worksheet, parametersSettings):
        """ <summary>
             Export a schedule to an Excel file
         </summary>
         <param name="doc">Document</param>
         <param name="schedule">Schedule information</param>
         <param name="worksheet">Excel file</param>
         <param name="parametersSettings">ParametersSettings</param>
         <returns></returns>
        """
        appliedParameters = parametersSettings.ParametersTranslations.Where().ToList()
        LstParameter = Dictionary[int, Parameter]()
        LstLastTypeFamilly = Dictionary[str, int]()
        revitLinksElements = FilteredElementCollector(doc, schedule.Id).OfCategory(
            BuiltInCategory.OST_RvtLinks).ToElementIds()
        # ---Gets the list of items---
        collector = FilteredElementCollector(doc, schedule.Id).WhereElementIsNotElementType()
        iStartRow = 2  # Position of content insertion
        bAnalyticalNodesShedule = False
        bRvtLinksShedule = False
        if BuiltInCategory.OST_AnalyticalNodes == schedule.Definition.CategoryId.IntegerValue:
            bAnalyticalNodesShedule = True
        elif BuiltInCategory.OST_RvtLinks == schedule.Definition.CategoryId.IntegerValue:
            bRvtLinksShedule = True
        # Excluded revit links
        if revitLinksElements.Any() and bRvtLinksShedule == False:
            collector = collector.Excluding(revitLinksElements)
        # ----------------------------------
        fieldsList = List[ScheduleField]()
        dt = DataTable()
        # =========================================Creating the excel table header=================================
        fieldsCount = schedule.Definition.GetFieldCount()
        dt.Columns.Add("ID")
        dt.Columns.Add("FamilyAndType")
        fieldIndex = 0
        while fieldIndex < fieldsCount:
            field = schedule.Definition.GetField(fieldIndex)
            if not field.HasSchedulableField:
            # continue;
            if not RevitUtilities.CanExportParameter(field, parametersSettings.IgnoredParameters,
                                                     "ViewSchedule_" + schedule.Name):
                continue
            fieldType = clr.GetClrType(str)
            if field.CanTotal():
                fieldType = clr.GetClrType(Double)
            fieldsList.Add(field)
            columnName = field.GetName()
            i = 1
            while dt.Columns.Contains(columnName):
                columnName = "{field.GetName()}({i})"
                i += 1
            dt.Columns.Add(columnName, fieldType)
            fieldIndex += 1
        # ================================End of the creation of the header of the table excel======================
        # =================================Create a list with parameters that are read-only=========================
        readonlyParameters = RevitUtilities.GetListReadOnlyParamater(parametersSettings)
        # =============================================Get each element workset_name========================================
        iRow = iStartRow
        enumerator = collector.GetEnumerator()
        while enumerator.MoveNext():
            element = enumerator.Current
            if element.Name == str.Empty and bAnalyticalNodesShedule == False:  # Remove empty lines
                continue
            col = 2
            data = dt.NewRow()
            data["ID"] = element.UniqueId
            # =========================We will look for the type and family and note its position in the dictionary==========================
            # For ElementsType, only the values written on the last workset_name of a type and family member used for the update. We then note the last workset_name of each family type and we will lock the other cells to avoid errors
            parameter_temp = element.get_Parameter((-1002052))
            if parameter_temp != None:
                elementType = doc.GetElement(parameter_temp.AsElementId())
                if elementType != None:
                    familyName = RevitUtilities.GetElementFamilyName(doc, elementType)
                    sTypeNameFamilly = familyName.Trim() + ": " + elementType.Name.Trim()
                    data["FamilyAndType"] = sTypeNameFamilly
            # ===========================================Get each of the values for the fields===========================
            pElement = RevitUtilities.GetElementPhase(doc, element)
            enumerator = fieldsList.GetEnumerator()
            while enumerator.MoveNext():
                scheduleField = enumerator.Current  # Use the list of columns generated above
                if self._cancellationToken.IsCancellationRequested:
                    return
                # We call the method that will get the parameters associated with the cell
                parameter = RevitUtilities.GetParameter(doc, element, scheduleField, pElement)
                if parameter != None:
                    if not LstParameter.ContainsKey(scheduleField.ParameterId.IntegerValue):
                        LstParameter.Add(scheduleField.ParameterId.IntegerValue, parameter)
                # We call the method that will get the rights associated with the cell
                readonlyParameter = RevitUtilities.GetIsReadOnly(parameter, scheduleField, readonlyParameters)
                # We call the method that will get the value associated with the cell
                cellVal = RevitUtilities.GetParameterValue(parameter, scheduleField, doc, element, appliedParameters)
                # Assign values and parameters to the cell
                dt.Columns[col].ReadOnly = readonlyParameter
                data[col] = cellVal == DBNull.Value
                col += 1
            iRow += 1
            # ===================End of the recovery each of the values for the fields===========================
            dt.Rows.Add(data)
        # ========================================End of the Recovery of each element workset_name==========================
        # =========================================Creation of sort and filter string===================================
        sStringSort = RevitUtilities.GetStringSort(schedule, doc, fieldsList)
        sStringFilter = RevitUtilities.GetStringFilter(schedule, doc)
        sScheduleName = schedule.Name
        # ===========================================Application of filter==========================================
        if not str.IsNullOrEmpty(sStringFilter):
            dt.DefaultView.RowFilter = sStringFilter
            dt = dt.DefaultView.ToTable(sScheduleName)
        # ===========================================Application of sort and filter=========================================
        if not str.IsNullOrEmpty(sStringSort):
            dt.DefaultView.Sort = sStringSort
            dt = dt.DefaultView.ToTable(sScheduleName)
            dtTemp = NaturalSorting.DataTableSort(dt, sStringSort, )
            sMsgError
            if str.IsNullOrEmpty(sMsgError):
                dt = dtTemp.Copy()
        # ======================================We get the positioning of the elements which corresponds to the last ElementType=========================
        iRow = iStartRow
        enumerator = dt.Rows.GetEnumerator()
        while enumerator.MoveNext():
            vRow = enumerator.Current
            sFamilyType = vRow[1].ToString().Trim()
            if sFamilyType != "":
                if LstLastTypeFamilly.ContainsKey(sFamilyType):
                    LstLastTypeFamilly[sFamilyType] = iRow
                else:
                    LstLastTypeFamilly.Add(sFamilyType, iRow)
            iRow += 1
        # ===========================================================================================================================================================================
        worksheet.Cells.LoadFromDataTable(dt, True)
        # Insert one row at the topValue to store schedule unique id
        worksheet.InsertRow(self._ScheduleGuidRow, 1)
        worksheet.Cells[self._ScheduleGuidRow][self._ScheduleGuidColumn].Value = schedule.UniqueId
        # Hide the first column
        worksheet.Column(self._ScheduleGuidColumn).Hidden = True
        # Hide the first row
        worksheet.Row(self._ScheduleGuidRow).Hidden = True
        worksheet.View.FreezePanes(3, 1)  # We freeze the menu
        self.FormatWorksheet(doc, schedule, worksheet, fieldsList, dt, LstParameter, LstLastTypeFamilly)

    def FormatWorksheet(self, doc, schedule, worksheet, fieldsList, dt, LstParameter, LstLastTypeFamilly):
        """ <summary>
             This method changes the format of the table.
         </summary>
         <param name="doc">Document</param>
         <param name="schedule">Schedule information</param>
         <param name="worksheet">Excel file</param>
         <param name="fieldsList">List of columns</param>
         <param name="dt">Contents of the table</param>
         <param name="LstParameter">Parameter list</param>
         <param name="LstLastTypeFamilly">List of unlocked cells for item types</param>
         <returns></returns>
        """
        iStartCol = 3
        iRowAjust = 1
        iStartRow = 3
        iTotalRows = worksheet.Dimension.Rows  # Gives the total number of lines
        ListColHidden = List[int](1, 2)  # List which contains the numbers which must be hidden
        ListColFormula = List[int]()  # List of columns which contains a formula
        RevitUtilities.FormatingTable(worksheet)
        enumerator = fieldsList.GetEnumerator()
        while enumerator.MoveNext():
            scheduleField = enumerator.Current
            fieldId = scheduleField.GetName()
            colIndex = dt.Columns[fieldId].Ordinal + 1
            # Hide the column
            if scheduleField.IsHidden:
                ListColHidden.Add(colIndex)
            if scheduleField.FieldType == ScheduleFieldType.Formula:
                ListColFormula.Add(colIndex)
            # Get the field format
            format = ""
            formatOptions = scheduleField.GetFormatOptions()
            if not formatOptions.UseDefault and not formatOptions.GetSymbolTypeId().Empty():
                formatValueOptions = FormatValueOptions()
                formatValueOptions.SetFormatOptions(formatOptions)
                format = UnitFormatUtils.Format(doc.GetUnits(), scheduleField.GetSpecTypeId(), 0, True,
                                                formatValueOptions)
            elif formatOptions.UseDefault and not scheduleField.GetSpecTypeId().Empty():
                format = RevitUtilities.GetUnitTypeSymbol(doc, scheduleField.GetSpecTypeId())
            if not formatOptions.UseDefault and formatOptions.UnitSymbol != UnitSymbolType.UST_NONE:
                formatValueOptions = FormatValueOptions()
                formatValueOptions.SetFormatOptions(formatOptions)
                format = UnitFormatUtils.Format(doc.GetUnits(), scheduleField.UnitType, 0, True, False,
                                                formatValueOptions)
            elif formatOptions.UseDefault and scheduleField.UnitType != UnitType.UT_Undefined:
                format = RevitUtilities.GetUnitTypeSymbol(doc, scheduleField.UnitType)
            format = format.Replace(" ", " \"") + "\"" if format.IndexOf(" ") > 0 else format
            if not str.IsNullOrEmpty(format):
                worksheet.Column(colIndex).Style.Numberformat.Format = format
            # Change the color of the column if it can not be modified
            if dt.Columns[
                fieldId].ReadOnly or scheduleField.FieldType == ScheduleFieldType.Count or scheduleField.FieldType == ScheduleFieldType.Formula or scheduleField.FieldType == ScheduleFieldType.MaterialQuantity:
                RevitUtilities.LockColumn(worksheet, colIndex)
            else:
                worksheet.Column(colIndex).Style.Locked = False
                # ===================We indicate the cells for the ElementType columns which can be modified and we lock the others==============
                if scheduleField.FieldType == ScheduleFieldType.ElementType and LstLastTypeFamilly.Count > 0:
                    RevitUtilities.FormattingColElementType(worksheet, colIndex)
                    iRow = iStartRow
                    while iRow <= iTotalRows:
                        if worksheet.Cells[iRow][2].Value != None:
                            sTypeAndFamilly = worksheet.Cells[iRow][2].Value.ToString()
                            iPosition = LstLastTypeFamilly[sTypeAndFamilly]
                            if iPosition > 0:
                                if iPosition == iRow - iRowAjust:
                                    # Unlock the cell
                                    RevitUtilities.UnlockCell(worksheet, iRow, colIndex)
                                    # Addition "" to not have 0 for null cell
                                    if worksheet.Cells[iRow][colIndex].Value == None:
                                        worksheet.Cells[iRow][colIndex].Value = ""
                                else:
                                    # Adding a formula
                                    worksheet.Cells[iRow][colIndex].Formula = "=" + \
                                                                              worksheet.Cells[iPosition + iRowAjust][
                                                                                  colIndex].Address
                        iRow += 1
        # We group the group lines
        level = 0
        iLevelMax = schedule.Definition.GetSortGroupFields().Count
        dGroupFieldId = Dictionary[str, int]()
        enumerator = schedule.Definition.GetSortGroupFields().GetEnumerator()
        while enumerator.MoveNext():
            scheduleSortGroupField = enumerator.Current
            level += 1
            # We will get the name of the column
            fieldId = schedule.Definition.GetField(scheduleSortGroupField.FieldId).GetSchedulableField().GetName(
                doc)  # Give the Id of the column
            column = dt.Columns[fieldId]  # It will look for the properties of the column
            if column == None:
                continue
            dGroupFieldId.Add(fieldId, level)
            colIndex = column.Ordinal + 1  # Indicates the column number. We do plus 1 in the first column this is the id
            dic = Dictionary[str, int]()
            groupFirstRow = 3  # To start playback after declaring the title bar
            bSubRow = False
            rowIndex = groupFirstRow
            while rowIndex <= iTotalRows:
                sIdRowIndex = worksheet.Cells[rowIndex][1].Value + ""
                if sIdRowIndex == "":
                    bSubRow = True
                    continue
                sCellValue = "StringEmpty"
                if worksheet.Cells[rowIndex][colIndex].Value != None:
                    sCellValue = worksheet.Cells[rowIndex][colIndex].Value.ToString()
                elif worksheet.Cells[rowIndex][colIndex].Formula != None:
                    sFormula = worksheet.Cells[rowIndex][colIndex].Formula
                    if sFormula != "":
                        sCell = sFormula.Substring(1, sFormula.Length - 1)
                        sCellValue = worksheet.Cells[sCell].Value.ToString()
                sIdKey = sCellValue + "-level=" + level
                bContainsKey = dic.ContainsKey(sIdKey)
                if not bContainsKey or bSubRow:  # We check if the column name has already been inserted
                    bSubRow = False
                    if iTotalRows != rowIndex and not bContainsKey:  # We validate that we haven't come to the end
                        dic.Add(sIdKey, level)  # We add the value to the dictionary with its level
                    if self._cancellationToken.IsCancellationRequested:  # If the user has clicked on the cancel button we stop everything.
                        return
                    if dic.Count > 1 and (scheduleSortGroupField.ShowFooter or not schedule.Definition.IsItemized):
                        self.AddFooter(worksheet, rowIndex, colIndex, groupFirstRow, fieldsList, dt, level, iLevelMax,
                                       dGroupFieldId)
                        rowIndex += 1
                        iTotalRows += 1
                    groupFirstRow = rowIndex
                if iTotalRows == rowIndex and (
                        scheduleSortGroupField.ShowFooter or not schedule.Definition.IsItemized):  # When we reach the last workset_name, we create a foot
                    self.AddFooter(worksheet, rowIndex + 1, colIndex, groupFirstRow, fieldsList, dt, level, iLevelMax,
                                   dGroupFieldId)
                worksheet.Row(
                    rowIndex).OutlineLevel = level  # defines the current hierarchical level of the specified row or column.
                if not schedule.Definition.IsItemized:
                    worksheet.Row(rowIndex).Collapsed = True
                rowIndex += 1
        # ===============================Creating the total workset_name and formatting the header==============================
        if level > 0:
            iFirstRow = 3
            iLastRow = worksheet.Dimension.Rows
            iNewRow = iLastRow + 1
            worksheet.InsertRow(iNewRow, 1)
            index = 0
            while index < fieldsList.Count():
                field = fieldsList[index]
                fieldId = field.GetName()
                columnIndex = dt.Columns[fieldId].Ordinal + 1
                if field.IsDisplayTypeTotals():
                    worksheet.Cells[iNewRow][columnIndex].Formula = str.Format("=SUBTOTAL(9,{0})",
                                                                               worksheet.Cells[iFirstRow][columnIndex][
                                                                                   iLastRow][columnIndex].Address)
                if field.FieldType == ScheduleFieldType.Count:
                    worksheet.Cells[iNewRow][columnIndex].Formula = str.Format("=SUBTOTAL(9,{0})",
                                                                               worksheet.Cells[iFirstRow][columnIndex][
                                                                                   iLastRow][columnIndex].Address)
                index += 1
            # Format for the total workset_name
            RevitUtilities.FormatingTotalRow(worksheet, iNewRow)
        # Format for the header workset_name
        iHeaderRow = 2
        # Adding the custom header and the type of value that the column must contain
        worksheet.InsertRow(3, 2)
        iCol = iStartCol
        enumerator = fieldsList.GetEnumerator()
        while enumerator.MoveNext():
            FieldItem = enumerator.Current
            worksheet.Cells[iHeaderRow + 1][iCol].Value = FieldItem.ColumnHeading
            sParamType = str.Empty
            if LstParameter.ContainsKey(FieldItem.ParameterId.IntegerValue):
                vParam = LstParameter[FieldItem.ParameterId.IntegerValue]
                sParamType = LstParameter[FieldItem.ParameterId.IntegerValue].Definition.ParameterType.ToString()
                if sParamType == "Invalid":
                    sParamType = vParam.StorageType.ToString()
                elif sParamType == "YesNo":
                    sParamType = "TrueFalse"
            worksheet.Cells[iHeaderRow + 2][iCol].Value = sParamType
            iCol += 1
        worksheet.Row(iHeaderRow).Hidden = True
        RevitUtilities.Unlock(worksheet, iHeaderRow + 1)
        if ListColFormula.Count >= 1:  # If it has formula columns, change the color of the column and display which indicates that the formulas are not exportable.
            enumerator = ListColFormula.GetEnumerator()
            while enumerator.MoveNext():
                iColu = enumerator.Current
                RevitUtilities.FormattingColFormula(worksheet, iStartRow, worksheet.Dimension.Rows, iColu)
            iRowInsert = worksheet.Dimension.Rows + 2
            iColInsertEnd = worksheet.Dimension.Columns
            worksheet.Cells[iRowInsert][2].Value = Resources.WarningFormula
            worksheet.Cells[iRowInsert][2][iRowInsert][iColInsertEnd].Merge = True
            worksheet.Cells[iRowInsert][2][iRowInsert][iColInsertEnd].Style.WrapText = True
            worksheet.Cells[iRowInsert][2][iRowInsert][
                iColInsertEnd].Style.VerticalAlignment = ExcelVerticalAlignment.Center
            worksheet.Cells[iRowInsert][2][iRowInsert][
                iColInsertEnd].Style.HorizontalAlignment = ExcelHorizontalAlignment.Center
            RevitUtilities.FormattingRowWarningFormula(worksheet, iRowInsert, 2, iRowInsert, iColInsertEnd)
            worksheet.Row(iRowInsert).Height *= 2
        RevitUtilities.FormattingTheHeader(worksheet, iHeaderRow + 1)
        RevitUtilities.LockRow(worksheet, iHeaderRow + 2)
        RevitUtilities.FormattingTheHeaderTypeField(worksheet, iHeaderRow + 2)
        RevitUtilities.LockRow(worksheet, iHeaderRow)
        RevitUtilities.FreezeRow(worksheet, iHeaderRow + 3)
        # =====================================End of the creation of the total workset_name and formatting of the header====================================================
        # Finalize the Excel table
        worksheet.OutLineApplyStyle = True
        worksheet.ApplyDefaultProtection()
        RevitUtilities.AutoFitAllCol(worksheet)
        # Hide the add columns in the ListColHidden list
        enumerator = ListColHidden.GetEnumerator()
        while enumerator.MoveNext():
            iItemHidden = enumerator.Current
            worksheet.Column(iItemHidden).Hidden = True

    def AddFooter(worksheet, rowIndex, groupColumnIndex, groupFirstRow, fieldsList, dt, iLevel, iMaxLevel,
                  dGroupFieldId):
        # Validation to insert a subtotal over the previous sub-total
        if worksheet.Cells[rowIndex - 1][1].Value + "" == "":
            iSubRow = iLevel - 1
            rowIndex = rowIndex - iSubRow
        worksheet.InsertRow(rowIndex, 1)
        index = 0
        while index < fieldsList.Count():
            field = fieldsList[index]
            fieldId = field.GetName()
            columnIndex = dt.Columns[fieldId].Ordinal + 1
            bFieldCount = False
            if field.IsDisplayTypeTotals():
                worksheet.Cells[rowIndex][columnIndex].Formula = str.Format("=SUBTOTAL(9,{0})",
                                                                            worksheet.Cells[groupFirstRow][columnIndex][
                                                                                rowIndex - 1][columnIndex].Address)
                bFieldCount = True
            if field.FieldType == ScheduleFieldType.Count:
                worksheet.Cells[rowIndex][columnIndex].Formula = str.Format("=SUBTOTAL(9,{0})",
                                                                            worksheet.Cells[groupFirstRow][columnIndex][
                                                                                rowIndex - 1][columnIndex].Address)
                bFieldCount = True
            if bFieldCount == False:
                if dGroupFieldId.ContainsKey(fieldId):
                    worksheet.Cells[rowIndex][columnIndex].Value = Convert.ToString(
                        worksheet.Cells[rowIndex - 1][columnIndex].Value + "").Replace("\"", "''")
            index += 1
        if iLevel == 1:
            RevitUtilities.FormatingLevel1(worksheet, rowIndex)
        elif iLevel == 2:
            RevitUtilities.FormatingLevel2(worksheet, rowIndex)

    AddFooter = staticmethod(AddFooter)
