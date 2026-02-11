"""
Optimization Module for Smart Microgrid Manager Pro.

This module implements the core microgrid optimization algorithm using linear
programming to minimize total energy cost while satisfying power balance,
battery state-of-charge, and grid import/export constraints.
"""

import pulp
import pandas as pd
from typing import Any, Optional
from datetime import datetime

from src.config.settings import (
    DEFAULT_CARBON_INTENSITY,
    DEFAULT_BATTERY_EFFICIENCY,
    DEFAULT_MIN_SOC_RESERVE,
    DEFAULT_INITIAL_SOC,
)
from src.types import (
    EnergyProfile,
    PriceSchedule,
    BatteryAction,
)
from src.utils.logging import get_logger


logger = get_logger(__name__)


class OptimizationSummary(dict):
    """
    Summary statistics from an optimization run.
    
    This is a dict subclass for backward compatibility.
    """
    
    def __init__(
        self,
        total_cost: float = 0.0,
        total_emissions: float = 0.0,
        total_grid_usage: float = 0.0,
        total_renewable: float = 0.0,
        renewable_percentage: float = 0.0,
        peak_grid_import: float = 0.0,
        battery_cycles: float = 0.0,
        max_battery_soc: float = 0.0,
        min_battery_soc: float = 0.0,
    ):
        super().__init__()
        self['total_cost'] = total_cost
        self['total_emissions'] = total_emissions
        self['total_grid_usage'] = total_grid_usage
        self['total_renewable'] = total_renewable
        self['renewable_percentage'] = renewable_percentage
        self['peak_grid_import'] = peak_grid_import
        self['battery_cycles'] = battery_cycles
        self['max_battery_soc'] = max_battery_soc
        self['min_battery_soc'] = min_battery_soc
    
    # Property accessors for compatibility
    @property
    def total_cost(self) -> float:
        return self.get('total_cost', 0.0)
    
    @property
    def total_emissions(self) -> float:
        return self.get('total_emissions', 0.0)
    
    @property
    def total_grid_usage(self) -> float:
        return self.get('total_grid_usage', 0.0)
    
    @property
    def total_renewable(self) -> float:
        return self.get('total_renewable', 0.0)
    
    @property
    def renewable_percentage(self) -> float:
        return self.get('renewable_percentage', 0.0)
    
    @property
    def peak_grid_import(self) -> float:
        return self.get('peak_grid_import', 0.0)
    
    @property
    def battery_cycles(self) -> float:
        return self.get('battery_cycles', 0.0)
    
    @property
    def max_battery_soc(self) -> float:
        return self.get('max_battery_soc', 0.0)
    
    @property
    def min_battery_soc(self) -> float:
        return self.get('min_battery_soc', 0.0)


class OptimizationResult(dict):
    """
    Complete optimization result with hourly data and summary.
    
    This is a dict subclass for backward compatibility.
    """
    
    def __init__(
        self,
        dataframe: pd.DataFrame,
        summary: OptimizationSummary,
        status: str = "Optimal",
        message: Optional[str] = None,
        solver_time_seconds: Optional[float] = None,
    ):
        super().__init__()
        self['dataframe'] = dataframe
        self['summary'] = summary
        self['status'] = status
        self['message'] = message
        self['solver_time_seconds'] = solver_time_seconds
    
    @property
    def dataframe(self) -> pd.DataFrame:
        return self.get('dataframe', pd.DataFrame())
    
    @property
    def summary(self) -> OptimizationSummary:
        return self.get('summary', OptimizationSummary())
    
    @property
    def status(self) -> str:
        return self.get('status', 'Unknown')


def _validate_inputs(
    load_profile: EnergyProfile,
    solar_profile: EnergyProfile,
    wind_profile: EnergyProfile,
    price_schedule: PriceSchedule,
    battery_capacity_kwh: float,
    carbon_intensity: float,
    battery_efficiency: float,
) -> None:
    """Validate input parameters."""
    expected_length = 24
    
    profiles = {
        "load_profile": load_profile,
        "solar_profile": solar_profile,
        "wind_profile": wind_profile,
        "price_schedule": price_schedule,
    }
    
    for name, profile in profiles.items():
        if len(profile) != expected_length:
            raise ValueError(f"{name} must have exactly 24 hourly values, got {len(profile)}")
    
    if not (0 < battery_capacity_kwh <= 1000):
        raise ValueError(f"Battery capacity must be between 0 and 1000 kWh, got {battery_capacity_kwh}")
    
    if not (0 < carbon_intensity <= 2.0):
        raise ValueError(f"Carbon intensity must be between 0 and 2.0, got {carbon_intensity}")
    
    if not (0 < battery_efficiency <= 1):
        raise ValueError(f"Battery efficiency must be between 0 and 1, got {battery_efficiency}")


def run_optimization(
    load_profile: EnergyProfile,
    solar_profile: EnergyProfile,
    wind_profile: EnergyProfile,
    price_schedule: PriceSchedule,
    battery_capacity_kwh: float,
    carbon_intensity: float = DEFAULT_CARBON_INTENSITY,
    battery_efficiency: float = DEFAULT_BATTERY_EFFICIENCY,
) -> OptimizationResult:
    """
    Solve the microgrid optimization problem using linear programming.
    
    Uses PuLP's CBC solver to minimize total energy cost while satisfying:
        - Power balance constraints
        - Battery state-of-charge limits
        - Grid import limits
    
    Args:
        load_profile: Hourly load demand in kW (24 values)
        solar_profile: Hourly solar generation in kW (24 values)
        wind_profile: Hourly wind generation in kW (24 values)
        price_schedule: Hourly electricity prices in INR/kWh (24 values)
        battery_capacity_kwh: Total battery capacity in kWh
        carbon_intensity: Grid carbon emission factor (kg CO2/kWh)
        battery_efficiency: Round-trip battery efficiency (0-1)
    
    Returns:
        OptimizationResult containing hourly dispatch schedule and summary
    
    Raises:
        ValueError: If input parameters are invalid
    """
    # Validate inputs
    _validate_inputs(
        load_profile, solar_profile, wind_profile, price_schedule,
        battery_capacity_kwh, carbon_intensity, battery_efficiency
    )
    
    logger.info(
        "Starting optimization",
        extra={
            "battery_capacity": battery_capacity_kwh,
            "carbon_intensity": carbon_intensity,
            "simulation_hours": 24,
        }
    )
    
    hours = range(24)
    min_soc_kwh = battery_capacity_kwh * DEFAULT_MIN_SOC_RESERVE
    initial_soc_kwh = battery_capacity_kwh * DEFAULT_INITIAL_SOC
    
    model = pulp.LpProblem("Microgrid_Optimization", pulp.LpMinimize)
    
    # Decision variables
    grid_import = pulp.LpVariable.dicts("grid_import", hours, lowBound=0)
    battery_charge = pulp.LpVariable.dicts("battery_charge", hours, lowBound=0)
    battery_discharge = pulp.LpVariable.dicts("battery_discharge", hours, lowBound=0)
    soc = pulp.LpVariable.dicts(
        "soc",
        hours,
        lowBound=min_soc_kwh,
        upBound=battery_capacity_kwh,
    )
    
    # Objective: minimize total cost
    objective = pulp.lpSum([
        grid_import[t] * price_schedule[t] for t in hours
    ])
    model += objective
    
    # Power balance constraints
    for t in hours:
        model += (
            solar_profile[t]
            + wind_profile[t]
            + grid_import[t]
            + battery_discharge[t]
            == load_profile[t]
            + battery_charge[t]
        )
    
    # Battery state evolution
    for t in hours:
        if t == 0:
            model += soc[t] == (
                initial_soc_kwh
                + battery_charge[t] * battery_efficiency
                - battery_discharge[t]
            )
        else:
            model += soc[t] == (
                soc[t-1]
                + battery_charge[t] * battery_efficiency
                - battery_discharge[t]
            )
    
    # Solve
    solver = pulp.PULP_CBC_CMD(msg=0)
    start_time = datetime.now()
    model.solve(solver)
    solve_time = (datetime.now() - start_time).total_seconds()
    
    solver_status = pulp.LpStatus[model.status]
    logger.info(
        "Optimization solver completed",
        extra={
            "status": solver_status,
            "solve_time_seconds": solve_time,
        }
    )
    
    # Check solution quality
    if solver_status != "Optimal":
        if solver_status == "Infeasible":
            error_msg = (
                "No feasible solution exists with current constraints. "
                "Consider reducing grid limits or adjusting battery parameters."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        elif solver_status == "Unbounded":
            error_msg = "Optimization problem is unbounded - check constraint definitions."
            logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            error_msg = f"Solver returned non-optimal status: {solver_status}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    # Extract results
    return _extract_results(
        hours=hours,
        load_profile=load_profile,
        solar_profile=solar_profile,
        wind_profile=wind_profile,
        price_schedule=price_schedule,
        carbon_intensity=carbon_intensity,
        battery_capacity_kwh=battery_capacity_kwh,
        grid_import=grid_import,
        battery_charge=battery_charge,
        battery_discharge=battery_discharge,
        soc=soc,
        solve_time=solve_time,
    )


def _extract_results(
    hours: range,
    load_profile: EnergyProfile,
    solar_profile: EnergyProfile,
    wind_profile: EnergyProfile,
    price_schedule: PriceSchedule,
    carbon_intensity: float,
    battery_capacity_kwh: float,
    grid_import: Any,
    battery_charge: Any,
    battery_discharge: Any,
    soc: Any,
    solve_time: float,
) -> OptimizationResult:
    """Extract and format optimization results."""
    
    hourly_data = []
    total_cost = 0.0
    total_emissions = 0.0
    total_renewable = 0.0
    total_grid = 0.0
    battery_soc_values = []
    peak_grid_import = 0.0
    
    for t in hours:
        grid_val = grid_import[t].varValue or 0.0
        soc_val = soc[t].varValue or 0.0
        charge_val = battery_charge[t].varValue or 0.0
        discharge_val = battery_discharge[t].varValue or 0.0
        
        hourly_cost = grid_val * price_schedule[t]
        hourly_emissions = grid_val * carbon_intensity
        hourly_renewable = solar_profile[t] + wind_profile[t]
        
        # Determine battery action
        if charge_val > discharge_val:
            action = BatteryAction.CHARGING
        elif discharge_val > charge_val:
            action = BatteryAction.DISCHARGING
        else:
            action = BatteryAction.IDLE
        
        renewable_pct = (
            (hourly_renewable / load_profile[t] * 100)
            if load_profile[t] > 0 else 0
        )
        
        total_cost += hourly_cost
        total_emissions += hourly_emissions
        total_renewable += hourly_renewable
        total_grid += grid_val
        battery_soc_values.append(soc_val)
        
        if grid_val > peak_grid_import:
            peak_grid_import = grid_val
        
        hourly_data.append({
            "Hour": t,
            "Load (kW)": load_profile[t],
            "Solar (kW)": solar_profile[t],
            "Wind (kW)": wind_profile[t],
            "Grid Usage (kW)": grid_val,
            "Battery SOC (kWh)": round(soc_val, 2),
            "Battery Action": action.value,
            "Price (INR)": price_schedule[t],
            "Hourly Cost (₹)": round(hourly_cost, 2),
            "CO2 Emissions (kg)": round(hourly_emissions, 2),
            "Renewable %": round(renewable_pct, 1),
        })
    
    # Calculate summary statistics
    total_load = sum(load_profile)
    renewable_percentage = (
        (total_renewable / total_load * 100)
        if total_load > 0 else 0
    )
    
    # Estimate battery cycles
    total_battery_energy = sum(battery_charge[t].varValue or 0 for t in hours)
    battery_cycles = total_battery_energy / (2 * battery_capacity_kwh)
    
    summary = OptimizationSummary(
        total_cost=round(total_cost, 2),
        total_emissions=round(total_emissions, 2),
        total_grid_usage=round(total_grid, 2),
        total_renewable=round(total_renewable, 2),
        renewable_percentage=round(renewable_percentage, 1),
        peak_grid_import=round(peak_grid_import, 2),
        battery_cycles=round(battery_cycles, 3),
        max_battery_soc=max(battery_soc_values),
        min_battery_soc=min(battery_soc_values),
    )
    
    result_df = pd.DataFrame(hourly_data)
    
    logger.info(
        "Optimization completed successfully",
        extra={
            "total_cost": summary.total_cost,
            "renewable_pct": summary.renewable_percentage,
            "peak_grid": summary.peak_grid_import,
        }
    )
    
    return OptimizationResult(
        dataframe=result_df,
        summary=summary,
        status="Optimal",
        message=None,
        solver_time_seconds=solve_time,
    )


def calculate_baseline_emissions(
    load_profile: EnergyProfile,
    grid_import_profile: list[float],
    carbon_intensity: float = DEFAULT_CARBON_INTENSITY,
) -> float:
    """
    Calculate baseline emissions without optimization.
    
    Compares actual emissions against an unoptimized scenario where
    all load is met by grid power.
    """
    return sum(
        grid_val * carbon_intensity
        for grid_val in grid_import_profile
    )


def generate_scenario_comparison(
    scenarios: list[dict],
) -> pd.DataFrame:
    """
    Compare multiple optimization scenarios.
    
    Args:
        scenarios: List of scenario dictionaries
    
    Returns:
        DataFrame with side-by-side comparison of all scenarios
    """
    comparison = []
    
    for scenario in scenarios:
        comparison.append({
            "Scenario": scenario.get("name", "Unnamed"),
            "Total Cost (₹)": scenario.get("total_cost", 0),
            "CO2 Emissions (kg)": scenario.get("total_emissions", 0),
            "Grid Usage (kWh)": scenario.get("total_grid_usage", 0),
            "Renewable %": scenario.get("renewable_percentage", 0),
            "Battery Capacity": scenario.get("battery_size", 0),
        })
    
    return pd.DataFrame(comparison)

