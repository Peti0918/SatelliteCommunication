import numpy as np

class LinkModel:
    def __init__(self, wavelength_nm=800, atmospheric_alpha=0.1):
        self.wavelength = wavelength_nm * 1e-9
        self.alpha = atmospheric_alpha

    def geometric_loss(self, distance_m):
        return 1.0 / (distance_m ** 2)

    def atmospheric_loss(self, elevation_rad):
        return np.exp(-self.alpha / np.sin(elevation_rad))

    def total_efficiency(self, distance_m, elevation_rad):
        return (self.geometric_loss(distance_m) *
                self.atmospheric_loss(elevation_rad))