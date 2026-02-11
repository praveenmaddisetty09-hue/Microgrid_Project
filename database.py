"""
Database Module for Smart Microgrid Manager Pro
Handles all database operations using SQLite.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import json
import os

# Database file
DB_FILE = "microgrid_data.db"


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            email TEXT,
            created_at TEXT,
            last_login TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Create optimization results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS optimization_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            scenario_name TEXT,
            date TEXT,
            total_cost REAL,
            total_emissions REAL,
            renewable_percentage REAL,
            total_grid_usage REAL,
            battery_size REAL,
            parameters TEXT,
            results TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create historical data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            hour INTEGER,
            solar REAL,
            wind REAL,
            load REAL,
            grid_usage REAL,
            battery_soc REAL,
            price REAL,
            cost REAL,
            emissions REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create scenarios table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            description TEXT,
            parameters TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create EV charging records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ev_charging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            hour INTEGER,
            ev_load REAL,
            charging_cost REAL,
            energy_delivered REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT,
            message TEXT,
            severity TEXT,
            date TEXT,
            hour INTEGER,
            resolved INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create carbon credits table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carbon_credits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            baseline_emissions REAL,
            actual_emissions REAL,
            credits_earned REAL,
            credits_used REAL,
            net_credits REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


def save_optimization_result(user_id: Optional[int], scenario_name: str, 
                             total_cost: float, total_emissions: float,
                             renewable_percentage: float, total_grid_usage: float,
                             battery_size: float, parameters: Dict, results: Dict):
    """Save optimization result to database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO optimization_results 
        (user_id, scenario_name, date, total_cost, total_emissions, 
         renewable_percentage, total_grid_usage, battery_size, parameters, results)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        scenario_name,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_cost,
        total_emissions,
        renewable_percentage,
        total_grid_usage,
        battery_size,
        json.dumps(parameters),
        json.dumps(results)
    ))
    
    conn.commit()
    conn.close()


def get_optimization_history(limit: int = 100) -> pd.DataFrame:
    """Get optimization history."""
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT * FROM optimization_results 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', conn, params=(limit,))
    conn.close()
    return df


def save_historical_data(data: List[Dict]):
    """Save historical hourly data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    for item in data:
        cursor.execute('''
            INSERT INTO historical_data 
            (date, hour, solar, wind, load, grid_usage, battery_soc, price, cost, emissions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.get("date", datetime.now().strftime("%Y-%m-%d")),
            item.get("hour", 0),
            item.get("solar", 0),
            item.get("wind", 0),
            item.get("load", 0),
            item.get("grid_usage", 0),
            item.get("battery_soc", 0),
            item.get("price", 0),
            item.get("cost", 0),
            item.get("emissions", 0)
        ))
    
    conn.commit()
    conn.close()


def get_historical_data(start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> pd.DataFrame:
    """Get historical data for date range."""
    conn = get_connection()
    
    query = "SELECT * FROM historical_data"
    params = []
    
    if start_date and end_date:
        query += " WHERE date BETWEEN ? AND ?"
        params = [start_date, end_date]
    elif start_date:
        query += " WHERE date >= ?"
        params = [start_date]
    elif end_date:
        query += " WHERE date <= ?"
        params = [end_date]
    
    query += " ORDER BY date, hour"
    
    df = pd.read_sql_query(query, conn, params=params if params else None)
    conn.close()
    return df


def save_scenario(user_id: Optional[int], name: str, description: str, 
                  parameters: Dict):
    """Save a scenario."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO scenarios (user_id, name, description, parameters)
        VALUES (?, ?, ?, ?)
    ''', (user_id, name, description, json.dumps(parameters)))
    
    conn.commit()
    conn.close()


def get_scenarios(user_id: Optional[int] = None) -> pd.DataFrame:
    """Get saved scenarios."""
    conn = get_connection()
    
    if user_id:
        df = pd.read_sql_query('''
            SELECT * FROM scenarios WHERE user_id = ?
            ORDER BY created_at DESC
        ''', conn, params=(user_id,))
    else:
        df = pd.read_sql_query('''
            SELECT * FROM scenarios ORDER BY created_at DESC
        ''', conn)
    
    conn.close()
    return df


def delete_scenario(scenario_id: int) -> bool:
    """Delete a scenario."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM scenarios WHERE id = ?', (scenario_id,))
    conn.commit()
    conn.close()
    
    return cursor.rowcount > 0


def save_ev_charging_data(data: List[Dict]):
    """Save EV charging data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    for item in data:
        cursor.execute('''
            INSERT INTO ev_charging (date, hour, ev_load, charging_cost, energy_delivered)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            item.get("date", datetime.now().strftime("%Y-%m-%d")),
            item.get("hour", 0),
            item.get("ev_load", 0),
            item.get("charging_cost", 0),
            item.get("energy_delivered", 0)
        ))
    
    conn.commit()
    conn.close()


def get_ev_charging_data(start_date: Optional[str] = None, 
                         end_date: Optional[str] = None) -> pd.DataFrame:
    """Get EV charging data."""
    conn = get_connection()
    
    query = "SELECT * FROM ev_charging"
    params = []
    
    if start_date and end_date:
        query += " WHERE date BETWEEN ? AND ?"
        params = [start_date, end_date]
    elif start_date:
        query += " WHERE date >= ?"
        params = [start_date]
    elif end_date:
        query += " WHERE date <= ?"
        params = [end_date]
    
    query += " ORDER BY date, hour"
    
    df = pd.read_sql_query(query, conn, params=params if params else None)
    conn.close()
    return df


def save_alert(alert_type: str, message: str, severity: str, 
               date: Optional[str] = None, hour: Optional[int] = None):
    """Save an alert."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO alerts (alert_type, message, severity, date, hour)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        alert_type,
        message,
        severity,
        date or datetime.now().strftime("%Y-%m-%d"),
        hour or datetime.now().hour
    ))
    
    conn.commit()
    conn.close()


def get_alerts(resolved: Optional[bool] = None, limit: int = 100) -> pd.DataFrame:
    """Get alerts."""
    conn = get_connection()
    
    query = "SELECT * FROM alerts"
    
    if resolved is not None:
        query += " WHERE resolved = ?"
        df = pd.read_sql_query(query + " ORDER BY created_at DESC LIMIT ?", 
                              conn, params=(int(resolved), limit))
    else:
        df = pd.read_sql_query(query + " ORDER BY created_at DESC LIMIT ?", 
                              conn, params=(limit,))
    
    conn.close()
    return df


def resolve_alert(alert_id: int) -> bool:
    """Mark an alert as resolved."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE alerts SET resolved = 1 WHERE id = ?', (alert_id,))
    conn.commit()
    conn.close()
    
    return cursor.rowcount > 0


def save_carbon_credits(baseline_emissions: float, actual_emissions: float,
                        credits_earned: float, credits_used: float):
    """Save carbon credits record."""
    conn = get_connection()
    cursor = conn.cursor()
    
    net_credits = credits_earned - credits_used
    
    cursor.execute('''
        INSERT INTO carbon_credits 
        (date, baseline_emissions, actual_emissions, credits_earned, credits_used, net_credits)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d"),
        baseline_emissions,
        actual_emissions,
        credits_earned,
        credits_used,
        net_credits
    ))
    
    conn.commit()
    conn.close()


def get_carbon_credits(start_date: Optional[str] = None, 
                       end_date: Optional[str] = None) -> pd.DataFrame:
    """Get carbon credits history."""
    conn = get_connection()
    
    query = "SELECT * FROM carbon_credits"
    params = []
    
    if start_date and end_date:
        query += " WHERE date BETWEEN ? AND ?"
        params = [start_date, end_date]
    elif start_date:
        query += " WHERE date >= ?"
        params = [start_date]
    elif end_date:
        query += " WHERE date <= ?"
        params = [end_date]
    
    query += " ORDER BY date"
    
    df = pd.read_sql_query(query, conn, params=params if params else None)
    conn.close()
    return df


def get_summary_stats() -> Dict:
    """Get summary statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total optimization runs
    cursor.execute('SELECT COUNT(*) FROM optimization_results')
    stats['total_runs'] = cursor.fetchone()[0]
    
    # Today's runs
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('SELECT COUNT(*) FROM optimization_results WHERE date LIKE ?', (f"{today}%",))
    stats['today_runs'] = cursor.fetchone()[0]
    
    # Total alerts
    cursor.execute('SELECT COUNT(*) FROM alerts WHERE resolved = 0')
    stats['unresolved_alerts'] = cursor.fetchone()[0]
    
    # Recent data points
    cursor.execute('SELECT COUNT(*) FROM historical_data')
    stats['data_points'] = cursor.fetchone()[0]
    
    conn.close()
    
    return stats


def cleanup_old_data(days: int = 30):
    """Remove data older than specified days."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    cursor.execute('DELETE FROM historical_data WHERE date < ?', (cutoff_date,))
    deleted_history = cursor.rowcount
    
    cursor.execute('DELETE FROM alerts WHERE date < ? AND resolved = 1', (cutoff_date,))
    deleted_alerts = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return deleted_history, deleted_alerts


# Initialize database on import
if not os.path.exists(DB_FILE):
    init_database()
else:
    # Check if tables exist, if not initialize
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone() is None:
            init_database()
        conn.close()
    except:
        init_database()

