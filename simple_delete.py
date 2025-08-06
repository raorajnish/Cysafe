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
    SECRET_KEY='django-insecure-temp-key-for-deletion',
    DEBUG=True,
)

django.setup()

from main.models import CyberCrime

def delete_crime():
    """Delete crime with type 'type 12'"""
    
    try:
        # Find the crime
        crime = CyberCrime.objects.get(type="type 12")
        print(f"Found crime: {crime.type} (ID: {crime.id})")
        
        # Delete it
        crime.delete()
        print("✅ Crime 'type 12' has been deleted successfully!")
        
    except CyberCrime.DoesNotExist:
        print("❌ Crime with type 'type 12' not found in database.")
    except Exception as e:
        print(f"❌ Error deleting crime: {e}")

if __name__ == '__main__':
    delete_crime() 