import math


class NightWatchPositionsCalculator:
    """
    A class to calculate positions for members of a night watch around a given central location.
    """

    def __init__(self, location):
        """
        Initializes the calculator with a specific location.

        Parameters:
        - location (dict): A dictionary with 'latitude' and 'longitude' keys for the central location.
        """
        # Store latitude and longitude from the provided location dictionary
        self.lat = location["latitude"]
        self.lon = location["longitude"]

    def generate_circle_positions(self, radius, points_amount):
        """
        Generates positions in a circle around the central location.

        Parameters:
        - radius (float): The radius of the circle in kilometers.
        - points_amount (int): The number of positions to generate around the circle.

        Returns:
        - list: A list of dictionaries, each containing the 'Latitude' and 'Longitude' of a point.
        """
        # Convert latitude and longitude from degrees to radians for calculation
        lat_rad = math.radians(self.lat)
        lon_rad = math.radians(self.lon)

        # Earth's radius in kilometers (approximation)
        earth_radius = 6371.0

        # Calculate angular distance covered on Earth's surface for the given radius
        angular_distance = radius / earth_radius

        # Initialize a list to hold the generated positions
        points = []
        for i in range(points_amount):
            # Calculate the angle for this point
            angle = math.radians((360 / points_amount) * i)

            # Calculate the latitude and longitude of the point using spherical trigonometry
            point_lat_rad = math.asin(math.sin(lat_rad) * math.cos(angular_distance) +
                                      math.cos(lat_rad) * math.sin(angular_distance) * math.cos(angle))
            point_lon_rad = lon_rad + math.atan2(math.sin(angle) * math.sin(angular_distance) * math.cos(lat_rad),
                                                 math.cos(angular_distance) - math.sin(lat_rad) * math.sin(
                                                     point_lat_rad))

            # Convert the point's latitude and longitude back to degrees from radians
            point_lat = math.degrees(point_lat_rad)
            point_lon = math.degrees(point_lon_rad)

            # Add the point to the list as a dictionary
            points.append({"Latitude": point_lat, "Longitude": point_lon})

        return points

    def assign_member_to_position(self, positions, members):
        """
        Assigns members to specified positions.

        Parameters:
        - positions (list): A list of dictionaries containing position 'Latitude' and 'Longitude'.
        - members (list): A list of dictionaries, each containing 'id' and 'name' of a member.

        Returns:
        - list: A list of dictionaries, each representing a member with their 'id', 'name', and assigned 'position'.
        """
        # Initialize a list to hold the information about members and their assigned positions
        inlays = []
        for pos, mem in zip(positions, members):
            # Combine the member info with their assigned position into a new dictionary
            inlay = {"id": mem["id"], "name": mem["name"], "position": pos}
            inlays.append(inlay)
        return inlays
