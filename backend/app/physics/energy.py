"""
Energy and fuel consumption calculations.

Phase 3 scope: convert mechanical engine power into fuel energy and
fuel volume consumption, using a constant engine efficiency
(a full efficiency map is a later-phase improvement, see Phase 5/V2).
"""

# Gasoline lower heating value [J/L] (approx, typical value)
GASOLINE_LHV_J_PER_L = 34.2e6

# Diesel lower heating value [J/L] (approx, typical value)
DIESEL_LHV_J_PER_L = 38.6e6


def fuel_power_from_engine_power(
    engine_power_w: float, engine_efficiency: float
) -> float:
    """
    Compute fuel chemical power required to produce a given engine
    mechanical power.

    P_fuel = P_engine / eta_engine

    Only positive engine power consumes fuel (engine braking / negative
    torque is assumed to use fuel cutoff, i.e. zero fuel power).
    """
    if engine_power_w <= 0:
        return 0.0
    if engine_efficiency <= 0:
        raise ValueError("Engine efficiency must be positive.")
    return engine_power_w / engine_efficiency


def fuel_energy_to_volume(fuel_energy_j: float, fuel_lhv_j_per_l: float) -> float:
    """
    Convert cumulative fuel energy [J] into fuel volume [L].

    V_fuel = E_fuel / LHV
    """
    if fuel_lhv_j_per_l <= 0:
        raise ValueError("Fuel LHV must be positive.")
    return fuel_energy_j / fuel_lhv_j_per_l