"""
Notification System Module for Smart Microgrid Manager Pro
Handles user notifications, alerts, and messaging.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import json
import os
import sqlite3

# Database file
DB_FILE = "microgrid_data.db"


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_notifications():
    """Initialize notification tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            notification_type TEXT,
            title TEXT,
            message TEXT,
            priority TEXT DEFAULT 'normal',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT
        )
    ''')
    
    # Create notification preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT UNIQUE,
            email_alerts INTEGER DEFAULT 1,
            push_notifications INTEGER DEFAULT 1,
            critical_alerts INTEGER DEFAULT 1,
            daily_summary INTEGER DEFAULT 1,
            weekly_report INTEGER DEFAULT 0,
            grid_alerts INTEGER DEFAULT 1,
            carbon_alerts INTEGER DEFAULT 1,
            cost_alerts INTEGER DEFAULT 1,
            system_updates INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create notification templates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT UNIQUE,
            notification_type TEXT,
            title_template TEXT,
            message_template TEXT,
            priority TEXT DEFAULT 'normal',
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Initialize default templates
    init_default_templates()


def init_default_templates():
    """Initialize default notification templates."""
    templates = [
        {
            'template_name': 'grid_overload',
            'notification_type': 'critical',
            'title_template': '⚠️ Grid Overload Detected',
            'message_template': 'Grid overload detected at hour {hour}: {power:.2f} kW. System has tripped.',
            'priority': 'critical'
        },
        {
            'template_name': 'high_cost',
            'notification_type': 'warning',
            'title_template': '💰 High Energy Cost Alert',
            'message_template': 'Hourly energy cost exceeded threshold: ₹{cost:.2f}',
            'priority': 'warning'
        },
        {
            'template_name': 'carbon_goal',
            'notification_type': 'info',
            'title_template': '🌍 Carbon Goal Achieved',
            'message_template': 'Carbon emissions reduced by {savings:.1f}% today!',
            'priority': 'info'
        },
        {
            'template_name': 'battery_low',
            'notification_type': 'warning',
            'title_template': '🔋 Low Battery Warning',
            'message_template': 'Battery SOC below 20%: {soc:.1f} kWh',
            'priority': 'warning'
        },
        {
            'template_name': 'daily_summary',
            'notification_type': 'info',
            'title_template': '📊 Daily Summary',
            'message_template': 'Today\'s total cost: ₹{cost:.2f}, Emissions: {emissions:.1f} kg, Renewable: {renewable:.1f}%',
            'priority': 'info'
        },
        {
            'template_name': 'system_optimization',
            'notification_type': 'info',
            'title_template': '✨ Optimization Complete',
            'message_template': 'System optimization completed with {renewable:.1f}% renewable usage.',
            'priority': 'info'
        }
    ]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for template in templates:
        cursor.execute('''
            INSERT OR IGNORE INTO notification_templates 
            (template_name, notification_type, title_template, message_template, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            template['template_name'],
            template['notification_type'],
            template['title_template'],
            template['message_template'],
            template['priority']
        ))
    
    conn.commit()
    conn.close()


# Notification CRUD Operations
def create_notification(
    username: str,
    notification_type: str,
    title: str,
    message: str,
    priority: str = 'normal',
    expires_in_hours: int = 24
) -> int:
    """
    Create a new notification.
    
    Args:
        username: Target username
        notification_type: Type of notification (critical, warning, info)
        title: Notification title
        message: Notification message
        priority: Priority level (low, normal, high, critical)
        expires_in_hours: Hours until notification expires
        
    Returns:
        Notification ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    expires_at = (datetime.now() + timedelta(hours=expires_in_hours)).isoformat()
    
    cursor.execute('''
        INSERT INTO notifications 
        (username, notification_type, title, message, priority, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, notification_type, title, message, priority, expires_at))
    
    notification_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return notification_id


def get_notifications(
    username: str,
    unread_only: bool = False,
    limit: int = 50,
    notification_type: Optional[str] = None
) -> pd.DataFrame:
    """
    Get notifications for a user.
    
    Args:
        username: Target username
        unread_only: If True, return only unread notifications
        limit: Maximum number of notifications to return
        notification_type: Filter by type (critical, warning, info)
        
    Returns:
        DataFrame of notifications
    """
    conn = get_connection()
    
    query = "SELECT * FROM notifications WHERE username = ?"
    params = [username]
    
    if unread_only:
        query += " AND is_read = 0"
    
    if notification_type:
        query += " AND notification_type = ?"
        params.append(notification_type)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df


def mark_notification_read(notification_id: int) -> bool:
    """Mark a notification as read."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE notifications SET is_read = 1 WHERE id = ?',
        (notification_id,)
    )
    
    conn.commit()
    conn.close()
    
    return cursor.rowcount > 0


def mark_all_notifications_read(username: str) -> int:
    """Mark all notifications as read for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE notifications SET is_read = 1 WHERE username = ? AND is_read = 0',
        (username,)
    )
    
    count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return count


def delete_notification(notification_id: int) -> bool:
    """Delete a notification."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM notifications WHERE id = ?', (notification_id,))
    conn.commit()
    conn.close()
    
    return cursor.rowcount > 0


def delete_expired_notifications() -> int:
    """Delete expired notifications."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'DELETE FROM notifications WHERE expires_at < ?',
        (datetime.now().isoformat(),)
    )
    
    count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return count


def get_unread_count(username: str) -> int:
    """Get count of unread notifications for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT COUNT(*) FROM notifications WHERE username = ? AND is_read = 0',
        (username,)
    )
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count


# Notification Preferences
def get_notification_preferences(username: str) -> Dict:
    """Get notification preferences for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT * FROM notification_preferences WHERE username = ?',
        (username,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    else:
        # Return default preferences
        return {
            'email_alerts': 1,
            'push_notifications': 1,
            'critical_alerts': 1,
            'daily_summary': 1,
            'weekly_report': 0,
            'grid_alerts': 1,
            'carbon_alerts': 1,
            'cost_alerts': 1,
            'system_updates': 1
        }


def save_notification_preferences(
    username: str,
    preferences: Dict
) -> Tuple[bool, str]:
    """
    Save notification preferences for a user.
    
    Args:
        username: Target username
        preferences: Dictionary of preference values
        
    Returns:
        Tuple of (success, message)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if preferences exist
    cursor.execute(
        'SELECT id FROM notification_preferences WHERE username = ?',
        (username,)
    )
    
    existing = cursor.fetchone()
    
    now = datetime.now().isoformat()
    
    if existing:
        # Update existing preferences
        cursor.execute('''
            UPDATE notification_preferences SET
                email_alerts = ?,
                push_notifications = ?,
                critical_alerts = ?,
                daily_summary = ?,
                weekly_report = ?,
                grid_alerts = ?,
                carbon_alerts = ?,
                cost_alerts = ?,
                system_updates = ?,
                updated_at = ?
            WHERE username = ?
        ''', (
            preferences.get('email_alerts', 1),
            preferences.get('push_notifications', 1),
            preferences.get('critical_alerts', 1),
            preferences.get('daily_summary', 1),
            preferences.get('weekly_report', 0),
            preferences.get('grid_alerts', 1),
            preferences.get('carbon_alerts', 1),
            preferences.get('cost_alerts', 1),
            preferences.get('system_updates', 1),
            now,
            username
        ))
    else:
        # Insert new preferences
        cursor.execute('''
            INSERT INTO notification_preferences
            (username, email_alerts, push_notifications, critical_alerts,
             daily_summary, weekly_report, grid_alerts, carbon_alerts,
             cost_alerts, system_updates, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            username,
            preferences.get('email_alerts', 1),
            preferences.get('push_notifications', 1),
            preferences.get('critical_alerts', 1),
            preferences.get('daily_summary', 1),
            preferences.get('weekly_report', 0),
            preferences.get('grid_alerts', 1),
            preferences.get('carbon_alerts', 1),
            preferences.get('cost_alerts', 1),
            preferences.get('system_updates', 1),
            now,
            now
        ))
    
    conn.commit()
    conn.close()
    
    return True, "Preferences saved successfully"


# Notification Templates
def get_template(template_name: str) -> Optional[Dict]:
    """Get a notification template by name."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT * FROM notification_templates WHERE template_name = ? AND is_active = 1',
        (template_name,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def render_template(template_name: str, context: Dict) -> Tuple[str, str]:
    """
    Render a notification template with context.
    
    Args:
        template_name: Name of the template
        context: Dictionary of values to substitute
        
    Returns:
        Tuple of (title, message)
    """
    template = get_template(template_name)
    
    if not template:
        return "Notification", "Template not found"
    
    title = template['title_template']
    message = template['message_template']
    
    # Simple string formatting
    try:
        title = title.format(**context)
        message = message.format(**context)
    except KeyError as e:
        message = f"Template error: missing key {e}"
    
    return title, message


# Quick notification creation functions
def notify_grid_overload(username: str, hour: int, power: float):
    """Create notification for grid overload."""
    create_notification(
        username=username,
        notification_type='critical',
        title='⚠️ Grid Overload Detected',
        message=f'Grid overload detected at hour {hour}: {power:.2f} kW. System has tripped.',
        priority='critical'
    )


def notify_high_cost(username: str, cost: float, threshold: float = 100):
    """Create notification for high energy cost."""
    if cost > threshold:
        create_notification(
            username=username,
            notification_type='warning',
            title='💰 High Energy Cost Alert',
            message=f'Hourly energy cost exceeded threshold: ₹{cost:.2f}',
            priority='warning'
        )


def notify_carbon_achievement(username: str, savings_pct: float):
    """Create notification for carbon goal achievement."""
    create_notification(
        username=username,
        notification_type='info',
        title='🌍 Carbon Goal Achieved',
        message=f'Carbon emissions reduced by {savings_pct:.1f}% today!',
        priority='info'
    )


def notify_low_battery(username: str, soc: float, threshold: float = 20):
    """Create notification for low battery."""
    if soc < threshold:
        create_notification(
            username=username,
            notification_type='warning',
            title='🔋 Low Battery Warning',
            message=f'Battery SOC below {threshold}%: {soc:.1f} kWh',
            priority='warning'
        )


def notify_daily_summary(username: str, cost: float, emissions: float, renewable: float):
    """Create daily summary notification."""
    create_notification(
        username=username,
        notification_type='info',
        title='📊 Daily Summary',
        message=f"Today's totals: Cost ₹{cost:.2f}, Emissions {emissions:.1f} kg, Renewable {renewable:.1f}%",
        priority='info',
        expires_in_hours=48
    )


def notify_optimization_complete(username: str, renewable_pct: float, cost: float):
    """Create notification for optimization completion."""
    create_notification(
        username=username,
        notification_type='info',
        title='✨ Optimization Complete',
        message=f'System optimization completed with {renewable_pct:.1f}% renewable usage. Cost: ₹{cost:.2f}',
        priority='info'
    )


# UI Components
def show_notification_center():
    """Display the notification center UI."""
    username = st.session_state.get('username', 'guest')
    
    st.subheader("🔔 Notification Center")
    
    # Get unread count
    unread_count = get_unread_count(username)
    if unread_count > 0:
        st.markdown(f"**{unread_count} unread notifications**")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📖 Mark All as Read"):
                count = mark_all_notifications_read(username)
                st.success(f"Marked {count} notifications as read")
                st.rerun()
        with col2:
            if st.button("🗑️ Delete Read"):
                delete_expired_notifications()
                st.success("Cleaned up old notifications")
                st.rerun()
    else:
        st.info("No unread notifications")
    
    st.markdown("---")
    
    # Filter options
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_type = st.selectbox(
            "Filter by Type",
            ["All", "Critical", "Warning", "Info"]
        )
    with col2:
        show_unread = st.checkbox("Unread Only", value=False)
    
    # Get notifications
    notif_type = None if filter_type == "All" else filter_type.lower()
    notifications = get_notifications(
        username=username,
        unread_only=show_unread,
        limit=50,
        notification_type=notif_type
    )
    
    if notifications.empty:
        st.info("No notifications found")
        return
    
    # Display notifications
    for _, notif in notifications.iterrows():
        priority = notif.get('priority', 'normal')
        
        # Choose styling based on priority
        if priority == 'critical':
            icon = "🚨"
            border_color = "#e74c3c"
            bg_color = "#ffebee"
        elif priority == 'warning':
            icon = "⚠️"
            border_color = "#f39c12"
            bg_color = "#fff3e0"
        else:
            icon = "ℹ️"
            border_color = "#3498db"
            bg_color = "#e3f2fd"
        
        # Notification card
        with st.container():
            st.markdown(f"""
            <div style="
                border: 2px solid {border_color};
                background-color: {bg_color};
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
            ">
                <strong>{icon} {notif.get('title', 'Notification')}</strong>
                <p style="margin: 5px 0;">{notif.get('message', '')}</p>
                <small style="color: #666;">
                    {notif.get('created_at', '')} | 
                    Priority: {priority.capitalize()}
                    {'| 🔴 Unread' if not notif.get('is_read', 0) else ''}
                </small>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            cols = st.columns([1, 1, 1])
            with cols[0]:
                if not notif.get('is_read', 0):
                    if st.button("Mark Read", key=f"read_{notif['id']}"):
                        mark_notification_read(notif['id'])
                        st.rerun()
            with cols[1]:
                if st.button("Delete", key=f"del_{notif['id']}"):
                    delete_notification(notif['id'])
                    st.rerun()
            with cols[2]:
                if st.button("Details", key=f"detail_{notif['id']}"):
                    st.session_state[f"show_detail_{notif['id']}"] = True


def show_notification_settings():
    """Display notification settings page."""
    st.title("🔔 Notification Settings")
    
    username = st.session_state.get('username')
    if not username:
        st.error("Please log in to manage settings")
        return
    
    # Get current preferences
    prefs = get_notification_preferences(username)
    
    with st.form("notification_settings"):
        st.subheader("📧 Email Notifications")
        email_alerts = st.checkbox(
            "Enable Email Alerts",
            value=bool(prefs.get('email_alerts', 1)),
            help="Receive notifications via email"
        )
        
        st.subheader("🔔 In-App Notifications")
        push_notifications = st.checkbox(
            "Enable Push Notifications",
            value=bool(prefs.get('push_notifications', 1)),
            help="Receive notifications in the app"
        )
        
        st.subheader("⚠️ Alert Types")
        col1, col2 = st.columns(2)
        
        with col1:
            critical_alerts = st.checkbox(
                "Critical Alerts (Grid Overloads)",
                value=bool(prefs.get('critical_alerts', 1))
            )
            grid_alerts = st.checkbox(
                "Grid Alerts",
                value=bool(prefs.get('grid_alerts', 1))
            )
            carbon_alerts = st.checkbox(
                "Carbon Tracking Alerts",
                value=bool(prefs.get('carbon_alerts', 1))
            )
        
        with col2:
            cost_alerts = st.checkbox(
                "Cost Alerts",
                value=bool(prefs.get('cost_alerts', 1))
            )
            daily_summary = st.checkbox(
                "Daily Summary",
                value=bool(prefs.get('daily_summary', 1))
            )
            weekly_report = st.checkbox(
                "Weekly Report",
                value=bool(prefs.get('weekly_report', 0))
            )
        
        system_updates = st.checkbox(
            "System Updates",
            value=bool(prefs.get('system_updates', 1))
        )
        
        submit = st.form_submit_button("💾 Save Settings")
        
        if submit:
            new_prefs = {
                'email_alerts': int(email_alerts),
                'push_notifications': int(push_notifications),
                'critical_alerts': int(critical_alerts),
                'daily_summary': int(daily_summary),
                'weekly_report': int(weekly_report),
                'grid_alerts': int(grid_alerts),
                'carbon_alerts': int(carbon_alerts),
                'cost_alerts': int(cost_alerts),
                'system_updates': int(system_updates)
            }
            
            success, msg = save_notification_preferences(username, new_prefs)
            if success:
                st.success(msg)
            else:
                st.error(msg)
    
    # Test notification
    st.markdown("---")
    st.subheader("🧪 Test Notification")
    
    if st.button("Send Test Notification"):
        create_notification(
            username=username,
            notification_type='info',
            title='🧪 Test Notification',
            message='This is a test notification to verify your notification settings are working correctly.',
            priority='info'
        )
        st.success("Test notification sent!")
        st.rerun()


# Initialize on import
if __name__ == "__main__":
    init_notifications()
    print("Notification system initialized successfully!")

