"""
Machine Learning Forecasting Module for Smart Microgrid Manager Pro
Handles load, solar, and wind predictions using ML models.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

# Model directory
MODEL_DIR = "models"


def ensure_model_dir():
    """Create model directory if not exists."""
    os.makedirs(MODEL_DIR, exist_ok=True)


class EnergyForecaster:
    """Machine learning forecaster for energy predictions."""
    
    def __init__(self):
        ensure_model_dir()
        self.models = {}
        self.scalers = {}
        self.is_trained = False
        
        # Feature names
        self.feature_names = [
            'hour', 'day_of_week', 'month', 'is_weekend',
            'temperature', 'cloud_cover', 'wind_speed',
            'lag_24h', 'lag_48h', 'rolling_mean_24h'
        ]
        
        # Initialize default models
        self._create_default_models()
    
    def _create_default_models(self):
        """Initialize models for different energy types."""
        self.models = {
            'load': RandomForestRegressor(n_estimators=50, random_state=42),
            'solar': Ridge(alpha=1.0),
            'wind': GradientBoostingRegressor(n_estimators=50, random_state=42)
        }
        
        self.scalers = {
            'X': StandardScaler(),
            'load_y': StandardScaler(),
            'solar_y': StandardScaler(),
            'wind_y': StandardScaler()
        }
    
    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract features from dataframe."""
        features = pd.DataFrame()
        
        if 'datetime' in df.columns:
            features['hour'] = df['datetime'].dt.hour
            features['day_of_week'] = df['datetime'].dt.dayofweek
            features['month'] = df['datetime'].dt.month
            features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)
        else:
            features['hour'] = df.get('hour', 12)
            features['day_of_week'] = df.get('day_of_week', 0)
            features['month'] = df.get('month', 1)
            features['is_weekend'] = df.get('is_weekend', 0)
        
        # Weather features
        features['temperature'] = df.get('temperature', 25)
        features['cloud_cover'] = df.get('cloud_cover', 50)
        features['wind_speed'] = df.get('wind_speed', 5)
        
        # Lag features (if available)
        features['lag_24h'] = df.get('lag_24h', df.get('value', 50) * 0.9)
        features['lag_48h'] = df.get('lag_48h', df.get('value', 50) * 0.85)
        features['rolling_mean_24h'] = df.get('rolling_mean_24h', df.get('value', 50))
        
        return features.values
    
    def _create_synthetic_training_data(self, hours: int = 8760) -> pd.DataFrame:
        """Create synthetic training data based on typical energy patterns."""
        np.random.seed(42)
        
        # Generate datetime range
        start_date = datetime(2020, 1, 1)
        dates = [start_date + timedelta(hours=i) for i in range(hours)]
        
        df = pd.DataFrame({'datetime': dates})
        
        # Hour of day
        df['hour'] = df['datetime'].dt.hour
        
        # Day of week
        df['day_of_week'] = df['datetime'].dt.dayofweek
        
        # Month
        df['month'] = df['datetime'].dt.month
        
        # Temperature (seasonal pattern)
        df['temperature'] = 25 + 10 * np.sin(2 * np.pi * (df['month'] - 1) / 12) + np.random.normal(0, 3, hours)
        
        # Cloud cover (random with monthly variation)
        df['cloud_cover'] = np.clip(30 + 20 * np.sin(2 * np.pi * (df['month'] - 1) / 12) + np.random.normal(0, 20, hours), 0, 100)
        
        # Wind speed
        df['wind_speed'] = np.clip(5 + 3 * np.sin(2 * np.pi * (df['hour'] - 6) / 24) + np.random.normal(0, 2, hours), 0, 25)
        
        # Load profile (typical daily and seasonal patterns)
        base_load = 30 + 50 * np.sin(2 * np.pi * (df['hour'] - 6) / 24)
        seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * (df['month'] - 1) / 12)
        weekend_factor = np.where(df['day_of_week'] >= 5, 0.8, 1.0)
        df['load'] = np.clip(base_load * seasonal_factor * weekend_factor + np.random.normal(0, 5, hours), 10, 150)
        
        # Solar profile (hourly and seasonal)
        solar_base = np.where(
            (df['hour'] >= 6) & (df['hour'] <= 18),
            50 * np.sin(np.pi * (df['hour'] - 6) / 12),
            0
        )
        solar_season = 1 + 0.3 * np.sin(2 * np.pi * (df['month'] - 1) / 12)
        solar_cloud = 1 - df['cloud_cover'] / 150
        df['solar'] = np.clip(solar_base * solar_season * solar_cloud + np.random.normal(0, 3, hours), 0, 80)
        
        # Wind profile
        wind_base = 15 + 10 * np.sin(2 * np.pi * (df['hour'] - 0) / 24)
        wind_season = 1 + 0.2 * np.cos(2 * np.pi * (df['month'] - 1) / 12)
        df['wind'] = np.clip(wind_base * wind_season + np.random.normal(0, 3, hours), 0, 50)
        
        return df
    
    def train(self, data: Optional[pd.DataFrame] = None):
        """Train the forecasting models."""
        if data is None:
            data = self._create_synthetic_training_data()
        
        # Prepare features
        X = self._extract_features(data)
        
        # Scale features
        X_scaled = self.scalers['X'].fit_transform(X)
        
        # Train load model
        y_load = data['load'].values
        y_load_scaled = self.scalers['load_y'].fit_transform(y_load.reshape(-1, 1)).ravel()
        self.models['load'].fit(X_scaled, y_load_scaled)
        
        # Train solar model
        y_solar = data['solar'].values
        y_solar_scaled = self.scalers['solar_y'].fit_transform(y_solar.reshape(-1, 1)).ravel()
        self.models['solar'].fit(X_scaled, y_solar_scaled)
        
        # Train wind model
        y_wind = data['wind'].values
        y_wind_scaled = self.scalers['wind_y'].fit_transform(y_wind.reshape(-1, 1)).ravel()
        self.models['wind'].fit(X_scaled, y_wind_scaled)
        
        self.is_trained = True
        
        # Save models
        self.save_models()
        
        return self
    
    def save_models(self):
        """Save trained models to disk."""
        ensure_model_dir()
        for name, model in self.models.items():
            joblib.dump(model, os.path.join(MODEL_DIR, f"{name}_model.pkl"))
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, os.path.join(MODEL_DIR, f"{name}_scaler.pkl"))
    
    def load_models(self) -> bool:
        """Load models from disk."""
        try:
            for name in ['load', 'solar', 'wind']:
                self.models[name] = joblib.load(os.path.join(MODEL_DIR, f"{name}_model.pkl"))
            for name, _ in self.scalers.items():
                self.scalers[name] = joblib.load(os.path.join(MODEL_DIR, f"{name}_scaler.pkl"))
            self.is_trained = True
            return True
        except:
            return False
    
    def predict(self, hours: int = 24, start_date: Optional[datetime] = None,
               weather: Optional[Dict] = None) -> pd.DataFrame:
        """Generate predictions for specified number of hours."""
        if not self.is_trained:
            self.load_models()
        
        if not self.is_trained:
            self.train()
        
        if start_date is None:
            start_date = datetime.now()
        
        # Generate prediction timestamps
        predictions = []
        current_date = start_date
        
        # Use provided weather or defaults
        temp = weather.get('temperature', 25) if weather else 25
        clouds = weather.get('cloud_cover', 50) if weather else 50
        wind = weather.get('wind_speed', 5) if weather else 5
        
        for i in range(hours):
            pred_time = current_date + timedelta(hours=i)
            
            # Create feature vector
            features = {
                'hour': pred_time.hour,
                'day_of_week': pred_time.weekday(),
                'month': pred_time.month,
                'is_weekend': 1 if pred_time.weekday() >= 5 else 0,
                'temperature': temp + np.random.normal(0, 2),
                'cloud_cover': min(100, max(0, clouds + np.random.normal(0, 10))),
                'wind_speed': max(0, wind + np.random.normal(0, 2)),
                'lag_24h': 50,  # Simplified
                'lag_48h': 50,
                'rolling_mean_24h': 50
            }
            
            X = self._extract_features(pd.DataFrame([features]))
            X_scaled = self.scalers['X'].transform(X)
            
            # Predict
            load_pred = self.scalers['load_y'].inverse_transform(
                self.models['load'].predict(X_scaled).reshape(-1, 1)
            )[0, 0]
            
            solar_pred = self.scalers['solar_y'].inverse_transform(
                self.models['solar'].predict(X_scaled).reshape(-1, 1)
            )[0, 0]
            
            wind_pred = self.scalers['wind_y'].inverse_transform(
                self.models['wind'].predict(X_scaled).reshape(-1, 1)
            )[0, 0]
            
            # Apply physical constraints
            load_pred = max(0, load_pred)
            solar_pred = max(0, solar_pred)
            if pred_time.hour < 6 or pred_time.hour > 18:
                solar_pred = 0
            
            predictions.append({
                'datetime': pred_time,
                'hour': pred_time.hour,
                'day_of_week': pred_time.strftime('%A'),
                'Load (kW)': round(load_pred, 1),
                'Solar (kW)': round(solar_pred, 1),
                'Wind (kW)': round(wind_pred, 1),
                'Total Renewable (kW)': round(solar_pred + wind_pred, 1)
            })
        
        return pd.DataFrame(predictions)
    
    def evaluate(self, test_data: pd.DataFrame) -> Dict:
        """Evaluate model performance on test data."""
        if not self.is_trained:
            self.load_models()
        
        if not self.is_trained:
            return {'error': 'Models not trained'}
        
        X = self._extract_features(test_data)
        X_scaled = self.scalers['X'].transform(X)
        
        results = {}
        
        for target in ['load', 'solar', 'wind']:
            y_true = test_data[target].values
            y_pred = self.scalers[f'{target}_y'].inverse_transform(
                self.models[target].predict(X_scaled).reshape(-1, 1)
            ).ravel()
            
            results[target] = {
                'MAE': mean_absolute_error(y_true, y_pred),
                'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
                'R2': r2_score(y_true, y_pred)
            }
        
        return results


def generate_base_profiles() -> Tuple[List[int], List[float], List[float], List[float]]:
    """Generate base load, solar, and wind profiles for simulation."""
    hours = list(range(24))
    
    # Solar: Peak at noon (High sun)
    base_solar = [0, 0, 0, 0, 0, 1, 5, 15, 30, 45, 50, 55, 55, 50, 40, 25, 10, 2, 0, 0, 0, 0, 0, 0]
    
    # Wind: Peak at night/evening (typically wind picks up at night)
    base_wind = [15, 18, 20, 18, 15, 12, 8, 5, 3, 2, 2, 2, 3, 4, 5, 8, 12, 18, 25, 30, 28, 22, 18, 15]
    
    # Load: Peaks in morning and evening
    base_load = [10, 10, 10, 10, 20, 30, 40, 50, 40, 30, 30, 30, 30, 30, 40, 60, 80, 90, 80, 60, 40, 30, 20, 10]
    
    return hours, base_solar, base_wind, base_load


def predict_with_ml(hours: int = 24, weather: Optional[Dict] = None) -> pd.DataFrame:
    """Quick prediction function using ML models."""
    forecaster = EnergyForecaster()
    return forecaster.predict(hours=hours, weather=weather)


def compare_predictions(base_profiles: Tuple, ml_predictions: pd.DataFrame) -> Dict:
    """Compare base profiles with ML predictions."""
    _, base_solar, base_wind, base_load = base_profiles
    
    comparison = {
        'load': {
            'base': sum(base_load),
            'ml': ml_predictions['Load (kW)'].sum(),
            'difference': ml_predictions['Load (kW)'].sum() - sum(base_load)
        },
        'solar': {
            'base': sum(base_solar),
            'ml': ml_predictions['Solar (kW)'].sum(),
            'difference': ml_predictions['Solar (kW)'].sum() - sum(base_solar)
        },
        'wind': {
            'base': sum(base_wind),
            'ml': ml_predictions['Wind (kW)'].sum(),
            'difference': ml_predictions['Wind (kW)'].sum() - sum(base_wind)
        }
    }
    
    return comparison


# Global forecaster instance
forecaster = EnergyForecaster()


def get_quick_forecast(hours: int = 24, weather: Optional[Dict] = None) -> pd.DataFrame:
    """Get quick forecast using global forecaster."""
    return forecaster.predict(hours=hours, weather=weather)


def train_forecaster():
    """Train the global forecaster."""
    global forecaster
    forecaster = EnergyForecaster()
    forecaster.train()
    return forecaster


if __name__ == "__main__":
    # Quick test
    print("Testing ML Forecaster...")
    
    # Train model
    forecaster = EnergyForecaster()
    forecaster.train()
    
    # Generate predictions
    predictions = forecaster.predict(hours=24)
    print("\n24-Hour Predictions:")
    print(predictions)
    
    # Evaluate
    test_data = forecaster._create_synthetic_training_data(100)
    metrics = forecaster.evaluate(test_data)
    print("\nModel Performance:")
    for target, metrics_dict in metrics.items():
        print(f"{target}: MAE={metrics_dict['MAE']:.2f}, RMSE={metrics_dict['RMSE']:.2f}, R2={metrics_dict['R2']:.3f}")

