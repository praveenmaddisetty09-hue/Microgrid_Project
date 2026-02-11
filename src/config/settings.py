"""
Centralized Configuration Module for Smart Microgrid Manager Pro.

This module provides a single source of truth for all application constants,
environment variables, and configuration settings. All magic numbers and
hardcoded values should be defined here rather than scattered throughout
the codebase.

Usage:
    from src.config.settings import (
        DEFAULT_CARBON_INTENSITY,
        DEFAULT_BATTERY_EFFICIENCY,
        PricingTiers,
        DatabaseConfig,
    )
"""

from dataclasses import dataclass, field
from typing import Literal
import os


# =============================================================================
# ENERGY SYSTEM CONSTANTS
# =============================================================================
# Default carbon emission factor for grid electricity (kg CO2 per kWh)
# Source: India's national average (approx. 0.82 kg/kWh in 2024)
DEFAULT_CARBON_INTENSITY: float = 0.82

# Round-trip efficiency for battery storage systems
# Typical lithium-ion battery efficiency range: 85-95%
DEFAULT_BATTERY_EFFICIENCY: float = 0.95

# Minimum state of charge (SOC) reserve as percentage of capacity
# Reserved for emergency backup scenarios
DEFAULT_MIN_SOC_RESERVE: float = 0.10

# Initial battery state of charge when starting simulation
DEFAULT_INITIAL_SOC: float = 0.50


# =============================================================================
# ECONOMIC/PRICING CONSTANTS
# =============================================================================
# Base electricity price (₹ per kWh) during off-peak hours
DEFAULT_BASE_PRICE: float = 5.0

# Peak hour electricity price (₹ per kWh)
DEFAULT_PEAK_PRICE: float = 15.0

# Default peak hour start time (24-hour format)
DEFAULT_PEAK_START: int = 17

# Default peak hour end time (24-hour format)
DEFAULT_PEAK_END: int = 21

# Feed-in tariff for grid export (₹ per kWh)
DEFAULT_FEED_IN_TARIFF: float = 3.0

# Battery degradation cost per cycle (₹ per kWh)
# Represents wear-and-tear on battery per full cycle
BATTERY_DEGRADATION_COST: float = 0.01


@dataclass
class PricingTiers:
    """
    Electricity pricing structure with time-of-use tiers.
    
    Attributes:
        base_price: Off-peak rate (₹/kWh)
        peak_price: Peak hour rate (₹/kWh)
        peak_start: Hour when peak pricing begins (0-23)
        peak_end: Hour when peak pricing ends (0-23)
    """
    base_price: float = DEFAULT_BASE_PRICE
    peak_price: float = DEFAULT_PEAK_PRICE
    peak_start: int = DEFAULT_PEAK_START
    peak_end: int = DEFAULT_PEAK_END
    
    def get_price(self, hour: int) -> float:
        """Get the applicable price for a given hour."""
        if self.peak_start <= hour <= self.peak_end:
            return self.peak_price
        return self.base_price


# =============================================================================
# BATTERY SYSTEM CONSTANTS
# =============================================================================
# Maximum charge/discharge rate as percentage of capacity per hour
# Prevents battery stress from rapid cycling
MAX_BATTERY_RATE: float = 0.50

# Maximum depth of discharge (DoD) percentage
# Protects battery lifespan by limiting full discharges
MAX_DEPTH_OF_DISCHARGE: float = 0.90

# Minimum recommended SOC for battery health (%)
MIN_RECOMMENDED_SOC: float = 0.20


@dataclass
class BatteryConfig:
    """
    Battery energy storage system configuration.
    
    Attributes:
        capacity_kwh: Total usable capacity in kilowatt-hours
        efficiency: Round-trip efficiency (0-1)
        min_soc_reserve: Minimum SOC to maintain for backup (0-1)
        max_charge_rate: Maximum charge rate as fraction of capacity
        max_discharge_rate: Maximum discharge rate as fraction of capacity
    """
    capacity_kwh: float = 100.0
    efficiency: float = DEFAULT_BATTERY_EFFICIENCY
    min_soc_reserve: float = DEFAULT_MIN_SOC_RESERVE
    max_charge_rate: float = MAX_BATTERY_RATE
    max_discharge_rate: float = MAX_BATTERY_RATE
    
    @property
    def max_charge_kw(self) -> float:
        """Maximum charge power in kW."""
        return self.capacity_kwh * self.max_charge_rate
    
    @property
    def max_discharge_kw(self) -> float:
        """Maximum discharge power in kW."""
        return self.capacity_kwh * self.max_discharge_rate
    
    @property
    def min_soc_kwh(self) -> float:
        """Minimum SOC in kWh (reserve for emergencies)."""
        return self.capacity_kwh * self.min_soc_reserve


# =============================================================================
# GRID SYSTEM CONSTANTS
# =============================================================================
# Maximum grid import power in kilowatts (safety limit)
DEFAULT_GRID_LIMIT_KW: float = 50.0

# Maximum grid export power in kilowatts
DEFAULT_GRID_EXPORT_LIMIT: float = 50.0

# Warning threshold as percentage of grid limit
GRID_WARNING_THRESHOLD: float = 0.80


# =============================================================================
# WEATHER API CONSTANTS
# =============================================================================
# OpenWeatherMap API base URL
OPENWEATHERMAP_BASE_URL: str = "http://api.openweathermap.org/data/2.5/"

# Cache duration for weather data in seconds (10 minutes)
WEATHER_CACHE_DURATION: int = 600

# Default location coordinates (New Delhi, India)
DEFAULT_LOCATION = {
    "lat": 28.6139,
    "lon": 77.2090,
    "city": "New Delhi",
    "country": "IN"
}


@dataclass
class WeatherConfig:
    """Weather service configuration."""
    api_key: str = ""
    base_url: str = OPENWEATHERMAP_BASE_URL
    cache_duration_seconds: int = WEATHER_CACHE_DURATION
    default_location: dict = field(default_factory=lambda: DEFAULT_LOCATION.copy())


# =============================================================================
# DATABASE CONSTANTS
# =============================================================================
# SQLite database filename
DATABASE_FILENAME: str = "microgrid_data.db"

# User database filename
USER_DB_FILENAME: str = "users.json"

# Maximum historical data retention in days
DATA_RETENTION_DAYS: int = 30


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    database_file: str = DATABASE_FILENAME
    user_db_file: str = USER_DB_FILENAME
    data_retention_days: int = DATA_RETENTION_DAYS


# =============================================================================
# AUTHENTICATION SECURITY CONSTANTS
# =============================================================================
# Session timeout in minutes
SESSION_TIMEOUT_MINUTES: int = 30

# Maximum failed login attempts before lockout
MAX_LOGIN_ATTEMPTS: int = 5

# Account lockout duration in minutes
LOCKOUT_DURATION_MINUTES: int = 15

# Minimum password length
PASSWORD_MIN_LENGTH: int = 8

# Password requirement flags
PASSWORD_REQUIRE_UPPERCASE: bool = True
PASSWORD_REQUIRE_LOWERCASE: bool = True
PASSWORD_REQUIRE_DIGIT: bool = True
PASSWORD_REQUIRE_SPECIAL: bool = True


@dataclass
class SecurityConfig:
    """Authentication and security settings."""
    session_timeout_minutes: int = SESSION_TIMEOUT_MINUTES
    max_login_attempts: int = MAX_LOGIN_ATTEMPTS
    lockout_duration_minutes: int = LOCKOUT_DURATION_MINUTES
    password_min_length: int = PASSWORD_MIN_LENGTH
    password_require_uppercase: bool = PASSWORD_REQUIRE_UPPERCASE
    password_require_lowercase: bool = PASSWORD_REQUIRE_LOWERCASE
    password_require_digit: bool = PASSWORD_REQUIRE_DIGIT
    password_require_special: bool = PASSWORD_REQUIRE_SPECIAL


# =============================================================================
# NOTIFICATION CONSTANTS
# =============================================================================
# Default notification expiry time in hours
DEFAULT_NOTIFICATION_EXPIRY_HOURS: int = 24

# Cost threshold for high-cost alerts (₹)
HIGH_COST_THRESHOLD: float = 100.0

# Low battery SOC threshold for warnings (%)
LOW_BATTERY_THRESHOLD: float = 20.0


@dataclass
class NotificationConfig:
    """Notification system configuration."""
    default_expiry_hours: int = DEFAULT_NOTIFICATION_EXPIRY_HOURS
    high_cost_threshold: float = HIGH_COST_THRESHOLD
    low_battery_threshold: float = LOW_BATTERY_THRESHOLD


# =============================================================================
# SIMULATION CONSTANTS
# =============================================================================
# Number of hours in simulation horizon
SIMULATION_HOURS: int = 24

# Number of forecast hours
FORECAST_HOURS: int = 24


@dataclass
class SimulationConfig:
    """Simulation parameters."""
    horizon_hours: int = SIMULATION_HOURS
    forecast_hours: int = FORECAST_HOURS


# =============================================================================
# DEFAULT USER CREDENTIALS
# =============================================================================
# Default admin credentials (OVERRIDE IN PRODUCTION!)
# WARNING: These should be set via environment variables in production
DEFAULT_ADMIN_USERNAME: str = "admin"
DEFAULT_ADMIN_PASSWORD: str = "microgrid"
DEFAULT_ADMIN_EMAIL: str = "admin@microgrid.com"

DEFAULT_USER_USERNAME: str = "user"
DEFAULT_USER_PASSWORD: str = "user123"
DEFAULT_USER_EMAIL: str = "user@microgrid.com"


def get_default_credentials() -> dict:
    """
    Get default user credentials from environment or fallbacks.
    
    Environment variables (if set):
        MICROGRID_ADMIN_USER
        MICROGRID_ADMIN_PASS
        MICROGRID_USER_USER
        MICROGRID_USER_PASS
    """
    return {
        "admin": {
            "username": os.getenv("MICROGRID_ADMIN_USER", DEFAULT_ADMIN_USERNAME),
            "password": os.getenv("MICROGRID_ADMIN_PASS", DEFAULT_ADMIN_PASSWORD),
            "email": os.getenv("MICROGRID_ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL),
            "role": "admin",
        },
        "user": {
            "username": os.getenv("MICROGRID_USER_USER", DEFAULT_USER_USERNAME),
            "password": os.getenv("MICROGRID_USER_PASS", DEFAULT_USER_PASSWORD),
            "email": os.getenv("MICROGRID_USER_EMAIL", DEFAULT_USER_EMAIL),
            "role": "user",
        },
    }


# =============================================================================
# ML MODEL CONSTANTS
# =============================================================================
# Model directory relative to project root
MODEL_DIR: str = "models"

# Default model hyperparameters
DEFAULT_RANDOM_STATE: int = 42
DEFAULT_N_ESTIMATORS: int = 50


@dataclass
class MLConfig:
    """Machine learning model configuration."""
    model_dir: str = MODEL_DIR
    random_state: int = DEFAULT_RANDOM_STATE
    n_estimators: int = DEFAULT_N_ESTIMATORS


# =============================================================================
# APPLICATION METADATA
# =============================================================================
# Application version (semantic versioning)
APP_VERSION: str = "2.0.0"

# Application name
APP_NAME: str = "Smart Microgrid Manager Pro"

# Application name for display
APP_DISPLAY_NAME: str = "⚡ Smart Microgrid Manager Pro"


@dataclass
class AppInfo:
    """Application metadata."""
    name: str = APP_NAME
    display_name: str = APP_DISPLAY_NAME
    version: str = APP_VERSION
    year: int = 2024


# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================
def validate_configuration() -> list[str]:
    """
    Validate critical configuration values.
    
    Returns:
        List of warning messages (empty if valid)
    """
    warnings = []
    
    if DEFAULT_CARBON_INTENSITY <= 0:
        warnings.append("Carbon intensity should be positive")
    
    if not (0 < DEFAULT_BATTERY_EFFICIENCY <= 1):
        warnings.append("Battery efficiency must be between 0 and 1")
    
    if not (0 <= DEFAULT_MIN_SOC_RESERVE < 1):
        warnings.append("Min SOC reserve should be between 0 and 1")
    
    if DEFAULT_PEAK_START < 0 or DEFAULT_PEAK_END > 23:
        warnings.append("Peak hours should be in range 0-23")
    
    if DEFAULT_PEAK_START > DEFAULT_PEAK_END:
        warnings.append("Peak start hour should be before peak end hour")
    
    if PASSWORD_MIN_LENGTH < 8:
        warnings.append("Password minimum length should be at least 8")
    
    if SESSION_TIMEOUT_MINUTES < 5:
        warnings.append("Session timeout should be at least 5 minutes")
    
    return warnings


# Run validation on module import
_config_warnings = validate_configuration()
if _config_warnings:
    import warnings as _warnings
    for msg in _config_warnings:
        _warnings.warn(f"Configuration warning: {msg}")

