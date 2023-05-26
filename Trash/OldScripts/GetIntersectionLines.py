def Intersection(c1, c2):
		p1 = c1.GetEndPoint(0)
		q1 = c1.GetEndPoint(1)
		p2 = c2.GetEndPoint(0)
		q2 = c2.GetEndPoint(1)
		v1 = q1 - p1; v2 = q2 - p2; w = p2 - p1
		c = (v2.X * w.Y - v2.Y * w.X) / (v2.X * v1.Y - v2.Y * v1.X)
		p5 = None
		if not Double.IsInfinity(c):
			x = p1.X + c * v1.X
			y = p1.Y + c * v1.Y
			p5 = XYZ(x, y, 0)
		return p5