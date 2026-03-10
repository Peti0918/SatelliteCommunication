class OrbitPropagator:
    def __init__(self, satellite: Satellite,
                 ground_station: GroundStation):
        ...

    def compute_visibility(self, times):
        """
        Visszatér:
        - elevation array
        - distance array (m)
        """