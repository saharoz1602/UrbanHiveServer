import math


class NightWatchPositionsCalculator:
    import math
    def __init__(self,location):
        self.lat = location["latitude"]
        self.lon = location["longitude"]

    def generate_circle_positions(self, radius, points_amount):
        # Convert latitude and longitude from degrees to radians
        lat_rad = math.radians(self.lat)
        lon_rad = math.radians(self.lon)

        # Earth's radius in kilometers (approx.)
        earth_radius = 6371.0

        # Calculate angular distance covered on Earth's surface
        angular_distance = radius / earth_radius

        points = []
        for i in range(points_amount):
            # Calculate the angle for this point
            angle = math.radians((360 / points_amount) * i)

            # Calculate the latitude and longitude of the point
            point_lat_rad = math.asin(math.sin(lat_rad) * math.cos(angular_distance) +
                                      math.cos(lat_rad) * math.sin(angular_distance) * math.cos(angle))
            point_lon_rad = lon_rad + math.atan2(math.sin(angle) * math.sin(angular_distance) * math.cos(lat_rad),
                                                 math.cos(angular_distance) - math.sin(lat_rad) * math.sin(
                                                     point_lat_rad))

            # Convert the point's latitude and longitude back to degrees
            point_lat = math.degrees(point_lat_rad)
            point_lon = math.degrees(point_lon_rad)

            # Add the point to the list
            points.append({"Latitude": point_lat, "Longitude": point_lon})

        return points

    def assign_member_to_position(self, positions, members):
        inlays = []
        for pos, mem in zip(positions, members):
            # Create a new dictionary combining the member info with their assigned position
            inlay = {"id": mem["id"], "name": mem["name"], "position": pos}
            inlays.append(inlay)
        return inlays






