#!/usr/bin/env python3
"""
Snowflake Setup Script for Smart Microgrid Manager Pro
Run this script to configure and test Snowflake connection.
"""

import os
import sys
import getpass

def get_input(prompt, default=None):
    """Get user input with optional default."""
    if default:
        value = input(f"{prompt} [{default}]: ").strip()
        return value if value else default
    return input(f"{prompt}: ").strip()

def main():
    print("=" * 60)
    print("🚀 Snowflake Setup for Smart Microgrid Manager Pro")
    print("=" * 60)
    print()
    
    # Get Snowflake credentials
    print("📋 Step 1: Enter Snowflake Credentials")
    print("-" * 40)
    
    account = get_input("Snowflake Account Identifier", "xxxxxxx.us-east-1.aws")
    user = get_input("Snowflake Username")
    
    # Get password securely
    while True:
        password = getpass.getpass("Snowflake Password: ")
        if password:
            break
        print("Password cannot be empty!")
    
    warehouse = get_input("Warehouse name", "MICROGRID_WH")
    database = get_input("Database name", "MICROGRID_DB")
    schema = get_input("Schema name", "PUBLIC")
    role = get_input("Role (optional, press Enter to skip)", "")
    
    print()
    print("💾 Step 2: Creating Configuration File")
    print("-" * 40)
    
    # Create .env file
    env_content = f"""# Snowflake Configuration
SNOWFLAKE_ACCOUNT={account}
SNOWFLAKE_USER={user}
SNOWFLAKE_PASSWORD={password}
SNOWFLAKE_WAREHOUSE={warehouse}
SNOWFLAKE_DATABASE={database}
SNOWFLAKE_SCHEMA={schema}
"""
    if role:
        env_content += f"SNOWFLAKE_ROLE={role}\n"
    
    env_content += """
# Application Settings
SECRET_KEY=your-super-secret-key-change-in-production

# Session Settings
SESSION_TIMEOUT_MINUTES=30
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file with your credentials")
    print()
    
    # Create SQL setup script
    print("📝 Step 3: Creating Snowflake SQL Setup")
    print("-" * 40)
    
    sql_content = f"""-- Snowflake Setup Script for Smart Microgrid Manager Pro
-- Run these commands in Snowflake Worksheets

-- Create Warehouse
CREATE WAREHOUSE IF NOT EXISTS {warehouse} 
WITH WAREHOUSE_SIZE = 'X-SMALL' 
AUTO_SUSPEND = 300 
AUTO_RESUME = TRUE;

-- Create Database
CREATE DATABASE IF NOT EXISTS {database};

-- Create Schema
CREATE SCHEMA IF NOT EXISTS {database}.{schema};

-- Grant privileges to user
GRANT ALL PRIVILEGES ON DATABASE {database} TO {user};
GRANT ALL PRIVILEGES ON SCHEMA {database}.{schema} TO {user};
GRANT ALL PRIVILEGES ON WAREHOUSE {warehouse} TO {user};

-- Verify setup
SHOW WAREHOUSES;
SHOW DATABASES;
SHOW SCHEMAS IN DATABASE {database};
"""
    
    with open('snowflake_setup.sql', 'w') as f:
        f.write(sql_content)
    
    print("✅ Created snowflake_setup.sql")
    print()
    print("📦 Step 4: Running Snowflake Connection Test")
    print("-" * 40)
    
    # Test connection
    try:
        import snowflake.connector
        
        print("🔌 Connecting to Snowflake...")
        
        conn = snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            warehouse=warehouse,
            database=database,
            schema=schema,
        )
        
        print("✅ Successfully connected to Snowflake!")
        
        # Create warehouse, database, schema
        cursor = conn.cursor()
        
        print("🏗️  Creating warehouse, database, and schema...")
        
        cursor.execute(f"CREATE WAREHOUSE IF NOT EXISTS {warehouse} "
                      f"WITH WAREHOUSE_SIZE = 'X-SMALL' "
                      f"AUTO_SUSPEND = 300 AUTO_RESUME = TRUE")
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {database}.{schema}")
        
        print("✅ Warehouse, database, and schema created!")
        
        # Run schema creation
        print("📋 Creating application tables...")
        
        # Import and run schema creation
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from snowflake_db import SnowflakeMicrogridDB, SnowflakeConfig
        
        config = SnowflakeConfig(
            account=account,
            user=user,
            password=password,
            warehouse=warehouse,
            database=database,
            schema=schema,
            role=role if role else None,
        )
        
        db = SnowflakeMicrogridDB(config)
        
        if db.connected:
            print("📦 Initializing schema (creating tables)...")
            db.initialize_schema()
            print("✅ All tables created successfully!")
            
            # Populate time dimension
            print("⏰ Populating time dimension...")
            db.populate_time_dimension()
            print("✅ Time dimension populated!")
            
            db.close()
        else:
            print("⚠️  Connected but initialization skipped (check logs)")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 60)
        print("🎉 Snowflake Setup Complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Run: streamlit run app.py")
        print("2. Your app will connect to Snowflake automatically!")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Please check your credentials and try again.")
        print("Make sure your Snowflake account is active.")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("Please install Snowflake connector:")
        print("  pip install snowflake-connector-python snowflake-snowpark-python")
        sys.exit(1)

