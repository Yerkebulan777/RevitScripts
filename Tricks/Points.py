import math


def circle_points(center, nums, radius):
    points = []
    arc = (2 * math.pi) / nums  # angle between two of the points
    dx, dy, dz = center.X, center.Y, center.Z
    for i in range(nums):
        theta = arc * i  # golden angle increment
        x = radius * math.cos(theta) + dx
        y = radius * math.sin(theta) + dy
        p = Point.ByCoordinates(x, y, dz)
        points.append(p)
    return points


center = XYZ(0, 0, 0)
result = circle_points(center, 15, 150)

print result
