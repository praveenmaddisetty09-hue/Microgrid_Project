"""
Optimal Scheduling Module for Smart Microgrid Manager Pro
Advanced scheduling features including multi-objective optimization, peak shaving,
battery degradation scheduling, load shifting, day-ahead scheduling, and more.
"""

import pulp
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


@dataclass
class SchedulingParameters:
    """Parameters for optimal scheduling."""
    # Economic parameters
    base_price: float = 5.0  # ₹/kWh
    peak_price: float = 15.0  # ₹/kWh
    peak_start: int = 17  # Hour
    peak_end: int = 21  # Hour
    demand_charge: float = 0.0  # ₹/kW (peak demand charge)
    
    # Battery parameters
    battery_capacity: float = 100.0  # kWh
    battery_efficiency: float = 0.95  # Round-trip efficiency
    min_soc_reserve: float = 0.1  # 10% minimum reserve
    battery_degradation_cost: float = 0.01  # ₹/kWh per cycle
    
    # Grid parameters
    grid_safety_limit: float = 50.0  # kW
    grid_export_price: float = 3.0  # ₹/kWh (feed-in tariff)
    max_grid_import: float = 100.0  # kW
    max_grid_export: float = 50.0  # kW
    
    # Environmental parameters
    carbon_intensity: float = 0.82  # kg CO2/kWh
    carbon_price: float = 0.0  # ₹/kg CO2
    
    # Generator parameters
    generator_available: bool = False
    generator_capacity: float = 50.0  # kW
    generator_efficiency: float = 0.35  # L/kWh
    fuel_price: float = 100.0  # ₹/L
    generator_co2: float = 2.5  # kg CO2/L
    
    # Load management parameters
    flexible_loads: Dict[str, float] = None  # {name: energy_needed_kWh}
    flexible_load_windows: Dict[str, Tuple[int, int]] = None  # {name: (start_hour, end_hour)}
    shiftable_loads: Dict[str, float] = None  # {name: power_kW}
    
    # Demand response parameters
    demand_response_enabled: bool = False
    demand_response_threshold: float = 12.0  # ₹/kWh (price threshold)
    demand_response_reduction: float = 0.2  # 20% reduction possible
    
    # Optimization preferences
    objective: str = 'cost'  # 'cost', 'emissions', 'balanced', 'reliability'
    time_horizon: int = 24  # hours
    solver: str = 'CBC'


class OptimalScheduler:
    """
    Advanced Optimal Scheduler for Microgrid Management.
    """
    
    def __init__(self, params: SchedulingParameters = None):
        """Initialize the optimal scheduler."""
        self.params = params or SchedulingParameters()
        self.hours = range(self.params.time_horizon)
    
    def _generate_price_profile(self) -> List[float]:
        """Generate hourly price profile based on parameters."""
        return [
            self.params.base_price if not (self.params.peak_start <= h <= self.params.peak_end)
            else self.params.peak_price
            for h in self.hours
        ]
    
    def _battery_degradation_cost(self) -> pulp.LpExpression:
        """Calculate battery degradation cost."""
        return self.params.battery_degradation_cost * self.params.battery_capacity
    
    def _add_power_balance_constraints(self, model, load, solar, wind, grid_imp, grid_exp, 
                                       charge, discharge, flex_loads, dr):
        """Add power balance constraints."""
        for t in self.hours:
            flex_sum = sum(flex_loads[ln][t] for ln in flex_loads) if flex_loads else 0
            model += (
                solar[t] + wind[t] + grid_imp[t] + discharge[t]
                == load[t] + charge[t] + flex_sum - dr[t]
            )
    
    def _add_battery_constraints(self, model, charge, discharge, soc):
        """Add battery constraints."""
        for t in self.hours:
            if t == 0:
                model += soc[t] == (self.params.battery_capacity * 0.5) + \
                          charge[t] * self.params.battery_efficiency - discharge[t]
            else:
                model += soc[t] == soc[t-1] + charge[t] * self.params.battery_efficiency - discharge[t]
    
    def _add_grid_constraints(self, model, grid_imp, grid_exp):
        """Add grid constraints."""
        for t in self.hours:
            model += grid_imp[t] <= self.params.max_grid_import
            model += grid_exp[t] <= self.params.max_grid_export
    
    def _add_generator_constraints(self, model, gen):
        """Add generator constraints."""
        if self.params.generator_available:
            for t in self.hours:
                model += gen[t] <= self.params.generator_capacity
    
    def _add_flexible_load_constraints(self, model, flex_loads):
        """Add flexible load constraints."""
        if flex_loads and self.params.flexible_loads:
            for load_name, energy in self.params.flexible_loads.items():
                window = self.params.flexible_load_windows.get(load_name, (0, 23))
                total = pulp.lpSum([
                    flex_loads[load_name][t] for t in range(window[0], window[1] + 1)
                ])
                model += total == energy
    
    def _add_demand_response_constraints(self, model, dr, load):
        """Add demand response constraints."""
        if self.params.demand_response_enabled:
            for t in self.hours:
                model += dr[t] <= self.params.demand_response_reduction * load[t]
    
    def run_multi_objective_optimization(
        self, load_profile, solar_profile, wind_profile, price_profile=None
    ) -> Dict[str, Any]:
        """Run multi-objective optimization."""
        if price_profile is None:
            price_profile = self._generate_price_profile()
        
        model = pulp.LpProblem("Multi_Objective_Scheduling", pulp.LpMinimize)
        
        grid_import = pulp.LpVariable.dicts("Grid_Import", self.hours, lowBound=0)
        grid_export = pulp.LpVariable.dicts("Grid_Export", self.hours, lowBound=0)
        battery_charge = pulp.LpVariable.dicts("Battery_Charge", self.hours, lowBound=0)
        battery_discharge = pulp.LpVariable.dicts("Battery_Discharge", self.hours, lowBound=0)
        soc = pulp.LpVariable.dicts("SOC", self.hours,
                                    lowBound=self.params.battery_capacity * self.params.min_soc_reserve,
                                    upBound=self.params.battery_capacity)
        generator_output = pulp.LpVariable.dicts("Generator", self.hours, lowBound=0)
        
        flex_load_vars = {}
        if self.params.flexible_loads:
            for load_name in self.params.flexible_loads:
                flex_load_vars[load_name] = pulp.LpVariable.dicts(
                    f"Flex_{load_name}", self.hours, lowBound=0
                )
        
        dr_reduction = pulp.LpVariable.dicts("DR_Reduction", self.hours, lowBound=0)
        
        if self.params.objective == 'cost':
            objective = pulp.lpSum([
                grid_import[t] * price_profile[t] - grid_export[t] * self.params.grid_export_price
                for t in self.hours
            ])
            objective += self._battery_degradation_cost()
            if self.params.generator_available:
                objective += pulp.lpSum([
                    generator_output[t] * self.params.fuel_price * self.params.generator_efficiency
                    for t in self.hours
                ])
        elif self.params.objective == 'emissions':
            objective = pulp.lpSum([
                grid_import[t] * self.params.carbon_intensity * self.params.carbon_price
                for t in self.hours
            ])
        else:
            cost_obj = pulp.lpSum([
                grid_import[t] * price_profile[t] - grid_export[t] * self.params.grid_export_price
                for t in self.hours
            ])
            emissions_obj = pulp.lpSum([
                grid_import[t] * self.params.carbon_intensity * 10
                for t in self.hours
            ])
            objective = 0.6 * cost_obj + 0.4 * emissions_obj
        
        model += objective
        
        for t in self.hours:
            flex_sum = sum(flex_load_vars[ln][t] for ln in flex_load_vars) if flex_load_vars else 0
            model += (
                solar_profile[t] + wind_profile[t] + grid_import[t] + battery_discharge[t]
                == load_profile[t] + battery_charge[t] + flex_sum - dr_reduction[t]
            )
        
        for t in self.hours:
            if t == 0:
                model += soc[t] == (self.params.battery_capacity * 0.5) + \
                          battery_charge[t] * self.params.battery_efficiency - battery_discharge[t]
            else:
                model += soc[t] == soc[t-1] + battery_charge[t] * self.params.battery_efficiency - battery_discharge[t]
        
        for t in self.hours:
            model += grid_import[t] <= self.params.max_grid_import
            model += grid_export[t] <= self.params.max_grid_export
        
        if self.params.generator_available:
            for t in self.hours:
                model += generator_output[t] <= self.params.generator_capacity
        
        if self.params.flexible_loads:
            for load_name, energy in self.params.flexible_loads.items():
                window = self.params.flexible_load_windows.get(load_name, (0, 23))
                total = pulp.lpSum([
                    flex_load_vars[load_name][t] for t in range(window[0], window[1] + 1)
                ])
                model += total == energy
        
        if self.params.demand_response_enabled:
            for t in self.hours:
                model += dr_reduction[t] <= self.params.demand_response_reduction * load_profile[t]
        
        for t in self.hours:
            model += grid_import[t] <= self.params.grid_safety_limit
        
        solver = pulp.PULP_CBC_CMD(msg=0)
        model.solve(solver)
        
        if pulp.LpStatus[model.status] == 'Optimal':
            return self._extract_results(model, load_profile, solar_profile, wind_profile,
                                        price_profile, grid_import, grid_export,
                                        battery_charge, battery_discharge, soc,
                                        generator_output, flex_load_vars, dr_reduction)
        return {'status': 'failed', 'message': pulp.LpStatus[model.status]}
    
    def _extract_results(self, model, load, solar, wind, price, grid_imp, grid_exp,
                         charge, discharge, soc, generator, flex_loads, dr) -> Dict[str, Any]:
        """Extract optimization results."""
        results = []
        total_cost = 0
        total_emissions = 0
        total_renewable = 0
        total_grid = 0
        total_gen = 0
        
        for t in self.hours:
            grid_val = grid_imp[t].varValue or 0
            gen_val = generator[t].varValue if self.params.generator_available else 0
            soc_val = soc[t].varValue or 0
            dr_val = dr[t].varValue or 0
            
            hourly_cost = grid_val * price[t] - (grid_exp[t].varValue or 0) * self.params.grid_export_price
            if self.params.generator_available:
                hourly_cost += gen_val * self.params.fuel_price * self.params.generator_efficiency
            
            hourly_emissions = (grid_val + gen_val) * self.params.carbon_intensity
            hourly_renewable = solar[t] + wind[t]
            
            total_cost += hourly_cost
            total_emissions += hourly_emissions
            total_renewable += hourly_renewable
            total_grid += grid_val
            total_gen += gen_val
            
            flex_load_dict = {}
            if flex_loads:
                for ln in flex_loads:
                    flex_load_dict[ln] = flex_loads[ln][t].varValue or 0
            
            results.append({
                "Hour": t,
                "Solar (kW)": solar[t],
                "Wind (kW)": wind[t],
                "Load (kW)": load[t],
                "Grid Import (kW)": round(grid_val, 2),
                "Grid Export (kW)": round(grid_exp[t].varValue or 0, 2),
                "Battery SOC (kWh)": round(soc_val, 2),
                "Battery Charge (kW)": round(charge[t].varValue or 0, 2),
                "Battery Discharge (kW)": round(discharge[t].varValue or 0, 2),
                "Generator (kW)": round(gen_val, 2),
                "DR Reduction (kW)": round(dr_val, 2),
                "Price (₹/kWh)": price[t],
                "Hourly Cost (₹)": round(hourly_cost, 2),
                "CO2 (kg)": round(hourly_emissions, 2),
                "Renewable %": round(hourly_renewable / load[t] * 100, 1) if load[t] > 0 else 0,
                **flex_load_dict
            })
        
        df = pd.DataFrame(results)
        avg_renewable = total_renewable / sum(load) * 100 if sum(load) > 0 else 0
        
        return {
            'status': 'Optimal',
            'dataframe': df,
            'total_cost': round(total_cost, 2),
            'total_emissions': round(total_emissions, 2),
            'total_renewable': round(total_renewable, 2),
            'total_grid': round(total_grid, 2),
            'total_generator': round(total_gen, 2),
            'renewable_percentage': round(avg_renewable, 1),
            'peak_demand': max(results, key=lambda x: x['Grid Import (kW)'])['Grid Import (kW)'],
            'battery_cycles': round(total_grid / self.params.battery_capacity, 3)
        }
    
    def run_peak_shaving_optimization(self, load_profile, solar_profile, wind_profile, 
                                     price_profile=None) -> Dict[str, Any]:
        """Optimize for peak shaving."""
        if price_profile is None:
            price_profile = self._generate_price_profile()
        
        model = pulp.LpProblem("Peak_Shaving", pulp.LpMinimize)
        
        grid_import = pulp.LpVariable.dicts("Grid_Import", self.hours, lowBound=0)
        grid_export = pulp.LpVariable.dicts("Grid_Export", self.hours, lowBound=0)
        battery_charge = pulp.LpVariable.dicts("Battery_Charge", self.hours, lowBound=0)
        battery_discharge = pulp.LpVariable.dicts("Battery_Discharge", self.hours, lowBound=0)
        soc = pulp.LpVariable.dicts("SOC", self.hours,
                                    lowBound=self.params.battery_capacity * self.params.min_soc_reserve,
                                    upBound=self.params.battery_capacity)
        peak_demand = pulp.LpVariable("Peak_Demand", lowBound=0)
        
        energy_cost = pulp.lpSum([
            grid_import[t] * price_profile[t] - grid_export[t] * self.params.grid_export_price
            for t in self.hours
        ])
        demand_cost = peak_demand * self.params.demand_charge
        model += energy_cost + demand_cost
        
        for t in self.hours:
            model += (
                solar_profile[t] + wind_profile[t] + grid_import[t] + battery_discharge[t]
                == load_profile[t] + battery_charge[t]
            )
        
        for t in self.hours:
            if t == 0:
                model += soc[t] == (self.params.battery_capacity * 0.5) + \
                          battery_charge[t] * self.params.battery_efficiency - battery_discharge[t]
            else:
                model += soc[t] == soc[t-1] + battery_charge[t] * self.params.battery_efficiency - battery_discharge[t]
        
        for t in self.hours:
            model += grid_import[t] <= peak_demand
            model += grid_import[t] <= self.params.max_grid_import
            model += grid_export[t] <= self.params.max_grid_export
        
        solver = pulp.PULP_CBC_CMD(msg=0)
        model.solve(solver)
        
        if pulp.LpStatus[model.status] == 'Optimal':
            return self._extract_peak_results(model, load_profile, solar_profile, wind_profile,
                                              price_profile, grid_import, grid_export,
                                              battery_charge, battery_discharge, soc, peak_demand)
        return {'status': 'failed'}
    
    def _extract_peak_results(self, model, load, solar, wind, price, grid_imp, grid_exp,
                             charge, discharge, soc, peak) -> Dict[str, Any]:
        """Extract peak shaving results."""
        results = []
        total_cost = 0
        
        for t in self.hours:
            grid_val = grid_imp[t].varValue or 0
            hourly_cost = grid_val * price[t] - (grid_exp[t].varValue or 0) * self.params.grid_export_price
            total_cost += hourly_cost
            
            results.append({
                "Hour": t, "Solar (kW)": solar[t], "Wind (kW)": wind[t],
                "Load (kW)": load[t], "Grid (kW)": round(grid_val, 2),
                "Battery SOC (kWh)": round(soc[t].varValue or 0, 2),
                "Price (₹/kWh)": price[t], "Hourly Cost (₹)": round(hourly_cost, 2)
            })
        
        return {
            'status': 'Optimal',
            'dataframe': pd.DataFrame(results),
            'total_cost': round(total_cost, 2),
            'peak_demand': round(peak.varValue or 0, 2),
            'demand_charge': round((peak.varValue or 0) * self.params.demand_charge, 2)
        }
    
    def run_battery_degradation_scheduling(self, load_profile, solar_profile, wind_profile,
                                           price_profile=None) -> Dict[str, Any]:
        """Schedule battery with degradation awareness."""
        if price_profile is None:
            price_profile = self._generate_price_profile()
        
        model = pulp.LpProblem("Battery_Degradation", pulp.LpMinimize)
        
        grid_import = pulp.LpVariable.dicts("Grid_Import", self.hours, lowBound=0)
        battery_charge = pulp.LpVariable.dicts("Battery_Charge", self.hours, lowBound=0)
        battery_discharge = pulp.LpVariable.dicts("Battery_Discharge", self.hours, lowBound=0)
        soc = pulp.LpVariable.dicts("SOC", self.hours,
                                    lowBound=self.params.battery_capacity * self.params.min_soc_reserve,
                                    upBound=self.params.battery_capacity)
        
        energy_cost = pulp.lpSum([grid_import[t] * price_profile[t] for t in self.hours])
        degradation = self.params.battery_degradation_cost * pulp.lpSum([
            (battery_charge[t] + battery_discharge[t]) for t in self.hours
        ])
        model += energy_cost + degradation
        
        for t in self.hours:
            model += (
                solar_profile[t] + wind_profile[t] + grid_import[t] + battery_discharge[t]
                == load_profile[t] + battery_charge[t]
            )
        
        for t in self.hours:
            if t == 0:
                model += soc[t] == (self.params.battery_capacity * 0.5) + \
                          battery_charge[t] * self.params.battery_efficiency - battery_discharge[t]
            else:
                model += soc[t] == soc[t-1] + battery_charge[t] * self.params.battery_efficiency - battery_discharge[t]
            
            max_rate = self.params.battery_capacity * 0.5
            model += battery_charge[t] <= max_rate
            model += battery_discharge[t] <= max_rate
        
        for t in self.hours:
            model += grid_import[t] <= self.params.max_grid_import
        
        solver = pulp.PULP_CBC_CMD(msg=0)
        model.solve(solver)
        
        if pulp.LpStatus[model.status] == 'Optimal':
            return self._extract_battery_results(model, load_profile, solar_profile, wind_profile,
                                                 price_profile, grid_import, battery_charge,
                                                 battery_discharge, soc)
        return {'status': 'failed'}
    
    def _extract_battery_results(self, model, load, solar, wind, price, grid_imp,
                                 charge, discharge, soc) -> Dict[str, Any]:
        """Extract battery scheduling results."""
        results = []
        total_cost = 0
        total_cycles = 0
        
        for t in self.hours:
            grid_val = grid_imp[t].varValue or 0
            ch_val = charge[t].varValue or 0
            dis_val = discharge[t].varValue or 0
            hourly_cost = grid_val * price[t]
            total_cost += hourly_cost
            total_cycles += ch_val + dis_val
            
            results.append({
                "Hour": t, "Solar (kW)": solar[t], "Wind (kW)": wind[t],
                "Load (kW)": load[t], "Grid (kW)": round(grid_val, 2),
                "Battery SOC (kWh)": round(soc[t].varValue or 0, 2),
                "Charge (kW)": round(ch_val, 2), "Discharge (kW)": round(dis_val, 2),
                "Hourly Cost (₹)": round(hourly_cost, 2)
            })
        
        cycles = total_cycles / (2 * self.params.battery_capacity)
        
        return {
            'status': 'Optimal',
            'dataframe': pd.DataFrame(results),
            'total_cost': round(total_cost, 2),
            'battery_cycles': round(cycles, 3),
            'degradation_cost': round(cycles * self.params.battery_degradation_cost * 100, 2)
        }
    
    def run_load_shifting_optimization(self, base_load, solar_profile, wind_profile,
                                      price_profile=None) -> Dict[str, Any]:
        """Optimize load shifting."""
        if price_profile is None:
            price_profile = self._generate_price_profile()
        
        flexible_loads = self.params.flexible_loads or {}
        load_windows = self.params.flexible_load_windows or {}
        
        model = pulp.LpProblem("Load_Shifting", pulp.LpMinimize)
        
        grid_import = pulp.LpVariable.dicts("Grid_Import", self.hours, lowBound=0)
        grid_export = pulp.LpVariable.dicts("Grid_Export", self.hours, lowBound=0)
        battery_charge = pulp.LpVariable.dicts("Battery_Charge", self.hours, lowBound=0)
        battery_discharge = pulp.LpVariable.dicts("Battery_Discharge", self.hours, lowBound=0)
        soc = pulp.LpVariable.dicts("SOC", self.hours,
                                    lowBound=self.params.battery_capacity * self.params.min_soc_reserve,
                                    upBound=self.params.battery_capacity)
        
        shifted_loads = {}
        for load_name in flexible_loads:
            shifted_loads[load_name] = pulp.LpVariable.dicts(
                f"Shifted_{load_name}", self.hours, lowBound=0
            )
        
        model += pulp.lpSum([
            (base_load[t] + sum(shifted_loads[ln][t] for ln in flexible_loads)) * price_profile[t]
            for t in self.hours
        ])
        
        for t in self.hours:
            shifted_sum = sum(shifted_loads[ln][t] for ln in flexible_loads)
            model += (
                solar_profile[t] + wind_profile[t] + grid_import[t] + battery_discharge[t]
                == base_load[t] + shifted_sum + battery_charge[t]
            )
        
        for t in self.hours:
            if t == 0:
                model += soc[t] == (self.params.battery_capacity * 0.5) + \
                          battery_charge[t] * self.params.battery_efficiency - battery_discharge[t]
            else:
                model += soc[t] == soc[t-1] + battery_charge[t] * self.params.battery_efficiency - battery_discharge[t]
        
        for load_name, energy in flexible_loads.items():
            window = load_windows.get(load_name, (0, 23))
            total = pulp.lpSum([
                shifted_loads[load_name][t] for t in range(window[0], window[1] + 1)
            ])
            model += total == energy
        
        for t in self.hours:
            model += grid_import[t] <= self.params.max_grid_import
            model += grid_export[t] <= self.params.max_grid_export
        
        solver = pulp.PULP_CBC_CMD(msg=0)
        model.solve(solver)
        
        if pulp.LpStatus[model.status] == 'Optimal':
            return self._extract_load_shift_results(
                model, base_load, solar_profile, wind_profile, price_profile,
                grid_import, grid_export, battery_charge, battery_discharge, soc, shifted_loads
            )
        return {'status': 'failed'}
    
    def _extract_load_shift_results(self, model, base_load, solar, wind, price, grid_imp,
                                    grid_exp, charge, discharge, soc, shifted) -> Dict[str, Any]:
        """Extract load shifting results."""
        results = []
        total_cost = 0
        
        for t in self.hours:
            grid_val = grid_imp[t].varValue or 0
            shifted_dict = {}
            for ln in shifted:
                shifted_dict[ln] = round(shifted[ln][t].varValue or 0, 2)
            
            total_load = base_load[t] + sum(shifted_dict.values())
            hourly_cost = grid_val * price[t] - (grid_exp[t].varValue or 0) * self.params.grid_export_price
            total_cost += hourly_cost
            
            results.append({
                "Hour": t, "Base Load (kW)": base_load[t], "Solar (kW)": solar[t],
                "Wind (kW)": wind[t], "Grid (kW)": round(grid_val, 2),
                "Total Load (kW)": round(total_load, 2), "Battery SOC (kWh)": round(soc[t].varValue or 0, 2),
                "Hourly Cost (₹)": round(hourly_cost, 2), **shifted_dict
            })
        
        return {
            'status': 'Optimal',
            'dataframe': pd.DataFrame(results),
            'total_cost': round(total_cost, 2)
        }
    
    def run_scenario_analysis(self, base_load, base_solar, base_wind,
                             scenarios: Dict) -> pd.DataFrame:
        """Run what-if scenario analysis."""
        comparison = []
        
        for name, profiles in scenarios.items():
            load = profiles.get('load', base_load)
            solar = profiles.get('solar', base_solar)
            wind = profiles.get('wind', base_wind)
            
            result = self.run_multi_objective_optimization(load, solar, wind)
            
            if result.get('status') == 'Optimal':
                comparison.append({
                    'Scenario': name,
                    'Total Cost (₹)': result.get('total_cost', 0),
                    'CO2 Emissions (kg)': result.get('total_emissions', 0),
                    'Renewable %': result.get('renewable_percentage', 0),
                    'Peak (kW)': result.get('peak_demand', 0)
                })
        
        return pd.DataFrame(comparison)
    
    def compare_strategies(self, load_profile, solar_profile, wind_profile,
                         price_profile=None) -> pd.DataFrame:
        """Compare different scheduling strategies."""
        if price_profile is None:
            price_profile = self._generate_price_profile()
        
        results = []
        original_obj = self.params.objective
        
        self.params.objective = 'cost'
        cost_result = self.run_multi_objective_optimization(load_profile, solar_profile, wind_profile, price_profile)
        if cost_result.get('status') == 'Optimal':
            results.append({
                'Strategy': 'Cost Optimization',
                'Cost (₹)': cost_result.get('total_cost', 0),
                'Emissions (kg)': cost_result.get('total_emissions', 0),
                'Renewable %': cost_result.get('renewable_percentage', 0)
            })
        
        self.params.objective = 'balanced'
        balanced = self.run_multi_objective_optimization(load_profile, solar_profile, wind_profile, price_profile)
        if balanced.get('status') == 'Optimal':
            results.append({
                'Strategy': 'Balanced',
                'Cost (₹)': balanced.get('total_cost', 0),
                'Emissions (kg)': balanced.get('total_emissions', 0),
                'Renewable %': balanced.get('renewable_percentage', 0)
            })
        
        self.params.objective = original_obj
        return pd.DataFrame(results)

