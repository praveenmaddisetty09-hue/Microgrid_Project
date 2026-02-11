import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from logic import run_optimization, generate_scenario_comparison, OptimizationSummary
from auth import (init_session_state, login_page, logout, show_user_menu, 
                  show_admin_panel, show_profile_page, authenticate, create_user, 
                  list_users, delete_user, check_session_timeout, update_activity,
                  record_session_activity)
from database import (init_database, save_optimization_result, get_optimization_history,
                      save_historical_data, get_historical_data, save_scenario, get_scenarios,
                      save_alert, get_alerts, resolve_alert, save_carbon_credits, 
                      get_carbon_credits, get_summary_stats)
from notifications import (init_notifications, show_notification_center, 
                          show_notification_settings, get_unread_count, create_notification)
from forecast import (EnergyForecaster, get_quick_forecast, generate_base_profiles,
                      compare_predictions)
from weather import (generate_weather_scenarios, apply_weather_to_profiles,
                     get_weather_alerts)
from reports import generate_quick_report, generate_text_report, EnhancedReportGenerator
from branding import COMPANY_BRANDING, SVG_LOGO_SMALL, get_branding_css
from scheduling import OptimalScheduler, SchedulingParameters
import numpy as np
from datetime import datetime, timedelta
import json
import io

# For file upload handling
import tempfile
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Smart Microgrid Manager Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME SETTINGS ---
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'light'

# Theme definitions with CSS variables
THEMES = {
    'light': {
        'name': 'Light',
        'primary': '#2ecc71',
        'secondary': '#3498db',
        'background': '#ffffff',
        'secondary_bg': '#f0f2f6',
        'text': '#2c3e50',
        'text_secondary': '#666666',
        'metric_value': '#1f77b4',
        'card_bg': '#f0f2f6'
    },
    'dark': {
        'name': 'Dark Professional',
        'primary': '#3498db',
        'secondary': '#2ecc71',
        'background': '#1e1e1e',
        'secondary_bg': '#2d2d2d',
        'text': '#ffffff',
        'text_secondary': '#a0a0a0',
        'metric_value': '#4ade80',
        'card_bg': '#2d2d2d'
    },
    'corporate_blue': {
        'name': 'Corporate Blue',
        'primary': '#1a5276',
        'secondary': '#2874a6',
        'background': '#f8f9fa',
        'secondary_bg': '#ffffff',
        'text': '#2c3e50',
        'text_secondary': '#5d6d7e',
        'metric_value': '#1a5276',
        'card_bg': '#e8f4f8'
    },
    'nature_green': {
        'name': 'Nature Green',
        'primary': '#27ae60',
        'secondary': '#229954',
        'background': '#f4fdf4',
        'secondary_bg': '#ffffff',
        'text': '#1e5f2e',
        'text_secondary': '#27ae60',
        'metric_value': '#27ae60',
        'card_bg': '#e8f5e9'
    },
    'solar_gold': {
        'name': 'Solar Gold',
        'primary': '#d4ac0d',
        'secondary': '#f39c12',
        'background': '#fef9e7',
        'secondary_bg': '#ffffff',
        'text': '#7d6608',
        'text_secondary': '#9a7d0a',
        'metric_value': '#d4ac0d',
        'card_bg': '#fcf3cf'
    }
}

# --- CUSTOM CSS ---
def get_custom_css():
    """Generate custom CSS based on selected theme."""
    theme_key = st.session_state.get('theme', 'light')
    theme = THEMES.get(theme_key, THEMES['light'])
    
    return f"""
<style>
    /* Base Theme Styles */
    .stApp {{
        background-color: {theme['background']};
        color: {theme['text']};
    }}
    
    /* Metric Cards */
    .metric-card {{
        background-color: {theme['card_bg']};
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid {theme['secondary']}20;
    }}
    .metric-value {{
        font-size: 24px;
        font-weight: bold;
        color: {theme['metric_value']};
    }}
    .metric-label {{
        font-size: 14px;
        color: {theme['text_secondary']};
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {theme['secondary_bg']};
    }}
    
    /* Headers */
    h1, h2, h3 {{
        color: {theme['primary']};
    }}
    
    /* Buttons */
    .stButton > button {{
        background: linear-gradient(90deg, {theme['primary']} 0%, {theme['secondary']} 100%);
        color: white;
        border-radius: 8px;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {theme['secondary_bg']};
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {theme['text']};
    }}
    
    /* Cards and containers */
    .css-1r6slb0, .css-1cpxqw2 {{
        background-color: {theme['secondary_bg']};
        border-radius: 10px;
        padding: 20px;
    }}
</style>
"""

st.markdown(get_custom_css(), unsafe_allow_html=True)

# --- INITIALIZATION ---
init_session_state()
init_database()
init_notifications()

# Check for profile page display
if st.session_state.get("show_profile", False):
    show_profile_page()
    st.stop()

# --- AUTHENTICATION CHECK ---
if not st.session_state.get("authenticated", False):
    login_page()
    st.stop()

# --- SIDEBAR (USER CONTROLS) ---
with st.sidebar:
    st.header("⚙️ System Control Panel")
    
    # Theme Selection
    st.subheader("🎨 Theme")
    theme_options = {
        'light': '☀️ Light',
        'dark': '🌙 Dark Professional',
        'corporate_blue': '💼 Corporate Blue',
        'nature_green': '🌿 Nature Green',
        'solar_gold': '☀️ Solar Gold'
    }
    
    theme_labels = list(theme_options.values())
    theme_keys = list(theme_options.keys())
    current_theme_key = st.session_state.get('theme', 'light')
    current_index = theme_keys.index(current_theme_key) if current_theme_key in theme_keys else 0
    
    selected_theme_label = st.selectbox("Select Theme", theme_labels, index=current_index)
    selected_theme = theme_keys[theme_labels.index(selected_theme_label)] if selected_theme_label in theme_labels else 'light'
    
    if selected_theme != st.session_state.get('theme'):
        st.session_state['theme'] = selected_theme
        st.rerun()
    
    st.markdown("---")
    
    # Economic Settings
    st.subheader("💰 Economic Settings")
    base_price = st.slider("Base Price (₹/unit)", 1, 15, 5)
    peak_price = st.slider("Peak Hour Price (₹/unit)", 10, 30, 15)
    peak_start = st.slider("Peak Start Hour", 0, 23, 17)
    peak_end = st.slider("Peak End Hour", 0, 23, 21)
    
    # Battery Settings
    st.subheader("🔋 Battery Settings")
    battery_size = st.number_input("Battery Capacity (kWh)", min_value=10, value=100, step=10)
    battery_eff = st.slider("Battery Efficiency (%)", 80, 100, 95) / 100
    
    # Safety Settings
    st.subheader("🛡️ Safety Relay Settings")
    grid_safety_limit = st.slider("Max Grid Current Limit (kW)", 10, 200, 50, 
                                   help="If grid power exceeds this, the system trips.")
    
    # Advanced Settings
    with st.expander("🔧 Advanced Settings"):
        carbon_intensity = st.number_input("Carbon Intensity (kg CO2/kWh)", value=0.82, step=0.01)
        min_soc = st.slider("Minimum SOC Reserve (%)", 0, 30, 10) / 100
    
    st.markdown("---")
    
    # Weather/Scenario Selection
    st.subheader("🌤️ Weather & Scenario")
    weather_scenario = st.selectbox(
        "Weather Condition",
        list(generate_weather_scenarios().keys()),
        help="Select a weather scenario to see how the smart microgrid adapts"
    )
    
    # EV Charging Settings
    with st.expander("🚗 EV Charging Settings"):
        ev_enabled = st.checkbox("Enable EV Charging Simulation")
        ev_count = st.number_input("Number of EVs", min_value=0, value=5, step=1)
        ev_charge_rate = st.number_input("EV Charge Rate (kW)", min_value=1, value=11, step=1)
        ev_battery_size = st.number_input("EV Battery Size (kWh)", min_value=10, value=60, step=5)
    
    st.markdown("---")
    
    # Data Upload Section
    st.subheader("📁 Data Source Selection")
    data_source = st.radio(
        "Choose Data Source",
        ["Use Default Data", "Upload Custom Data"],
        help="Select 'Upload Custom Data' to use your own CSV/Excel file with custom profiles"
    )
    
    # Custom Data Upload
    if data_source == "Upload Custom Data":
        with st.expander("📤 Upload Your Data", expanded=True):
            uploaded_file = st.file_uploader(
                "Upload CSV or Excel file",
                type=['csv', 'xlsx', 'xls'],
                help="File must contain columns: Hour (0-23), Load (kW), Solar (kW), Wind (kW)"
            )
            
            if uploaded_file is not None:
                try:
                    # Read the file based on extension
                    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                    if file_ext == '.csv':
                        uploaded_df = pd.read_csv(uploaded_file)
                    elif file_ext in ['.xlsx', '.xls']:
                        uploaded_df = pd.read_excel(uploaded_file)
                    else:
                        st.error("Unsupported file format")
                        uploaded_df = None
                    
                    if uploaded_df is not None:
                        # Display uploaded data preview
                        st.markdown("**📋 Data Preview:**")
                        st.dataframe(uploaded_df.head(10), use_container_width=True)
                        
                        # Validate required columns
                        required_columns = ['Hour', 'Load (kW)', 'Solar (kW)', 'Wind (kW)']
                        missing_columns = [col for col in required_columns if col not in uploaded_df.columns]
                        
                        if missing_columns:
                            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                            st.info("Required columns: Hour, Load (kW), Solar (kW), Wind (kW)")
                        else:
                            st.success("✅ Data format validated successfully!")
                            
                            # Check if data has 24 hours
                            if len(uploaded_df) >= 24:
                                st.info(f"ℹ️ Data contains {len(uploaded_df)} rows (using first 24 hours)")
                            else:
                                st.warning(f"⚠️ Data contains only {len(uploaded_df)} hours. Add more rows for complete 24-hour analysis.")
                            
                            # Store uploaded data in session state
                            st.session_state['uploaded_data'] = uploaded_df
                            st.session_state['data_source'] = 'custom'
                            
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
    else:
        # Use default data - clear any uploaded data
        if 'uploaded_data' in st.session_state:
            del st.session_state['uploaded_data']
        st.session_state['data_source'] = 'default'
        st.info("ℹ️ Using default hardcoded data profiles")
    
    st.markdown("---")
    
    # Scenario Management
    st.subheader("📊 Scenario Management")
    save_scenario_check = st.checkbox("Save this scenario for comparison")
    scenario_name = st.text_input("Scenario Name", value=f"Scenario {pd.Timestamp.now().strftime('%H:%M')}")
    
    if st.button("🚀 Run System Analysis", type="primary"):
        st.session_state.run_app = True
        if save_scenario_check:
            if 'scenarios' not in st.session_state:
                st.session_state.scenarios = []
            st.session_state.scenarios.append({
                'name': scenario_name,
                'params': {
                    'base_price': base_price,
                    'peak_price': peak_price,
                    'battery_size': battery_size,
                    'grid_safety_limit': grid_safety_limit
                }
            })
    else:
        if 'run_app' not in st.session_state:
            st.session_state.run_app = False
    
    # User menu
    show_user_menu()
    
    # Notification center in sidebar
    st.markdown("---")
    st.subheader("🔔 Notifications")
    username = st.session_state.get('username', 'guest')
    unread_count = get_unread_count(username)
    
    if unread_count > 0:
        st.markdown(f"**{unread_count} unread**")
        if st.button("📬 Open Notifications", use_container_width=True):
            st.session_state["show_notifications"] = True
    else:
        st.info("No new notifications")
    
    if st.button("⚙️ Notification Settings", use_container_width=True):
        st.session_state["show_notification_settings"] = True

# --- MAIN DASHBOARD ---
st.title("⚡ Smart Microgrid Manager Pro")
st.markdown(f"**Advanced Energy Optimization with Wind Power & Carbon Tracking** | Welcome, {st.session_state.get('username', 'User')}!")

# Initialize scenarios storage
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = []

if st.session_state.run_app:
    # 1. Generate Data
    hours = list(range(24))
    
    # Get weather scenario adjustments
    weather_scenarios = generate_weather_scenarios()
    selected_weather = weather_scenarios[weather_scenario]
    
    # Check if custom data was uploaded
    use_custom_data = st.session_state.get('data_source') == 'custom' and 'uploaded_data' in st.session_state
    
    if use_custom_data and st.session_state.uploaded_data is not None:
        # Use uploaded data
        uploaded_df = st.session_state.uploaded_data.copy()
        
        # Ensure we have at least 24 hours of data
        if len(uploaded_df) >= 24:
            uploaded_df = uploaded_df.head(24).copy()
        
        # Extract data columns
        load_data = uploaded_df['Load (kW)'].tolist()
        solar_data = uploaded_df['Solar (kW)'].tolist()
        wind_data = uploaded_df['Wind (kW)'].tolist()
        
        # Apply weather scenario multipliers to uploaded data
        solar_data = [s * selected_weather["solar_mult"] for s in solar_data]
        wind_data = [w * selected_weather["wind_mult"] for w in wind_data]
        
        # Pad with zeros if less than 24 hours
        while len(load_data) < 24:
            load_data.append(0)
            solar_data.append(0)
            wind_data.append(0)
        
        # Display info about using custom data
        st.info(f"📊 Using custom uploaded data ({len(uploaded_df)} hours loaded)")
        
        # Show uploaded data summary
        with st.expander("📈 Uploaded Data Summary", expanded=False):
            col_sum1, col_sum2, col_sum3 = st.columns(3)
            with col_sum1:
                st.metric("Avg Load (kW)", f"{sum(load_data)/len(load_data):.1f}")
            with col_sum2:
                st.metric("Avg Solar (kW)", f"{sum(solar_data)/len(solar_data):.1f}")
            with col_sum3:
                st.metric("Avg Wind (kW)", f"{sum(wind_data)/len(wind_data):.1f}")
            
            # Show data preview chart
            fig_uploaded = go.Figure()
            fig_uploaded.add_trace(go.Scatter(
                x=list(range(len(load_data))), y=load_data,
                mode='lines+markers', name='Load', line=dict(color='#2C3E50')
            ))
            fig_uploaded.add_trace(go.Scatter(
                x=list(range(len(solar_data))), y=solar_data,
                mode='lines', name='Solar', fill='tozeroy', line=dict(color='#F4D03F')
            ))
            fig_uploaded.add_trace(go.Scatter(
                x=list(range(len(wind_data))), y=wind_data,
                mode='lines', name='Wind', fill='tozeroy', line=dict(color='#3498DB')
            ))
            fig_uploaded.update_layout(
                title="Custom Data Profile",
                xaxis_title="Hour",
                yaxis_title="Power (kW)",
                height=300
            )
            st.plotly_chart(fig_uploaded, use_container_width=True)
    else:
        # Use default hardcoded data
        # Base Solar: Peak at noon (High sun)
        base_solar = [0,0,0,0,0,1,5,15,30,45,50,55,55,50,40,25,10,2,0,0,0,0,0,0]
        
        # Base Wind: Peak at night/evening
        base_wind = [15,18,20,18,15,12,8,5,3,2,2,2,3,4,5,8,12,18,25,30,28,22,18,15]
        
        # Apply weather scenario multipliers
        solar_data = [s * selected_weather["solar_mult"] for s in base_solar]
        wind_data = [w * selected_weather["wind_mult"] for w in base_wind]
        
        # Load: Peaks in morning and evening
        load_data = [10,10,10,10,20,30,40,50,40,30,30,30,30,30,40,60,80,90,80,60,40,30,20,10]
    
    # Add EV load if enabled
    if ev_enabled:
        # Calculate EV load for all hours (0-23)
        ev_load = [ev_count * ev_charge_rate * 0.1 if 0 <= h <= 6 else 
                   ev_count * ev_charge_rate * 0.5 if 22 <= h <= 23 else 0 for h in hours]
        
        # Extend load_data if needed
        while len(load_data) < 24:
            load_data.append(0)
        
        # Add EV load to the base load
        load_data = [l + e for l, e in zip(load_data[:24], ev_load)]
    
    # Price: Variable based on peak hours
    price_data = [base_price if (h < peak_start or h > peak_end) else peak_price for h in hours]

    # Total Renewable Generation
    renewable_data = [s + w for s, w in zip(solar_data, wind_data)]

    # 2. RUN THE OPTIMIZER
    with st.spinner("Calculating optimal schedule with wind integration..."):
        # run_optimization returns OptimizationResult (dict subclass with 'dataframe', 'summary', etc.)
        optimization_result = run_optimization(
            load_data, solar_data, wind_data, price_data, battery_size,
            carbon_intensity=carbon_intensity
        )

    # Extract DataFrame and Summary from OptimizationResult
    if optimization_result is not None:
        # optimization_result is a dict subclass with keys: 'dataframe', 'summary', 'status', 'message', 'solver_time_seconds'
        df_result = optimization_result.get('dataframe', pd.DataFrame())
        summary = optimization_result.get('summary', OptimizationSummary())
        
        # Check if we have a valid DataFrame
        if df_result.empty or not isinstance(df_result, pd.DataFrame):
            st.error("Optimization returned an invalid result.")
            st.stop()
        
        # Save to database (access summary properties correctly)
        save_optimization_result(
            user_id=None,
            scenario_name=scenario_name,
            total_cost=summary.total_cost,
            total_emissions=summary.total_emissions,
            renewable_percentage=summary.renewable_percentage,
            total_grid_usage=summary.total_grid_usage,
            battery_size=battery_size,
            parameters={
                'base_price': base_price,
                'peak_price': peak_price,
                'battery_size': battery_size,
                'grid_safety_limit': grid_safety_limit,
                'weather_scenario': weather_scenario
            },
            results=df_result.to_dict(orient='records')
        )
        
        # --- PROTECTION RELAY LOGIC ---
        trip_occured = False
        warning_occured = False
        tripped_hours = []

        for index, row in df_result.iterrows():
            grid_power = row["Grid Usage (kW)"]
            
            if grid_power > grid_safety_limit:
                trip_occured = True
                tripped_hours.append(row["Hour"])
                df_result.at[index, "Grid Usage (kW)"] = 0
                
                save_alert(
                    alert_type="grid_trip",
                    message=f"Grid overload detected at hour {row['Hour']}: {grid_power:.2f} kW",
                    severity="critical",
                    date=datetime.now().strftime("%Y-%m-%d"),
                    hour=row["Hour"]
                )
            elif grid_power > (grid_safety_limit * 0.8):
                warning_occured = True

        # --- ALERTS SECTION ---
        if trip_occured:
            st.error(f"🚨 CRITICAL ALERT: GRID TRIPPED! Overload detected at hours: {tripped_hours}")
        elif warning_occured:
            st.warning("⚠️ WARNING: High Grid Load. System nearing capacity.")
        else:
            st.success("✅ System Normal. All parameters within safety limits.")

        # --- KEY METRICS ---
        st.subheader("📈 Key Performance Metrics")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">₹{summary.total_cost}</div>
                <div class="metric-label">Total Cost</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{summary.total_emissions} kg</div>
                <div class="metric-label">CO₂ Emissions</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{summary.renewable_percentage}%</div>
                <div class="metric-label">Renewable Share</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{summary.total_grid_usage} kWh</div>
                <div class="metric-label">Grid Usage</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{df_result["Battery SOC (kWh)"].max():.0f} kWh</div>
                <div class="metric-label">Max Battery SOC</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- TABS FOR DIFFERENT VIEWS ---
        # Note: Tab7 is for Data Export, Tab8 is for Optimal Scheduling
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "⚡ Power Generation", 
            "🔋 Battery Analytics", 
            "💰 Cost Analysis", 
            "🌍 Carbon Tracking",
            "📊 ML Forecast",
            "🚗 EV Charging",
            "📋 Data Export",        # tab7
            "🎯 Optimal Scheduling"   # tab8
        ])
        
        with tab1:
            st.subheader("⚡ Power Generation Mix")
            
            fig_power = go.Figure()
            
            fig_power.add_trace(go.Scatter(
                x=df_result["Hour"], y=df_result["Solar (kW)"],
                mode='lines', name='Solar', stackgroup='one',
                fillcolor='#F4D03F', line=dict(color='#F4D03F')
            ))
            
            fig_power.add_trace(go.Scatter(
                x=df_result["Hour"], y=df_result["Wind (kW)"],
                mode='lines', name='Wind', stackgroup='one',
                fillcolor='#3498DB', line=dict(color='#3498DB')
            ))
            
            fig_power.add_trace(go.Scatter(
                x=df_result["Hour"], y=df_result["Grid Usage (kW)"],
                mode='lines', name='Grid', stackgroup='one',
                fillcolor='#E74C3C', line=dict(color='#E74C3C')
            ))
            
            fig_power.add_trace(go.Scatter(
                x=df_result["Hour"], y=df_result["Load (kW)"],
                mode='lines+markers', name='Load Demand',
                line=dict(color='#2C3E50', width=2)
            ))
            
            fig_power.add_hline(y=grid_safety_limit, line_dash="dash", 
                               line_color="red", annotation_text="Safety Limit")
            
            fig_power.update_layout(
                title="24-Hour Power Balance",
                xaxis_title="Hour",
                yaxis_title="Power (kW)",
                hovermode="x unified",
                height=400
            )
            
            st.plotly_chart(fig_power, width='stretch')
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                total_solar = sum(df_result["Solar (kW)"])
                total_wind = sum(df_result["Wind (kW)"])
                total_grid = sum(df_result["Grid Usage (kW)"])
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Solar', 'Wind', 'Grid'],
                    values=[total_solar, total_wind, total_grid],
                    hole=0.4,
                    marker=dict(colors=['#F4D03F', '#3498DB', '#E74C3C'])
                )])
                fig_pie.update_layout(title="Energy Source Distribution")
                st.plotly_chart(fig_pie, width='stretch')
            
            with col_b:
                df_result["Total Renewable"] = df_result["Solar (kW)"] + df_result["Wind (kW)"]
                df_result["Renewable %"] = (df_result["Total Renewable"] / df_result["Load (kW)"] * 100).clip(0, 100)
                
                fig_renewable = px.bar(
                    df_result, x="Hour", y="Renewable %",
                    title="Hourly Renewable Penetration (%)",
                    color="Renewable %",
                    color_continuous_scale="Greens"
                )
                st.plotly_chart(fig_renewable, width='stretch')
        
        with tab2:
            st.subheader("🔋 Battery Storage Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_soc = px.area(
                    df_result, x="Hour", y="Battery SOC (kWh)",
                    title="Battery State of Charge (SOC)",
                    markers=True
                )
                fig_soc.update_traces(line_color="#2ECC71", fillcolor="rgba(46, 204, 113, 0.3)")
                fig_soc.add_hline(y=battery_size, line_dash="dot", line_color="green", 
                                 annotation_text="Max Capacity")
                fig_soc.add_hline(y=battery_size * min_soc, line_dash="dot", line_color="red",
                                 annotation_text="Min Reserve")
                st.plotly_chart(fig_soc, width='stretch')
            
            with col2:
                df_result["Battery Action"] = df_result.apply(
                    lambda x: "Charging" if x["Solar (kW)"] + x["Wind (kW)"] > x["Load (kW)"] else "Discharging",
                    axis=1
                )
                
                fig_action = px.scatter(
                    df_result, x="Hour", y="Battery SOC (kWh)",
                    color="Battery Action",
                    color_discrete_map={"Charging": "green", "Discharging": "red"},
                    size="Load (kW)",
                    title="Battery Operation Pattern"
                )
                st.plotly_chart(fig_action, width='stretch')
        
        with tab3:
            st.subheader("💰 Cost Analytics Dashboard")
            
            df_result["Total Renewable Used"] = df_result.apply(
                lambda x: min(x["Load (kW)"], x["Solar (kW)"] + x["Wind (kW)"]), axis=1
            )
            
            fig_cost = px.bar(
                df_result, x="Hour", y="Hourly Cost (₹)",
                title="Hourly Electricity Cost",
                color="Hourly Cost (₹)",
                color_continuous_scale="Reds"
            )
            fig_cost.add_hline(y=df_result["Hourly Cost (₹)"].mean(), 
                              line_dash="dash", line_color="blue",
                              annotation_text=f"Avg: ₹{df_result['Hourly Cost (₹)'].mean():.2f}")
            st.plotly_chart(fig_cost, width='stretch')
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_price = px.line(
                    df_result, x="Hour", y="Price (INR)",
                    markers=True, title="Electricity Price Profile"
                )
                fig_price.update_traces(line_color="#9B59B6")
                peak_hours = df_result[df_result["Price (INR)"] == peak_price]
                fig_price.add_trace(go.Scatter(
                    x=peak_hours["Hour"], y=peak_hours["Price (INR)"],
                    mode='markers', name='Peak Hours',
                    marker=dict(color='red', size=10)
                ))
                st.plotly_chart(fig_price, width='stretch')
            
            with col2:
                baseline_cost = sum(load_data) * peak_price
                savings = baseline_cost - summary.total_cost
                savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0
                
                fig_savings = go.Figure()
                fig_savings.add_trace(go.Bar(
                    x=["Without Optimization", "With Optimization"],
                    y=[baseline_cost, summary.total_cost],
                    marker_color=["#E74C3C", "#2ECC71"],
                    text=[f"₹{baseline_cost:.0f}", f"₹{summary.total_cost:.0f}"],
                    textposition="auto"
                ))
                fig_savings.update_layout(
                    title=f"Cost Savings: ₹{savings:.0f} ({savings_pct:.1f}%)",
                    yaxis_title="Total Cost (₹)"
                )
                st.plotly_chart(fig_savings, width='stretch')
        
        with tab4:
            st.subheader("🌍 Carbon Emissions Tracking")
            
            fig_emissions = px.bar(
                df_result, x="Hour", y="CO2 Emissions (kg)",
                title="Hourly Carbon Emissions",
                color="CO2 Emissions (kg)",
                color_continuous_scale="Oranges"
            )
            st.plotly_chart(fig_emissions, width='stretch')
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=summary.total_emissions,
                    title={"text": "Total Daily Emissions (kg CO₂)"},
                    gauge={
                        "axis": {"range": [0, max(100, summary.total_emissions * 1.2)]},
                        "bar": {"color": "#E74C3C"},
                        "steps": [
                            {"range": [0, 50], "color": "#2ECC71"},
                            {"range": [50, 100], "color": "#F39C12"},
                            {"range": [100, 200], "color": "#E74C3C"}
                        ],
                    }
                ))
                st.plotly_chart(fig_gauge, width='stretch')
            
            with col2:
                baseline_emissions = sum(load_data) * carbon_intensity
                carbon_savings = baseline_emissions - summary.total_emissions
                carbon_savings_pct = (carbon_savings / baseline_emissions * 100) if baseline_emissions > 0 else 0
                
                st.markdown(f"""
                **Carbon Savings Analysis:**
                
                | Metric | Value |
                |--------|-------|
                | Baseline Emissions | {baseline_emissions:.1f} kg CO₂ |
                | Optimized Emissions | {summary.total_emissions:.1f} kg CO₂ |
                | **Carbon Saved** | **{carbon_savings:.1f} kg CO₂ ({carbon_savings_pct:.1f}%)** |
                
                💡 *Equivalent to planting ~{carbon_savings/21:.0f} trees per day!*
                """)
                
                save_carbon_credits(baseline_emissions, summary.total_emissions,
                                   carbon_savings * 0.1, 0)
        
        with tab5:
            st.subheader("🤖 ML-Powered Forecasting")
            
            with st.spinner("Training ML models..."):
                forecaster = EnergyForecaster()
                forecaster.train()
            
            weather_for_ml = {
                'temperature': 25 + selected_weather.get('temperature', 25) / 5,
                'cloud_cover': selected_weather.get('cloud_cover', 20),
                'wind_speed': selected_weather.get('wind_speed', 5)
            }
            
            ml_predictions = forecaster.predict(hours=24, weather=weather_for_ml)
            
            st.markdown("### 📈 ML Predictions vs Base Profile")
            
            fig_ml = go.Figure()
            
            base_profiles = generate_base_profiles()
            fig_ml.add_trace(go.Scatter(
                x=hours, y=base_profiles[3],
                mode='lines', name='Base Load',
                line=dict(color='#2C3E50', dash='dash')
            ))
            fig_ml.add_trace(go.Scatter(
                x=ml_predictions['hour'], y=ml_predictions['Load (kW)'],
                mode='lines', name='ML Predicted Load',
                line=dict(color='#9B59B6')
            ))
            
            fig_ml.update_layout(
                title="Load Prediction: Base vs ML Model",
                xaxis_title="Hour",
                yaxis_title="Load (kW)"
            )
            st.plotly_chart(fig_ml, width='stretch')
            
            st.markdown("### 📊 24-Hour Forecast")
            st.dataframe(ml_predictions, width='stretch')
            
            comparison = compare_predictions(base_profiles, ml_predictions)
            st.markdown("### 📈 Prediction Comparison")
            for energy_type, data in comparison.items():
                st.markdown(f"**{energy_type.title()}:** Base={data['base']:.1f}, ML={data['ml']:.1f}, Diff={data['difference']:.1f}")
        
        with tab6:
            st.subheader("🚗 EV Charging Analysis")
            
            if ev_enabled:
                ev_load = [ev_count * ev_charge_rate * 0.1 if 0 <= h <= 6 else 
                           ev_count * ev_charge_rate * 0.5 if 22 <= h <= 23 else 0 for h in hours]
                
                ev_cost = [e * price_data[h] for h, e in enumerate(ev_load)]
                
                fig_ev = go.Figure()
                fig_ev.add_trace(go.Bar(
                    x=hours, y=ev_load,
                    name='EV Load (kW)',
                    marker_color='#3498DB'
                ))
                fig_ev.update_layout(
                    title=f"EV Charging Load ({ev_count} vehicles)",
                    xaxis_title="Hour",
                    yaxis_title="Power (kW)"
                )
                st.plotly_chart(fig_ev, width='stretch')
                
                total_ev_cost = sum(ev_cost)
                total_ev_energy = sum(ev_load)
                
                st.markdown(f"""
                **EV Charging Summary:**
                - Total Energy Delivered: {total_ev_energy:.1f} kWh
                - Total Charging Cost: ₹{total_ev_cost:.2f}
                - Average Cost per EV: ₹{total_ev_cost/ev_count:.2f}
                - Peak Charging Power: {max(ev_load):.1f} kW
                """)
            else:
                st.info("Enable EV Charging in settings to see analysis")
        
        with tab8:
            st.subheader("🎯 Advanced Optimal Scheduling")
            
            # Scheduling Strategy Selection
            st.markdown("### 📊 Scheduling Strategy")
            strategy = st.selectbox(
                "Select Scheduling Strategy",
                ["Multi-Objective (Cost & Emissions)", "Peak Shaving", 
                 "Battery Degradation Optimization", "Load Shifting",
                 "Demand Response", "Grid Export Optimization"]
            )
            
            # Advanced Parameters
            with st.expander("🔧 Advanced Scheduling Parameters"):
                # Economic Parameters
                st.markdown("#### 💰 Economic Parameters")
                sched_base_price = st.number_input("Base Price (₹/kWh)", value=base_price)
                sched_peak_price = st.number_input("Peak Price (₹/kWh)", value=peak_price)
                demand_charge = st.number_input("Demand Charge (₹/kW)", value=0.0, step=1.0)
                grid_export_price = st.number_input("Grid Export Price (₹/kWh)", value=3.0)
                
                # Battery Parameters
                st.markdown("#### 🔋 Battery Parameters")
                sched_battery_capacity = st.number_input("Battery Capacity (kWh)", value=battery_size)
                sched_min_soc = st.slider("Min SOC Reserve (%)", 5, 30, 10) / 100
                battery_deg_cost = st.number_input("Battery Degradation Cost (₹/cycle)", value=0.01, step=0.01)
                
                # Generator Parameters
                st.markdown("#### ⚙️ Generator Parameters")
                gen_available = st.checkbox("Enable Backup Generator")
                gen_capacity = st.number_input("Generator Capacity (kW)", value=50.0)
                fuel_price = st.number_input("Fuel Price (₹/L)", value=100.0)
                
                # Demand Response
                st.markdown("#### 📉 Demand Response")
                dr_enabled = st.checkbox("Enable Demand Response")
                dr_threshold = st.number_input("DR Price Threshold (₹/kWh)", value=12.0)
                dr_reduction = st.slider("Max Load Reduction (%)", 10, 50, 20) / 100
            
            # Flexible Loads
            with st.expander("🔌 Flexible Loads"):
                flex_ev_charging = st.checkbox("EV Charging as Flexible Load")
                flex_water_heater = st.checkbox("Water Heater as Flexible Load")
                flex_hvac = st.checkbox("HVAC Pre-cooling as Flexible Load")
                
                flex_loads = {}
                if flex_ev_charging:
                    flex_loads['EV Charging'] = 50.0  # kWh
                if flex_water_heater:
                    flex_loads['Water Heater'] = 20.0
                if flex_hvac:
                    flex_loads['HVAC'] = 30.0
            
            # Run Optimal Scheduling
            if st.button("🚀 Run Advanced Scheduling", type="primary"):
                with st.spinner("Running optimal scheduling algorithm..."):
                    # Create scheduler parameters
                    sched_params = SchedulingParameters(
                        base_price=sched_base_price,
                        peak_price=sched_peak_price,
                        demand_charge=demand_charge,
                        grid_export_price=grid_export_price,
                        battery_capacity=sched_battery_capacity,
                        min_soc_reserve=sched_min_soc,
                        battery_degradation_cost=battery_deg_cost,
                        generator_available=gen_available,
                        generator_capacity=gen_capacity,
                        fuel_price=fuel_price,
                        demand_response_enabled=dr_enabled,
                        demand_response_threshold=dr_threshold,
                        demand_response_reduction=dr_reduction,
                        flexible_loads=flex_loads if flex_loads else None,
                        flexible_load_windows={'EV Charging': (1, 6), 'Water Heater': (22, 6), 'HVAC': (12, 15)},
                        objective='balanced'
                    )
                    
                    scheduler = OptimalScheduler(sched_params)
                    
                    # Run selected strategy
                    if strategy == "Multi-Objective (Cost & Emissions)":
                        result = scheduler.run_multi_objective_optimization(
                            load_data, solar_data, wind_data, price_data
                        )
                    elif strategy == "Peak Shaving":
                        result = scheduler.run_peak_shaving_optimization(
                            load_data, solar_data, wind_data, price_data
                        )
                    elif strategy == "Battery Degradation Optimization":
                        result = scheduler.run_battery_degradation_scheduling(
                            load_data, solar_data, wind_data, price_data
                        )
                    elif strategy == "Load Shifting":
                        result = scheduler.run_load_shifting_optimization(
                            load_data, solar_data, wind_data, price_data
                        )
                    else:
                        result = scheduler.run_multi_objective_optimization(
                            load_data, solar_data, wind_data, price_data
                        )
                    
                    if result.get('status') == 'Optimal':
                        df_sched = result['dataframe']
                        
                        st.success("✅ Scheduling optimization completed successfully!")
                        
                        # Show Results
                        st.markdown("### 📊 Scheduling Results")
                        
                        # Key Metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Cost", f"₹{result.get('total_cost', 0)}")
                        with col2:
                            st.metric("Total Emissions", f"{result.get('total_emissions', 0)} kg CO₂")
                        with col3:
                            st.metric("Renewable %", f"{result.get('renewable_percentage', 0)}%")
                        with col4:
                            st.metric("Peak Demand", f"{result.get('peak_demand', 0)} kW")
                        
                        # Schedule Visualization
                        st.markdown("#### ⚡ Optimal Dispatch Schedule")
                        
                        fig_sched = go.Figure()
                        
                        # Generation sources
                        fig_sched.add_trace(go.Scatter(
                            x=df_sched["Hour"], y=df_sched["Solar (kW)"],
                            mode='lines', name='Solar', stackgroup='one',
                            fillcolor='#F4D03F'
                        ))
                        
                        fig_sched.add_trace(go.Scatter(
                            x=df_sched["Hour"], y=df_sched["Wind (kW)"],
                            mode='lines', name='Wind', stackgroup='one',
                            fillcolor='#3498DB'
                        ))
                        
                        if "Grid Import (kW)" in df_sched.columns:
                            fig_sched.add_trace(go.Scatter(
                                x=df_sched["Hour"], y=df_sched["Grid Import (kW)"],
                                mode='lines', name='Grid Import', stackgroup='one',
                                fillcolor='#E74C3C'
                            ))
                            
                            fig_sched.add_trace(go.Scatter(
                                x=df_sched["Hour"], y=df_sched["Grid Export (kW)"],
                                mode='lines', name='Grid Export', stackgroup='one',
                                fillcolor='#27AE60'
                            ))
                        
                        fig_sched.add_trace(go.Scatter(
                            x=df_sched["Hour"], y=df_sched["Load (kW)"],
                            mode='lines+markers', name='Load',
                            line=dict(color='#2C3E50', width=2)
                        ))
                        
                        fig_sched.update_layout(
                            title="24-Hour Optimal Dispatch Schedule",
                            xaxis_title="Hour",
                            yaxis_title="Power (kW)",
                            hovermode="x unified",
                            height=400
                        )
                        st.plotly_chart(fig_sched, width='stretch')
                        
                        # Battery Schedule
                        if "Battery SOC (kWh)" in df_sched.columns:
                            st.markdown("#### 🔋 Battery Schedule")
                            
                            fig_battery = go.Figure()
                            fig_battery.add_trace(go.Scatter(
                                x=df_sched["Hour"], y=df_sched["Battery SOC (kWh)"],
                                mode='lines+markers', name='Battery SOC',
                                fillcolor='rgba(46, 204, 113, 0.3)',
                                line=dict(color='#2ECC71', width=2)
                            ))
                            
                            if "Battery Charge (kW)" in df_sched.columns:
                                fig_battery.add_trace(go.Bar(
                                    x=df_sched["Hour"], y=df_sched["Battery Charge (kW)"],
                                    name='Charging', marker_color='#27AE60'
                                ))
                                fig_battery.add_trace(go.Bar(
                                    x=df_sched["Hour"], y=-df_sched["Battery Discharge (kW)"],
                                    name='Discharging', marker_color='#E74C3C'
                                ))
                            
                            fig_battery.update_layout(
                                title="Battery State of Charge & Charge/Discharge",
                                xaxis_title="Hour",
                                yaxis_title="Energy (kWh)",
                                height=350
                            )
                            st.plotly_chart(fig_battery, width='stretch')
                        
                        # Cost Breakdown
                        st.markdown("#### 💰 Cost Breakdown")
                        
                        if "Hourly Cost (₹)" in df_sched.columns:
                            fig_cost = px.bar(
                                df_sched, x="Hour", y="Hourly Cost (₹)",
                                title="Hourly Scheduling Cost",
                                color="Hourly Cost (₹)",
                                color_continuous_scale="RdYlGn_r"
                            )
                            st.plotly_chart(fig_cost, width='stretch')
                        
                        # Data Table
                        st.markdown("#### 📋 Detailed Schedule")
                        st.dataframe(df_sched, width='stretch')
                        
                        # Export Options
                        col_exp1, col_exp2 = st.columns(2)
                        with col_exp1:
                            csv_sched = df_sched.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download Schedule (CSV)",
                                data=csv_sched,
                                file_name="optimal_schedule.csv",
                                mime="text/csv",
                            )
                        with col_exp2:
                            json_sched = json.dumps(result, indent=2, default=str).encode('utf-8')
                            st.download_button(
                                label="📥 Download Results (JSON)",
                                data=json_sched,
                                file_name="scheduling_results.json",
                                mime="application/json",
                            )
                    
                    else:
                        st.error("Scheduling optimization failed. Please check parameters.")
            
            # Compare Scheduling Strategies
            st.markdown("---")
            st.markdown("### 📊 Compare Scheduling Strategies")
            
            if st.button("🔄 Run Strategy Comparison"):
                with st.spinner("Comparing all scheduling strategies..."):
                    sched_params = SchedulingParameters(
                        base_price=sched_base_price,
                        peak_price=sched_peak_price,
                        battery_capacity=sched_battery_capacity,
                        objective='balanced'
                    )
                    
                    scheduler = OptimalScheduler(sched_params)
                    comparison_df = scheduler.compare_strategies(
                        load_data, solar_data, wind_data, price_data
                    )
                    
                    if not comparison_df.empty:
                        st.dataframe(comparison_df, width='stretch')
                        
                        fig_compare = px.bar(
                            comparison_df, x="Strategy", y=["Cost (₹)", "Emissions (kg)"],
                            barmode="group",
                            title="Scheduling Strategy Comparison"
                        )
                        st.plotly_chart(fig_compare, width='stretch')
                    else:
                        st.warning("Could not generate comparison results.")
        
        with tab7:
            st.subheader("📊 Data Export & Reports")
            
            st.dataframe(df_result, width='stretch')
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df_result.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name="microgrid_optimization_results.csv",
                    mime="text/csv",
                )
            
            with col2:
                json_data = {
                    'results': df_result.to_dict(orient='records'),
                    'summary': summary,
                    'parameters': {
                        'battery_size': battery_size,
                        'base_price': base_price,
                        'peak_price': peak_price,
                        'grid_safety_limit': grid_safety_limit,
                        'weather_scenario': weather_scenario
                    }
                }
                json_str = json.dumps(json_data, indent=2).encode('utf-8')
                st.download_button(
                    label="📥 Download as JSON",
                    data=json_str,
                    file_name="microgrid_optimization_results.json",
                    mime="application/json",
                )
            

            
            report_type = st.selectbox("Report Type", ["HTML Report", "Text Report"])
            
            if st.button("Generate Report"):
                if report_type == "Text Report":
                    report_text = generate_text_report(df_result, summary, {
                        'battery_size': battery_size,
                        'base_price': base_price,
                        'peak_price': peak_price,
                        'grid_safety_limit': grid_safety_limit,
                        'carbon_intensity': carbon_intensity
                    })
                    st.download_button(
                        label="📥 Download Text Report",
                        data=report_text,
                        file_name="microgrid_report.txt",
                        mime="text/plain",
                    )
                else:
                    report_data, content_type, filename = generate_quick_report(
                        df_result, summary,
                        {
                            'battery_size': battery_size,
                            'base_price': base_price,
                            'peak_price': peak_price,
                            'grid_safety_limit': grid_safety_limit,
                            'carbon_intensity': carbon_intensity
                        }
                    )
                    st.download_button(
                        label="📥 Download HTML Report",
                        data=report_data,
                        file_name=f"{filename}.html",
                        mime=content_type,
                    )
        
        # --- SCENARIO COMPARISON ---
        if len(st.session_state.scenarios) > 1:
            st.markdown("---")
            st.subheader("📊 Scenario Comparison")
            
            comparison_data = []
            for i, scenario in enumerate(st.session_state.scenarios):
                comparison_data.append({
                    "Scenario": f"Scenario {i+1}",
                    "Battery (kWh)": scenario['params']['battery_size'],
                    "Base Price (₹)": scenario['params']['base_price'],
                    "Peak Price (₹)": scenario['params']['peak_price'],
                    "Grid Limit (kW)": scenario['params']['grid_safety_limit']
                })
            
            df_comparison = pd.DataFrame(comparison_data)
            st.dataframe(df_comparison, width='stretch')
            
            fig_compare = px.bar(
                df_comparison, x="Scenario", 
                y=["Battery (kWh)", "Grid Limit (kW)"],
                barmode="group",
                title="Scenario Parameter Comparison"
            )
            st.plotly_chart(fig_compare, width='stretch')
            
            if st.button("🗑️ Clear All Scenarios"):
                st.session_state.scenarios = []
                st.rerun()
    
    else:
        st.error("Optimization Failed! Could not find a valid schedule.")
        st.info("Try adjusting the parameters or increasing the battery capacity.")

# --- ADMIN PANEL (if admin) ---
if st.session_state.get("show_admin") and st.session_state.get("role") == "admin":
    show_admin_panel()

# --- HISTORY SECTION ---
if not st.session_state.get("run_app"):
    st.markdown("---")
    st.subheader("📜 Historical Data")
    
    hist_data = get_optimization_history(10)
    if not hist_data.empty:
        st.dataframe(hist_data, width='stretch')
    
    alerts = get_alerts(resolved=False, limit=5)
    if not alerts.empty:
        st.subheader("🔔 Recent Alerts")
        for _, alert in alerts.iterrows():
            severity = alert.get('severity', 'info')
            if severity == 'critical':
                st.error(f"🚨 {alert.get('message', '')}")
            elif severity == 'warning':
                st.warning(f"⚠️ {alert.get('message', '')}")
            else:
                st.info(f"ℹ️ {alert.get('message', '')}")
            
            if st.button(f"Resolve (ID: {alert['id']})"):
                resolve_alert(alert['id'])
                st.rerun()

# --- WELCOME SCREEN ---
else:
    st.info("👈 Use the sidebar to configure your microgrid parameters and click 'Run System Analysis' to begin.")
    
    st.subheader("✨ Features")
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1:
        st.markdown("**📁 Custom Data**")
        st.caption("Upload your own CSV/Excel data")
    with col2:
        st.markdown("**🌬️ Wind Power**")
        st.caption("Wind turbine simulation")
    with col3:
        st.markdown("**🌍 Carbon Tracking**")
        st.caption("Carbon footprint analysis")
    with col4:
        st.markdown("**💰 Cost Analytics**")
        st.caption("Detailed cost breakdown")
    with col5:
        st.markdown("**🤖 ML Forecast**")
        st.caption("AI-powered predictions")
    with col6:
        st.markdown("**🚗 EV Charging**")
        st.caption("Electric vehicle support")
    with col7:
        st.markdown("**📊 Reports**")
        st.caption("Export & reporting")

# --- NOTIFICATION CENTER PAGE ---
if st.session_state.get("show_notifications"):
    show_notification_center()
    if st.button("← Back to Dashboard"):
        st.session_state["show_notifications"] = False
        st.rerun()
    st.stop()

# --- NOTIFICATION SETTINGS PAGE ---
if st.session_state.get("show_notification_settings"):
    show_notification_settings()
    if st.button("← Back to Dashboard"):
        st.session_state["show_notification_settings"] = False
        st.rerun()
    st.stop()

# --- FOOTER ---
st.markdown("---")
st.markdown(
    f"""
    <div style="text-align: center; color: #1A365D; padding: 20px;">
        <div style="margin-bottom: 10px;">{SVG_LOGO_SMALL}</div>
        <div style="font-weight: bold; font-size: 16px;">⚡ {COMPANY_BRANDING['company_name']}</div>
        <div style="font-size: 12px; color: #48BB78;">{COMPANY_BRANDING['footer_text']}</div>
        <div style="font-size: 11px; color: #999; margin-top: 10px;">
            © 2024 {COMPANY_BRANDING['company_name']} | 
            Built with Streamlit, Plotly & PuLP
        </div>
    </div>
    """, 
    unsafe_allow_html=True
)

