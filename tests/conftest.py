import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lenme_project.settings')

def pytest_configure():
    if not settings.configured:
        django.setup()