from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.geos import Point

wgs84 = SpatialReference(4326)
pseudo_mercartor = SpatialReference(3857)
planification = CoordTransform(wgs84, pseudo_mercartor)


def planify_coords(lat, lon):
    """ Transforms a WGS84 (GPS) coordinates into a projected point

    Projected points are expected in database.

    :param lat: latitude as per WGS84
    :param lon: longitude as per WGS84
    :return: a point ready to be inserted into DB.
    :rtype: Point
    """
    point = Point(lon, lat, srid=4326)
    point.transform(planification)
    return point
