import json
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx

from satlink import has_inter_satellite_los, inter_satellite_distance_m

def build_temporal_edge_table(
    satellites,
    ground_stations,
    times,
    threshold,
    key_model=None,
    link_model=None,
    include_inter_sat_links=False,
    earth_radius_m=6371e3,
    clearance_m=0.0,
    max_isl_distance_m=None,
):

    #egy sor egy lehetséges kapcsolat
    rows = []

    for t in range(len(times)):
        timestamp = times[t].utc_iso()
        current_time = times[t]

        # Satellite -> ground station rows
        for sd in satellites:
            for gs_name, data in sd.station_data.items():
                elev = float(data["elevation_deg"][t])
                dist = float(data["distance_m"][t])

                # A hálózati élek súlyaként az ESKR-t használjuk.
                # ESKR = Effective Secure Key Rate [bit/s]
                if "eskr" in data:
                    eskr = float(data["eskr"][t])
                else:
                    raise KeyError(
                        "Nincs ESKR adat ennél az állomásnál: "
                        f"{gs_name}, elérhető kulcsok: {list(data.keys())}"
                    )

                link_exists = elev > threshold

                rows.append(
                    {
                        "time_idx": t,
                        "timestamp": timestamp,
                        "src": sd.name,
                        "dst": gs_name,
                        "src_type": "satellite",
                        "dst_type": "ground_station",
                        "link_type": "sat_ground",
                        "link_exists": bool(link_exists),
                        "elevation_deg": elev,
                        "distance_m": dist,
                        "key_rate": eskr if link_exists else 0.0,
                    }
                )

        # Optional satellite -> satellite rows
        if include_inter_sat_links:
            for i in range(len(satellites)):
                for j in range(i + 1, len(satellites)):
                    sd1 = satellites[i]
                    sd2 = satellites[j]

                    dist = inter_satellite_distance_m(sd1, sd2, current_time)
                    los = has_inter_satellite_los(
                        sd1,
                        sd2,
                        current_time,
                        earth_radius_m=earth_radius_m,
                        clearance_m=clearance_m,
                    )

                    within_distance = (
                        True
                        if max_isl_distance_m is None
                        else dist <= max_isl_distance_m
                    )

                    link_exists = bool(los and within_distance)

                    # Sat-sat ESKR számítás.
                    # Ha a link létezik, a távolságból becsült optikai hatásfokot
                    # átadjuk a KeyRateModel-nek.
                    if link_exists and key_model is not None and link_model is not None:
                        eta_isl = link_model.inter_satellite_efficiency(dist)

                        metrics = key_model.metrics(np.asarray([eta_isl]))
                        eskr_isl = float(np.asarray(metrics["eskr"]).reshape(-1)[0])
                        
                    else:
                        eskr_isl = 0.0

                    rows.append(
                        {
                            "time_idx": t,
                            "timestamp": timestamp,
                            "src": sd1.name,
                            "dst": sd2.name,
                            "src_type": "satellite",
                            "dst_type": "satellite",
                            "link_type": "sat_sat",
                            "link_exists": link_exists,
                            "elevation_deg": None,
                            "distance_m": dist,
                            # key_rate = ESKR [bit/s]
                            "key_rate": eskr_isl if link_exists else 0.0,
                        }
                    )

    df = pd.DataFrame(rows)
    return df.set_index(["time_idx", "src", "dst"]).sort_index()



def save_temporal_edge_table(df, filename="temporal_edges.csv"):
    #élek lementése
    if filename.endswith(".parquet"):
        df.to_parquet(filename)
    else:
        df.to_csv(filename)



def load_temporal_edge_table(filename="temporal_edges.csv"):
    #élek betöltése
    if filename.endswith(".parquet"):
        df = pd.read_parquet(filename)
    else:
        df = pd.read_csv(filename)

    if not isinstance(df.index, pd.MultiIndex):
        df = df.set_index(["time_idx", "src", "dst"])

    if "link_exists" in df.columns:
        if df["link_exists"].dtype == object:
            df["link_exists"] = df["link_exists"].astype(str).str.lower().isin(["true", "1", "yes"])
        else:
            df["link_exists"] = df["link_exists"].astype(bool)

    return df.sort_index()




def _config_hash(config):
    """Stabil hash a cache-konfigurációhoz."""
    payload = json.dumps(config, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_filename_part(text):
    """Fájlnévbarát rövidítés: csak betű, szám, kötőjel és aláhúzás marad."""
    text = str(text).lower()
    safe = []
    for ch in text:
        if ch.isalnum() or ch in ["-", "_"]:
            safe.append(ch)
        else:
            safe.append("_")
    return "".join(safe).strip("_") or "cache"


def make_temporal_edge_cache_filename(config, cache_dir="temporal_cache", prefix="temporal_edges", ext=".csv"):
    """
    Paraméterfüggő cache-fájlnevet készít.

    Példa:
    temporal_cache/temporal_edges_iridium_20sat_a1b2c3d4e5f6.csv
    """
    Path(cache_dir).mkdir(parents=True, exist_ok=True)

    constellation = _safe_filename_part(config.get("constellation_name", "constellation"))
    sat_count = config.get("satellite_count", "n")
    short_hash = _config_hash(config)[:12]

    return str(Path(cache_dir) / f"{prefix}_{constellation}_{sat_count}sat_{short_hash}{ext}")


def _metadata_filename(edge_filename):
    return f"{edge_filename}.meta.json"


def _save_cache_metadata(edge_filename, config):
    metadata = {
        "config_hash": _config_hash(config),
        "config": config,
    }
    with open(_metadata_filename(edge_filename), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)


def _is_cache_valid(edge_filename, config):
    meta_file = _metadata_filename(edge_filename)

    if not Path(edge_filename).exists():
        return False
    if not Path(meta_file).exists():
        return False

    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False

    return metadata.get("config_hash") == _config_hash(config)


def load_or_build_temporal_edge_table(
    edge_filename,
    config,
    build_kwargs,
    force_rebuild=False,
):
    """
    Ha van érvényes cache, betölti az időindexelt él-táblát.
    Ha nincs, újragenerálja, elmenti, majd azt adja vissza.
    """
    if not force_rebuild and _is_cache_valid(edge_filename, config):
        print(f"Meglévő időindexelt él-tábla használata: {edge_filename}")
        return load_temporal_edge_table(edge_filename)

    if force_rebuild:
        print("FORCE_REBUILD_EDGE_TABLE=True, ezért új él-tábla generálódik.")
    else:
        print("Nincs ehhez a konfigurációhoz érvényes él-tábla cache.")

    print("Időindexelt él-tábla generálása...")
    edge_df = build_temporal_edge_table(**build_kwargs)

    print(f"Él-tábla mentése: {edge_filename}")
    save_temporal_edge_table(edge_df, edge_filename)
    _save_cache_metadata(edge_filename, config)

    return edge_df


def graph_from_edge_table(df, time_idx, only_active=True):
    #Rebuild a NetworkX graph for a given time index.
    G = nx.Graph()
    snapshot = df.xs(time_idx, level="time_idx")

    for (src, dst), row in snapshot.iterrows():
        G.add_node(src, type=row["src_type"])
        G.add_node(dst, type=row["dst_type"])

        is_active = bool(row["link_exists"])
        if (not only_active) or is_active:
            elevation = row["elevation_deg"]
            elevation = None if pd.isna(elevation) else float(elevation)

            # key_rate mező tartalma: ESKR bit/s, gráfsúlyként
            kr = float(row["key_rate"])
            G.add_edge(
                src,
                dst,
                weight=kr,
                routing_cost=float("inf") if kr <= 0 else 1.0 / kr,
                distance=float(row["distance_m"]),
                elevation_deg=elevation,
                active=is_active,
                link_type=row.get("link_type", "unknown"),
            )

    return G



def build_dynamic_graphs_from_edge_table(df, num_timesteps, only_active=True):
    #Rebuild one graph per time step from the edge table.
    return [graph_from_edge_table(df, t, only_active=only_active) for t in range(num_timesteps)]
