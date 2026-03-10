import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from skyfield.api import wgs84
import cartopy.crs as ccrs
import cartopy.feature as cfeature


class Visualizer2D:
    def __init__(self, sat, times, elevation_deg,
                 ground_lat, ground_lon,
                 threshold=20.0):

        self.sat = sat
        self.times = times
        self.elevation_deg = elevation_deg
        self.threshold = threshold

        self.gs_lat = ground_lat
        self.gs_lon = ground_lon

        self._compute_subpoints()


    def _compute_subpoints(self):
        # Gyorsított numpy alapú előszámolás
        sub_lats = []
        sub_lons = []

        for t in self.times:
            sub = wgs84.subpoint(self.sat.at(t))
            sub_lats.append(sub.latitude.degrees)
            sub_lons.append(sub.longitude.degrees)

        self.sub_lats = np.array(sub_lats)
        self.sub_lons = np.array(sub_lons)


    def animate(self, interval=40, frame_step=4):

        fig = plt.figure(figsize=(12, 5))

        gs = fig.add_gridspec(1, 2, width_ratios=[1, 4])

        info_ax = fig.add_subplot(gs[0])
        ax = fig.add_subplot(gs[1], projection=ccrs.PlateCarree())

        # ---- OPTIMALIZÁLÁSOK ----
        ax.set_autoscale_on(False)

        info_ax.axis("off")

        ax.set_global()
        ax.coastlines(resolution="110m")  # gyorsabb
        ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5)

        ax.gridlines(draw_labels=False)

        ax.set_title("Satellite Visibility (2D Map Projection)")

        sat_point, = ax.plot([], [], 'ro',
                             transform=ccrs.PlateCarree(),
                             label="Satellite")

        ax.plot(self.gs_lon, self.gs_lat,
                'bo',
                transform=ccrs.PlateCarree(),
                label="Ground Station")

        link_line, = ax.plot([], [], 'g-',
                             transform=ccrs.PlateCarree(),
                             linewidth=1.2)

        text_info = info_ax.text(
            0.05, 0.9, "",
            transform=info_ax.transAxes,
            fontsize=11,
            verticalalignment='top'
        )

        ax.legend()

        frames = range(0, len(self.times), frame_step)


        def update(frame):

            lat = self.sub_lats[frame]
            lon = self.sub_lons[frame]
            elev = self.elevation_deg[frame]

            sat_point.set_data([lon], [lat])

            if elev > self.threshold:
                link_line.set_data(
                    [self.gs_lon, lon],
                    [self.gs_lat, lat]
                )
                status = "LINK ACTIVE"
            else:
                link_line.set_data([], [])
                status = "NO LINK"

            text_info.set_text(
                f"Step: {frame}\n"
                f"Elevation: {elev:.2f} deg\n"
                f"{status}"
            )

            return sat_point, link_line, text_info

        ani = FuncAnimation(
            fig,
            update,
            frames=frames,
            interval=interval,
            blit=False   # Cartopy miatt stabilabb
        )

        plt.show()