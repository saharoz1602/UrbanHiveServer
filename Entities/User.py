class User:
    def __init__(self, username, password, email, location, area_radius, first_name, last_name, id):
        self.username = username
        self.password = password
        self.email = email
        self.location = location
        self.area_radius = area_radius
        self.first_name = first_name
        self.last_name = last_name
        self.friends_list = []
        self.requests = []
        self.id = id

    def change_password(self, new_password):
        self.password = new_password
        return True
