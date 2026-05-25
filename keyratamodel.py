import numpy as np


class KeyRateModel:
    def __init__(
        self,
        detector_efficiency=0.5,
        basis_sift_factor=0.5, 
        error_correction_efficiency=1.16,
        internal_fraction=0.1,

        coincidence_window_s=1e-9,
        background_rate_hz=450.0,
        detector_error_rate=0.015,

        # Lokális oldal fix hatásfoka (Alice ág egyszerűsített modellje)
        local_detection_efficiency=0.25,

        # Optimalizáció
        optimize_mu=True,
        mu_min=1e-4,
        mu_max=0.25,
        mu_points=200,
    ):
        self.detector_eff = detector_efficiency
        self.basis_sift_factor = basis_sift_factor
        self.f_ec = error_correction_efficiency
        self.internal_fraction = internal_fraction

        self.coincidence_window_s = coincidence_window_s
        self.background_rate_hz = background_rate_hz
        self.detector_error_rate = detector_error_rate
        self.local_detection_efficiency = local_detection_efficiency

        self.optimize_mu = optimize_mu
        self.mu_min = mu_min
        self.mu_max = mu_max
        self.mu_points = mu_points

    @staticmethod
    def binary_entropy(x):
        x = np.clip(x, 1e-12, 1 - 1e-12)
        return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

    def secret_fraction_from_qber(self, qber):
        h2 = self.binary_entropy(qber)
        return np.maximum(0.0, 1.0 - self.f_ec * h2 - h2)

    def _single_link_metrics_for_mu(self, mu, channel_efficiency):
        #Egyszerű single-link modell.
        #mu és channel_efficiency lehet skalár vagy tömb.


        mu = np.asarray(mu, dtype=float)
        eta_b = np.asarray(channel_efficiency, dtype=float)

        tau = self.coincidence_window_s
        pair_rate = mu / tau

        eta_a = self.local_detection_efficiency

        # Bob teljes hatásfoka
        eta_b = eta_b * self.detector_eff

        # Jel eredetű singles
        s_a_sig = pair_rate * eta_a
        s_b_sig = pair_rate * eta_b

        # Háttérrel növelt singles
        s_a = s_a_sig
        s_b = s_b_sig + self.background_rate_hz

        # Valódi coincidences
        c_true = pair_rate * eta_a * eta_b

        # Accidentals
        c_acc = s_a * s_b * tau

        # Nyers coincidence ráta
        c_raw = c_true + c_acc

        # Dinamikus QBER 50% hibaarány
        qber = (self.detector_error_rate * c_true + 0.5 * c_acc) / np.maximum(c_raw, 1e-30)

        # Siftelés utáni ráta
        sifted = self.basis_sift_factor * c_raw

        # Secure key rate
        skr = sifted * self.secret_fraction_from_qber(qber)
        eskr = skr * (1.0 - self.internal_fraction)

        return {
            "raw_rate": c_raw,
            "skr": skr,
            "eskr": eskr,
            "qber": qber,
            "mu": mu,
            "pair_rate_hz": pair_rate,
            "accidental_rate": c_acc,
            "true_coincidence_rate": c_true,
        }

    def metrics(self, channel_efficiency):

        #Ha channel_efficiency tömb, akkor minden időlépésre külön kiválasztja
        #a legjobb μ értéket.


        eta = np.asarray(channel_efficiency, dtype=float)

        # Ha nem kérünk optimalizációt, akkor fix μ-val számolunk
        if not self.optimize_mu:
            fixed_mu = 0.1
            mu_array = np.full_like(eta, fixed_mu, dtype=float)
            return self._single_link_metrics_for_mu(mu_array, eta)

        mu_values = np.linspace(self.mu_min, self.mu_max, self.mu_points)

        best_metrics = None
        best_eskr = np.full_like(eta, -np.inf, dtype=float)

        for mu in mu_values:
            mu_array = np.full_like(eta, mu, dtype=float)
            m = self._single_link_metrics_for_mu(mu_array, eta)

            better = m["eskr"] > best_eskr

            if best_metrics is None:
                best_metrics = {}
                for key, value in m.items():
                    best_metrics[key] = np.array(value, copy=True)
                best_eskr = np.array(m["eskr"], copy=True)
            else:
                for key in best_metrics.keys():
                    best_metrics[key] = np.where(better, m[key], best_metrics[key])
                best_eskr = np.where(better, m["eskr"], best_eskr)

        return best_metrics
    
    def sweep_mu(self, channel_efficiency, mu_values=None):
        #Fix csatornahatásfok mellett végigsöpri a μ értékeket, és
        #visszaadja az ezekhez tartozó key rate görbéket.
        eta = float(channel_efficiency)

        if mu_values is None:
            mu_values = np.linspace(self.mu_min, self.mu_max, self.mu_points)

        mu_values = np.asarray(mu_values, dtype=float)

        raw_list = []
        skr_list = []
        eskr_list = []
        qber_list = []
        pair_rate_list = []

        for mu in mu_values:
            m = self._single_link_metrics_for_mu(mu, eta)
            raw_list.append(float(np.asarray(m["raw_rate"])))
            skr_list.append(float(np.asarray(m["skr"])))
            eskr_list.append(float(np.asarray(m["eskr"])))
            qber_list.append(float(np.asarray(m["qber"])))
            pair_rate_list.append(float(np.asarray(m["pair_rate_hz"])))

        return {
            "mu": mu_values,
            "pair_rate_hz": np.asarray(pair_rate_list),
            "raw_rate": np.asarray(raw_list),
            "skr": np.asarray(skr_list),
            "eskr": np.asarray(eskr_list),
            "qber": np.asarray(qber_list),
        }

    def sweep_mu_symmetric_dual_downlink(self, single_link_efficiency, mu_values=None):
        
        #Egyszerűsített szimmetrikus dual downlink modell:
        #két azonos csatorna esetén az összhatásfokot eta^2-ként közelítjük.
        eta_single = float(single_link_efficiency)
        eta_dual = eta_single * eta_single
        return self.sweep_mu(eta_dual, mu_values=mu_values)