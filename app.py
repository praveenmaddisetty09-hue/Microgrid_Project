import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from logic import run_optimization, generate_scenario_comparison
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Smart Microgrid Manager Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
    }
    .stAlert {
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (USER CONTROLS) ---
with st.sidebar:
    st.header("⚙️ System Control Panel")
    
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
    
    # Scenario Management
    st.subheader("📊 Scenario Management")
    save_scenario = st.checkbox("Save this scenario for comparison")
    scenario_name = st.text_input("Scenario Name", value=f"Scenario {pd.Timestamp.now().strftime('%H:%M')}")
    
    if st.button("🚀 Run System Analysis", type="primary"):
        st.session_state.run_app = True
        if save_scenario:
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

# --- MAIN DASHBOARD ---
st.title("⚡ Smart Microgrid Manager Pro")
st.markdown("**Advanced Energy Optimization with Wind Power & Carbon Tracking**")

# Initialize scenarios storage
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = []

if st.session_state.run_app:
    # 1. Generate Data (Simulated for Demo)
    hours = list(range(24))
    
    # Solar: Peak at noon (High sun)
    solar_data = [0,0,0,0,0,1,5,15,30,45,50,55,55,50,40,25,10,2,0,0,0,0,0,0]
    
    # Wind: Peak at night/evening (typically wind picks up at night)
    wind_data = [15,18,20,18,15,12,8,5,3,2,2,2,3,4,5,8,12,18,25,30,28,22,18,15]
    
    # Load: Peaks in morning and evening
    load_data = [10,10,10,10,20,30,40,50,40,30,30,30,30,30,40,60,80,90,80,60,40,30,20,10]
    
    # Price: Variable based on peak hours
    price_data = [base_price if (h < peak_start or h > peak_end) else peak_price for h in hours]

    # Total Renewable Generation
    renewable_data = [s + w for s, w in zip(solar_data, wind_data)]

    # 2. RUN THE OPTIMIZER
    with st.spinner("Calculating optimal schedule with wind integration..."):
        df_result = run_optimization(
            load_data, solar_data, wind_data, price_data, battery_size,
            carbon_intensity=carbon_intensity
        )

    if df_result is not None:
        # Get summary metrics from dataframe attributes
        summary = df_result.attrs
        
        # --- PROTECTION RELAY LOGIC (The Safety Check) ---
        trip_occured = False
        warning_occured = False
        tripped_hours = []

        # Check every hour
        for index, row in df_result.iterrows():
            grid_power = row["Grid Usage (kW)"]
            
            # CHECK 1: CRITICAL OVERLOAD -> TRIP
            if grid_power > grid_safety_limit:
                trip_occured = True
                tripped_hours.append(row["Hour"])
                
                # Action: Cut Grid Power to 0
                df_result.at[index, "Grid Usage (kW)"] = 0
            
            # CHECK 2: WARNING -> NEAR LIMIT
            elif grid_power > (grid_safety_limit * 0.8): 
                warning_occured = True

        # --- ALERTS SECTION ---
        if trip_occured:
            st.error(f"🚨 CRITICAL ALERT: GRID TRIPPED! Overload detected at hours: {tripped_hours}")
            st.caption("Automatic Switch-Off initiated. Grid Power set to 0kW to prevent damage.")
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
                <div class="metric-value">₹{summary['total_cost']}</div>
                <div class="metric-label">Total Cost</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{summary['total_emissions']} kg</div>
                <div class="metric-label">CO₂ Emissions</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{summary['renewable_percentage']}%</div>
                <div class="metric-label">Renewable Share</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{summary['total_grid_usage']} kWh</div>
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
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "⚡ Power Generation", 
            "🔋 Battery Analytics", 
            "💰 Cost Analysis", 
            "🌍 Carbon Tracking",
            "📊 Data Export"
        ])
        
        with tab1:
            st.subheader("⚡ Power Generation Mix")
            
            # Stacked area chart for all sources
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
            
            # Add safety limit line
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
            
            # Renewable vs Grid breakdown
            col_a, col_b = st.columns(2)
            
            with col_a:
                # Pie chart for energy sources
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
                # Hourly renewable percentage
                df_result["Total Renewable"] = df_result["Solar (kW)"] + df_result["Wind (kW)"]
                df_result["Renewable %"] = (df_result["Total Renewable"] / df_result["Load (kW)"] * 100).clip(0, 100)
                
                fig_renewable = px.bar(
                    df_result, x="Hour", y="Renewable %",
                    title="Hourly Renewable Penetration (%)",
                    color="Renewable %",
                    color_continuous_scale="Greens"
                )
                fig_renewable.add_hline(y=summary['renewable_percentage'], 
                                       line_dash="dash", line_color="blue",
                                       annotation_text=f"Avg: {summary['renewable_percentage']}%")
                st.plotly_chart(fig_renewable, width='stretch')
        
        with tab2:
            st.subheader("🔋 Battery Storage Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Battery SOC over time
                fig_soc = px.area(
                    df_result, x="Hour", y="Battery SOC (kWh)",
                    title="Battery State of Charge (SOC)",
                    markers=True
                )
                fig_soc.update_traces(line_color="#2ECC71", fillcolor="rgba(46, 204, 113, 0.3)")
                
                # Add min/max lines
                fig_soc.add_hline(y=battery_size, line_dash="dot", line_color="green", 
                                 annotation_text="Max Capacity")
                fig_soc.add_hline(y=battery_size * min_soc, line_dash="dot", line_color="red",
                                 annotation_text="Min Reserve")
                
                st.plotly_chart(fig_soc, width='stretch')
            
            with col2:
                # Charge/Discharge patterns
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
            
            # Battery statistics
            bat_stats = df_result["Battery SOC (kWh)"].describe()
            st.markdown(f"""
            **Battery Statistics:**
            - Average SOC: {bat_stats['mean']:.1f} kWh
            - Min SOC: {bat_stats['min']:.1f} kWh
            - Max SOC: {bat_stats['max']:.1f} kWh
            - SOC Std Dev: {bat_stats['std']:.1f} kWh
            """)
        
        with tab3:
            st.subheader("💰 Cost Analytics Dashboard")
            
            # Cost breakdown
            df_result["Total Renewable Used"] = df_result.apply(
                lambda x: min(x["Load (kW)"], x["Solar (kW)"] + x["Wind (kW)"]), axis=1
            )
            
            # Cost by hour
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
                # Price profile
                fig_price = px.line(
                    df_result, x="Hour", y="Price (INR)",
                    markers=True, title="Electricity Price Profile"
                )
                fig_price.update_traces(line_color="#9B59B6")
                # Highlight peak hours
                peak_hours = df_result[df_result["Price (INR)"] == peak_price]
                fig_price.add_trace(go.Scatter(
                    x=peak_hours["Hour"], y=peak_hours["Price (INR)"],
                    mode='markers', name='Peak Hours',
                    marker=dict(color='red', size=10)
                ))
                st.plotly_chart(fig_price, width='stretch')
            
            with col2:
                # Cost savings comparison
                baseline_cost = sum(load_data) * peak_price  # All at peak price
                savings = baseline_cost - summary['total_cost']
                savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0
                
                fig_savings = go.Figure()
                
                fig_savings.add_trace(go.Bar(
                    x=["Without Optimization", "With Optimization"],
                    y=[baseline_cost, summary['total_cost']],
                    marker_color=["#E74C3C", "#2ECC71"],
                    text=[f"₹{baseline_cost:.0f}", f"₹{summary['total_cost']:.0f}"],
                    textposition="auto"
                ))
                
                fig_savings.update_layout(
                    title=f"Cost Savings: ₹{savings:.0f} ({savings_pct:.1f}%)",
                    yaxis_title="Total Cost (₹)"
                )
                
                st.plotly_chart(fig_savings, width='stretch')
        
        with tab4:
            st.subheader("🌍 Carbon Emissions Tracking")
            
            # Emissions over time
            fig_emissions = px.bar(
                df_result, x="Hour", y="CO2 Emissions (kg)",
                title="Hourly Carbon Emissions",
                color="CO2 Emissions (kg)",
                color_continuous_scale="Oranges"
            )
            st.plotly_chart(fig_emissions, width='stretch')
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Carbon intensity gauge
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=summary['total_emissions'],
                    title={"text": "Total Daily Emissions (kg CO₂)"},
                    gauge={
                        "axis": {"range": [0, max(100, summary['total_emissions'] * 1.2)]},
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
                # Carbon savings compared to all-grid
                baseline_emissions = sum(load_data) * carbon_intensity
                carbon_savings = baseline_emissions - summary['total_emissions']
                carbon_savings_pct = (carbon_savings / baseline_emissions * 100) if baseline_emissions > 0 else 0
                
                st.markdown(f"""
                **Carbon Savings Analysis:**
                
                | Metric | Value |
                |--------|-------|
                | Baseline Emissions | {baseline_emissions:.1f} kg CO₂ |
                | Optimized Emissions | {summary['total_emissions']:.1f} kg CO₂ |
                | **Carbon Saved** | **{carbon_savings:.1f} kg CO₂ ({carbon_savings_pct:.1f}%)** |
                
                💡 *Equivalent to planting ~{carbon_savings/21:.0f} trees per day!*
                *(Based on ~21 kg CO₂ absorption per tree annually)*
                """)
                
                # Emissions pie chart
                fig_carbon = go.Figure(data=[go.Pie(
                    labels=['Renewable Offset', 'Grid Emissions'],
                    values=[carbon_savings, summary['total_emissions']],
                    hole=0.4,
                    marker=dict(colors=['#2ECC71', '#E74C3C'])
                )])
                fig_carbon.update_layout(title="Carbon Impact")
                st.plotly_chart(fig_carbon, width='stretch')
        
        with tab5:
            st.subheader("📊 Data Export & Analysis")
            
            # Display data table
            st.dataframe(df_result, width='stretch')
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV Download
                csv = df_result.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name="microgrid_optimization_results.csv",
                    mime="text/csv",
                )
            
            with col2:
                # JSON Download
                import json
                result_dict = df_result.to_dict(orient='records')
                json_data = {
                    'results': result_dict,
                    'summary': summary,
                    'parameters': {
                        'battery_size': battery_size,
                        'base_price': base_price,
                        'peak_price': peak_price,
                        'grid_safety_limit': grid_safety_limit
                    }
                }
                json_str = json.dumps(json_data, indent=2).encode('utf-8')
                st.download_button(
                    label="📥 Download as JSON",
                    data=json_str,
                    file_name="microgrid_optimization_results.json",
                    mime="application/json",
                )
            
            # Optimization summary report
            st.markdown("### 📋 Optimization Summary Report")
            st.markdown(f"""
            **System Configuration:**
            - Battery Capacity: {battery_size} kWh
            - Base Price: ₹{base_price}/unit
            - Peak Price: ₹{peak_price}/unit
            - Grid Safety Limit: {grid_safety_limit} kW
            - Carbon Intensity: {carbon_intensity} kg CO₂/kWh
            
            **Results:**
            - Total Energy Load: {sum(load_data)} kWh
            - Solar Generation: {sum(solar_data)} kWh
            - Wind Generation: {sum(wind_data)} kWh
            - Total Grid Usage: {summary['total_grid_usage']} kWh
            - Renewable Penetration: {summary['renewable_percentage']}%
            - Total Cost: ₹{summary['total_cost']}
            - Total CO₂ Emissions: {summary['total_emissions']} kg
            """)
        
        # --- SCENARIO COMPARISON ---
        if len(st.session_state.scenarios) > 1:
            st.markdown("---")
            st.subheader("📊 Scenario Comparison")
            
            # Create comparison dataframe
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
            
            # Comparison chart
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

else:
    # Welcome screen with instructions
    st.info("👈 Use the sidebar to configure your microgrid parameters and click 'Run System Analysis' to begin.")
    
    # Show sample data preview
    st.subheader("📊 Sample Data Preview")
    
    # Generate sample data for preview
    hours = list(range(24))
    solar_preview = [0,0,0,0,0,1,5,15,30,45,50,55,55,50,40,25,10,2,0,0,0,0,0,0]
    wind_preview = [15,18,20,18,15,12,8,5,3,2,2,2,3,4,5,8,12,18,25,30,28,22,18,15]
    load_preview = [10,10,10,10,20,30,40,50,40,30,30,30,30,30,40,60,80,90,80,60,40,30,20,10]
    
    preview_df = pd.DataFrame({
        "Hour": hours,
        "Solar (kW)": solar_preview,
        "Wind (kW)": wind_preview,
        "Load (kW)": load_preview,
        "Total Renewable (kW)": [s+w for s,w in zip(solar_preview, wind_preview)]
    })
    
    st.dataframe(preview_df, width='stretch')
    
    # Preview chart
    fig_preview = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               subplot_titles=("Renewable Generation", "Load Demand"))
    
    fig_preview.add_trace(go.Scatter(x=hours, y=solar_preview, name="Solar", 
                                     fill='tozeroy', stackgroup='one'),
                         row=1, col=1)
    fig_preview.add_trace(go.Scatter(x=hours, y=wind_preview, name="Wind",
                                     fill='tozeroy', stackgroup='one'),
                         row=1, col=1)
    fig_preview.add_trace(go.Scatter(x=hours, y=load_preview, name="Load",
                                     line=dict(color='red', width=2)),
                         row=2, col=1)
    
    fig_preview.update_layout(height=500, title="Sample 24-Hour Profile Preview")
    st.plotly_chart(fig_preview, width='stretch')
    
    # Feature highlights
    st.subheader("✨ New Features")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**🌬️ Wind Power**")
        st.caption("Integrated wind turbine simulation with variable generation")
    
    with col2:
        st.markdown("**🌍 Carbon Tracking**")
        st.caption("Monitor your carbon footprint and savings")
    
    with col3:
        st.markdown("**💰 Cost Analytics**")
        st.caption("Detailed cost breakdown and savings analysis")
    
    with col4:
        st.markdown("**📊 Scenario Comparison**")
        st.caption("Compare different configuration scenarios")

