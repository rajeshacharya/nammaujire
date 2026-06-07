import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nammaujire.settings")
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("DELETE FROM django_migrations WHERE app='locations'")
print('Deleted locations from django_migrations')
