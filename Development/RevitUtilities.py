# from Autodesk.Revit.DB import *
# from Autodesk.Revit.DB.Architecture import *
# from Autodesk.Revit.DB.Mechanical import *
# from Floor import *
# from OfficeOpenXml import *
# from OfficeOpenXml.FormulaParsing.Excel.Functions.Math import *
# from OfficeOpenXml.Style import *
# from System import *
# from System.Collections import *
# from System.Collections.Generic import *
# from System.Linq import *
# from System.Reflection import *
#
#
# class RevitUtilities(object):
#     def __init__(self):
#         self._CountHost = 23
#
#     def GetMaterialValumeOfElement(e):
#         materials = e.GetMaterialIds(False)
#         return materials.Sum()
#
#     GetMaterialValumeOfElement = staticmethod(GetMaterialValumeOfElement)
#
#     def GetMaterialAreaOfElement(e):
#         materials = e.GetMaterialIds(False)
#         return materials.Sum()
#
#     GetMaterialAreaOfElement = staticmethod(GetMaterialAreaOfElement)
#
#     def ConvertToDisplayUnit(doc, unitType, value):
#         fo = doc.GetUnits().GetFormatOptions(unitType)
#         dut = fo.GetUnitTypeId()
#         return UnitUtils.ConvertFromInternalUnits(value, dut)
#
#     ConvertToDisplayUnit = staticmethod(ConvertToDisplayUnit)
#
#     def ConvertToDisplayUnit(doc, unitType, value):
#         fo = doc.GetUnits().GetFormatOptions(unitType)
#         dut = fo.DisplayUnits
#         return UnitUtils.ConvertFromInternalUnits(value, dut)
#
#     ConvertToDisplayUnit = staticmethod(ConvertToDisplayUnit)
#
#     def GetUnitTypeSymbol(doc, unitType):
#         if unitType.Empty():
#             return ""
#         fo = doc.GetUnits().GetFormatOptions(unitType)
#         if fo.GetSymbolTypeId().Empty():
#             return ""
#         formatValueOptions = FormatValueOptions()
#         formatValueOptions.SetFormatOptions(fo)
#         if fo.GetUnitTypeId() == UnitTypeId.Celsius and fo.GetSymbolTypeId() == SymbolTypeId.DegreeC:  # Problem with format for degrees, replace error with the correct format
#             sResult = "0.00 °C"
#         else:
#             sResult = UnitFormatUtils.Format(doc.GetUnits(), unitType, 0, True, formatValueOptions)
#         return sResult
#
#     GetUnitTypeSymbol = staticmethod(GetUnitTypeSymbol)
#
#     def GetUnitTypeSymbol(doc, unitType):
#         if unitType == UnitType.UT_Undefined:
#             return ""
#         fo = doc.GetUnits().GetFormatOptions(unitType)
#         if fo.UnitSymbol == UnitSymbolType.UST_NONE:
#             return ""
#         formatValueOptions = FormatValueOptions()
#         formatValueOptions.SetFormatOptions(fo)
#         if fo.DisplayUnits == DisplayUnitType.DUT_CELSIUS and fo.UnitSymbol == UnitSymbolType.UST_DEGREE_C:  # Problem with format for degrees, replace error with the correct format
#             sResult = "0.00 °C"
#         else:
#             sResult = UnitFormatUtils.Format(doc.GetUnits(), unitType, 0, True, False, formatValueOptions)
#         return sResult
#
#     GetUnitTypeSymbol = staticmethod(GetUnitTypeSymbol)
#
#     def GetFamilySymbol(element, parameterId, parameter):
#         parameter2 = None
#         FIelement = element
#         if FIelement != None:
#             familysymbol = FIelement.Symbol
#             if familysymbol != None:
#                 parameter2 = familysymbol.get_Parameter(parameterId.IntegerValue)
#                 if parameter2 != None:
#                     parameter = parameter2
#         return parameter
#
#     GetFamilySymbol = staticmethod(GetFamilySymbol)
#
#     def GetWallType(element, parameterId, parameter):
#         parameter2 = None
#         Welement = element
#         if Welement != None:
#             walltype = Welement.WallType
#             if walltype != None:
#                 parameter2 = walltype.get_Parameter(parameterId.IntegerValue)
#                 if parameter2 != None:
#                     parameter = parameter2
#         return parameter
#
#     GetWallType = staticmethod(GetWallType)
#
#     def GetParameter(doc, element, scheduleField, pElement):
#         parameter = None
#         parameterId = scheduleField.ParameterId
#         #
#         sColName11 = scheduleField.GetName()  # Ligne pour facilité le débugage
#         vName11 = parameterId.IntegerValue  # Ligne pour facilité le débugage
#         sStop121 = "asdfasdf"
#         # Il va chercher les paramètres du champs pour permettre l'affichage du bon format
#         # ----Action selon le type de champ / Action according to the type of field----
#         if scheduleField.FieldType == ScheduleFieldType.Formula or scheduleField.FieldType == ScheduleFieldType.Count or scheduleField.FieldType == self._CountHost:
#             pass
#         elif scheduleField.FieldType == ScheduleFieldType.ElementType:
#             ListParam = element.GetOrderedParameters()
#             parameter = ListParam.Where().FirstOrDefault()
#             if parameter == None:
#                 ElementType = doc.GetElement(element.GetTypeId())
#                 if ElementType != None:
#                     parameter = ElementType.get_Parameter(parameterId.IntegerValue)
#                     if parameter != None:
#                         tTypeParameter = parameter.Element.GetType()
#                         if tTypeParameter.Name == "FamilyInstance":
#                         elif tTypeParameter.Name == "FamilySymbol":
#                             parameter = RevitUtilities.GetFamilySymbol(element, parameterId, parameter)
#                         elif tTypeParameter.Name == "WallType":
#                             parameter = RevitUtilities.GetWallType(element, parameterId, parameter)
#         elif scheduleField.FieldType == ScheduleFieldType.Space:
#             familyInstanceSpace = element
#             if familyInstanceSpace != None:
#                 space = familyInstanceSpace.Space
#                 if space != None:
#                     parameter = space.get_Parameter(parameterId.IntegerValue)
#         elif scheduleField.FieldType == ScheduleFieldType.Analytical:
#             elementanalytical = element.GetAnalyticalModel()
#             if elementanalytical != None:
#                 parameter = elementanalytical.get_Parameter(parameterId.IntegerValue)
#         elif scheduleField.FieldType == ScheduleFieldType.ProjectInfo:
#             vProjectInfo = doc.ProjectInformation
#             if vProjectInfo != None:
#                 parameter = vProjectInfo.get_Parameter(parameterId.IntegerValue)
#         elif scheduleField.FieldType == ScheduleFieldType.FromRoom or scheduleField.FieldType == ScheduleFieldType.ToRoom or scheduleField.FieldType == ScheduleFieldType.Room:
#             familyInstance = element
#             if familyInstance != None:
#                 room = RevitUtilities.GetFamillyRoom(familyInstance, pElement, scheduleField.FieldType)
#                 if room != None:
#                     parameter = room.get_Parameter(parameterId.IntegerValue)
#             else:
#                 sElement = element
#                 if sElement != None:
#                     sRoom = sElement.Room
#                     if sRoom != None:
#                         parameter = sRoom.get_Parameter(parameterId.IntegerValue)
#         elif scheduleField.FieldType == ScheduleFieldType.MaterialQuantity:
#             parameter = element.get_Parameter(parameterId.IntegerValue)
#         elif scheduleField.FieldType == ScheduleFieldType.PhysicalInstance:
#             parameter = element.get_Parameter(parameterId.IntegerValue)
#         elif scheduleField.FieldType == ScheduleFieldType.StructuralMaterial:
#             SM_familyInstance = element
#             SM_Wall = element
#             SM_FloorElement = element
#             if SM_familyInstance != None:
#                 Material_FamilyInstance = doc.GetElement(SM_familyInstance.StructuralMaterialId)
#                 if Material_FamilyInstance != None:
#                     SAI_Material_FamilyInstance = doc.GetElement(Material_FamilyInstance.StructuralAssetId)
#                     if SAI_Material_FamilyInstance != None:
#                         parameter = SAI_Material_FamilyInstance.get_Parameter(parameterId.IntegerValue)
#                     if parameter == None:
#                         parameter = Material_FamilyInstance.get_Parameter(parameterId.IntegerValue)
#                 else:
#                     SM_FamilySymbol = SM_familyInstance.Symbol
#                     if SM_FamilySymbol != None and parameter == None:
#                         # On va chercher le Element Id dans Maétriau Structurel
#                         ParameterFamilySymbol = SM_FamilySymbol.get_Parameter(
#                             BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)
#                         if ParameterFamilySymbol != None:
#                             SM_Material_FamilySymbol = doc.GetElement(ParameterFamilySymbol.AsElementId())
#                             if SM_Material_FamilySymbol != None:
#                                 SAI_Material_FamilySymbol = doc.GetElement(SM_Material_FamilySymbol.StructuralAssetId)
#                                 if SAI_Material_FamilySymbol != None:
#                                     parameter = SAI_Material_FamilySymbol.get_Parameter(parameterId.IntegerValue)
#                                 if parameter == None:
#                                     parameter = SM_Material_FamilySymbol.get_Parameter(parameterId.IntegerValue)
#             if SM_FloorElement != None and parameter == None:
#                 Material_FloorType = doc.GetElement(SM_FloorElement.FloorType.StructuralMaterialId)
#                 if Material_FloorType != None:
#                     SAI_Material_FloorType = doc.GetElement(Material_FloorType.StructuralAssetId)
#                     if SAI_Material_FloorType != None:
#                         parameter = SAI_Material_FloorType.get_Parameter(parameterId.IntegerValue)
#                     if parameter == None:
#                         parameter = Material_FloorType.get_Parameter(parameterId.IntegerValue)
#             if SM_Wall != None and parameter == None:
#                 SM_WallType = doc.GetElement(SM_Wall.GetTypeId())
#                 if SM_WallType != None:
#                     ParameterWallType = SM_WallType.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)
#                     if ParameterWallType != None:
#                         Material_WallType = doc.GetElement(ParameterWallType.AsElementId())
#                         if Material_WallType != None:
#                             SAI_Material_WallType = doc.GetElement(Material_WallType.StructuralAssetId)
#                             if SAI_Material_WallType != None:
#                                 parameter = SAI_Material_WallType.get_Parameter(parameterId.IntegerValue)
#                             if parameter == None:
#                                 parameter = Material_WallType.get_Parameter(parameterId.IntegerValue)
#             SM_WallFoundation = element
#             if SM_WallFoundation != None and parameter == None:
#                 SM_WallFoundationType = doc.GetElement(SM_WallFoundation.GetTypeId())
#                 if SM_WallFoundationType != None:
#                     ParameterWallFoundationType = SM_WallFoundationType.get_Parameter(
#                         BuiltInParameter.STRUCTURAL_MATERIAL_PARAM)
#                     if ParameterWallFoundationType != None:
#                         Material_WallFoundationType = doc.GetElement(ParameterWallFoundationType.AsElementId())
#                         if Material_WallFoundationType != None:
#                             SAI_Material_WallFoundationType = doc.GetElement(
#                                 Material_WallFoundationType.StructuralAssetId)
#                             if SAI_Material_WallFoundationType != None:
#                                 parameter = SAI_Material_WallFoundationType.get_Parameter(parameterId.IntegerValue)
#                             if parameter == None:
#                                 parameter = Material_WallFoundationType.get_Parameter(parameterId.IntegerValue)
#         elif scheduleField.FieldType == ScheduleFieldType.Instance:  # Éventuellement simplifié ce code
#             if parameterId.IntegerValue > 0:  # Indique que c'est un paramètre partagé
#                 ElementType = doc.GetElement(element.GetTypeId())
#                 if ElementType != None:
#                     parameter = ElementType.get_Parameter(parameterId.IntegerValue)
#                     if parameter != None:
#                         tTypeParameter = parameter.Element.GetType()
#                         if tTypeParameter.Name == "FamilyInstance":
#                         elif tTypeParameter.Name == "FamilySymbol":
#                             parameter = RevitUtilities.GetFamilySymbol(element, parameterId, parameter)
#                         elif tTypeParameter.Name == "WallType":
#                             parameter = RevitUtilities.GetWallType(element, parameterId, parameter)
#                 if parameter == None or not parameter.HasValue:
#                     parameter = element.get_Parameter(parameterId.IntegerValue)
#                     if parameter != None:
#                         tTypeParameter = parameter.Element.GetType()
#                         if tTypeParameter.Name == "FamilyInstance":
#                             if parameter.IsShared and parameter.IsReadOnly:
#                                 parameter = RevitUtilities.GetFamilySymbol(element, parameterId, parameter)
#                         elif tTypeParameter.Name == "FamilySymbol":
#                             parameter = RevitUtilities.GetFamilySymbol(element, parameterId, parameter)
#             else:  # Ce n'est pas un paramètre partagé
#                 parameter = element.get_Parameter(parameterId.IntegerValue)
#                 if not RevitUtilities.ValidValue(parameter):
#                     AM_Element = element.GetAnalyticalModel()
#                     if AM_Element != None:
#                         parameter = AM_Element.get_Parameter(parameterId.IntegerValue)
#                     if parameter != None:
#                         tTypeParameter = parameter.Element.GetType()
#                         if tTypeParameter.Name == "FamilyInstance":
#                             if parameter.IsShared and parameter.IsReadOnly:
#                                 parameter = RevitUtilities.GetFamilySymbol(element, parameterId, parameter)
#                         elif tTypeParameter.Name == "FamilySymbol":
#                             parameter = RevitUtilities.GetFamilySymbol(element, parameterId, parameter)
#         else:
#             try:
#                 sColName = scheduleField.GetName()  # Ligne pour facilité le débugage
#                 vName = parameterId.IntegerValue  # Ligne pour facilité le débugage
#                 AM_Element = element.GetAnalyticalModel()
#                 if AM_Element != None:
#                     parameter = AM_Element.get_Parameter(parameterId.IntegerValue)
#                 if parameter == None:
#                     parameter = element.get_Parameter(parameterId.IntegerValue)
#                 if parameter != None:  # Pour obtenir les valeurs des paramètres partagé
#                     tTypeParameter = parameter.Element.GetType()
#                     if tTypeParameter.Name == "FamilyInstance":
#                         if parameter.Definition.ParameterGroup == BuiltInParameterGroup.INVALID:  # Clause a des fin de tests seulement
#                             if parameter.IsShared and parameter.IsReadOnly:
#                                 parameter = RevitUtilities.GetFamilySymbol(element, parameterId, parameter)
#                     elif tTypeParameter.Name == "FamilySymbol":
#                         parameter = RevitUtilities.GetFamilySymbol(element, parameterId, parameter)
#                 else:
#                     # Valide si c'est un paramètre de type
#                     ElementType2 = doc.GetElement(element.GetTypeId())
#                     if ElementType2 != None:
#                         parameter = ElementType2.get_Parameter(parameterId.IntegerValue)
#                         if parameter != None:
#                             tTypeParameter = parameter.Element.GetType()
#                             if tTypeParameter.Name == "FamilyInstance":
#                             elif tTypeParameter.Name == "FamilySymbol":
#                                 parameter = RevitUtilities.GetFamilySymbol(element, parameterId, parameter)
#                             elif tTypeParameter.Name == "WallType":
#                                 parameter = RevitUtilities.GetWallType(element, parameterId, parameter)
#             except Exception,:
#             finally:
#         # ----End of the action according to the type of field----
#         return parameter
#
#     GetParameter = staticmethod(GetParameter)
#
#     def ValidValue(parameter):
#         """ <summary>
#              indicates whether the parameter variable contains a value
#          </summary>
#          <param name="parameter"></param>
#          <returns></returns>
#         """
#         bResult = False
#         if parameter != None:
#             if parameter.HasValue:
#                 bResult = True
#         return bResult
#
#     ValidValue = staticmethod(ValidValue)
#
#     def GetIsReadOnly(parameter, scheduleField, readonlyParameters):
#         """ <summary>
#              Method for obtaining cell rights
#          </summary>
#          <param name="parameter"></param>
#          <param name="scheduleField"></param>
#          <param name="readonlyParameters"></param>
#          <returns>True or False</returns>
#         """
#         readonlyParameter = True
#         bExtSchedule = False  # Indique que l'information provient d'une nomenclature parent
#         # ----Action selon le type de champ / Action according to the type of field----
#         if scheduleField.FieldType == ScheduleFieldType.Formula or scheduleField.FieldType == ScheduleFieldType.Count or scheduleField.FieldType == self._CountHost or scheduleField.FieldType == ScheduleFieldType.Space or scheduleField.FieldType == ScheduleFieldType.Analytical or scheduleField.FieldType == ScheduleFieldType.ProjectInfo or scheduleField.FieldType == ScheduleFieldType.FromRoom or scheduleField.FieldType == ScheduleFieldType.ToRoom or scheduleField.FieldType == ScheduleFieldType.Room or scheduleField.FieldType == ScheduleFieldType.MaterialQuantity or scheduleField.FieldType == ScheduleFieldType.StructuralMaterial:
#             bExtSchedule = True
#         # ----End of the action according to the type of field----
#         if parameter == None:
#             readonlyParameter = True
#         else:
#             if readonlyParameters.ContainsKey(
#                     scheduleField.ParameterId.IntegerValue) or parameter.IsReadOnly or bExtSchedule:
#                 readonlyParameter = True
#             else:
#                 readonlyParameter = False
#         return readonlyParameter
#
#     GetIsReadOnly = staticmethod(GetIsReadOnly)
#
#     def GetParameterValue(parameter, scheduleField, doc, element, appliedParameters):
#         """ <summary>
#              Gets the value for a schedule parameter
#          </summary>
#          <param name="parameter"></param>
#          <param name="scheduleField"></param>
#          <param name="doc"></param>
#          <param name="element"></param>
#          <param name="appliedParameters"></param>
#          <returns>Returns the value or null value</returns>
#         """
#         cellVal = None
#         parameterId = scheduleField.ParameterId
#         if scheduleField.FieldType == ScheduleFieldType.Formula:
#             cellVal = "0"
#         elif scheduleField.FieldType == ScheduleFieldType.Count or scheduleField.FieldType == self._CountHost:
#             cellVal = "1"
#         elif scheduleField.FieldType == ScheduleFieldType.MaterialQuantity:
#             if parameterId.IntegerValue == BuiltInParameter.MATERIAL_AREA:
#                 cellVal = RevitUtilities.ConvertToDisplayUnit(doc, scheduleField.GetSpecTypeId(),
#                                                               RevitUtilities.GetMaterialAreaOfElement(element))
#                 cellVal = RevitUtilities.ConvertToDisplayUnit(doc, scheduleField.UnitType,
#                                                               RevitUtilities.GetMaterialAreaOfElement(element))
#             elif parameterId.IntegerValue == BuiltInParameter.MATERIAL_VOLUME:
#                 cellVal = RevitUtilities.ConvertToDisplayUnit(doc, scheduleField.GetSpecTypeId(),
#                                                               RevitUtilities.GetMaterialValumeOfElement(element))
#                 cellVal = RevitUtilities.ConvertToDisplayUnit(doc, scheduleField.UnitType,
#                                                               RevitUtilities.GetMaterialValumeOfElement(element))
#             elif parameterId.IntegerValue == BuiltInParameter.MATERIAL_ASPAINT:
#                 cellVal = "No"
#                 if element.GetMaterialIds(True).Count > 0:
#                     cellVal = "Yes"
#             elif parameterId.IntegerValue == BuiltInParameter.PHY_MATERIAL_PARAM_UNIT_WEIGHT:
#                 dCellVal = 0
#                 materials = element.GetMaterialIds(False)
#                 if materials.Count > 0:
#                     enumerator = materials.GetEnumerator()
#                     while enumerator.MoveNext():
#                         Item = enumerator.Current
#                         eMaterial = doc.GetElement(Item)
#                         if eMaterial != None:
#                             pseProperty = doc.GetElement(eMaterial.StructuralAssetId)
#                             if pseProperty != None:
#                                 parameter = pseProperty.get_Parameter(parameterId.IntegerValue)
#                                 if parameter != None:
#                                     dCellVal += Convert.ToDouble(
#                                         RevitUtilities.GetParameterValue(doc, parameter, scheduleField))
#                                     parameter = None
#                 cellVal = dCellVal
#         # ---- End of the action according to the type of field----
#         if parameter != None:
#             cellVal = RevitUtilities.GetParameterValue(doc, parameter, scheduleField)
#             # Translate parameter value based on XML settings
#             appliedTranslations = appliedParameters.Where().ToList()
#             cellVal = RevitUtilities.TranslateValueToText(Convert.ToString(cellVal),
#                                                           appliedTranslations) if appliedTranslations.Any() else cellVal
#         return cellVal
#
#     GetParameterValue = staticmethod(GetParameterValue)
#
#     def GetParameterValue(doc, parameter, scheduleField):
#         """ <summary>
#              Gets the right value depending on its type of storage
#          </summary>
#          <param name="doc"></param>
#          <param name="parameter"></param>
#          <param name="scheduleField"></param>
#          <returns>Returns the good value</returns>
#         """
#         val = None
#         if parameter.StorageType == StorageType.Double:
#             dVal = parameter.AsProjectUnitTypeDouble(scheduleField)
#             try:
#                 if parameter.GetUnitTypeId() == UnitTypeId.Percentage:
#                     val = dVal / 100.0
#                 else:
#                     val = dVal
#                 if parameter.DisplayUnitType == DisplayUnitType.DUT_PERCENTAGE:
#                     val = dVal / 100.0
#                 else:
#                     val = dVal
#             except Exception,:
#                 val = dVal
#             finally:
#         elif parameter.StorageType == StorageType.String:
#             val = parameter.AsString()
#             if val == None:  # Adding an empty string to replace null solved sorting problems
#                 val = str.Empty
#         elif parameter.StorageType == StorageType.Integer:
#             val = parameter.AsInteger()
#             if parameter.Definition.ParameterType == ParameterType.YesNo:
#                 val = "False" if val == 0 else "True"
#         elif parameter.StorageType == StorageType.ElementId:
#             elementId = parameter.AsElementId()
#             if elementId.IntegerValue < 0:
#                 cat = doc.Settings.Categories.get_Item(elementId.IntegerValue)
#                 if cat != None:
#                     val = cat.Name
#             else:
#                 if parameter.Id.IntegerValue == -1002051 or parameter.Id.IntegerValue == -1002052:
#                     elementType = doc.GetElement(elementId)
#                     if elementType != None:
#                         familyName = RevitUtilities.GetElementFamilyName(doc, elementType)
#                         if parameter.Id.IntegerValue == -1002052:
#                             val = familyName + ": " + elementType.Name
#                         else:
#                             val = familyName
#                 elif parameter.Id.IntegerValue == -1012701:  # Pour un type area
#                     val = parameter.AsValueString()
#                 else:
#                     element = doc.GetElement(elementId)
#                     if element != None:
#                         val = element.Name
#         return val
#
#     GetParameterValue = staticmethod(GetParameterValue)
#
#     def GetListReadOnlyParamater(parametersSettings):
#         """ <summary>
#              Gets the list of columns that is write-only.
#          </summary>
#          <param name="parametersSettings"></param>
#          <returns>Returns the list</returns>
#         """
#         readonlyParameters = Hashtable()
#         enumerator = parametersSettings.ReadonlyParameters.GetEnumerator()
#         while enumerator.MoveNext():
#             parameter = enumerator.Current
#             readonlyParameters[parameter.Id] = True
#         # ============================================Added column to manually lock==========================================================
#         #
#         # -1152384 = Image type
#         # -1012101 = Phase demolished
#         # -1012100 = Phase created
#         # -1002064 = Top level
#         # -1002063 = Base level
#         # -1001305 = Rough Width
#         # -1001304 = Rough Heigh
#         # -1012201 = Scope Box
#         # -1007110 = Story above
#         # -1012030 = Conceptual Types
#         # -1012023 = Graphical Appearance
#         # -1007235 = Niveau supérieur multiétage
#         # -1007201 = Niveau supérieur
#         # -1007200 = Niveau de base
#         # -1006922 = Limite supérieure
#         # -1151210 = Type de support gauche
#         # -1151209 = Type de support droit
#         # -1151208 = Type de palier
#         # -1151207 = Type de volée
#         # -1008620 = Niveau de base
#         # -1005500 = Matériau structurel
#         # -1001107 = Contrainte inférieure
#         # -1001105 = Hauteur non contrainte
#         # -1001103 = Contrainte supérieure
#         # -1140036 = Type de fil
#         # -1140334 = Type de système
#         # -1150115 = Dépréciation due aux impuretés sur le luminaire
#         # -1150114 = Dépréciation de lumen de la lampe
#         # -1150113 = Perte de dépréciation de la surface
#         # -1150112 = Perte d'inclinaison de la lampe
#         # -1150110 = Perte de tension
#         # -1114251 = Type de construction
#         # -1114172 = Type d'espace
#         # -1018257 = Type de barre mineure inférieure/intérieure
#         # -1018256 = Type de barre majeure inférieure/intérieure
#         # -1018255 = Type de barre mineure supérieure/extérieure
#         # -1018254 = Type de barre majeure supérieure/extérieure
#         # -1018023 = Correspondances de couches mineures supérieures et inférieures
#         # -1018022 = Correspondances de couches majeures supérieures et inférieures
#         # -1018021 = Correspondances de couches majeures et mineures inférieures
#         # -1018020 = Correspondances de couches majeures et mineures supérieures
#         # -1012809 = Sous-catégorie de murs
#         # -1012800 = Profil
#         # -1002107 = Matériau
#         # -1017701 = Panneau de treillis
#         # -1017733 = Clé de famille partagée
#         # -1017604 = Type de treillis sens répartition
#         # -1017603 = Type de treillis sens porteur
#         # -1012819 = Profil
#         # -1012836 = Profil
#         # -1152335 = Niveau de base
#         # -1018361 = Barre principale
#         # -1018305 = Barre principale
#         # -1018300 = Face
#         # -1015000 = Cas de charge
#         # -1013411 = Type de poutre
#         # -1012701 = Type de surface
#         # -1017705 = Emplacement
#         # -1152385 = Physique: Image
#         # -1140217 = Température du fluide
#         #
#         tAddColReadOnly =
#         enumerator = tAddColReadOnly.GetEnumerator()
#         while enumerator.MoveNext():
#             iIdCol = enumerator.Current
#             readonlyParameters[iIdCol] = True
#         return readonlyParameters
#
#     GetListReadOnlyParamater = staticmethod(GetListReadOnlyParamater)
#
#     def SetParameterValue(parameter, value, scheduleField):
#         """ <summary>
#              Method to change the value of a parameter
#          </summary>
#          <param name="parameter"></param>
#          <param name="value"></param>
#          <param name="scheduleField"></param>
#         """
#         if parameter.StorageType == StorageType.Double:
#             if value == None:
#                 value = 0
#             dVal = Double.Parse(value.ToString())
#             dValueAct = parameter.AsProjectUnitTypeDouble(scheduleField)
#             try:
#                 if parameter.GetUnitTypeId() == UnitTypeId.Percentage:
#                     dVal *= 100.0
#                 if parameter.DisplayUnitType == DisplayUnitType.DUT_PERCENTAGE:
#                     dVal *= 100.0
#             except Exception,:
#             finally:
#             # ignored
#             if Math.Round(dValueAct, 4) != Math.Round(dVal, 4):
#                 if not parameter.Set(parameter.ToProjectUnitType(dVal, scheduleField)):
#                     raise TargetInvocationException(
#                         str.Format(Resources.ErrorOccurredWhileSettingParameter, parameter.Definition.Name, value),
#                         None)
#         elif parameter.StorageType == StorageType.String:
#             strVal = Convert.ToString(parameter.AsString())
#             bInsertString = False
#             if strVal != None:
#                 if not strVal.Equals(Convert.ToString(value), StringComparison.InvariantCultureIgnoreCase):
#                     bInsertString = True
#             elif value != None and value.ToString() != str.Empty:
#                 bInsertString = True
#             if bInsertString:
#                 if not parameter.Set(Convert.ToString(value)):  # Insertion du string
#                     raise TargetInvocationException(
#                         str.Format(Resources.ErrorOccurredWhileSettingParameter, parameter.Definition.Name, value),
#                         None)
#         elif parameter.StorageType == StorageType.Integer:
#             if parameter.Definition.ParameterType == ParameterType.YesNo:
#                 iVal = 1 if Convert.ToBoolean(value) else 0
#             else:
#                 iVal = Convert.ToInt32(value)
#             if iVal != parameter.AsInteger():
#                 # if (!parameter.SetValueString(iVal.ToString()))//Insertion de la valeur
#                 if not parameter.Set(iVal):  # Insertion de la valur
#                     raise TargetInvocationException(
#                         str.Format(Resources.ErrorOccurredWhileSettingParameter, parameter.Definition.Name, iVal), None)
#         elif parameter.StorageType == StorageType.ElementId:
#             doc = parameter.Element.Document
#             collector = None
#             newElement = None
#             if parameter.Id.IntegerValue == BuiltInParameter.ELEM_TYPE_PARAM:
#                 collector = FilteredElementCollector(doc).WhereElementIsElementType()
#                 newElement = collector.FirstOrDefault()
#             elif parameter.Id.IntegerValue == BuiltInParameter.ELEM_FAMILY_PARAM:
#                 collector = FilteredElementCollector(doc).WhereElementIsElementType()
#                 newElement = collector.Cast().FirstOrDefault()
#             else:
#                 return
#             originalElement = doc.GetElement(parameter.AsElementId())
#             if originalElement != None and newElement == None:
#                 if not parameter.Set(ElementId(BuiltInParameter.INVALID)):  # Insertion de la valeur
#                     raise TargetInvocationException(
#                         str.Format(Resources.ErrorOccurredWhileSettingParameter, parameter.Definition.Name,
#                                    "(Invalid)"), None)
#             elif newElement != None:
#                 if originalElement != None and originalElement.Id.IntegerValue != newElement.Id.IntegerValue or originalElement == None:
#                     if not parameter.Set(newElement.Id):  # Insertion de la valeur
#                         raise TargetInvocationException(
#                             str.Format(Resources.ErrorOccurredWhileSettingParameter, parameter.Definition.Name,
#                                        newElement.Id), None)
#
#     SetParameterValue = staticmethod(SetParameterValue)
#
#     def GetElementPhase(doc, element):
#         """ <summary>
#              Method for obtaining the current phase for an element
#          </summary>
#          <param name="doc"></param>
#          <param name="element"></param>
#          <returns>Null or Phase object</returns>
#         """
#         pPhase = None
#         ParameterPhase = element.get_Parameter(BuiltInParameter.PHASE_CREATED)
#         if ParameterPhase != None:
#             elementId = ParameterPhase.AsElementId()
#             enumerator = doc.Phases.GetEnumerator()
#             while enumerator.MoveNext():
#                 phase = enumerator.Current
#                 if phase.Id.IntegerValue == elementId.IntegerValue:
#                     pPhase = phase
#         return pPhase
#
#     GetElementPhase = staticmethod(GetElementPhase)
#
#     def GetFamillyRoom(familyInstance, pPhase, fieldType):
#         """ <summary>
#              Method thast gets Familly Room
#          </summary>
#          <param name="familyInstance"></param>
#          <param name="pPhase"></param>
#          <param name="fieldType"></param>
#          <returns>Null or Room object</returns>
#         """
#         room = None
#         if pPhase != None:
#             if fieldType == ScheduleFieldType.FromRoom:
#                 room = familyInstance.get_FromRoom(pPhase)
#             elif fieldType == ScheduleFieldType.ToRoom:
#                 room = familyInstance.get_ToRoom(pPhase)
#             elif fieldType == ScheduleFieldType.Room:
#                 room = familyInstance.get_Room(pPhase)
#         else:
#             if fieldType == ScheduleFieldType.FromRoom:
#             elif  # room = familyInstance.FromRoom;
#
#
# fieldType == ScheduleFieldType.ToRoom:
# elif  # room = familyInstance.ToRoom;
# fieldType == ScheduleFieldType.Room:
# # room = familyInstance.Room;
# return room
#
# GetFamillyRoom = staticmethod(GetFamillyRoom)
#
#
# def TranslateValueToText(value, parameters):
#     """ <summary>
#          Translate value to text
#      </summary>
#      <param name="value"></param>
#      <param name="parameters"></param>
#      <returns>Result translate</returns>
#     """
#     enumerator = parameters.GetEnumerator()
#     while enumerator.MoveNext():
#         parameter = enumerator.Current
#         enumerator = parameter.Translations.GetEnumerator()
#         while enumerator.MoveNext():
#             translation = enumerator.Current
#             if translation.Value.ToLower().Trim() == value.ToLower().Trim():
#                 return translation.Text.ToLower().Trim()
#     return value
#
#
# TranslateValueToText = staticmethod(TranslateValueToText)
#
#
# def TranslateTextToValue(text, parameters):
#     """ <summary>
#          Translate text to value
#      </summary>
#      <param name="text"></param>
#      <param name="parameters"></param>
#      <returns>Result value</returns>
#     """
#     enumerator = parameters.GetEnumerator()
#     while enumerator.MoveNext():
#         parameter = enumerator.Current
#         enumerator = parameter.Translations.GetEnumerator()
#         while enumerator.MoveNext():
#             translation = enumerator.Current
#             if translation.Text.ToLower().Trim() == text.ToLower().Trim():
#                 return translation.Value.ToLower().Trim()
#     raise ArgumentOutOfRangeException("text", str.Format(Resources.UnableFindCorrespondingValue, text))
#
#
# TranslateTextToValue = staticmethod(TranslateTextToValue)
#
#
# def CanExportParameter(parameter, ignoredParameters, location):
#     """ <summary>
#          Valid if the parameter can be exported
#      </summary>
#      <param name="parameter"></param>
#      <param name="ignoredParameters"></param>
#      <param name="location"></param>
#      <returns>True or False</returns>
#     """
#     if ignoredParameters.Any():
#         return False
#     if parameter.Definition.Name.ToLower().Contains("none"):
#         return False
#     return True
#
#
# CanExportParameter = staticmethod(CanExportParameter)
#
#
# def CanExportParameter(scheduleField, ignoredParameters, location):
#     """ <summary>
#          Valid if the parameter can be exported
#      </summary>
#      <param name="scheduleField"></param>
#      <param name="ignoredParameters"></param>
#      <param name="location"></param>
#      <returns></returns>
#     """
#     if ignoredParameters.Any():
#         return False
#     return True
#
#
# CanExportParameter = staticmethod(CanExportParameter)
#
#
# def ConvertRgbToColor(colorString):
#     """ <summary>
#          Convert RGB value to color object
#      </summary>
#      <param name="colorString"></param>
#      <returns>Color</returns>
#     """
#     if not str.IsNullOrEmpty(colorString):
#         rgb = colorString.Split(',')
#         if rgb.Length == 3:
#             try:
#                 return Color(Convert.ToByte(rgb[0]), Convert.ToByte(rgb[1]), Convert.ToByte(rgb[2]))
#             except FormatException,:
#             except OverflowException,:
#             finally:
#     return None
#
#
# ConvertRgbToColor = staticmethod(ConvertRgbToColor)
#
#
# def InsertMsgNotBeImported(worksheet):
#     """ <summary>
#          A method that inserts a row at the end of the table indicating that this table can not be imported.
#      </summary>
#      <param name="worksheet"></param>
#     """
#     iColCnt = worksheet.Dimension.End.Column
#     iRowCnt = worksheet.Dimension.End.Row
#     row = iRowCnt + 1
#     worksheet.Cells[row][1][row][iColCnt].Merge = True
#     worksheet.Cells[row][1].Value = Resources.ThisSheetCanNotBeImported
#     worksheet.Cells[row][1][row][iColCnt].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[row][1][row][iColCnt].Style.Fill.BackgroundColor.SetColor(Styles.BackgroundColor.MsgNotBeImported)
#     worksheet.Cells[row][1][row][iColCnt].Style.Font.Color.SetColor(Styles.FontColor.MsgNotBeImported)
#
#
# InsertMsgNotBeImported = staticmethod(InsertMsgNotBeImported)
#
#
# def LockAllColumns(worksheet):
#     """ <summary>
#          Method that locks all columns in a table
#      </summary>
#      <param name="worksheet"></param>
#     """
#     x = 1
#     while x <= worksheet.Dimension.End.Column:
#         RevitUtilities.LockColumn(worksheet, x)
#         x += 1
#
#
# LockAllColumns = staticmethod(LockAllColumns)
#
#
# def LockColumn(worksheet, iCol):
#     """ <summary>
#          Method that locks a column in an excel table
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iCol"></param>
#     """
#     worksheet.Column(iCol).Style.Locked = True
#     worksheet.Column(iCol).Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Column(iCol).Style.Fill.BackgroundColor.SetColor(Styles.BackgroundColor.CellLocked)
#     worksheet.Column(iCol).Style.Font.Color.SetColor(Styles.FontColor.CellLocked)
#
#
# LockColumn = staticmethod(LockColumn)
#
#
# def FormattingColElementType(worksheet, iCol):
#     """ <summary>
#          Method that locks and formats an ElementType column
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iCol"></param>
#     """
#     worksheet.Column(iCol).Style.Locked = True
#     worksheet.Column(iCol).Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Column(iCol).Style.Fill.BackgroundColor.SetColor(Styles.BackgroundColor.ColElementType)
#     worksheet.Column(iCol).Style.Font.Color.SetColor(Styles.FontColor.ColElementType)
#
#
# FormattingColElementType = staticmethod(FormattingColElementType)
#
#
# def FormattingColFormula(worksheet, iRowStart, iRowEnd, iCol):
#     """ <summary>
#          Modify the format of a formula column
#      </summary>
#      <param name="workbook"></param>
#      <param name="iCol"></param>
#     """
#     worksheet.Cells[iRowStart][iCol][iRowEnd][iCol].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[iRowStart][iCol][iRowEnd][iCol].Style.Fill.BackgroundColor.SetColor(
#         Styles.BackgroundColor.TypeFormula)
#     worksheet.Cells[iRowStart][iCol][iRowEnd][iCol].Style.Font.Color.SetColor(Styles.FontColor.TypeFormula)
#
#
# FormattingColFormula = staticmethod(FormattingColFormula)
#
#
# def FormattingRowWarningFormula(worksheet, iRowStart, iColStart, iRowEnd, iColEnd):
#     """ <summary>
#          Format the cell that contains the warning for formulas
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iRowStart"></param>
#      <param name="iColStart"></param>
#      <param name="iRowEnd"></param>
#      <param name="iColEnd"></param>
#     """
#     worksheet.Cells[iRowStart][iColStart][iRowEnd][iColEnd].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[iRowStart][iColStart][iRowEnd][iColEnd].Style.Fill.BackgroundColor.SetColor(
#         Styles.BackgroundColor.TypeFormula)
#     worksheet.Cells[iRowStart][iColStart][iRowEnd][iColEnd].Style.Font.Color.SetColor(Styles.FontColor.TypeFormula)
#     worksheet.Cells[iRowStart][iColStart][iRowEnd][iColEnd].Style.Border.Left.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRowStart][iColStart][iRowEnd][iColEnd].Style.Border.Left.Color.SetColor(
#         Styles.BorderColor.TypeFormula)
#     worksheet.Cells[iRowStart][iColStart][iRowEnd][iColEnd].Style.Border.Right.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRowStart][iColStart][iRowEnd][iColEnd].Style.Border.Right.Color.SetColor(
#         Styles.BorderColor.TypeFormula)
#     worksheet.Cells[iRowStart][iColStart][iRowEnd][iColEnd].Style.Border.Top.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRowStart][iColStart][iRowEnd][iColEnd].Style.Border.Top.Color.SetColor(
#         Styles.BorderColor.TypeFormula)
#     worksheet.Cells[iRowStart][iColStart][iRowEnd][iColEnd].Style.Border.Bottom.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRowStart][iColStart][iRowEnd][iColEnd].Style.Border.Bottom.Color.SetColor(
#         Styles.BorderColor.TypeFormula)
#
#
# FormattingRowWarningFormula = staticmethod(FormattingRowWarningFormula)
#
#
# def FormattingTheHeader(worksheet, iRow):
#     """ <summary>
#          Method that applies the formatting of the header
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iRow"></param>
#     """
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.BackgroundColor.SetColor(
#         Styles.BackgroundColor.Header)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Font.Color.SetColor(Styles.FontColor.Header)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Left.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Left.Color.SetColor(
#         Styles.BorderColor.HeaderCell)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Right.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Right.Color.SetColor(
#         Styles.BorderColor.HeaderCell)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Top.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Top.Color.SetColor(
#         Styles.BorderColor.Header)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Bottom.Style = ExcelBorderStyle.Thick
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Bottom.Color.SetColor(
#         Styles.BorderColor.Header)
#     worksheet.Cells[iRow][1].Style.Border.Left.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][1].Style.Border.Left.Color.SetColor(Styles.BorderColor.Header)
#     worksheet.Cells[iRow][worksheet.Dimension.Columns].Style.Border.Right.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][worksheet.Dimension.Columns].Style.Border.Right.Color.SetColor(Styles.BorderColor.Header)
#
#
# FormattingTheHeader = staticmethod(FormattingTheHeader)
#
#
# def FormatingTable(worksheet):
#     """ <summary>
#          Method that formats the Excel table
#      </summary>
#      <param name="worksheet"></param>
#     """
#     worksheet.Cells[1][1][worksheet.Dimension.Rows][
#         worksheet.Dimension.Columns].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[1][1][worksheet.Dimension.Rows][worksheet.Dimension.Columns].Style.Fill.BackgroundColor.SetColor(
#         Styles.BackgroundColor.General)
#     worksheet.Cells[1][1][worksheet.Dimension.Rows][worksheet.Dimension.Columns].Style.Font.Color.SetColor(
#         Styles.FontColor.General)
#     worksheet.Cells[1][1][worksheet.Dimension.Rows][
#         worksheet.Dimension.Columns].Style.Border.Top.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[1][1][worksheet.Dimension.Rows][worksheet.Dimension.Columns].Style.Border.Top.Color.SetColor(
#         Styles.BorderColor.Cell)
#     worksheet.Cells[1][1][worksheet.Dimension.Rows][
#         worksheet.Dimension.Columns].Style.Border.Bottom.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[1][1][worksheet.Dimension.Rows][worksheet.Dimension.Columns].Style.Border.Bottom.Color.SetColor(
#         Styles.BorderColor.Cell)
#     worksheet.Cells[1][1][worksheet.Dimension.Rows][
#         worksheet.Dimension.Columns].Style.Border.Left.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[1][1][worksheet.Dimension.Rows][worksheet.Dimension.Columns].Style.Border.Left.Color.SetColor(
#         Styles.BorderColor.Cell)
#     worksheet.Cells[1][1][worksheet.Dimension.Rows][
#         worksheet.Dimension.Columns].Style.Border.Right.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[1][1][worksheet.Dimension.Rows][worksheet.Dimension.Columns].Style.Border.Right.Color.SetColor(
#         Styles.BorderColor.Cell)
#
#
# FormatingTable = staticmethod(FormatingTable)
#
#
# def AutoFitAllCol(worksheet):
#     """ <summary>
#          Automatic resize all columns
#      </summary>
#      <param name="worksheet"></param>
#     """
#     x = 1
#     while x <= worksheet.Dimension.End.Column:
#         worksheet.Column(x).AutoFit()
#         x += 1
#
#
# AutoFitAllCol = staticmethod(AutoFitAllCol)
#
#
# def LockRow(worksheet, iRow):
#     """ <summary>
#          Method to lock a workset_name
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iRow"></param>
#     """
#     worksheet.Row(iRow).Style.Locked = True
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.BackgroundColor.SetColor(
#         Styles.BackgroundColor.CellLocked)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Font.Color.SetColor(Styles.FontColor.CellLocked)
#
#
# LockRow = staticmethod(LockRow)
#
#
# def Unlock(worksheet, iRow):
#     """ <summary>
#          Unlocks all cells in a row
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iRow"></param>
#     """
#     worksheet.Row(iRow).Style.Locked = False
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.BackgroundColor.SetColor(
#         Styles.BackgroundColor.CellUnlocked)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Font.Color.SetColor(Styles.FontColor.CellUnlocked)
#
#
# Unlock = staticmethod(Unlock)
#
#
# def UnlockCell(worksheet, iRow, iCol):
#     """ <summary>
#          Unlocks a cell
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iRow"></param>
#      <param name="iCol"></param>
#     """
#     worksheet.Cells[iRow][iCol].Style.Locked = False
#     worksheet.Cells[iRow][iCol].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[iRow][iCol].Style.Fill.BackgroundColor.SetColor(Styles.BackgroundColor.CellUnlocked)
#     worksheet.Cells[iRow][iCol].Style.Font.Color.SetColor(Styles.FontColor.CellUnlocked)
#
#
# UnlockCell = staticmethod(UnlockCell)
#
#
# def FormattingTheHeaderTypeField(worksheet, iRow):
#     """ <summary>
#          Formats the workset_name that contains the value types
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iRow"></param>
#     """
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.BackgroundColor.SetColor(
#         Styles.BackgroundColor.HeaderTypeField)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Font.Color.SetColor(
#         Styles.FontColor.HeaderTypeField)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Font.Italic = True
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Left.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Left.Color.SetColor(
#         Styles.BorderColor.HeaderTypeFieldCell)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Right.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Right.Color.SetColor(
#         Styles.BorderColor.HeaderTypeFieldCell)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Bottom.Style = ExcelBorderStyle.Medium
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Bottom.Color.SetColor(
#         Styles.BorderColor.HeaderTypeField)
#     worksheet.Cells[iRow][1].Style.Border.Left.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][1].Style.Border.Left.Color.SetColor(Styles.BorderColor.HeaderTypeField)
#     worksheet.Cells[iRow][worksheet.Dimension.Columns].Style.Border.Right.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][worksheet.Dimension.Columns].Style.Border.Right.Color.SetColor(
#         Styles.BorderColor.HeaderTypeField)
#
#
# FormattingTheHeaderTypeField = staticmethod(FormattingTheHeaderTypeField)
#
#
# def FormatingLevel1(worksheet, iRow):
#     """ <summary>
#          Formats a workset_name of subtotal level 1
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iRow"></param>
#     """
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Locked = True
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Font.Bold = True
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Font.Color.SetColor(Styles.FontColor.Level1)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.BackgroundColor.SetColor(
#         Styles.BackgroundColor.Level1)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Top.Style = ExcelBorderStyle.Medium
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Top.Color.SetColor(
#         Styles.BorderColor.Level1)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Bottom.Style = ExcelBorderStyle.Medium
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Bottom.Color.SetColor(
#         Styles.BorderColor.Level1)
#     worksheet.Cells[iRow][1].Style.Border.Left.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][1].Style.Border.Left.Color.SetColor(Styles.BorderColor.Level1)
#     worksheet.Cells[iRow][worksheet.Dimension.Columns].Style.Border.Right.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][worksheet.Dimension.Columns].Style.Border.Right.Color.SetColor(Styles.BorderColor.Level1)
#
#
# FormatingLevel1 = staticmethod(FormatingLevel1)
#
#
# def FormatingLevel2(worksheet, iRow):
#     """ <summary>
#          Formats a workset_name of subtotal level 2
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iRow"></param>
#     """
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Locked = True
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Font.Bold = True
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Font.Color.SetColor(Styles.FontColor.Level2)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.BackgroundColor.SetColor(
#         Styles.BackgroundColor.Level2)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Top.Style = ExcelBorderStyle.Medium
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Top.Color.SetColor(
#         Styles.BorderColor.Level2)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Bottom.Style = ExcelBorderStyle.Medium
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Bottom.Color.SetColor(
#         Styles.BorderColor.Level2)
#     worksheet.Cells[iRow][1].Style.Border.Left.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][1].Style.Border.Left.Color.SetColor(Styles.BorderColor.Level2)
#     worksheet.Cells[iRow][worksheet.Dimension.Columns].Style.Border.Right.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][worksheet.Dimension.Columns].Style.Border.Right.Color.SetColor(Styles.BorderColor.Level2)
#
#
# FormatingLevel2 = staticmethod(FormatingLevel2)
#
#
# def FormatingTotalRow(worksheet, iRow):
#     """ <summary>
#          Formats a workset_name of total
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iRow"></param>
#     """
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Locked = True
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Font.Bold = True  # Active le caractère gras
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Font.Color.SetColor(Styles.FontColor.Total)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.PatternType = ExcelFillStyle.Solid
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Fill.BackgroundColor.SetColor(
#         Styles.BackgroundColor.Total)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Top.Style = ExcelBorderStyle.Thick
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Top.Color.SetColor(
#         Styles.BorderColor.Total)
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Bottom.Style = ExcelBorderStyle.Thick
#     worksheet.Cells[iRow][1][iRow][worksheet.Dimension.Columns].Style.Border.Bottom.Color.SetColor(
#         Styles.BorderColor.Total)
#     worksheet.Cells[iRow][1].Style.Border.Left.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][1].Style.Border.Left.Color.SetColor(Styles.BorderColor.Total)
#     worksheet.Cells[iRow][worksheet.Dimension.Columns].Style.Border.Right.Style = ExcelBorderStyle.Thin
#     worksheet.Cells[iRow][worksheet.Dimension.Columns].Style.Border.Right.Color.SetColor(Styles.BorderColor.Total)
#
#
# FormatingTotalRow = staticmethod(FormatingTotalRow)
#
#
# def FreezeRow(worksheet, iRow):
#     """ <summary>
#          Freezes a row of the Excel table
#      </summary>
#      <param name="worksheet"></param>
#      <param name="iRow"></param>
#     """
#     worksheet.View.FreezePanes(iRow, 1)
#
#
# FreezeRow = staticmethod(FreezeRow)
#
#
# def GetOperator(sFilterType):
#     """ <summary>
#          Gets the operator in string format according to its type
#      </summary>
#      <param name="sFilterType"></param>
#      <returns>Returns the operator in string format or an empty string</returns>
#     """
#     sResult = str.Empty
#     if sFilterType == ScheduleFilterType.Equal:
#         sResult = "="
#     elif sFilterType == ScheduleFilterType.LessThan:
#         sResult = "<"
#     elif sFilterType == ScheduleFilterType.LessThanOrEqual:
#         sResult = "<="
#     elif sFilterType == ScheduleFilterType.GreaterThan:
#         sResult = ">"
#     elif sFilterType == ScheduleFilterType.GreaterThanOrEqual:
#         sResult = ">="
#     elif sFilterType == ScheduleFilterType.NotEqual:
#         sResult = "<>"
#     return sResult
#
#
# GetOperator = staticmethod(GetOperator)
#
#
# def GetStringSort(vSchedule, doc, FieldsList):
#     """ <summary>
#          Gets the string for sorting
#      </summary>
#      <param name="vSchedule">ViewSchedule</param>
#      <param name="doc">Document</param>
#      <param name="FieldsList">List<ScheduleField></param>
#      <returns>Returns the string for sorting or an empty string</returns>
#     """
#     sStringSort = str.Empty
#     enumerator = vSchedule.Definition.GetSortGroupFields().GetEnumerator()
#     while enumerator.MoveNext():
#         scheduleSortGroupField = enumerator.Current
#         scheduleField = FieldsList.FirstOrDefault()
#         if scheduleField != None:
#             if sStringSort != str.Empty:
#                 sStringSort += ", "
#             sStringSort += str.Format("[{0}] {1}", scheduleField.GetSchedulableField().GetName(doc),
#                                       "asc" if scheduleSortGroupField.SortOrder == ScheduleSortOrder.Ascending else "desc")
#     return sStringSort
#
#
# GetStringSort = staticmethod(GetStringSort)
#
#
# def GetStringFilter(vSchedule, doc):
#     """ <summary>
#          Gets the string to filter the table
#      </summary>
#      <param name="vSchedule">ViewSchedule</param>
#      <returns>Returns the string to filter or an empty string</returns>
#     """
#     sStringFilter = str.Empty
#     enumerator = vSchedule.Definition.GetFilters().GetEnumerator()
#     while enumerator.MoveNext():
#         sFilter = enumerator.Current
#         sOperator = RevitUtilities.GetOperator(sFilter.FilterType)
#         sField = vSchedule.Definition.GetField(sFilter.FieldId)
#         if sField != None and not str.IsNullOrEmpty(sOperator):
#             bValueFind = False
#             sFilterItem = "[" + sField.GetName() + "]" + sOperator
#             if sFilter.IsDoubleValue:
#                 foItem = doc.GetUnits().GetFormatOptions(sField.GetSpecTypeId())
#                 dut = foItem.GetUnitTypeId()
#                 dValue = UnitUtils.ConvertFromInternalUnits(sFilter.GetDoubleValue(), dut)
#                 sFilterItem += dValue.ToString()
#                 foItem = doc.GetUnits().GetFormatOptions(sField.UnitType)
#                 dut = foItem.DisplayUnits
#                 dValue = UnitUtils.ConvertFromInternalUnits(sFilter.GetDoubleValue(), dut)
#                 sFilterItem += dValue.ToString()
#                 bValueFind = True
#             elif sFilter.IsIntegerValue:
#                 sFilterItem += "'" + sFilter.GetIntegerValue() + "'"
#                 bValueFind = True
#             elif sFilter.IsStringValue:
#                 sFilterItem += "'" + sFilter.GetStringValue().AddSlashes() + "'"
#                 bValueFind = True
#             elif sFilter.IsElementIdValue:
#                 sFilterItem += sFilter.GetElementIdValue().ToString()
#             elif sFilter.IsNullValue:
#                 sFilterItem += "null"
#             if bValueFind:
#                 if sStringFilter != str.Empty:
#                     sStringFilter += " and "
#                 sStringFilter += sFilterItem
#     return sStringFilter
#
#
# GetStringFilter = staticmethod(GetStringFilter)
#
#
# def GetElementFamilyName(doc, elementType):
#     return elementType.FamilyName
#
#
# GetElementFamilyName = staticmethod(GetElementFamilyName)
#
#
# def GetElementParameter(assetElement, parameterName):
#     if assetElement == None:
#         return None
#     return assetElement.LookupParameter(parameterName)
#
#
# GetElementParameter = staticmethod(GetElementParameter)
