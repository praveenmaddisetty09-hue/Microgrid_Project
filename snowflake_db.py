"""
Snowflake Database Module for Smart Microgrid Manager Pro
Provides comprehensive Snowflake integration for energy data warehousing,
analytics, and ML features.
"""

import snowflake.connector
from snowflake.connector import DictCursor
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class SnowflakeConfig:
    """Snowflake connection configuration."""
    
    def __init__(
        self,
        account: str,
        user: str,
        password: str,
        warehouse: str,
        database: str,
        schema: str = "PUBLIC",
        role: str = None,
        authenticator: str = "snowflake",
    ):
        self.account = account
        self.user = user
        self.password = password
        self.warehouse = warehouse
        self.database = database
        self.schema = schema
        self.role = role
        self.authenticator = authenticator
    
    @classmethod
    def from_env(cls) -> 'SnowflakeConfig':
        """Create config from environment variables."""
        return cls(
            account=cls._get_env("SNOWFLAKE_ACCOUNT"),
            user=cls._get_env("SNOWFLAKE_USER"),
            password=cls._get_env("SNOWFLAKE_PASSWORD"),
            warehouse=cls._get_env("SNOWFLAKE_WAREHOUSE"),
            database=cls._get_env("SNOWFLAKE_DATABASE"),
            schema=cls._get_env("SNOWFLAKE_SCHEMA", "PUBLIC"),
            role=cls._get_env("SNOWFLAKE_ROLE"),
        )
    
    @staticmethod
    def _get_env(key: str, default: str = None) -> str:
        import os
        return os.environ.get(key, default)


class SnowflakeConnection:
    """Manages Snowflake connections with connection pooling."""
    
    _pool = {}
    
    def __init__(self, config: SnowflakeConfig):
        self.config = config
    
    def get_connection(self):
        """Get a Snowflake connection."""
        cache_key = f"{self.config.database}_{self.config.schema}"
        
        if cache_key in self._pool:
            try:
                conn = self._pool[cache_key]
                if conn.is_session_alive():
                    return conn
            except:
                pass
        
        conn = snowflake.connector.connect(
            account=self.config.account,
            user=self.config.user,
            password=self.config.password,
            warehouse=self.config.warehouse,
            database=self.config.database,
            schema=self.config.schema,
            role=self.config.role,
            authenticator=self.config.authenticator,
        )
        self._pool[cache_key] = conn
        return conn
    
    @contextmanager
    def cursor(self, dict_cursor: bool = True):
        """Context manager for cursor."""
        conn = self.get_connection()
        cursor = conn.cursor(DictCursor if dict_cursor else None)
        try:
            yield cursor
            cursor.close()
        except Exception as e:
            logger.error(f"Snowflake error: {e}")
            raise


class SnowflakeMicrogridDB:
    """
    Snowflake database operations for Smart Microgrid Manager.
    Supports energy data warehousing, optimization results, and analytics.
    """
    
    def __init__(self, config: Optional[SnowflakeConfig] = None):
        """Initialize Snowflake connection."""
        if config is None:
            try:
                config = SnowflakeConfig.from_env()
                self.config = config
                self.connection = SnowflakeConnection(config)
                self.connected = True
            except Exception as e:
                logger.warning(f"Snowflake not configured: {e}")
                self.config = None
                self.connection = None
                self.connected = False
        else:
            self.config = config
            self.connection = SnowflakeConnection(config)
            self.connected = True
    
    def initialize_schema(self):
        """Create all required tables and views."""
        if not self.connected:
            logger.warning("Snowflake not connected, skipping schema initialization")
            return
        
        queries = [
            # Energy Data Warehouse - Dimension Tables
            """
            CREATE TABLE IF NOT EXISTS DIM_HUBS (
                HUB_ID INTEGER IDENTITY PRIMARY KEY,
                HUB_NAME VARCHAR(100),
                LOCATION VARCHAR(200),
                LATITUDE FLOAT,
                LONGITUDE FLOAT,
                CAPACITY_KW FLOAT,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS DIM_ENERGY_SOURCES (
                SOURCE_ID INTEGER IDENTITY PRIMARY KEY,
                SOURCE_NAME VARCHAR(50),
                SOURCE_TYPE VARCHAR(30),
                CAPACITY_KW FLOAT,
                EFFICIENCY FLOAT,
                IS_RENEWABLE BOOLEAN
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS DIM_TIME (
                TIME_ID INTEGER PRIMARY KEY,
                HOUR_OF_DAY INTEGER,
                DAY_OF_WEEK INTEGER,
                DAY_NAME VARCHAR(20),
                DAY_OF_MONTH INTEGER,
                MONTH INTEGER,
                MONTH_NAME VARCHAR(20),
                QUARTER INTEGER,
                YEAR INTEGER,
                IS_WEEKEND BOOLEAN,
                IS_PEAK_HOUR BOOLEAN
            )
            """,
            
            # Fact Tables
            """
            CREATE TABLE IF NOT EXISTS FACT_HOURLY_GENERATION (
                TIME_ID INTEGER,
                HUB_ID INTEGER,
                SOURCE_ID INTEGER,
                GENERATION_KWH FLOAT,
                COST FLOAT,
                EMISSIONS_KG FLOAT,
                EFFICIENCY FLOAT,
                WEATHER_CONDITIONS VARCHAR(50),
                RECORDED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (TIME_ID) REFERENCES DIM_TIME(TIME_ID),
                FOREIGN KEY (HUB_ID) REFERENCES DIM_HUBS(HUB_ID),
                FOREIGN KEY (SOURCE_ID) REFERENCES DIM_ENERGY_SOURCES(SOURCE_ID)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS FACT_HOURLY_CONSUMPTION (
                TIME_ID INTEGER,
                HUB_ID INTEGER,
                LOAD_KWH FLOAT,
                PEAK_DEMAND_KW,
                POWER_FACTOR FLOAT,
                RECORDED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (TIME_ID) REFERENCES DIM_TIME(TIME_ID),
                FOREIGN KEY (HUB_ID) REFERENCES DIM_HUBS(HUB_ID)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS FACT_OPTIMIZATION_RESULTS (
                RESULT_ID INTEGER IDENTITY PRIMARY KEY,
                TIME_ID INTEGER,
                HUB_ID INTEGER,
                SCENARIO_NAME VARCHAR(100),
                TOTAL_COST FLOAT,
                TOTAL_EMISSIONS_KG FLOAT,
                RENEWABLE_PERCENTAGE FLOAT,
                GRID_USAGE_KWH FLOAT,
                BATTERY_CYCLES FLOAT,
                PARAMETERS VARIANT,
                RESULTS VARIANT,
                SOLVER_TIME_SECONDS FLOAT,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (TIME_ID) REFERENCES DIM_TIME(TIME_ID),
                FOREIGN KEY (HUB_ID) REFERENCES DIM_HUBS(HUB_ID)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS FACT_CARBON_TRACKING (
                TIME_ID INTEGER,
                HUB_ID INTEGER,
                BASELINE_EMISSIONS_KG FLOAT,
                ACTUAL_EMISSIONS_KG FLOAT,
                CREDITS_EARNED FLOAT,
                CREDITS_USED FLOAT,
                NET_CREDITS FLOAT,
                CARBON_INTENSITY FLOAT,
                RECORDED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (TIME_ID) REFERENCES DIM_TIME(TIME_ID),
                FOREIGN KEY (HUB_ID) REFERENCES DIM_HUBS(HUB_ID)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS FACT_BATTERY_OPERATIONS (
                TIME_ID INTEGER,
                HUB_ID INTEGER,
                SOC_KWH FLOAT,
                CHARGE_KWH FLOAT,
                DISCHARGE_KWH FLOAT,
                EFFICIENCY FLOAT,
                DEGRADATION_COST FLOAT,
                CYCLE_COUNT FLOAT,
                RECORDED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (TIME_ID) REFERENCES DIM_TIME(TIME_ID),
                FOREIGN KEY (HUB_ID) REFERENCES DIM_HUBS(HUB_ID)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS FACT_WEATHER_DATA (
                TIME_ID INTEGER,
                HUB_ID INTEGER,
                TEMPERATURE_C FLOAT,
                HUMIDITY_PERCENT INTEGER,
                CLOUD_COVER_PERCENT INTEGER,
                WIND_SPEED_MS FLOAT,
                WIND_DIRECTION_DEG INTEGER,
                SOLAR_IRRADIANCE FLOAT,
                PRECIPITATION_MM FLOAT,
                WEATHER_CONDITION VARCHAR(50),
                RECORDED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (TIME_ID) REFERENCES DIM_TIME(TIME_ID),
                FOREIGN KEY (HUB_ID) REFERENCES DIM_HUBS(HUB_ID)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS FACT_COST_BREAKDOWN (
                TIME_ID INTEGER,
                HUB_ID INTEGER,
                ENERGY_COST FLOAT,
                DEMAND_CHARGE FLOAT,
                PEAK_PENALTY FLOAT,
                CARBON_COST FLOAT,
                TOTAL_COST FLOAT,
                CURRENCY VARCHAR(10) DEFAULT 'INR',
                RECORDED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (TIME_ID) REFERENCES DIM_TIME(TIME_ID),
                FOREIGN KEY (HUB_ID) REFERENCES DIM_HUBS(HUB_ID)
            )
            """,
            
            # ML Predictions Table
            """
            CREATE TABLE IF NOT EXISTS FACT_ML_PREDICTIONS (
                PREDICTION_ID INTEGER IDENTITY PRIMARY KEY,
                TIME_ID INTEGER,
                HUB_ID INTEGER,
                MODEL_TYPE VARCHAR(50),
                PREDICTED_LOAD_KWH FLOAT,
                ACTUAL_LOAD_KWH FLOAT,
                PREDICTION_ERROR FLOAT,
                CONFIDENCE_SCORE FLOAT,
                WEATHER_CONDITIONS VARCHAR(50),
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                FOREIGN KEY (TIME_ID) REFERENCES DIM_TIME(TIME_ID),
                FOREIGN KEY (HUB_ID) REFERENCES DIM_HUBS(HUB_ID)
            )
            """,
            
            # Materialized Views for Analytics
            """
            CREATE OR REPLACE VIEW V_DAILY_SUMMARY AS
            SELECT 
                DATE(RECORDED_AT) as DATE,
                HUB_ID,
                SUM(GENERATION_KWH) as TOTAL_GENERATION_KWH,
                SUM(COST) as TOTAL_COST,
                SUM(EMISSIONS_KG) as TOTAL_EMISSIONS_KG,
                AVG(EFFICIENCY) as AVG_EFFICIENCY
            FROM FACT_HOURLY_GENERATION
            GROUP BY DATE(RECORDED_AT), HUB_ID
            """,
            
            """
            CREATE OR REPLACE VIEW V_RENEWABLE_ANALYSIS AS
            SELECT 
                TIME_ID,
                H.GUB_NAME,
                SUM(G.GENERATION_KWH) as TOTAL_RENEWABLE_KWH,
                SUM(C.TOTAL_COST) as TOTAL_COST,
                CASE 
                    WHEN SUM(G.GENERATION_KWH) > 0 
                    THEN SUM(G.COST) / SUM(G.GENERATION_KWH)
                    ELSE 0 
                END as COST_PER_KWH
            FROM FACT_HOURLY_GENERATION G
            JOIN DIM_HUBS H ON G.HUB_ID = H.HUB_ID
            LEFT JOIN FACT_COST_BREAKDOWN C ON G.TIME_ID = C.TIME_ID AND G.HUB_ID = C.HUB_ID
            WHERE EXISTS (
                SELECT 1 FROM DIM_ENERGY_SOURCES S 
                WHERE S.SOURCE_ID = G.SOURCE_ID AND S.IS_RENEWABLE = TRUE
            )
            GROUP BY TIME_ID, HUB_NAME
            """,
        ]
        
        with self.connection.cursor() as cursor:
            for query in queries:
                try:
                    cursor.execute(query)
                    logger.info(f"Executed: {query[:60]}...")
                except Exception as e:
                    logger.error(f"Error executing query: {e}")
    
    def populate_time_dimension(self):
        """Populate time dimension table."""
        if not self.connected:
            return
        
        time_data = []
        for hour in range(24):
            for day in range(1, 32):
                for month in range(1, 13):
                    for year in [2024, 2025]:
                        try:
                            dt = datetime(year, month, day, hour)
                            time_data.append({
                                'TIME_ID': int(f"{year}{month:02d}{day:02d}{hour:02d}"),
                                'HOUR_OF_DAY': hour,
                                'DAY_OF_WEEK': dt.weekday(),
                                'DAY_NAME': dt.strftime('%A'),
                                'DAY_OF_MONTH': day,
                                'MONTH': month,
                                'MONTH_NAME': dt.strftime('%B'),
                                'QUARTER': (month - 1) // 3 + 1,
                                'YEAR': year,
                                'IS_WEEKEND': dt.weekday() >= 5,
                                'IS_PEAK_HOUR': 17 <= hour <= 21,
                            })
                        except:
                            pass
        
        df = pd.DataFrame(time_data)
        
        with self.connection.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO DIM_TIME VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                df.values.tolist()
            )
    
    # CRUD Operations for Optimization Results
    def save_optimization_result(
        self,
        time_id: int,
        hub_id: int,
        scenario_name: str,
        total_cost: float,
        total_emissions: float,
        renewable_percentage: float,
        total_grid_usage: float,
        parameters: Dict,
        results: List[Dict],
        battery_cycles: float = 0.0,
        solver_time_seconds: float = 0.0,
    ):
        """Save optimization result to Snowflake."""
        if not self.connected:
            return
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO FACT_OPTIMIZATION_RESULTS (
                    TIME_ID, HUB_ID, SCENARIO_NAME, TOTAL_COST, TOTAL_EMISSIONS_KG,
                    RENEWABLE_PERCENTAGE, GRID_USAGE_KWH, BATTERY_CYCLES,
                    PARAMETERS, RESULTS, SOLVER_TIME_SECONDS
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                time_id, hub_id, scenario_name, total_cost, total_emissions,
                renewable_percentage, total_grid_usage, battery_cycles,
                json.dumps(parameters), json.dumps(results), solver_time_seconds,
            ))
    
    def get_optimization_history(
        self, 
        hub_id: int = None, 
        start_date: datetime = None, 
        end_date: datetime = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """Get optimization history from Snowflake."""
        if not self.connected:
            return pd.DataFrame()
        
        query = """
            SELECT * FROM FACT_OPTIMIZATION_RESULTS
            WHERE 1=1
        """
        params = []
        
        if hub_id:
            query += " AND HUB_ID = %s"
            params.append(hub_id)
        
        if start_date:
            query += " AND CREATED_AT >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND CREATED_AT <= %s"
            params.append(end_date)
        
        query += f" ORDER BY CREATED_AT DESC LIMIT {limit}"
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return pd.DataFrame([dict(row) for row in rows])
    
    # Energy Generation Operations
    def save_hourly_generation(
        self,
        time_id: int,
        hub_id: int,
        source_id: int,
        generation_kwh: float,
        cost: float,
        emissions_kg: float,
        efficiency: float,
        weather_conditions: str = None,
    ):
        """Save hourly generation data."""
        if not self.connected:
            return
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO FACT_HOURLY_GENERATION (
                    TIME_ID, HUB_ID, SOURCE_ID, GENERATION_KWH, COST,
                    EMISSIONS_KG, EFFICIENCY, WEATHER_CONDITIONS
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                time_id, hub_id, source_id, generation_kwh, cost,
                emissions_kg, efficiency, weather_conditions,
            ))
    
    def get_generation_summary(
        self, 
        hub_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """Get generation summary for date range."""
        if not self.connected:
            return pd.DataFrame()
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    t.HOUR_OF_DAY,
                    s.SOURCE_NAME,
                    SUM(g.GENERATION_KWH) as TOTAL_GENERATION,
                    AVG(g.EFFICIENCY) as AVG_EFFICIENCY,
                    SUM(g.COST) as TOTAL_COST
                FROM FACT_HOURLY_GENERATION g
                JOIN DIM_TIME t ON g.TIME_ID = t.TIME_ID
                JOIN DIM_ENERGY_SOURCES s ON g.SOURCE_ID = s.SOURCE_ID
                WHERE g.HUB_ID = %s 
                    AND g.CREATED_AT BETWEEN %s AND %s
                GROUP BY t.HOUR_OF_DAY, s.SOURCE_NAME
                ORDER BY t.HOUR_OF_DAY
            """, (hub_id, start_date, end_date))
            
            return pd.DataFrame([dict(row) for row in cursor.fetchall()])
    
    # Carbon Tracking Operations
    def save_carbon_tracking(
        self,
        time_id: int,
        hub_id: int,
        baseline_emissions_kg: float,
        actual_emissions_kg: float,
        credits_earned: float,
        credits_used: float,
        net_credits: float,
        carbon_intensity: float = 0.82,
    ):
        """Save carbon tracking data."""
        if not self.connected:
            return
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO FACT_CARBON_TRACKING (
                    TIME_ID, HUB_ID, BASELINE_EMISSIONS_KG, ACTUAL_EMISSIONS_KG,
                    CREDITS_EARNED, CREDITS_USED, NET_CREDITS, CARBON_INTENSITY
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                time_id, hub_id, baseline_emissions_kg, actual_emissions_kg,
                credits_earned, credits_used, net_credits, carbon_intensity,
            ))
    
    def get_carbon_summary(
        self, 
        hub_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict:
        """Get carbon emissions summary."""
        if not self.connected:
            return {}
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    SUM(BASELINE_EMISSIONS_KG) as TOTAL_BASELINE,
                    SUM(ACTUAL_EMISSIONS_KG) as TOTAL_ACTUAL,
                    SUM(CREDITS_EARNED) as TOTAL_CREDITS_EARNED,
                    SUM(CREDITS_USED) as TOTAL_CREDITS_USED,
                    SUM(NET_CREDITS) as NET_CREDITS
                FROM FACT_CARBON_TRACKING
                WHERE HUB_ID = %s AND RECORDED_AT BETWEEN %s AND %s
            """, (hub_id, start_date, end_date))
            
            row = cursor.fetchone()
            return dict(row) if row else {}
    
    # Cost Analysis Operations
    def save_cost_breakdown(
        self,
        time_id: int,
        hub_id: int,
        energy_cost: float,
        demand_charge: float = 0.0,
        peak_penalty: float = 0.0,
        carbon_cost: float = 0.0,
        total_cost: float = None,
    ):
        """Save cost breakdown data."""
        if not self.connected:
            return
        
        total = total_cost or (energy_cost + demand_charge + peak_penalty + carbon_cost)
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO FACT_COST_BREAKDOWN (
                    TIME_ID, HUB_ID, ENERGY_COST, DEMAND_CHARGE,
                    PEAK_PENALTY, CARBON_COST, TOTAL_COST
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                time_id, hub_id, energy_cost, demand_charge,
                peak_penalty, carbon_cost, total,
            ))
    
    def get_cost_analysis(
        self, 
        hub_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """Get detailed cost analysis."""
        if not self.connected:
            return pd.DataFrame()
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    t.HOUR_OF_DAY,
                    SUM(c.ENERGY_COST) as ENERGY_COST,
                    SUM(c.DEMAND_CHARGE) as DEMAND_CHARGE,
                    SUM(c.PEAK_PENALTY) as PEAK_PENALTY,
                    SUM(c.CARBON_COST) as CARBON_COST,
                    SUM(c.TOTAL_COST) as TOTAL_COST
                FROM FACT_COST_BREAKDOWN c
                JOIN DIM_TIME t ON c.TIME_ID = t.TIME_ID
                WHERE c.HUB_ID = %s AND c.RECORDED_AT BETWEEN %s AND %s
                GROUP BY t.HOUR_OF_DAY
                ORDER BY t.HOUR_OF_DAY
            """, (hub_id, start_date, end_date))
            
            return pd.DataFrame([dict(row) for row in cursor.fetchall()])
    
    # ML Predictions Operations
    def save_ml_prediction(
        self,
        time_id: int,
        hub_id: int,
        model_type: str,
        predicted_load_kwh: float,
        actual_load_kwh: float,
        prediction_error: float,
        confidence_score: float,
        weather_conditions: str = None,
    ):
        """Save ML prediction data."""
        if not self.connected:
            return
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO FACT_ML_PREDICTIONS (
                    TIME_ID, HUB_ID, MODEL_TYPE, PREDICTED_LOAD_KWH,
                    ACTUAL_LOAD_KWH, PREDICTION_ERROR, CONFIDENCE_SCORE,
                    WEATHER_CONDITIONS
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                time_id, hub_id, model_type, predicted_load_kwh,
                actual_load_kwh, prediction_error, confidence_score,
                weather_conditions,
            ))
    
    def get_ml_accuracy(self, hub_id: int, model_type: str = None) -> Dict:
        """Get ML model accuracy metrics."""
        if not self.connected:
            return {}
        
        query = """
            SELECT 
                MODEL_TYPE,
                COUNT(*) as SAMPLE_COUNT,
                AVG(PREDICTION_ERROR) as AVG_ERROR,
                AVG(CONFIDENCE_SCORE) as AVG_CONFIDENCE,
                MIN(PREDICTION_ERROR) as MIN_ERROR,
                MAX(PREDICTION_ERROR) as MAX_ERROR
            FROM FACT_ML_PREDICTIONS
            WHERE HUB_ID = %s
        """
        params = [hub_id]
        
        if model_type:
            query += " AND MODEL_TYPE = %s"
            params.append(model_type)
        
        query += " GROUP BY MODEL_TYPE"
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Weather Data Operations
    def save_weather_data(
        self,
        time_id: int,
        hub_id: int,
        temperature_c: float,
        humidity_percent: int,
        cloud_cover_percent: int,
        wind_speed_ms: float,
        wind_direction_deg: int,
        solar_irradiance: float,
        precipitation_mm: float,
        weather_condition: str,
    ):
        """Save weather data."""
        if not self.connected:
            return
        
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO FACT_WEATHER_DATA (
                    TIME_ID, HUB_ID, TEMPERATURE_C, HUMIDITY_PERCENT,
                    CLOUD_COVER_PERCENT, WIND_SPEED_MS, WIND_DIRECTION_DEG,
                    SOLAR_IRRADIANCE, PRECIPITATION_MM, WEATHER_CONDITION
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                time_id, hub_id, temperature_c, humidity_percent,
                cloud_cover_percent, wind_speed_ms, wind_direction_deg,
                solar_irradiance, precipitation_mm, weather_condition,
            ))
    
    # Analytics & Reporting
    def get_dashboard_summary(self, hub_id: int) -> Dict:
        """Get dashboard summary metrics."""
        if not self.connected:
            return {}
        
        with self.connection.cursor() as cursor:
            # Get generation summary
            cursor.execute("""
                SELECT 
                    SUM(GENERATION_KWH) as TODAY_GENERATION,
                    SUM(COST) as TODAY_COST,
                    SUM(EMISSIONS_KG) as TODAY_EMISSIONS,
                    AVG(EFFICIENCY) as AVG_EFFICIENCY
                FROM FACT_HOURLY_GENERATION
                WHERE HUB_ID = %s AND RECORDED_AT >= CURRENT_DATE()
            """, (hub_id,))
            
            gen_summary = dict(cursor.fetchone()) if cursor.rowcount > 0 else {}
            
            # Get latest optimization result
            cursor.execute("""
                SELECT 
                    TOTAL_COST, TOTAL_EMISSIONS_KG, RENEWABLE_PERCENTAGE,
                    GRID_USAGE_KWH, BATTERY_CYCLES
                FROM FACT_OPTIMIZATION_RESULTS
                WHERE HUB_ID = %s
                ORDER BY CREATED_AT DESC
                LIMIT 1
            """, (hub_id,))
            
            opt_result = dict(cursor.fetchone()) if cursor.rowcount > 0 else {}
            
            # Get carbon summary
            cursor.execute("""
                SELECT 
                    SUM(BASELINE_EMISSIONS_KG) as BASELINE,
                    SUM(ACTUAL_EMISSIONS_KG) as ACTUAL,
                    SUM(NET_CREDITS) as NET_CREDITS
                FROM FACT_CARBON_TRACKING
                WHERE HUB_ID = %s AND RECORDED_AT >= CURRENT_DATE()
            """, (hub_id,))
            
            carbon_summary = dict(cursor.fetchone()) if cursor.rowcount > 0 else {}
            
            return {
                'generation': gen_summary,
                'optimization': opt_result,
                'carbon': carbon_summary,
            }
    
    def run_ad_hoc_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Run custom SQL query."""
        if not self.connected:
            return pd.DataFrame()
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return pd.DataFrame([dict(row) for row in rows])
    
    def close(self):
        """Close all connections."""
        if self.connection:
            for conn in self._pool.values():
                try:
                    conn.close()
                except:
                    pass
            self._pool.clear()


# Global instance
_snowflake_db = None


def get_snowflake_db() -> SnowflakeMicrogridDB:
    """Get global Snowflake database instance."""
    global _snowflake_db
    if _snowflake_db is None:
        try:
            config = SnowflakeConfig.from_env()
            _snowflake_db = SnowflakeMicrogridDB(config)
        except Exception as e:
            logger.warning(f"Failed to initialize Snowflake: {e}")
            _snowflake_db = SnowflakeMicrogridDB(None)
    return _snowflake_db


if __name__ == "__main__":
    # Test connection
    print("Testing Snowflake connection...")
    
    try:
        db = get_snowflake_db()
        if db.connected:
            print("✅ Connected to Snowflake!")
            
            # Initialize schema
            print("Initializing schema...")
            db.initialize_schema()
            print("✅ Schema created!")
            
            # Get dashboard summary
            summary = db.get_dashboard_summary(hub_id=1)
            print(f"📊 Dashboard Summary: {summary}")
        else:
            print("⚠️ Snowflake not configured. Set environment variables:")
            print("   - SNOWFLAKE_ACCOUNT")
            print("   - SNOWFLAKE_USER")
            print("   - SNOWFLAKE_PASSWORD")
            print("   - SNOWFLAKE_WAREHOUSE")
            print("   - SNOWFLAKE_DATABASE")
    except Exception as e:
        print(f"❌ Error: {e}")

