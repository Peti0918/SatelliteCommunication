class GroundStation:
    def __init__(self, name: str, latitude_deg: float,
                 longitude_deg: float, elevation_m: float):
        self.name = name
        self.latitude_deg = latitude_deg
        self.longitude_deg = longitude_deg
        self.elevation_m = elevation_m