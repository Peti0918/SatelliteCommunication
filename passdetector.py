class PassDetector:
    def __init__(self, elevation_threshold_deg: float = 20.0):
        self.threshold = elevation_threshold_deg

    def detect_passes(self, elevation_array):
        #Megkeresi azokat az index-tartományokat, ahol a műhold a horizont felett van.
        #Visszatér: lista pass intervallumokról [(start_index, end_index), ..]

        visible = elevation_array > self.threshold
        passes = []
        in_pass = False
        start_idx = 0

        for i in range(len(visible)):
            if visible[i] and not in_pass:
                start_idx = i
                in_pass = True
            elif not visible[i] and in_pass:
                end_idx = i
                passes.append((start_idx, end_idx))
                in_pass = False
        
        # Ha a szimuláció végén épp látható maradna a műhold
        if in_pass:
            passes.append((start_idx, len(visible)))
            
        return passes