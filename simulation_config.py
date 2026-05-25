from dataclasses import dataclass, field
from datetime import datetime, UTC

from skyfield.api import wgs84


@dataclass(frozen=True)
class GroundStationConfig:
    """Egy földi állomás konfigurációs adatai."""

    name: str
    latitude_degrees: float
    longitude_degrees: float
    elevation_m: float = 0.0

    def to_skyfield(self):
        return wgs84.latlon(
            latitude_degrees=self.latitude_degrees,
            longitude_degrees=self.longitude_degrees,
            elevation_m=self.elevation_m,
        )


@dataclass(frozen=True)
class SimulationConfig:
    """
    A teljes szimuláció konfigurációja.
    Konstellációváltáskor vagy műholdszám módosításkor a fájl alján lévő
    SIMULATION_CONFIG objektum mezőit kell átírni.
    """

    constellation_name: str
    celestrak_url: str
    satellite_count: int

    start_time_utc: datetime
    duration_min: int
    step_min: int
    elevation_threshold_deg: float

    include_inter_sat_links: bool
    earth_radius_m: float
    clearance_m: float
    max_isl_distance_m: float | None

    force_rebuild_edge_table: bool = False

    link_model_params: dict = field(default_factory=dict)
    key_model_params: dict = field(default_factory=dict)
    ground_station_configs: tuple[GroundStationConfig, ...] = field(default_factory=tuple)

    @property
    def tle_cache_file(self) -> str:
        return f"sat_catalog_{self.constellation_name}.tle"

    def create_ground_stations(self) -> dict:
        """Skyfield-kompatibilis földiállomás-szótárat készít."""
        return {
            station.name: station.to_skyfield()
            for station in self.ground_station_configs
        }

    def base_edge_cache_config(self, satellite_fingerprint: list[dict]) -> dict:
        """
        Az időindexelt él-tábla cache-ének konfigurációs adatai

        Csak olyan paraméter kerül ide, amely megváltoztatja az edge table
        tényleges tartalmát. Ha ezek közül bármi változik, új cache-fájl készül.
        """
        return {
            "constellation_name": self.constellation_name,
            "celestrak_url": self.celestrak_url,
            "satellite_count": self.satellite_count,
            "satellites": satellite_fingerprint,
            "ground_stations": [station.name for station in self.ground_station_configs],
            "start_time_utc": self.start_time_utc.isoformat(),
            "duration_min": self.duration_min,
            "step_min": self.step_min,
            "threshold_deg": self.elevation_threshold_deg,
            "include_inter_sat_links": self.include_inter_sat_links,
            "earth_radius_m": self.earth_radius_m,
            "clearance_m": self.clearance_m,
            "max_isl_distance_m": self.max_isl_distance_m,
            "link_model": self.link_model_params,
            "key_model": self.key_model_params,
        }


# =========================
# Szimulációs konfiguráció
# =========================
# Ha konstellációt váltunk, itt elég ezeket a mezőket módosítani:
#   constellation_name
#   celestrak_url
#   satellite_count
#

SIMULATION_CONFIG = SimulationConfig(
    constellation_name="iridium",
    celestrak_url="https://celestrak.org/NORAD/elements/supplemental/sup-gp.php?FILE=iridium&FORMAT=tle",
    satellite_count=50,
    force_rebuild_edge_table=False,

    # Cache-eléshez fix kezdőidő kell.
    # Ha datetime.now(UTC)-t használnánk, minden futtatás más időablak lenne.
    start_time_utc=datetime(2026, 5, 20, 12, 0, tzinfo=UTC),
    duration_min=24 * 60,
    step_min=1,
    elevation_threshold_deg=20.0,

    include_inter_sat_links=True,
    earth_radius_m=6371e3,
    clearance_m=50000,
    max_isl_distance_m=4000e3,

    link_model_params={
        "atmospheric_alpha": 0.15,
        "geometric_gain": 1e8,
        "isl_geometric_gain": 1e8,
    },

    key_model_params={
        "detector_efficiency": 0.5,
        "basis_sift_factor": 0.5,
        "error_correction_efficiency": 1.16,
        "internal_fraction": 0.1,
        "coincidence_window_s": 1e-9,
        "background_rate_hz": 450.0,
        "detector_error_rate": 0.015,
        "local_detection_efficiency": 0.25,
        "optimize_mu": True,
        "mu_min": 1e-4,
        "mu_max": 0.25,
        "mu_points": 200,
    },

    ground_station_configs=(
        GroundStationConfig("Budapest", 47.4979, 19.0402, 150),
        GroundStationConfig("Vienna", 48.2082, 16.3738, 200),
        GroundStationConfig("Beijing", 39.916668, 116.383331, 200),
        GroundStationConfig("New York", 40.730610, -73.935242, 200),
        GroundStationConfig("Los Angeles", 34.0522342, -118.2436849, 230),
        GroundStationConfig("N'Djamena", 12.137752, 15.054325, 220),
    ),
)