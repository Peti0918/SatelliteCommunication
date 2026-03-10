import numpy as np
from skyfield.api import load, EarthSatellite, wgs84
from datetime import datetime, timedelta
from visualizer import Visualizer2D
from linkmodel import LinkModel
from app import App
import matplotlib.pyplot as plt

# TLE – ISS példa
#sorszám űrállomás jelzet időbélyeg keringésiSebesség Első másodikDerivált 
tle_line1 = "1 25544U 98067A   24067.51093750  .00016717  00000+0  10270-3 0  9007"
tle_line2 = "2 25544  51.6436  21.2025 0004417  64.8223  61.3141 15.50000000  9993"

sat = EarthSatellite(tle_line1, tle_line2, "ISS")

# Földi állomás – Budapest

ground_station = wgs84.latlon(
    latitude_degrees=47.4979,
    longitude_degrees=19.0402,
    elevation_m=150 #tengerszint felett
)

# Időskála 24 óra, 1 perc lépés

ts = load.timescale()
start_time = datetime.utcnow()
minutes = np.arange(0, 24*60, 1) #24 órát szimulálunk
times = ts.utc(
    start_time.year,
    start_time.month,
    start_time.day,
    start_time.hour,
    start_time.minute + minutes
)

# Geometria számítás

difference = sat - ground_station #vektor
topocentric = difference.at(times)

elevation, azimuth, distance = topocentric.altaz()

elevation_deg = elevation.degrees
distance_m = distance.m

# pass detektálás (20° küszöb)

threshold = 20.0
visible = elevation_deg > threshold

passes = []
in_pass = False

for i in range(len(visible)):
    if visible[i] and not in_pass:
        start_idx = i
        in_pass = True
    elif not visible[i] and in_pass:
        end_idx = i
        passes.append((start_idx, end_idx))
        in_pass = False

# Egyszerű link modell

link_model = LinkModel(atmospheric_alpha=0.15)
elevation_rad = np.deg2rad(elevation_deg)
elevation_rad = np.clip(elevation_rad, 1e-6, None) # Numerikus stabilitás

eta = link_model.total_efficiency(distance_m, elevation_deg)

pulse_rate = 1e8
detector_eff = 0.5

key_rate = pulse_rate * eta * detector_eff

# 7. Integrálás passonként

dt = 60  # 60 másodperc

print("Detected passes:", len(passes))
print("-" * 40)

for idx, (start, end) in enumerate(passes):
    key_generated = np.sum(key_rate[start:end] * dt)
    duration = (end - start) * dt #mennyi ideig látható
    max_elev = np.max(elevation_deg[start:end])

    print(f"Pass {idx+1}")
    print(f"  Duration: {duration/60:.1f} min")
    print(f"  Max elevation: {max_elev:.2f} deg")
    print(f"  Generated key: {key_generated:.2e} bits")
    print("-" * 40)


app = App(
    sat=sat,
    times=times,
    elevation_deg=elevation_deg,
    ground_lat=47.4979,
    ground_lon=19.0402,
    threshold=20.0
)

app.run()