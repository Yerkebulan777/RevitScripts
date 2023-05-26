
def getPolygon(self, floor):
    geomOptions = app.Create.NewGeometryOptions()
    elem = floor.get_Geometry(geomOptions)
    vertices = List[Vertex]()
    enumerator = elem.Objects.GetEnumerator()
    while enumerator.MoveNext():
        obj = enumerator.Current
        solid = obj
        if None != solid:
            face = solid.Faces.get_Item(0)
            loop = face.EdgeLoops.get_Item(0)
            enumerator = loop.GetEnumerator()
            while enumerator.MoveNext():
                edge = enumerator.Current
                edgePts = edge.Tessellate()
                n = edgePts.Size
                i = 0
                while i < n - 1:
                    p = edgePts.get_Item(i)
                    vertices.Add(Vertex(p.X, p.Y))
                    i += 1
            break
    vertexList = VertexList()
    vertexList.NofVertices = vertices.Count
    vertexList.Vertex = vertices.ToArray()
    poly = Polygon()
    poly.AddContour(vertexList, False)
    return poly