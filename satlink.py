import numpy as np


def inter_satellite_position_m(sat, time):
    #visszaad egy műhold pozícióvektort méterben, minden egyes skyfield időpillanathoz
    return np.array(sat.sat.at(time).position.m, dtype=float)




def inter_satellite_distance_m(sat1, sat2, time):
    
    r1 = inter_satellite_position_m(sat1, time)
    r2 = inter_satellite_position_m(sat2, time)
    #két műhold euklideszi távolsága
    return float(np.linalg.norm(r2 - r1))



def has_inter_satellite_los(sat1, sat2, time, earth_radius_m=6371e3, clearance_m=0.0):


    r1 = inter_satellite_position_m(sat1, time)
    r2 = inter_satellite_position_m(sat2, time)
    d = r2 - r1

    R = earth_radius_m + clearance_m

    # |r1 + u*d|^2 = R^2 for u in [0, 1]
    a = float(np.dot(d, d))
    b = float(2.0 * np.dot(r1, d))
    c = float(np.dot(r1, r1) - R * R)

    discriminant = b * b - 4.0 * a * c

    # egyenes nem érinti a földet nincs LOS
    if discriminant < 0:
        return True

    sqrt_disc = np.sqrt(discriminant)
    #u1 és u2 a két metszéspont
    u1 = (-b - sqrt_disc) / (2.0 * a)
    u2 = (-b + sqrt_disc) / (2.0 * a)

    #igaz ha a föld a két műhold között van
    intersects_segment = (0.0 <= u1 <= 1.0) or (0.0 <= u2 <= 1.0)
    return not intersects_segment
