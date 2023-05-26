def getWallElement(results):
	calculator = SpatialElementGeometryCalculator(doc)
	options = Autodesk.Revit.DB.SpatialElementBoundaryOptions()
	boundloc = Autodesk.Revit.DB.AreaVolumeSettings.GetAreaVolumeSettings(doc).GetSpatialElementBoundaryLocation(SpatialElementType.Room)
	options.SpatialElementBoundaryLocation = boundloc
	results = calculator.CalculateSpatialElementGeometry(item)
	elIds = []
	for bface in results.GetBoundaryFaceInfo(face):  
		elId = bface.SpatialBoundaryElement.HostElementId
		elIds.append(elId)
	return elIds