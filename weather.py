"""
Weather API Module for Smart Microgrid Manager Pro
Handles real-time weather data integration and forecasting.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import pandas as pd
import numpy as np

# OpenWeatherMap API key (placeholder - user needs to add their own)
API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"
BASE_URL = "http://api.openweathermap.org/data/2.5/"

# Default location (can be configured)
DEFAULT_LOCATION = {
    "lat": 28.6139,  # New Delhi
    "lon": 77.2090,
    "city": "New Delhi",
    "country": "IN"
}


def get_current_weather(lat: float, lon: float, api_key: str = None) -> Optional[Dict]:
    """Get current weather data."""
    if not api_key:
        api_key = API_KEY
    
    url = f"{BASE_URL}weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
                "wind_direction": data["wind"].get("deg", 0),
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "clouds": data["clouds"]["all"],
                "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]),
                "sunset": datetime.fromtimestamp(data["sys"]["sunset"])
            }
    except Exception as e:
        print(f"Weather API error: {e}")
    
    return None


def get_weather_forecast(lat: float, lon: float, api_key: str = None) -> Optional[List[Dict]]:
    """Get 5-day weather forecast."""
    if not api_key:
        api_key = API_KEY
    
    url = f"{BASE_URL}forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            forecasts = []
            
            for item in data["list"]:
                forecasts.append({
                    "datetime": datetime.fromtimestamp(item["dt"]),
                    "temperature": item["main"]["temp"],
                    "feels_like": item["main"]["feels_like"],
                    "humidity": item["main"]["humidity"],
                    "pressure": item["main"]["pressure"],
                    "wind_speed": item["wind"]["speed"],
                    "description": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"],
                    "clouds": item["clouds"]["all"],
                    "pop": item.get("pop", 0)  # Probability of precipitation
                })
            
            return forecasts
    except Exception as e:
        print(f"Weather forecast API error: {e}")
    
    return None


def calculate_solar_multiplier(cloud_cover: int, hour: int) -> float:
    """
    Calculate solar generation multiplier based on cloud cover and time of day.
    
    Args:
        cloud_cover: Cloud cover percentage (0-100)
        hour: Hour of day (0-23)
    
    Returns:
        Solar multiplier (0.0 - 1.0)
    """
    # Base solar potential by hour (assuming sunrise at 6, sunset at 18)
    if 6 <= hour <= 18:
        # Peak at noon (hour 12)
        hourly_factor = 1.0 - abs(hour - 12) / 6  # 0 at 6/18, 1 at 12
    else:
        hourly_factor = 0
    
    # Cloud cover reduction
    cloud_factor = 1.0 - (cloud_cover / 100) * 0.8  # Max 80% reduction from clouds
    
    return max(0, hourly_factor * cloud_factor)


def calculate_wind_multiplier(wind_speed: float, hour: int) -> float:
    """
    Calculate wind generation multiplier based on wind speed.
    
    Args:
        wind_speed: Wind speed in m/s
        hour: Hour of day (0-23)
    
    Returns:
        Wind multiplier (0.0 - 1.5)
    """
    # Wind turbine power curve (simplified)
    # Cut-in: 3 m/s, Rated: 12 m/s, Cut-out: 25 m/s
    if wind_speed < 3:
        return 0.1
    elif wind_speed < 12:
        # Linear increase from 0.1 to 1.0
        return 0.1 + (wind_speed - 3) / 9 * 0.9
    elif wind_speed < 25:
        # Constant at rated power
        return 1.0
    else:
        # Cut-out - no generation
        return 0
    
    # Night time bonus (wind often higher at night)
    if 0 <= hour <= 6 or 21 <= hour <= 23:
        return min(1.5, multiplier * 1.2)
    
    return multiplier


def estimate_daily_generation(weather_data: Dict) -> Dict:
    """Estimate daily solar and wind generation based on weather."""
    solar_potential = []
    wind_potential = []
    
    for hour in range(24):
        # Solar estimation
        cloud_cover = weather_data.get("clouds", 0)
        solar_mult = calculate_solar_multiplier(cloud_cover, hour)
        solar_potential.append(solar_mult)
        
        # Wind estimation
        wind_speed = weather_data.get("wind_speed", 5)
        wind_mult = calculate_wind_multiplier(wind_speed, hour)
        wind_potential.append(wind_mult)
    
    return {
        "solar_multipliers": solar_potential,
        "wind_multipliers": wind_potential,
        "avg_solar": np.mean(solar_potential) * 100,
        "avg_wind": np.mean(wind_potential) * 100,
        "peak_solar_hour": solar_potential.index(max(solar_potential)),
        "peak_wind_hour": wind_potential.index(max(wind_potential))
    }


def get_weather_alerts(forecast: List[Dict]) -> List[Dict]:
    """Generate weather alerts based on forecast."""
    alerts = []
    
    high_wind_hours = []
    low_solar_hours = []
    rain_hours = []
    
    for item in forecast:
        hour = item["datetime"].hour
        
        if item["wind_speed"] > 15:  # High wind warning (>54 km/h)
            high_wind_hours.append(hour)
        
        if item["clouds"] > 80 and 6 <= hour <= 18:  # Low solar hours
            low_solar_hours.append(hour)
        
        if item.get("pop", 0) > 0.7:  # High rain probability
            rain_hours.append(hour)
    
    if high_wind_hours:
        alerts.append({
            "type": "wind",
            "severity": "warning",
            "message": f"High wind speeds expected at hours: {sorted(set(high_wind_hours))}",
            "recommendation": "Consider reducing wind turbine output or performing maintenance"
        })
    
    if low_solar_hours:
        alerts.append({
            "type": "solar",
            "severity": "info",
            "message": f"Reduced solar generation expected due to cloud cover",
            "recommendation": "Ensure battery is charged before these hours"
        })
    
    if rain_hours:
        alerts.append({
            "type": "rain",
            "severity": "info",
            "message": f"Rain expected with {int(max(item.get('pop', 0) * 100))}% probability",
            "recommendation": "Check drainage systems and outdoor equipment"
        })
    
    return alerts


def generate_weather_scenarios() -> Dict:
    """Generate predefined weather scenarios for simulation."""
    return {
        "☀️ Sunny Day": {
            "cloud_cover": 10,
            "wind_speed": 5,
            "temperature": 30,
            "description": "Clear skies with moderate winds",
            "solar_mult": 1.0,
            "wind_mult": 0.8
        },
        "☁️ Cloudy Day": {
            "cloud_cover": 70,
            "wind_speed": 8,
            "temperature": 25,
            "description": "Overcast conditions",
            "solar_mult": 0.3,
            "wind_mult": 0.9
        },
        "🌧️ Rainy Day": {
            "cloud_cover": 90,
            "wind_speed": 12,
            "temperature": 22,
            "description": "Heavy rain expected",
            "solar_mult": 0.1,
            "wind_mult": 1.2
        },
        "💨 Windy Day": {
            "cloud_cover": 30,
            "wind_speed": 18,
            "temperature": 24,
            "description": "Strong winds throughout the day",
            "solar_mult": 0.6,
            "wind_mult": 1.5
        },
        "🌗 Night Time": {
            "cloud_cover": 20,
            "wind_speed": 6,
            "temperature": 20,
            "description": "Night time conditions",
            "solar_mult": 0.0,
            "wind_mult": 1.1
        },
        "⛈️ Storm": {
            "cloud_cover": 100,
            "wind_speed": 22,
            "temperature": 21,
            "description": "Storm conditions - reduced generation",
            "solar_mult": 0.05,
            "wind_mult": 0.3
        },
        "🌤️ Partly Cloudy": {
            "cloud_cover": 40,
            "wind_speed": 7,
            "temperature": 28,
            "description": "Mixed sun and clouds",
            "solar_mult": 0.7,
            "wind_mult": 0.85
        }
    }


def apply_weather_to_profiles(base_solar: List[float], base_wind: List[float], 
                              scenario: str = "☀️ Sunny Day") -> Tuple[List[float], List[float]]:
    """Apply weather scenario multipliers to base generation profiles."""
    scenarios = generate_weather_scenarios()
    
    if scenario not in scenarios:
        scenario = "☀️ Sunny Day"
    
    params = scenarios[scenario]
    
    solar_multipliers = params["solar_mult"]
    wind_multipliers = params["wind_mult"]
    
    # Apply multipliers
    adjusted_solar = [s * solar_multipliers for s in base_solar]
    adjusted_wind = [w * wind_multipliers for w in base_wind]
    
    return adjusted_solar, adjusted_wind


def get_weather_icon_url(icon_code: str) -> str:
    """Get weather icon URL from OpenWeatherMap."""
    return f"http://openweathermap.org/img/wn/{icon_code}@2x.png"


def format_weather_display(weather: Dict) -> Dict:
    """Format weather data for display in Streamlit."""
    if not weather:
        return None
    
    return {
        "🌡️ Temperature": f"{weather['temperature']:.1f}°C",
        "💧 Humidity": f"{weather['humidity']}%",
        "💨 Wind": f"{weather['wind_speed']:.1f} m/s",
        "☁️ Clouds": f"{weather['clouds']}%",
        "📖 Description": weather['description'].capitalize(),
        "🌅 Sunrise": weather['sunrise'].strftime("%H:%M"),
        "🌇 Sunset": weather['sunset'].strftime("%H:%M")
    }


class WeatherCache:
    """Simple cache for weather data."""
    
    def __init__(self, cache_duration: int = 600):  # 10 minutes default
        self.cache_duration = cache_duration
        self.data = {}
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached data if not expired."""
        if key in self.data:
            cached_time, value = self.data[key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                return value
            else:
                del self.data[key]
        return None
    
    def set(self, key: str, value: Dict):
        """Cache data with timestamp."""
        self.data[key] = (datetime.now(), value)


# Global weather cache
weather_cache = WeatherCache()


def get_cached_weather(lat: float, lon: float, api_key: str = None) -> Optional[Dict]:
    """Get weather with caching."""
    cache_key = f"{lat},{lon}"
    
    # Try cache first
    cached = weather_cache.get(cache_key)
    if cached:
        return cached
    
    # Fetch from API
    weather = get_current_weather(lat, lon, api_key)
    if weather:
        weather_cache.set(cache_key, weather)
    
    return weather


def get_cached_forecast(lat: float, lon: float, api_key: str = None) -> Optional[List[Dict]]:
    """Get forecast with caching."""
    cache_key = f"forecast_{lat},{lon}"
    
    # Try cache first
    cached = weather_cache.get(cache_key)
    if cached:
        return cached
    
    # Fetch from API
    forecast = get_weather_forecast(lat, lon, api_key)
    if forecast:
        weather_cache.set(cache_key, forecast)
    
    return forecast

