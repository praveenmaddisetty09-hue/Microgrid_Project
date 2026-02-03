import pulp
import pandas as pd
import numpy as np

def run_optimization(load_profile, solar_profile, wind_profile, price_profile, battery_capacity, 
                     carbon_intensity=0.82, battery_efficiency=0.95):
    """
    Calculates the optimal microgrid schedule with wind power support.
    
    Parameters:
    -----------
    load_profile : list - Hourly load demand (kW)
    solar_profile : list - Hourly solar generation (kW)
    wind_profile : list - Hourly wind generation (kW)
    price_profile : list - Hourly electricity prices (₹/unit)
    battery_capacity : float - Battery capacity (kWh)
    carbon_intensity : float - CO2 emission factor (kg CO2/kWh), default 0.82
    battery_efficiency : float - Round-trip efficiency, default 0.95
    
    Returns:
    --------
    DataFrame with optimization results or None if failed
    """
    # 1. Setup the Problem
    model = pulp.LpProblem("Microgrid_Cost_Optimization", pulp.LpMinimize)
    hours = range(24)
    
    # Minimum battery SOC (10% reserve)
    min_soc = battery_capacity * 0.1

    # 2. Define Variables (The controls)
    grid_power = pulp.LpVariable.dicts("Grid", hours, lowBound=0)
    battery_charge = pulp.LpVariable.dicts("Charge", hours, lowBound=0)
    battery_discharge = pulp.LpVariable.dicts("Discharge", hours, lowBound=0)
    # SOC = State of Charge (Energy inside battery)
    soc = pulp.LpVariable.dicts("SOC", hours, lowBound=min_soc, upBound=battery_capacity)

    # 3. Objective: Minimize Cost (Grid Power * Price)
    model += pulp.lpSum([grid_power[t] * price_profile[t] for t in hours])

    # 4. Constraints (The Rules)
    for t in hours:
        # A. Power Balance: Supply == Demand
        # Solar + Wind + Grid + Discharging = Load + Charging
        model += (solar_profile[t] + wind_profile[t] + grid_power[t] + battery_discharge[t] 
                  == load_profile[t] + battery_charge[t])

        # B. Battery Physics with Efficiency
        if t == 0:
            # Assume battery starts 50% full
            model += soc[t] == (battery_capacity * 0.5) + (battery_charge[t] * battery_efficiency) - battery_discharge[t]
        else:
            # Current Energy = Previous Energy + Charge (with efficiency) - Discharge
            model += soc[t] == soc[t-1] + (battery_charge[t] * battery_efficiency) - battery_discharge[t]

    # 5. Solve the Math
    model.solve()

    # 6. Format Data for the Website
    if pulp.LpStatus[model.status] == 'Optimal':
        results = []
        total_cost = 0
        total_emissions = 0
        total_renewable = 0
        total_grid = 0
        
        for t in hours:
            grid_val = grid_power[t].varValue
            soc_val = soc[t].varValue
            solar_val = solar_profile[t]
            wind_val = wind_profile[t]
            load_val = load_profile[t]
            price_val = price_profile[t]
            
            # Calculate metrics
            hourly_cost = grid_val * price_val
            hourly_emissions = grid_val * carbon_intensity
            hourly_renewable = solar_val + wind_val
            renewable_pct = (hourly_renewable / load_val * 100) if load_val > 0 else 0
            
            total_cost += hourly_cost
            total_emissions += hourly_emissions
            total_renewable += hourly_renewable
            total_grid += grid_val
            
            results.append({
                "Hour": t,
                "Solar (kW)": solar_val,
                "Wind (kW)": wind_val,
                "Load (kW)": load_val,
                "Grid Usage (kW)": grid_val,
                "Battery SOC (kWh)": round(soc_val, 2),
                "Price (INR)": price_val,
                "Hourly Cost (₹)": round(hourly_cost, 2),
                "CO2 Emissions (kg)": round(hourly_emissions, 2),
                "Renewable %": round(renewable_pct, 1)
            })
        
        # Add summary row
        avg_renewable = (total_renewable / sum(load_profile) * 100) if sum(load_profile) > 0 else 0
        
        df = pd.DataFrame(results)
        
        # Store summary metrics as attributes
        df.attrs = {
            'total_cost': round(total_cost, 2),
            'total_emissions': round(total_emissions, 2),
            'total_grid_usage': round(total_grid, 2),
            'renewable_percentage': round(avg_renewable, 1),
            'battery_cycles': round((battery_capacity * 0.5) / battery_capacity, 3)
        }
        
        return df
    else:
        return None


def calculate_baseline_emissions(load_profile, grid_profile, carbon_intensity=0.82):
    """
    Calculate baseline emissions without optimization or renewables.
    """
    return sum(g * carbon_intensity for g in grid_profile)


def generate_scenario_comparison(scenarios):
    """
    Compare multiple optimization scenarios.
    
    Parameters:
    -----------
    scenarios : list of dict - Each dict contains scenario parameters and results
    
    Returns:
    --------
    DataFrame with comparison metrics
    """
    comparison = []
    for i, scenario in enumerate(scenarios):
        comparison.append({
            "Scenario": f"Scenario {i+1}",
            "Total Cost (₹)": scenario.get('total_cost', 0),
            "CO2 Emissions (kg)": scenario.get('total_emissions', 0),
            "Grid Usage (kWh)": scenario.get('total_grid', 0),
            "Renewable %": scenario.get('renewable_percentage', 0),
            "Battery Capacity": scenario.get('battery_size', 0)
        })
    return pd.DataFrame(comparison)

