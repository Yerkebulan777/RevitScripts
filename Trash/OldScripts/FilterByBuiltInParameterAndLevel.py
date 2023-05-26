
def FilterByBuiltInParameterAndLevel( bip, filter_value, evaluator, builtIn_category, levelId ):
    parameter = bip.Definition
    provider = ParameterValueProvider( ElementId( bip ) )
    if   evaluator == 1: evaluator = FilterStringContains()
    elif evaluator == 2: evaluator = FilterStringEquals()
    elif evaluator == 3: evaluator = FilterNumericEquals()
    elif evaluator == 4: evaluator = FilterNumericGreaterOrEqual()
    elif evaluator == 5: evaluator = FilterNumericLessOrEqual()
    if parameter.StorageType == StorageType.String:
        filterrule = FilterStringRule( provider, evaluator, filter_value, False ) 
        ParameterFilter = ElementParameterFilter(filterrule)
    elif parameter.StorageType == StorageType.Double:
        filterrule = FilterDoubleRule( provider, evaluator, filter_value, 10.-3 )
        ParameterFilter = ElementParameterFilter(filterrule)
    LevelFilter =  ElementLevelFilter(levelId)
    LogicalFilter = LogicalAndFilter(LevelFilter, ParameterFilter)
    collector = FilteredElementCollector(doc).OfCategory( builtIn_category )
    return collector.WherePasses( LogicalFilter ).WhereElementIsNotElementType().ToElements()
    
    
    
    
    
    