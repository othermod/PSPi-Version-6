import sys

__all__ = ["liangbarsky", "cohensutherland", "clipline", "point_on_line"]


def cohensutherland(left, top, right, bottom, x1, y1, x2, y2):
    """Clips a line to a rectangular area.

    This implements the Cohen-Sutherland line clipping algorithm. ``left``,
    ``top``, ``right`` and ``bottom`` define the bounds of the clipping area,
    by which the line from ``(x1, y1)`` to ``(x2, y2)`` will be clipped.

    Args:
        left (int): The left boundary of the clipping area.
        top (int): The top boundary of the clipping area.
        right (int): The right boundary of the clipping area.
        bottom (int): The bottom boundary of the clipping area.
        x1 (int): The x-coordinate of the starting point of the line.
        y1 (int): The y-coordinate of the starting point of the line.
        x2 (int): The x-coordinate of the end point of the line.
        y2 (int): The y-coordinate of the end point of the line.

    Returns:
        tuple: The start and end coordinates of the clipped line in the form
        ``(cx1, cy1, cx2, cy2)``. If the line does not intersect with the
        rectangular clipping area, all 4 values will be ``None``.

    """
    LEFT, RIGHT, LOWER, UPPER = 1, 2, 4, 8

    if bottom > top:
        bottom, top = (top, bottom)

    def _getclip(xa, ya):
        p = 0
        if xa < left:
            p = LEFT
        elif xa > right:
            p = RIGHT
        if ya < bottom:
            p |= LOWER
        elif ya > top:
            p |= UPPER
        return p

    k1 = _getclip(x1, y1)
    k2 = _getclip(x2, y2)
    while (k1 | k2) != 0:
        if (k1 & k2) != 0:
            return None, None, None, None
        opt = k2 if k2 > k1 else k1
        if opt & UPPER:
            x = x1 + (x2 - x1) * (1.0 * (top - y1)) / (y2 - y1)
            y = top
        elif opt & LOWER:
            x = x1 + (x2 - x1) * (1.0 * (bottom - y1)) / (y2 - y1)
            y = bottom
        elif opt & RIGHT:
            y = y1 + (y2 - y1) * (1.0 * (right - x1)) / (x2 - x1)
            x = right
        elif opt & LEFT:
            y = y1 + (y2 - y1) * (1.0 * (left - x1)) / (x2 - x1)
            x = left
        else:
            # this should not happen
            raise RuntimeError("invalid clipping state")

        if opt == k1:
            x1, y1 = x, y
            k1 = _getclip(x1, y1)
        else:
            x2, y2 = x, y
            k2 = _getclip(x2, y2)

    return x1, y1, x2, y2


def liangbarsky(left, top, right, bottom, x1, y1, x2, y2):
    """Clips a line to a rectangular area.

    This implements the Liang-Barsky line clipping algorithm. ``left``,
    ``top``, ``right`` and ``bottom`` define the bounds of the clipping area,
    by which the line from ``(x1, y1)`` to ``(x2, y2)`` will be clipped.

    Args:
        left (int): The left boundary of the clipping area.
        top (int): The top boundary of the clipping area.
        right (int): The right boundary of the clipping area.
        bottom (int): The bottom boundary of the clipping area.
        x1 (int): The x-coordinate of the starting point of the line.
        y1 (int): The y-coordinate of the starting point of the line.
        x2 (int): The x-coordinate of the end point of the line.
        y2 (int): The y-coordinate of the end point of the line.

    Returns:
        tuple: The start and end coordinates of the clipped line in the form
        ``(cx1, cy1, cx2, cy2)``. If the line does not intersect with the
        rectangular clipping area, all 4 values will be ``None``.

    """
    dx = x2 - x1 * 1.0
    dy = y2 - y1 * 1.0
    dt0, dt1 = 0.0, 1.0
    xx1 = x1
    yy1 = y1

    if bottom > top:
        bottom, top = (top, bottom)

    checks = ((-dx, x1 - left),
              (dx, right - x1),
              (-dy, y1 - bottom),
              (dy, top - y1))

    for p, q in checks:
        if p == 0 and q < 0:
            return None, None, None, None
        if p != 0:
            dt = q / (p * 1.0)
            if p < 0:
                if dt > dt1:
                    return None, None, None, None
                dt0 = max(dt0, dt)
            else:
                if dt < dt0:
                    return None, None, None, None
                dt1 = min(dt1, dt)

    if dt0 > 0:
        x1 += dt0 * dx
        y1 += dt0 * dy
    if dt1 < 1:
        x2 = xx1 + dt1 * dx
        y2 = yy1 + dt1 * dy

    return x1, y1, x2, y2


def clipline(l, t, r, b, x1, y1, x2, y2, method='liangbarsky'):
    """Clips a line to a rectangular area using a given method.

    Args:
        l (int): The left boundary of the clipping area.
        t (int): The top boundary of the clipping area.
        r (int): The right boundary of the clipping area.
        b (int): The bottom boundary of the clipping area.
        x1 (int): The x-coordinate of the starting point of the line.
        y1 (int): The y-coordinate of the starting point of the line.
        x2 (int): The x-coordinate of the end point of the line.
        y2 (int): The y-coordinate of the end point of the line.
        method (str, optional): The method to use for clipping lines, can be
            either 'cohensutherland' or 'liangbarsky'. Defaults to liangbarsky.

    Returns:
        tuple: The start and end coordinates of the clipped line in the form
        ``(cx1, cy1, cx2, cy2)``. If the line does not intersect with the
        rectangular clipping area, all 4 values will be ``None``.

    """
    if method == 'cohensutherland':
        return cohensutherland(l, t, r, b, x1, y1, x2, y2)
    elif method == 'liangbarsky':
        return liangbarsky(l, t, r, b, x1, y1, x2, y2)
    else:
        raise ValueError("Unknown clipping method '{0}'".format(method))


def point_on_line(p1, p2, point):
    """Checks if a point falls along a given line segment.

    Args:
        p1 (tuple): The (x, y) coordinates of the starting point of the line.
        p2 (tuple): The (x, y) coordinates of the end point of the line.
        point (tuple): The (x, y) coordinates to test against the line.
    
    Returns:
        bool: ``True`` if the point falls along the line segment, otherwise
        ``False``.

    """
    x1, y1 = p1
    x2, y2 = p2
    px, py = point
    det = (py - y1) * (x2 - x1) - (px - x1) * (y2 - y1)
    if abs(det) > sys.float_info.epsilon:
        return False
    return (min(x1, x2) <= px <= max(x1, x2) and
            min(y1, y2) <= py <= max(y1, y2))
