import numpy as np
from skyfield.api import wgs84
import cartopy.crs as ccrs
import cartopy.feature as cfeature

class Visualizer2D:
    def __init__(self, satellites, times, ground_stations, threshold=20.0):
        self.times = times
        self.threshold = threshold
        self.ground_stations = ground_stations

        self.sub_lats_list = []
        self.sub_lons_list = []

        # Kiszámoljuk a koordinátákat egyszer az elején
        self._compute_subpoints(satellites)

    def _compute_subpoints(self, satellites):
        for sd in satellites:
            geocentric = sd.sat.at(self.times)
            sub = wgs84.subpoint_of(geocentric)
            self.sub_lats_list.append(sub.latitude.degrees)
            self.sub_lons_list.append(sub.longitude.degrees)

    def setup_map_axes(self, ax):
        ax.set_global()
        ax.coastlines(resolution="110m")
        ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5)
        ax.gridlines(draw_labels=True)

        # Földi állomások kirajzolása egy ciklussal
        for gs_name, gs_obj in self.ground_stations.items():
            lat = gs_obj.latitude.degrees
            lon = gs_obj.longitude.degrees
            ax.plot(lon, lat, 'bo', transform=ccrs.PlateCarree(), label=f"GS: {gs_name}")
            # Állomás nevének kiírása a pont mellé
            ax.text(lon + 2, lat + 2, gs_name, transform=ccrs.PlateCarree(), fontsize=8, color='blue')
        
        # A legend-et egy picit átrendezzük, hogy ne takarjon be mindent
        #ax.legend(loc='upper right', fontsize='small')