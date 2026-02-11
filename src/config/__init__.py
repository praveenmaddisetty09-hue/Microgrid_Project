"""
Configuration Package for Smart Microgrid Manager Pro.

This package provides centralized configuration management including:
- Energy system constants
- Economic/pricing parameters
- Battery specifications
- Security settings
- Database configuration
- Weather API settings
"""

from .settings import (
    # Energy System Constants
    DEFAULT_CARBON_INTENSITY,
    DEFAULT_BATTERY_EFFICIENCY,
    DEFAULT_MIN_SOC_RESERVE,
    DEFAULT_INITIAL_SOC,
    
    # Pricing Constants
    DEFAULT_BASE_PRICE,
    DEFAULT_PEAK_PRICE,
    DEFAULT_PEAK_START,
    DEFAULT_PEAK_END,
    DEFAULT_FEED_IN_TARIFF,
    BATTERY_DEGRADATION_COST,
    PricingTiers,
    
    # Battery Configuration
    MAX_BATTERY_RATE,
    MAX_DEPTH_OF_DISCHARGE,
    MIN_RECOMMENDED_SOC,
    BatteryConfig,
    
    # Grid Configuration
    DEFAULT_GRID_LIMIT_KW,
    DEFAULT_GRID_EXPORT_LIMIT,
    GRID_WARNING_THRESHOLD,
    
    # Weather Configuration
    OPENWEATHERMAP_BASE_URL,
    WEATHER_CACHE_DURATION,
    DEFAULT_LOCATION,
    WeatherConfig,
    
    # Database Configuration
    DATABASE_FILENAME,
    USER_DB_FILENAME,
    DATA_RETENTION_DAYS,
    DatabaseConfig,
    
    # Security Configuration
    SESSION_TIMEOUT_MINUTES,
    MAX_LOGIN_ATTEMPTS,
    LOCKOUT_DURATION_MINUTES,
    PASSWORD_MIN_LENGTH,
    SecurityConfig,
    
    # Notification Configuration
    DEFAULT_NOTIFICATION_EXPIRY_HOURS,
    HIGH_COST_THRESHOLD,
    LOW_BATTERY_THRESHOLD,
    NotificationConfig,
    
    # Simulation Configuration
    SIMULATION_HOURS,
    FORECAST_HOURS,
    SimulationConfig,
    
    # ML Configuration
    MODEL_DIR,
    DEFAULT_RANDOM_STATE,
    DEFAULT_N_ESTIMATORS,
    MLConfig,
    
    # Application Info
    APP_VERSION,
    APP_NAME,
    APP_DISPLAY_NAME,
    AppInfo,
    
    # Credentials
    get_default_credentials,
    
    # Validation
    validate_configuration,
)

__all__ = [
    # Energy System Constants
    "DEFAULT_CARBON_INTENSITY",
    "DEFAULT_BATTERY_EFFICIENCY",
    "DEFAULT_MIN_SOC_RESERVE",
    "DEFAULT_INITIAL_SOC",
    
    # Pricing Constants
    "DEFAULT_BASE_PRICE",
    "DEFAULT_PEAK_PRICE",
    "DEFAULT_PEAK_START",
    "DEFAULT_PEAK_END",
    "DEFAULT_FEED_IN_TARIFF",
    "BATTERY_DEGRADATION_COST",
    "PricingTiers",
    
    # Battery Configuration
    "MAX_BATTERY_RATE",
    "MAX_DEPTH_OF_DISCHARGE",
    "MIN_RECOMMENDED_SOC",
    "BatteryConfig",
    
    # Grid Configuration
    "DEFAULT_GRID_LIMIT_KW",
    "DEFAULT_GRID_EXPORT_LIMIT",
    "GRID_WARNING_THRESHOLD",
    
    # Weather Configuration
    "OPENWEATHERMAP_BASE_URL",
    "WEATHER_CACHE_DURATION",
    "DEFAULT_LOCATION",
    "WeatherConfig",
    
    # Database Configuration
    "DATABASE_FILENAME",
    "USER_DB_FILENAME",
    "DATA_RETENTION_DAYS",
    "DatabaseConfig",
    
    # Security Configuration
    "SESSION_TIMEOUT_MINUTES",
    "MAX_LOGIN_ATTEMPTS",
    "LOCKOUT_DURATION_MINUTES",
    "PASSWORD_MIN_LENGTH",
    "SecurityConfig",
    
    # Notification Configuration
    "DEFAULT_NOTIFICATION_EXPIRY_HOURS",
    "HIGH_COST_THRESHOLD",
    "LOW_BATTERY_THRESHOLD",
    "NotificationConfig",
    
    # Simulation Configuration
    "SIMULATION_HOURS",
    "FORECAST_HOURS",
    "SimulationConfig",
    
    # ML Configuration
    "MODEL_DIR",
    "DEFAULT_RANDOM_STATE",
    "DEFAULT_N_ESTIMATORS",
    "MLConfig",
    
    # Application Info
    "APP_VERSION",
    "APP_NAME",
    "APP_DISPLAY_NAME",
    "AppInfo",
    
    # Credentials
    "get_default_credentials",
    
    # Validation
    "validate_configuration",
]

