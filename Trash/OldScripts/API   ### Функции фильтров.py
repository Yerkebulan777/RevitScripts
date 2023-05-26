def LevelByElevation( value ):
    provider = ParameterValueProvider( ElementId(BuiltInParameter.LEVEL_ELEV) )
    filterrule = FilterDoubleRule( provider, FilterNumericEquals(),  value, 0.05 )
    return ElementParameterFilter( filterrule ) 

def GetFilterDoubleParameter( bip, value, evaluator ):
	provider = ParameterValueProvider( ElementId( bip ) )
	if evaluator == 0: evaluator = FilterNumericEquals()
	if evaluator == 1: evaluator = FilterNumericLessOrEqual()
	if evaluator == 2: evaluator = FilterNumericGreaterOrEqual()
	filterrule = FilterDoubleRule( provider, evaluator, value, 0.05 )
	ParameterFilter = ElementParameterFilter( filterrule )
	return ParameterFilter

def GetFilterStringParameter( bip, value ):
    provider = ParameterValueProvider( ElementId( bip ) )
    ParameterFilter = FilterStringRule( provider, FilterStringContains(), value, False )
    return ElementParameterFilter( ParameterFilter )
    
def FinishingByLevel( level, rooms ):
	BoundingBoxes = [ i.get_BoundingBox(None) for i in rooms if i.get_BoundingBox(None) ]
	Transforms = [ box.Transform for box in BoundingBoxes ]
	BBoxMinX = min([ t.OfPoint( box.Min ).X for box, t in zip(BoundingBoxes, Transforms)])
	BBoxMinY = min([ t.OfPoint( box.Min ).Y for box, t in zip(BoundingBoxes, Transforms)])
	BBoxMinZ = min([ t.OfPoint( box.Min ).Z for box, t in zip(BoundingBoxes, Transforms)])
	BBoxMaxX = max([ t.OfPoint( box.Max ).X for box, t in zip(BoundingBoxes, Transforms)])
	BBoxMaxY = max([ t.OfPoint( box.Max ).Y for box, t in zip(BoundingBoxes, Transforms)])
	BBoxMaxZ = max([ t.OfPoint( box.Max ).Z for box, t in zip(BoundingBoxes, Transforms)])
	BBoxMin = XYZ( BBoxMinX, BBoxMinY, BBoxMinZ )
	BBoxMax = XYZ( BBoxMaxX, BBoxMaxY, BBoxMaxZ )
	LevelFilter = ElementLevelFilter( level.Id )
	BBoxFilter = BoundingBoxIntersectsFilter(Outline( BBoxMin, BBoxMax ))
	### Filters ###
	builtInCats = List[BuiltInCategory]()
	builtInCats.Add(BuiltInCategory.OST_Ceilings)
	builtInCats.Add(BuiltInCategory.OST_Roofs)
	builtInCats.Add(BuiltInCategory.OST_GenericModel)
	LocationFilter = LogicalAndFilter(LevelFilter, BBoxFilter)
	CategoryFilter = ElementMulticategoryFilter(builtInCats)
	WallWidhtFilter = GetFilterDoubleParameter( BuiltInParameter.WALL_ATTR_WIDTH_PARAM, 50/304.8, 1 )
	FloorThicnessFilter = GetFilterDoubleParameter( BuiltInParameter.FLOOR_ATTR_THICKNESS_PARAM, 150/304.8, 1 )
	StringFilter = GetFilterStringParameter( BuiltInParameter.FUNCTION_PARAM, "Внутренние слои" )
	WallFilter = LogicalAndFilter(WallWidhtFilter, StringFilter)
	FloorFilter = LogicalAndFilter(FloorThicnessFilter, StringFilter)
	### Collectors ###
	collector = FilteredElementCollector(doc).WherePasses(LocationFilter)
	items = collector.WherePasses(CatsFilter).WhereElementIsNotElementType().ToElements()
	collector = FilteredElementCollector(doc).WherePasses(LocationFilter)
	walls = collector.OfCategory(BuiltInCategory.OST_Walls).WherePasses(WallFilter).WhereElementIsNotElementType().ToElements()
	collector = FilteredElementCollector(doc).WherePasses(LocationFilter)
	floors = collector.OfCategory(BuiltInCategory.OST_Floors).WherePasses(FloorFilter).WhereElementIsNotElementType().ToElements()
	return flatten(filter(lambda x: x, [ walls, items, floors ]))

