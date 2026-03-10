class PassDetector:
    def __init__(self, elevation_threshold_deg: float = 20.0):
        self.threshold = elevation_threshold_deg

    def detect_passes(self, times, elevation_array):
        """
        Visszatér: lista pass intervallumokról
        [(start_index, end_index), ...]
        """