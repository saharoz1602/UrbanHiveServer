




from math import radians, cos, sin, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in km
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Difference in coordinates
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance

def locations_within_radius(center_location, radius, locations):
    within_radius = []
    for location in locations:
        distance = calculate_distance(center_location[0], center_location[1], location[0], location[1])
        if distance <= radius:
            within_radius.append(location)
    return within_radius

# Example usage
center_location = [37.4219909, -122.0839496] # New York City, for example
radius = 50 # in km
locations = [
    [38.4219909, -123.0839496], # somewhere in New York
    [36.4219909, -121.0839496], # Los Angeles, definitely outside the radius
    [37.5769909, -122.1849496] # Chicago, also outside the radius
]

pr = locations_within_radius(center_location, radius, locations)
print(pr)
