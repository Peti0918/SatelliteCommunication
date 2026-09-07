import numpy as np
import os
from collections import namedtuple
from skyfield.api import load
from simulation_config import SIMULATION_CONFIG
from linkmodel import LinkModel
from passdetector import PassDetector
from keyratamodel import KeyRateModel
from app import App
from temporal_io import (
    build_dynamic_graphs_from_edge_table,
    make_temporal_edge_cache_filename,
    load_or_build_temporal_edge_table,
)

# A struktúra most egy 'station_data' szótárat tartalmaz a földi állomások adataihoz
SatelliteData = namedtuple('SatelliteData', [
    'sat', 'name', 'station_data'
])

# =========================
# Szimulációs konfiguráció
# =========================
# A konkrét konfiguráció a simulation_config.py fájlban van.
# Konstelláció, műholdszám, időablak, földi állomások és modellparaméterek
# módosítani akarunk valamit, akkor a Simulationconfigot kell átírni
config = SIMULATION_CONFIG

ground_stations = config.create_ground_stations()

# Konstelláció letöltése a Celestrak-ról
print("Konstelláció adatainak betöltése...")

celestrak_url = config.celestrak_url
cache_file = config.tle_cache_file

try:
    print("Próbálkozás online letöltéssel...")
    raw_satellites = load.tle_file(celestrak_url, filename=cache_file, reload=True)
    print("Online letöltés sikeres.")
except OSError as e:
    print(f"Online letöltés sikertelen: {e}")

    if os.path.exists(cache_file):
        print(f"Helyi cache használata: {cache_file}")
        raw_satellites = load.tle_file(cache_file)
    else:
        raise RuntimeError(
            f"Nincs elérhető online TLE és a helyi cache sem található: {cache_file}"
        )

my_constellation = raw_satellites[:config.satellite_count]
print(f"Sikeresen betöltve {len(my_constellation)} db műhold.")

# Időskála előkészítése
threshold_deg = config.elevation_threshold_deg
ts = load.timescale()
start_time = config.start_time_utc
minutes = np.arange(0, config.duration_min, config.step_min)
times = ts.utc(
    start_time.year,
    start_time.month,
    start_time.day,
    start_time.hour,
    start_time.minute + minutes
)

# Modellek inicializálása
link_model = LinkModel(**config.link_model_params)
key_model = KeyRateModel(**config.key_model_params)
detector = PassDetector(elevation_threshold_deg=threshold_deg)
dt = 60  # másodperc

satellites = []

# Műholdak - földi állomások pályaadatainak és linkértékeinek számolása
print("Pályaadatok és kapcsolatok számolása:")
for sat in my_constellation:
    station_results = {}

    for gs_name, gs in ground_stations.items():
        difference = sat - gs
        topocentric = difference.at(times)
        elevation, azimuth, distance = topocentric.altaz()

        elevation_deg = elevation.degrees
        distance_m = distance.m
        azimuth_deg = azimuth.degrees

        passes = detector.detect_passes(elevation_deg)

        elevation_rad = np.deg2rad(np.clip(elevation_deg, 1e-6, None))
        eta = link_model.total_efficiency(distance_m, elevation_rad)
        metrics = key_model.metrics(eta)
        raw_rate = metrics["raw_rate"]
        skr = metrics["skr"]
        eskr = metrics["eskr"]
        qber_dynamic = metrics["qber"]
        mu_opt = metrics["mu"]
        pair_rate_hz = metrics["pair_rate_hz"]
        accidental_rate = metrics["accidental_rate"]
        true_coincidence_rate = metrics["true_coincidence_rate"]

        # Egyszerű közeledik/távolodik információ
        distance_delta_m = np.diff(distance_m, prepend=distance_m[0])
        moving_towards = distance_delta_m < 0

        station_results[gs_name] = {
            "elevation_deg": elevation_deg,
            "azimuth_deg": azimuth_deg,
            "distance_m": distance_m,
            "distance_delta_m": distance_delta_m,
            "moving_towards": moving_towards,
            "passes": passes,
            "raw_rate": raw_rate,
            "skr": skr,
            "eskr": eskr,
            "qber_dynamic": qber_dynamic,
            "mu_opt": mu_opt,
            "pair_rate_hz": pair_rate_hz,
            "accidental_rate": accidental_rate,
            "true_coincidence_rate": true_coincidence_rate,
        }

    satellites.append(SatelliteData(
        sat=sat,
        name=sat.name,
        station_data=station_results
    ))


def efficiency_to_loss_db(eta):
    # Lineáris hatásfokból dB veszteség
    eta = np.asarray(eta, dtype=float)
    eta = np.clip(eta, 1e-30, None)
    return -10.0 * np.log10(eta)


def print_pass_report(satellites, ground_stations, link_model, dt):
    print("\n=== PASS SZINTŰ BŐVÍTETT RIPORT ===")

    for sat in satellites:
        print(f"\n=== Műhold: {sat.name} ===")

        for gs_name, data in sat.station_data.items():
            passes = data["passes"]

            if len(passes) == 0:
                print(f"  Állomás: {gs_name} | Nincs látható pass ebben az időablakban.")
                continue

            print(f"  Állomás: {gs_name} | Pass-ok száma: {len(passes)}")

            for idx, (start, end) in enumerate(passes, start=1):
                # Szeletek az adott pass időablakára
                elev = data["elevation_deg"][start:end]
                dist = data["distance_m"][start:end]
                eskr = data["eskr"][start:end]
                skr = data["skr"][start:end]
                raw = data["raw_rate"][start:end]
                qber = data["qber_dynamic"][start:end]
                mu_opt = data["mu_opt"][start:end]
                pair_rate = data["pair_rate_hz"][start:end]
                accidental = data["accidental_rate"][start:end]
                true_coinc = data["true_coincidence_rate"][start:end]
                moving_towards = data["moving_towards"][start:end]

                # Ugyanabból a modellből újraszámoljuk a veszteséget dB-ben
                elev_rad = np.deg2rad(np.clip(elev, 1e-6, None))
                eta = link_model.total_efficiency(dist, elev_rad)
                loss_db = efficiency_to_loss_db(eta)

                # Alap statisztikák
                duration_s = (end - start) * dt
                duration_min = duration_s / 60.0
                key_generated_bits = np.sum(eskr * dt)

                avg_eskr = np.mean(eskr)
                max_eskr = np.max(eskr)

                avg_qber = np.mean(qber)
                max_qber = np.max(qber)

                avg_mu_opt = np.mean(mu_opt)
                avg_pair_rate = np.mean(pair_rate)

                avg_loss_db = np.mean(loss_db)
                min_loss_db = np.min(loss_db)
                max_loss_db = np.max(loss_db)

                max_elev = np.max(elev)
                avg_elev = np.mean(elev)

                min_dist_km = np.min(dist) / 1000.0
                avg_dist_km = np.mean(dist) / 1000.0

                accidental_fraction = accidental / np.maximum(true_coinc + accidental, 1e-30)
                avg_accidental_fraction = np.mean(accidental_fraction)
                max_accidental_fraction = np.max(accidental_fraction)

                toward_fraction = np.mean(moving_towards) * 100.0

                print(
                    f"    Pass {idx}: "
                    f"időtartam = {duration_min:.1f} min | "
                    f"generált kulcs = {key_generated_bits:.2e} bit"
                )

                print(
                    f"      eleváció: avg = {avg_elev:.2f}°, max = {max_elev:.2f}° | "
                    f"távolság: avg = {avg_dist_km:.1f} km, min = {min_dist_km:.1f} km"
                )

                print(
                    f"      veszteség: avg = {avg_loss_db:.2f} dB, "
                    f"min = {min_loss_db:.2f} dB, max = {max_loss_db:.2f} dB"
                )

                print(
                    f"      ráta: avg ESKR = {avg_eskr:.2e} bit/s, "
                    f"max ESKR = {max_eskr:.2e} bit/s | "
                    f"avg SKR = {np.mean(skr):.2e} bit/s | "
                    f"avg RAW = {np.mean(raw):.2e} 1/s"
                )

                print(
                    f"      QBER: avg = {avg_qber:.4f}, max = {max_qber:.4f} | "
                    f"μopt avg = {avg_mu_opt:.5f} | "
                    f"pair rate avg = {avg_pair_rate:.2e} 1/s"
                )

                print(
                    f"      accidentals: avg arány = {avg_accidental_fraction:.4f}, "
                    f"max arány = {max_accidental_fraction:.4f} | "
                    f"közeledés-időarány = {toward_fraction:.1f}%"
                )


# Riport kiírása a konzolra
print_pass_report(satellites, ground_stations, link_model, dt)

# időindexelt él-tábla betöltése cache-ből, vagy generálása, ha még nincs ilyen konfigurációhoz
satellite_fingerprint = [
    {
        "name": sat.name,
        "satnum": int(sat.model.satnum),
        "epoch": sat.epoch.utc_iso(),
    }
    for sat in my_constellation
]

edge_cache_config = config.base_edge_cache_config(satellite_fingerprint)

edge_filename = make_temporal_edge_cache_filename(edge_cache_config)

edge_df = load_or_build_temporal_edge_table(
    edge_filename=edge_filename,
    config=edge_cache_config,
    force_rebuild=config.force_rebuild_edge_table,
    build_kwargs={
        "satellites": satellites,
        "ground_stations": ground_stations,
        "times": times,
        "threshold": threshold_deg,
        "key_model": key_model,
        "link_model": link_model,
        "include_inter_sat_links": config.include_inter_sat_links,
        "earth_radius_m": config.earth_radius_m,
        "clearance_m": config.clearance_m,
        "max_isl_distance_m": config.max_isl_distance_m,
    },
)

print("\n=== TEMPORAL EDGE TABLE ELLENŐRZÉS ===")
print(f"Sorok száma: {len(edge_df)}")
print(f"Oszlopok: {list(edge_df.columns)}")

if "key_rate" in edge_df.columns:
    print("OK: key_rate oszlop létezik.")
    print("Megjegyzés: key_rate = ESKR [bit/s]")

    active_edges = edge_df[edge_df["link_exists"] == True]
    active_with_key = active_edges[active_edges["key_rate"] > 0]

    print(f"Aktív élek száma: {len(active_edges)}")
    print(f"Aktív, pozitív ESKR-rel rendelkező élek száma: {len(active_with_key)}")

    if len(active_with_key) > 0:
        print("\nPélda aktív ESKR-es élek:")
        print(
            active_with_key[
                ["timestamp", "link_type", "elevation_deg", "distance_m", "key_rate"]
            ].head(10)
        )
    else:
        print("Figyelem: nincs pozitív ESKR-rel rendelkező aktív él.")
else:
    raise RuntimeError("Hiba: a temporal_edges táblában nincs key_rate oszlop.")

sat_sat = edge_df[  # átmeneti
    (edge_df["link_type"] == "sat_sat") &
    (edge_df["link_exists"] == True)
]

sat_sat_positive = sat_sat[sat_sat["key_rate"] > 0]

print("\n=== SAT-SAT ESKR DIAGNOSZTIKA ===")
print(f"Aktív sat-sat élek száma: {len(sat_sat)}")
print(f"Pozitív ESKR-es sat-sat élek száma: {len(sat_sat_positive)}")

if len(sat_sat) > 0:
    print("Sat-sat key_rate statisztika:")
    print(sat_sat["key_rate"].describe())

if len(sat_sat_positive) > 0:
    print("Példa pozitív sat-sat ESKR élek:")
    print(
        sat_sat_positive[
            ["timestamp", "distance_m", "key_rate"]
        ].sort_values("key_rate", ascending=False).head(10)
    )
else:
    print("Nincs pozitív ESKR-es sat-sat él.")  # átmeneti


print("Hálózati gráfok visszaépítése az él-táblából...")
dynamic_graphs = build_dynamic_graphs_from_edge_table(
    edge_df,
    num_timesteps=len(times),
    only_active=True,
)

# App indítása a visszaépített gráfokkal
app = App(
    satellites=satellites,
    times=times,
    ground_stations=ground_stations,
    dynamic_graphs=dynamic_graphs,
    threshold=threshold_deg,
    running=True,
    key_model=key_model,
    link_model=link_model,
)

app.run()