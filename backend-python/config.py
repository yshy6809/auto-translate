import os

# Base directory of the backend application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Data directory configuration
DATA_DIR = os.path.join(BASE_DIR, 'data')
PROJECTS_DIR = os.path.join(DATA_DIR, 'projects')
DB_FILE = os.path.join(DATA_DIR, 'database.sqlite')

# Flask App Configuration
class Config:
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_FILE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Max 16MB upload
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-default-secret-key') # Good practice to have a secret key

# Ensure data directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)
