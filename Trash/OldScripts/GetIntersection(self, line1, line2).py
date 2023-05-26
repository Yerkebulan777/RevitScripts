
def GetIntersection(self, line1, line2):
	result = line1.Intersect(line2)
	if result != SetComparisonResult.Overlap:
		raise InvalidOperationException("Input lines did not intersect.")
	if results == None or results.Size != 1:
		raise InvalidOperationException("Could not extract line intersection point.")
	iResult = results.get_Item(0)
	return iResult.XYZPoint