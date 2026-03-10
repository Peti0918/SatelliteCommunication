class Simulation:
    def __init__(self, satellite, ground_station,
                 propagator, pass_detector,
                 link_model, key_model, analyzer):
        ...

    def run(self, times):
        """
        Teljes pipeline:
        1. orbit
        2. visibility
        3. pass detection
        4. efficiency
        5. key rate
        6. integration
        """