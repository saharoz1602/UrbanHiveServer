from math import radians, sin, cos, sqrt, atan2


class RadiusCalculator:
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great-circle distance between two points on the Earth using the Haversine formula.

        Parameters:
        lat1 (float): Latitude of the first point in degrees.
        lon1 (float): Longitude of the first point in degrees.
        lat2 (float): Latitude of the second point in degrees.
        lon2 (float): Longitude of the second point in degrees.

        Returns:
        float: Distance between the two points in kilometers.
        """
        # Radius of the Earth in kilometers.
        radius_of_earth = 6371.0

        # Convert latitude and longitude from degrees to radians for the Haversine formula.
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Calculate the differences in latitude and longitude.
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula: calculates the distance between two points on a sphere
        # based on their longitudes and latitudes.
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        # Calculate the distance using the radius of the Earth.
        distance = radius_of_earth * c

        return distance

    def locations_within_radius(self, center_location, radius, locations):
        """
        Find all locations within a specified radius of a center location.

        Parameters:
        center_location (tuple): A tuple (lat, lon) representing the center location.
        radius (float): The radius within which to find locations, in kilometers.
        locations (list): A list of locations where each location is a dictionary
                          with 'latitude' and 'longitude' keys.

        Returns:
        list: A list of locations within the specified radius.
        """
        within_radius = []  # Initialize an empty list to hold locations within the radius.

        # Iterate through each location in the list.
        for location in locations:
            # Calculate the distance from the center location to the current location.
            distance = self.calculate_distance(center_location[0], center_location[1], location["latitude"],
                                               location["longitude"])

            # Check if the distance is within the specified radius.
            if distance <= radius:
                # If within the radius, add the location to the list.
                within_radius.append(location)

        return within_radius

def main():
    # Instance of the RadiusCalculator class.
    calculator = RadiusCalculator()

    # Example coordinates for distance calculation.
    lat1, lon1 = 40.7128, -74.0060  # New York City
    lat2, lon2 = 34.0522, -118.2437  # Los Angeles
    distance = calculator.calculate_distance(lat1, lon1, lat2, lon2)
    print(f"Distance between New York City and Los Angeles: {distance:.2f} kilometers")

    # Example for finding locations within a specified radius.
    center_location = (51.5074, -0.1278)  # London
    radius = 200  # 50 kilometers radius
    locations = [
        {"name": "London", "latitude": 51.5074, "longitude": -0.1278},
        {"name": "Cambridge", "latitude": 52.2053, "longitude": 0.1218},
        {"name": "Brighton", "latitude": 50.8225, "longitude": -0.1372},
    ]
    within_radius = calculator.locations_within_radius(center_location, radius, locations)
    print("Locations within 50 kilometers of London:")
    for location in within_radius:
        print(location["name"])
        print(location["latitude"],location["longitude"])

if __name__ == "__main__":
    main()