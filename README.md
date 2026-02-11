# Smart Microgrid Manager Pro

## Optimal Grid Solutions - Intelligent Energy Management System

A comprehensive web-based application for smart microgrid management, featuring real-time energy optimization, wind power integration, battery storage management, carbon emissions tracking, and AI-powered forecasting.

---

## 🎯 Project Overview

This project implements an **Intelligent Microgrid Management System** that optimizes energy distribution across multiple sources (solar, wind, grid, battery) while minimizing costs and carbon emissions. The system uses linear programming (LP) techniques for optimization and machine learning for load forecasting.

### Key Features

- **⚡ Real-time Energy Optimization** - Linear programming-based optimization using PuLP solver
- **🌬️ Wind Power Integration** - Dynamic wind energy modeling with weather scenarios
- **🔋 Battery Storage Management** - SOC (State of Charge) tracking and optimization
- **💰 Cost Analytics Dashboard** - Detailed cost breakdown and savings analysis
- **🌍 Carbon Emissions Tracking** - Carbon footprint calculation and reduction insights
- **🤖 ML Forecasting** - Machine learning-based load prediction using scikit-learn
- **🚗 EV Charging Simulation** - Electric vehicle charging load management
- **📊 Multiple Report Formats** - HTML, Excel, PDF, and Text report generation
- **🎨 Theme System** - Multiple color themes (Light, Dark, Corporate, Nature, Solar)

---

## 🏗️ Architecture

```
Smart Microgrid Manager Pro
├── app.py                 # Main Streamlit application
├── logic.py               # Optimization algorithms
├── auth.py                # Authentication & user management
├── database.py            # SQLite database operations
├── reports.py             # Report generation (HTML/Excel/PDF)
├── weather.py             # Weather integration
├── forecast.py           # ML-based forecasting
├── scheduling.py          # Advanced scheduling algorithms
├── notifications.py       # Alert system
├── branding.py           # Branding & theming
├── requirements.txt       # Python dependencies
└── README.md            # This file
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip or conda package manager

### Installation

```bash
# Clone or navigate to project directory
cd smart-microgrid-manager

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Start the Streamlit application
streamlit run app.py

# Access at: http://localhost:8501
```

### Default Credentials

| Role  | Username | Password  |
|-------|----------|-----------|
| Admin | admin    | microgrid |
| User  | user     | user123   |

---

## 📁 Project Structure

### Core Modules

#### 1. **app.py** - Main Application
- Streamlit UI configuration
- Sidebar controls for system parameters
- Dashboard with 8 main tabs
- Theme switching system

#### 2. **logic.py** - Optimization Engine
- `run_optimization()` - Main optimization function using PuLP
- `calculate_baseline_emissions()` - Baseline carbon calculation
- `generate_scenario_comparison()` - Multi-scenario analysis

#### 3. **auth.py** - Security Module
- User authentication with password hashing (SHA-256)
- Session management with timeout
- Account lockout after failed attempts
- Role-based access control (Admin/User)

#### 4. **database.py** - Data Layer
- SQLite database initialization
- Optimization results storage
- Scenario management
- Alert tracking
- Carbon credits management

#### 5. **reports.py** - Report Generation
- HTML reports with Plotly charts
- Excel spreadsheets (openpyxl)
- PDF reports (reportlab)
- Text reports

#### 6. **weather.py** - Weather Integration
- Weather scenarios (Sunny, Cloudy, Rainy, Stormy)
- Solar/wind generation multipliers
- Weather caching system

#### 7. **forecast.py** - ML Forecasting
- EnergyForecaster class with scikit-learn
- Random Forest regression model
- Load prediction comparison

#### 8. **scheduling.py** - Advanced Scheduling
- Multi-objective optimization
- Peak shaving
- Battery degradation scheduling
- Load shifting
- Demand response integration

#### 9. **notifications.py** - Alert System
- In-app notifications
- Grid overload alerts
- Cost threshold warnings

#### 10. **branding.py** - Branding Module
- Company branding settings
- SVG logo integration
- Theme CSS generation

---

## 📊 Features Breakdown

### Energy Optimization

The optimization engine uses **Linear Programming** with the PuLP library:

```python
# Objective: Minimize total cost
minimize: sum(price[i] * grid[i] for i in hours)

# Subject to:
# - Power balance: load[i] = solar[i] + wind[i] + grid[i] + battery_charge[i] - battery_discharge[i]
# - Battery limits: 0 <= battery_soc[i] <= battery_capacity
# - Grid limits: grid[i] >= 0 (can be adjusted for export)
```

### Weather Scenarios

| Scenario    | Solar Multiplier | Wind Multiplier | Description          |
|-------------|------------------|-----------------|----------------------|
| ☀️ Sunny    | 1.0             | 0.8            | Optimal conditions   |
| ⛅ Cloudy   | 0.6             | 0.9            | Reduced solar       |
| 🌧️ Rainy    | 0.3             | 0.7            | Low generation      |
| ⛈️ Stormy   | 0.1             | 1.2            | High wind, low solar|

### Battery Management

- State of Charge (SOC) tracking
- Minimum reserve threshold (configurable, default 10%)
- Round-trip efficiency (default 95%)
- Degradation-aware scheduling

### Carbon Tracking

- Carbon intensity calculation (default 0.82 kg CO2/kWh)
- Baseline vs. optimized comparison
- Carbon credits system
- Emissions savings reporting

---

## 🛠️ Technical Implementation

### Dependencies

```
streamlit>=1.28.0       # Web framework
pandas>=2.0.0          # Data manipulation
plotly>=5.18.0         # Interactive charts
numpy>=1.24.0          # Numerical computing
PuLP>=2.7.0            # Linear programming
scikit-learn>=1.3.0    # ML forecasting
openpyxl>=3.1.0        # Excel reports
reportlab>=4.0.0       # PDF reports
```

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT,
    email TEXT,
    failed_attempts INTEGER,
    lockout_info JSON
);

-- Optimization results
CREATE TABLE optimization_results (
    id INTEGER PRIMARY KEY,
    scenario_name TEXT,
    total_cost REAL,
    total_emissions REAL,
    parameters JSON,
    results JSON,
    created_at TIMESTAMP
);

-- Alerts
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    type TEXT,
    message TEXT,
    severity TEXT,
    resolved BOOLEAN
);
```

---

## 📈 Performance Metrics

### Optimization Results

| Metric               | Description                          |
|---------------------|--------------------------------------|
| Total Cost          | Daily energy cost (₹)               |
| Total Emissions     | Daily CO2 emissions (kg)             |
| Renewable Share     | Percentage of renewable energy      |
| Grid Usage          | Total grid electricity (kWh)       |
| Max Battery SOC     | Peak battery storage (kWh)           |

### Savings Analysis

- **Cost Savings**: Compared to baseline (all load from grid at peak price)
- **Carbon Reduction**: Percentage decrease in emissions vs. baseline
- **Renewable Penetration**: Hourly and daily renewable energy percentage

---

## 🎨 Theme System

The application supports 5 themes:

| Theme          | Primary Color | Description        |
|----------------|---------------|--------------------|
| ☀️ Light       | #2ecc71       | Default light theme|
| 🌙 Dark        | #3498db       | Dark professional  |
| 💼 Corporate   | #1a5276       | Corporate blue    |
| 🌿 Nature      | #27ae60       | Nature green      |
| ☀️ Solar Gold  | #d4ac0d       | Solar gold accent  |

---

## 📋 Use Cases

### 1. **Residential Microgrid**
- Small-scale solar + battery
- Cost optimization focus
- EV charging support

### 2. **Commercial Building**
- Larger capacity requirements
- Demand charge management
- Peak shaving strategies

### 3. **Campus/Industrial**
- Multi-source optimization
- Advanced scheduling
- Carbon neutrality goals

---

## 🔒 Security Features

- **Password hashing** with salt (SHA-256)
- **Session timeout** (30 minutes default)
- **Account lockout** (5 failed attempts, 15 min lockout)
- **Activity logging** with timestamps
- **Role-based access** (Admin/User)

---

## 📝 Academic Context

This project demonstrates:

1. **Operations Research**: Linear programming for optimization
2. **Machine Learning**: Random Forest regression for forecasting
3. **Database Systems**: SQLite with full CRUD operations
4. **Web Development**: Streamlit dashboard creation
5. **Data Visualization**: Plotly interactive charts
6. **Software Engineering**: Modular architecture, authentication

---

## 🤝 Contributing

For academic purposes, this project can be extended with:

- Additional optimization algorithms
- More ML models for forecasting
- Real-time data integration (APIs)
- Mobile application
- Cloud deployment

---

## 📄 License

This project is for educational and research purposes.

---

## 👨‍💻 Author

**Optimal Grid Solutions**

For questions or support, please refer to the project documentation.

---

## 🔗 References

- [Streamlit Documentation](https://docs.streamlit.io)
- [PuLP Documentation](https://coin-or.github.io/pulp/)
- [Plotly Python](https://plotly.com/python/)
- [scikit-learn](https://scikit-learn.org/)

---

*Last Updated: 2024*

