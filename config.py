import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24))
    
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Railway gives mysql://..., but we need mysql+pymysql://
        db_url = db_url.replace('mysql://', 'mysql+pymysql://', 1)
    SQLALCHEMY_DATABASE_URI = db_url or 'mysql+pymysql://root:asdfghjkl@localhost/medication_system'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
