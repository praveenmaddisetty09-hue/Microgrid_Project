"""
Smart Microgrid Manager Pro - Core Package

A professional-grade energy optimization system for microgrid management.
Uses linear programming to minimize energy costs while satisfying
power balance, battery constraints, and grid limits.

Installation:
    pip install -e ".[all]"

Usage:
    from logic import run_optimization
    
    result = run_optimization(
        load_profile=[...],
        solar_profile=[...],
        wind_profile=[...],
        price_schedule=[...],
        battery_capacity_kwh=100.0,
    )
"""

__version__ = "2.0.0"
__author__ = "Smart Microgrid Team"

