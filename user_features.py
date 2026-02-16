"""
Enhanced User Features Module for Smart Microgrid Manager Pro
Provides dataset management, configuration presets, and data comparison tools.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, List, Optional, Any
import json


# ============================================================================
# DEFAULT CONFIGURATION PRESETS
# ============================================================================

DEFAULT_CONFIG_PRESETS = {
    'Residential': {
        'name': 'Residential',
        'description': 'Typical residential microgrid setup',
        'params': {
            'base_price': 5,
            'peak_price': 12,
            'battery_size': 50,
            'grid_safety_limit': 30
        },
        'icon': '🏠'
    },
    'Commercial': {
        'name': 'Commercial',
        'description': 'Small commercial building',
        'params': {
            'base_price': 7,
            'peak_price': 15,
            'battery_size': 100,
            'grid_safety_limit': 50
        },
        'icon': '🏢'
    },
    'Industrial': {
        'name': 'Industrial',
        'description': 'Large industrial facility',
        'params': {
            'base_price': 6,
            'peak_price': 18,
            'battery_size': 200,
            'grid_safety_limit': 100
        },
        'icon': '🏭'
    },
    'Remote Off-Grid': {
        'name': 'Remote Off-Grid',
        'description': 'Off-grid remote installation',
        'params': {
            'base_price': 10,
            'peak_price': 25,
            'battery_size': 150,
            'grid_safety_limit': 20
        },
        'icon': '🏔️'
    },
    'Hospital': {
        'name': 'Hospital',
        'description': 'Critical healthcare facility',
        'params': {
            'base_price': 8,
            'peak_price': 20,
            'battery_size': 300,
            'grid_safety_limit': 150
        },
        'icon': '🏥'
    },
    'School': {
        'name': 'School',
        'description': 'Educational institution',
        'params': {
            'base_price': 6,
            'peak_price': 14,
            'battery_size': 80,
            'grid_safety_limit': 40
        },
        'icon': '🏫'
    },
    'Data Center': {
        'name': 'Data Center',
        'description': 'High-power computing facility',
        'params': {
            'base_price': 8,
            'peak_price': 22,
            'battery_size': 500,
            'grid_safety_limit': 200
        },
        'icon': '🖥️'
    },
    'Agricultural': {
        'name': 'Agricultural',
        'description': 'Farm and irrigation systems',
        'params': {
            'base_price': 4,
            'peak_price': 10,
            'battery_size': 60,
            'grid_safety_limit': 35
        },
        'icon': '🌾'
    }
}


# ============================================================================
# DATASET MANAGEMENT
# ============================================================================

def initialize_user_data():
    """Initialize session state for user data storage."""
    if 'saved_datasets' not in st.session_state:
        st.session_state.saved_datasets = {}
    if 'saved_configs' not in st.session_state:
        st.session_state.saved_configs = DEFAULT_CONFIG_PRESETS.copy()
    if 'recent_files' not in st.session_state:
        st.session_state.recent_files = []


def save_dataset(name: str, data: pd.DataFrame, description: str = "", metadata: Dict = None):
    """Save a dataset to session state."""
    if 'saved_datasets' not in st.session_state:
        st.session_state.saved_datasets = {}
    
    st.session_state.saved_datasets[name] = {
        'name': name,
        'description': description,
        'data': data.to_dict('records'),
        'columns': list(data.columns),
        'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'metadata': metadata or {}
    }
    
    # Add to recent files
    if 'recent_files' not in st.session_state:
        st.session_state.recent_files = []
    st.session_state.recent_files.insert(0, {
        'name': name,
        'type': 'dataset',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    # Keep only last 10 recent files
    st.session_state.recent_files = st.session_state.recent_files[:10]


def load_dataset(name: str) -> Optional[pd.DataFrame]:
    """Load a dataset from session state."""
    if 'saved_datasets' in st.session_state and name in st.session_state.saved_datasets:
        dataset = st.session_state.saved_datasets[name]
        return pd.DataFrame(dataset['data'])
    return None


def delete_dataset(name: str) -> bool:
    """Delete a dataset from session state."""
    if 'saved_datasets' in st.session_state and name in st.session_state.saved_datasets:
        del st.session_state.saved_datasets[name]
        return True
    return False


def get_saved_datasets() -> Dict[str, Dict]:
    """Get all saved datasets."""
    return st.session_state.get('saved_datasets', {})


# ============================================================================
# CONFIGURATION PRESETS MANAGEMENT
# ============================================================================

def save_config_preset(name: str, params: Dict, description: str = "", icon: str = "⚙️"):
    """Save a configuration preset."""
    if 'saved_configs' not in st.session_state:
        st.session_state.saved_configs = DEFAULT_CONFIG_PRESETS.copy()
    
    st.session_state.saved_configs[name] = {
        'name': name,
        'description': description,
        'params': params,
        'icon': icon,
        'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def load_config_preset(name: str) -> Optional[Dict]:
    """Load a configuration preset."""
    configs = st.session_state.get('saved_configs', DEFAULT_CONFIG_PRESETS)
    if name in configs:
        return configs[name]
    return None


def delete_config_preset(name: str) -> bool:
    """Delete a configuration preset."""
    if name in DEFAULT_CONFIG_PRESETS:
        st.error(f"Cannot delete default preset: {name}")
        return False
    
    if 'saved_configs' in st.session_state and name in st.session_state.saved_configs:
        del st.session_state.saved_configs[name]
        return True
    return False


def get_config_presets() -> Dict[str, Dict]:
    """Get all configuration presets."""
    return st.session_state.get('saved_configs', DEFAULT_CONFIG_PRESETS)


# ============================================================================
# DATASET COMPARISON TOOL
# ============================================================================

def compare_datasets(df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, Any]:
    """Compare two datasets and return statistics."""
    comparison = {
        'row_count': {
            'dataset_a': len(df1),
            'dataset_b': len(df2),
            'difference': len(df1) - len(df2)
        },
        'columns': {
            'common': list(set(df1.columns) & set(df2.columns)),
            'only_a': list(set(df1.columns) - set(df2.columns)),
            'only_b': list(set(df2.columns) - set(df1.columns))
        },
        'statistics': {}
    }
    
    # Calculate statistics for common numeric columns
    for col in comparison['columns']['common']:
        if pd.api.types.is_numeric_dtype(df1[col]) and pd.api.types.is_numeric_dtype(df2[col]):
            comparison['statistics'][col] = {
                'dataset_a_mean': df1[col].mean(),
                'dataset_b_mean': df2[col].mean(),
                'difference': df1[col].mean() - df2[col].mean(),
                'dataset_a_std': df1[col].std(),
                'dataset_b_std': df2[col].std(),
                'correlation': df1[col].corr(df2[col]) if len(df1) == len(df2) else None
            }
    
    return comparison


def show_dataset_comparison_tool():
    """Display the dataset comparison tool UI."""
    st.markdown("### 🔍 Dataset Comparison Tool")
    st.markdown("Compare two datasets side by side to analyze differences.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Dataset A**")
        file_a = st.file_uploader(
            "Upload first dataset (CSV/Excel)", 
            type=['csv', 'xlsx', 'xls'], 
            key='comp_file_a',
            help="Supported formats: CSV, Excel (.xlsx, .xls)"
        )
        if file_a:
            try:
                if file_a.name.endswith('.csv'):
                    df_a = pd.read_csv(file_a)
                else:
                    df_a = pd.read_excel(file_a)
                st.success(f"Loaded: {file_a.name}")
                st.markdown(f"**Shape:** {df_a.shape[0]} rows x {df_a.shape[1]} columns")
                with st.expander("Preview Dataset A", expanded=True):
                    st.dataframe(df_a.head(5), use_container_width=True)
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                df_a = None
        else:
            df_a = None
    
    with col2:
        st.markdown("**Dataset B**")
        file_b = st.file_uploader(
            "Upload second dataset (CSV/Excel)", 
            type=['csv', 'xlsx', 'xls'], 
            key='comp_file_b',
            help="Supported formats: CSV, Excel (.xlsx, .xls)"
        )
        if file_b:
            try:
                if file_b.name.endswith('.csv'):
                    df_b = pd.read_csv(file_b)
                else:
                    df_b = pd.read_excel(file_b)
                st.success(f"Loaded: {file_b.name}")
                st.markdown(f"**Shape:** {df_b.shape[0]} rows x {df_b.shape[1]} columns")
                with st.expander("Preview Dataset B", expanded=True):
                    st.dataframe(df_b.head(5), use_container_width=True)
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                df_b = None
        else:
            df_b = None
    
    # Run comparison button
    if df_a is not None and df_b is not None:
        if st.button("Run Comparison", type="primary", use_container_width=True):
            comparison = compare_datasets(df_a, df_b)
            
            # Display comparison results
            st.markdown("---")
            st.markdown("### Comparison Results")
            
            # Row count comparison
            col_stats1, col_stats2 = st.columns(2)
            
            with col_stats1:
                st.markdown("**Dataset A Statistics**")
                st.metric("Total Rows", comparison['row_count']['dataset_a'])
                for col in ['Load (kW)', 'Solar (kW)', 'Wind (kW)']:
                    if col in df_a.columns and pd.api.types.is_numeric_dtype(df_a[col]):
                        st.metric(f"Avg {col}", f"{df_a[col].mean():.1f}")
            
            with col_stats2:
                st.markdown("**Dataset B Statistics**")
                st.metric("Total Rows", comparison['row_count']['dataset_b'])
                for col in ['Load (kW)', 'Solar (kW)', 'Wind (kW)']:
                    if col in df_b.columns and pd.api.types.is_numeric_dtype(df_b[col]):
                        st.metric(f"Avg {col}", f"{df_b[col].mean():.1f}")
            
            # Visual comparison for Load column
            if 'Load (kW)' in df_a.columns and 'Load (kW)' in df_b.columns:
                st.markdown("### Load Profile Comparison")
                
                # Ensure same length for comparison
                min_len = min(len(df_a), len(df_b))
                
                fig_compare = go.Figure()
                fig_compare.add_trace(go.Scatter(
                    x=list(range(min_len)), 
                    y=df_a['Load (kW)'].iloc[:min_len],
                    mode='lines', 
                    name='Load A', 
                    line=dict(color='#2C3E50', width=2)
                ))
                fig_compare.add_trace(go.Scatter(
                    x=list(range(min_len)), 
                    y=df_b['Load (kW)'].iloc[:min_len],
                    mode='lines', 
                    name='Load B', 
                    line=dict(color='#E74C3C', width=2)
                ))
                fig_compare.update_layout(
                    title="Load Profile Comparison",
                    xaxis_title="Index",
                    yaxis_title="Load (kW)",
                    height=400,
                    hovermode="x unified"
                )
                st.plotly_chart(fig_compare, use_container_width=True)
                
                # Differences chart
                load_diff = df_a['Load (kW)'].iloc[:min_len].values - df_b['Load (kW)'].iloc[:min_len].values
                fig_diff = go.Figure()
                fig_diff.add_trace(go.Bar(
                    x=list(range(min_len)),
                    y=load_diff,
                    marker_color=['#2ECC71' if d >= 0 else '#E74C3C' for d in load_diff],
                    name='Difference (A - B)'
                ))
                fig_diff.update_layout(
                    title="Load Difference (A - B)",
                    xaxis_title="Index",
                    yaxis_title="Difference (kW)",
                    height=300
                )
                st.plotly_chart(fig_diff, use_container_width=True)
                
                # Summary metrics
                col_diff1, col_diff2, col_diff3 = st.columns(3)
                with col_diff1:
                    st.metric(
                        "Avg Load Difference", 
                        f"{load_diff.mean():.1f} kW",
                        delta_color="inverse"
                    )
                with col_diff2:
                    max_diff_idx = abs(load_diff).argmax()
                    st.metric("Max Difference", f"{abs(load_diff).max():.1f} kW", 
                             delta=f"at index {max_diff_idx}")
                with col_diff3:
                    correlation = df_a['Load (kW)'].iloc[:min_len].corr(df_b['Load (kW)'].iloc[:min_len])
                    st.metric("Correlation", f"{correlation:.3f}")
    
    else:
        st.info("Upload two datasets above to compare them")


# ============================================================================
# DATASET LIBRARY UI
# ============================================================================

def show_dataset_library():
    """Display the dataset library UI."""
    st.markdown("### Dataset Library")
    st.markdown("Manage your saved datasets.")
    
    # Initialize saved datasets
    if 'saved_datasets' not in st.session_state:
        st.session_state.saved_datasets = {}
    
    # Show saved datasets
    saved_datasets = st.session_state.saved_datasets
    
    if saved_datasets:
        st.markdown(f"**Saved Datasets ({len(saved_datasets)}):**")
        
        for i, (name, dataset) in enumerate(saved_datasets.items()):
            with st.expander(f"{dataset.get('icon', '📊')} {name}", expanded=True):
                col_info, col_actions = st.columns([3, 1])
                
                with col_info:
                    st.markdown(f"**Description:** {dataset.get('description', 'No description')}")
                    st.markdown(f"**Created:** {dataset.get('created', 'Unknown')}")
                    st.markdown(f"**Rows:** {len(dataset.get('data', []))}")
                    st.markdown(f"**Columns:** {', '.join(dataset.get('columns', []))}")
                
                with col_actions:
                    if st.button(f"Use", key=f"use_{name}", use_container_width=True):
                        st.session_state['selected_dataset'] = name
                        st.success(f"Selected: {name}")
                    
                    if st.button(f"Delete", key=f"del_{name}", use_container_width=True):
                        del st.session_state.saved_datasets[name]
                        st.success(f"Deleted: {name}")
                        st.rerun()
                
                # Preview
                preview_df = pd.DataFrame(dataset.get('data', [])[:5])
                if not preview_df.empty:
                    with st.expander("Preview", expanded=False):
                        st.dataframe(preview_df, use_container_width=True)
    else:
        st.info("No saved datasets yet. Upload and save datasets from the main interface.")


# ============================================================================
# CONFIGURATION PRESETS UI
# ============================================================================

def show_config_presets_ui():
    """Display the configuration presets UI."""
    st.markdown("### Configuration Presets")
    
    # Initialize saved configs
    if 'saved_configs' not in st.session_state:
        st.session_state.saved_configs = DEFAULT_CONFIG_PRESETS.copy()
    
    configs = st.session_state.saved_configs
    
    # Display presets
    for name, config in configs.items():
        icon = config.get('icon', '⚙️')
        params = config.get('params', {})
        
        with st.expander(f"{icon} {name}", expanded=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Description:** {config.get('description', 'No description')}")
                
                # Display parameters
                st.markdown("**Parameters:**")
                params_cols = st.columns(4)
                with params_cols[0]:
                    st.metric("Base Price", f"₹{params.get('base_price', 0)}/unit")
                with params_cols[1]:
                    st.metric("Peak Price", f"₹{params.get('peak_price', 0)}/unit")
                with params_cols[2]:
                    st.metric("Battery", f"{params.get('battery_size', 0)} kWh")
                with params_cols[3]:
                    st.metric("Grid Limit", f"{params.get('grid_safety_limit', 0)} kW")
            
            with col2:
                if st.button(f"Apply", key=f"apply_{name}", use_container_width=True):
                    st.session_state['applied_config'] = name
                    st.session_state['config_params'] = params
                    st.success(f"Applied: {name}")
                
                if name not in DEFAULT_CONFIG_PRESETS:
                    if st.button(f"Delete", key=f"del_cfg_{name}", use_container_width=True):
                        del st.session_state.saved_configs[name]
                        st.rerun()


# ============================================================================
# DATA STATISTICS DISPLAY
# ============================================================================

def show_data_statistics(data: pd.DataFrame):
    """Display comprehensive statistics for a dataset."""
    st.markdown("### Data Statistics")
    
    # Basic info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Rows", len(data))
    with col2:
        st.metric("Total Columns", len(data.columns))
    with col3:
        st.metric("Numeric Columns", len(data.select_dtypes(include=['number']).columns))
    with col4:
        st.metric("Missing Values", data.isnull().sum().sum())
    
    # Detailed statistics for numeric columns
    if not data.select_dtypes(include=['number']).empty:
        st.markdown("#### Numeric Column Statistics")
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        
        # Create statistics dataframe
        stats_df = data[numeric_cols].describe().T
        stats_df['range'] = stats_df['max'] - stats_df['min']
        stats_df['cv'] = stats_df['std'] / stats_df['mean'] * 100
        
        st.dataframe(stats_df, use_container_width=True)


# ============================================================================
# QUICK STATS WIDGET
# ============================================================================

def show_quick_stats(data: pd.DataFrame):
    """Show quick statistics widget."""
    st.markdown("### Quick Stats")
    
    cols = st.columns(5)
    
    if 'Load (kW)' in data.columns:
        with cols[0]:
            st.metric("Avg Load", f"{data['Load (kW)'].mean():.1f} kW")
    if 'Solar (kW)' in data.columns:
        with cols[1]:
            st.metric("Avg Solar", f"{data['Solar (kW)'].mean():.1f} kW")
    if 'Wind (kW)' in data.columns:
        with cols[2]:
            st.metric("Avg Wind", f"{data['Wind (kW)'].mean():.1f} kW")
    if 'Hour' in data.columns:
        with cols[3]:
            st.metric("Hours", f"{len(data)} / 24")
    with cols[4]:
        peak_load = data['Load (kW)'].max() if 'Load (kW)' in data.columns else 0
        st.metric("Peak Load", f"{peak_load:.1f} kW")


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_user_features():
    """Initialize all user features."""
    initialize_user_data()


# Run initialization
if __name__ == "__main__":
    # This module should be imported, not run directly
    pass

