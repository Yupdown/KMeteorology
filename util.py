
def convert_coordinate(lon, lat):
    x = 1 + 798 * (lon - 124.635) / 7.2339
    y = 1 - 758 * (lat - 38.6346) / 5.5223
    return x, y
