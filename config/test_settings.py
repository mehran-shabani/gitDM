from .settings import *

# Use SQLite for testing to avoid database connection issues
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}