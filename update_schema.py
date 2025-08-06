#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django with basic settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cysafe_project.settings')

# Temporarily modify settings to avoid decouple
import django.conf
django.conf.settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(os.path.dirname(__file__), 'db.sqlite3'),
        }
    },
    INSTALLED_APPS=[
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'main',
    ],
    SECRET_KEY='django-insecure-temp-key-for-schema-update',
    DEBUG=True,
)

django.setup()

from django.db import connection

def update_schema():
    """Update the database schema to use individual fields instead of JSON"""
    
    try:
        with connection.cursor() as cursor:
            # Drop the existing table
            cursor.execute("DROP TABLE IF EXISTS cybercrime_data")
            print("✅ Dropped existing cybercrime_data table")
            
            # Create the new table with individual fields
            cursor.execute("""
                CREATE TABLE cybercrime_data (
                    id CHAR(32) PRIMARY KEY,
                    type VARCHAR(200) NOT NULL,
                    description TEXT NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    prevention_tip_1 VARCHAR(500),
                    prevention_tip_2 VARCHAR(500),
                    prevention_tip_3 VARCHAR(500),
                    prevention_tip_4 VARCHAR(500),
                    reporting_step_1 VARCHAR(500),
                    reporting_step_2 VARCHAR(500),
                    reporting_step_3 VARCHAR(500),
                    reporting_step_4 VARCHAR(500),
                    learn_more_clicks INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created new cybercrime_data table with individual fields")
            
    except Exception as e:
        print(f"❌ Error updating schema: {e}")

if __name__ == '__main__':
    update_schema() 