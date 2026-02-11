"""
Custom Type Definitions for Smart Microgrid Manager Pro.

This module provides type aliases and simple classes for type hinting
throughout the codebase.
"""

from enum import Enum
from typing import Sequence


# Type aliases for common types
EnergyProfile = Sequence[float]
PriceSchedule = Sequence[float]


class BatteryAction(Enum):
    """Battery operational states."""
    CHARGING = "charging"
    DISCHARGING = "discharging"
    IDLE = "idle"


class EnergySource(Enum):
    """Types of energy sources."""
    SOLAR = "solar"
    WIND = "wind"
    GRID = "grid"
    BATTERY = "battery"


class OptimizationStatus(Enum):
    """Optimization result status."""
    OPTIMAL = "Optimal"
    INFEASIBLE = "Infeasible"
    UNBOUNDED = "Unbounded"
    TIMEOUT = "Timeout"
    ERROR = "Error"

