import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.animation import FuncAnimation
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from skyfield.api import wgs84


class App:

    def __init__(self, sat, times, elevation_deg,
                 ground_lat, ground_lon, threshold):

        self.sat = sat
        self.times = times
        self.elevation_deg = elevation_deg
        self.ground_lat = ground_lat
        self.ground_lon = ground_lon
        self.threshold = threshold

        self.fig = plt.figure(figsize=(10, 6) )
        self.views = {}

        self._create_menu_view()
        self._create_elevation_view()
        self._create_map_view()

        self.switch_view("menu")

    # ==================================================
    # VIEW SWITCHING
    # ==================================================

    def switch_view(self, name):

        for v in self.views.values():
            v["axes"].set_visible(False)
            for w in v["widgets"]:
                w.ax.set_visible(False)

        view = self.views[name]
        view["axes"].set_visible(True)
        for w in view["widgets"]:
            w.ax.set_visible(True)

        self.fig.canvas.draw_idle()

    # ==================================================
    # MENU
    # ==================================================

    def _create_menu_view(self):

        ax = self.fig.add_subplot(111)
        ax.axis("off")
        ax.set_title("Satellite Communication Simulator", fontsize=16)

        btn1_ax = self.fig.add_axes([0.35, 0.55, 0.3, 0.1])
        btn2_ax = self.fig.add_axes([0.35, 0.40, 0.3, 0.1])

        btn1 = Button(btn1_ax, "Elevation vs Time")
        btn2 = Button(btn2_ax, "2D Map View")

        btn1.on_clicked(lambda e: self.switch_view("elevation"))
        btn2.on_clicked(lambda e: self.switch_view("map"))

        self.views["menu"] = {
            "axes": ax,
            "widgets": [btn1, btn2]
        }


    def _create_elevation_view(self):

        ax = self.fig.add_subplot(111)
        ax.plot(self.elevation_deg)
        ax.axhline(self.threshold, linestyle='--')
        ax.set_title("Elevation vs Time")
        ax.set_xlabel("Time step")
        ax.set_ylabel("Elevation (deg)")

        back_ax = self.fig.add_axes([0.01, 0.01, 0.1, 0.05])
        back_btn = Button(back_ax, "← Back")
        back_btn.on_clicked(lambda e: self.switch_view("menu"))

        self.views["elevation"] = {
            "axes": ax,
            "widgets": [back_btn]
        }

    def _create_map_view(self):

        ax = self.fig.add_subplot(111, projection=ccrs.PlateCarree())

        ax.set_global()
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        ax.gridlines(draw_labels=True)
        ax.set_title("2D Satellite Map")

        # --- előszámolás ---
        sub_lats = []
        sub_lons = []

        for t in self.times:
            sub = wgs84.subpoint(self.sat.at(t))
            sub_lats.append(sub.latitude.degrees)
            sub_lons.append(sub.longitude.degrees)

        sub_lats = np.array(sub_lats)
        sub_lons = np.array(sub_lons)

        sat_point, = ax.plot([], [], 'ro',
                             transform=ccrs.PlateCarree(),
                             label="Satellite")

        ax.plot(self.ground_lon, self.ground_lat, 'bo',
                transform=ccrs.PlateCarree(),
                label="Ground Station")

        link_line, = ax.plot([], [], 'g-',
                             transform=ccrs.PlateCarree(),
                             linewidth=1.5)

        info_text = ax.text(
            -170, 80, "",
            transform=ccrs.PlateCarree(),
            fontsize=10
        )

        ax.legend()

        def update(frame):

            lat = sub_lats[frame]
            lon = sub_lons[frame]
            elev = self.elevation_deg[frame]

            sat_point.set_data([lon], [lat])

            if elev > self.threshold:
                link_line.set_data(
                    [self.ground_lon, lon],
                    [self.ground_lat, lat]
                )
                status = "LINK ACTIVE"
            else:
                link_line.set_data([], [])
                status = "NO LINK"

            info_text.set_text(
                f"Step: {frame}\nElev: {elev:.2f}°\n{status}"
            )

            return sat_point, link_line, info_text

        self.anim = FuncAnimation(
            self.fig,
            update,
            frames=len(self.times),
            interval=50,
            blit=False
        )

        back_ax = self.fig.add_axes([0.01, 0.01, 0.1, 0.05])
        back_btn = Button(back_ax, "← Back")
        back_btn.on_clicked(lambda e: self.switch_view("menu"))

        self.views["map"] = {
            "axes": ax,
            "widgets": [back_btn]
        }

    # ==================================================

    def run(self):
        plt.show()