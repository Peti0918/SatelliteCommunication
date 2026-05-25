import numpy as np

#kibocsátott fotonok mekkora része érkezik meg a vevőhöz?
class LinkModel:
    def __init__(
    self,
    wavelength_nm=800,
    atmospheric_alpha=0.1,
    geometric_gain=1e8,
    isl_geometric_gain=1e5,
):
        self.wavelength = wavelength_nm * 1e-9
        self.alpha = atmospheric_alpha
        self.geometric_gain = geometric_gain
        self.isl_geometric_gain = isl_geometric_gain

    def geometric_loss(self, distance_m):
        return self.geometric_gain / (distance_m ** 2)
    
    #https://en.wikipedia.org/wiki/Chapman_function
    def atmospheric_loss(self, elevation_rad):
        return np.exp(-self.alpha / np.sin(elevation_rad))

    def total_efficiency(self, distance_m, elevation_rad):
        return (self.geometric_loss(distance_m) *
                self.atmospheric_loss(elevation_rad))
    
    def inter_satellite_efficiency(self, distance_m):
    # Műhold-műhold optikai link egyszerűsített hatásfoka.
    # Itt nincs légköri veszteség, csak geometriai veszteséggel közelítünk.
        return self.geometric_loss(distance_m)
    
    def inter_satellite_efficiency(self, distance_m):
        return self.isl_geometric_gain / (distance_m ** 2)