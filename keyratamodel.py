class KeyRateModel:
    def __init__(self, pulse_rate_hz=1e8, detector_efficiency=0.5):
        self.pulse_rate = pulse_rate_hz
        self.detector_eff = detector_efficiency

    def key_rate(self, channel_efficiency):
        return (self.pulse_rate *
                channel_efficiency *
                self.detector_eff)