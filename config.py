# import os

# class Config:
#     SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24))
    
#     db_url = os.environ.get('DATABASE_URL')
#     if db_url:
#         # Railway gives mysql://..., but we need mysql+pymysql://
#         db_url = db_url.replace('mysql://', 'mysql+pymysql://', 1)
#     SQLALCHEMY_DATABASE_URI = db_url or 'mysql+pymysql://root:asdfghjkl@localhost/medication_system'
    
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     WTF_CSRF_ENABLED = True
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24))
    
    db_host = os.environ.get('MYSQLHOST', 'localhost')
    db_port = os.environ.get('MYSQLPORT', '3306')
    db_user = os.environ.get('MYSQLUSER', 'root')
    db_password = os.environ.get('MYSQLPASSWORD', 'asdfghjkl')
    db_name = os.environ.get('MYSQLDATABASE', 'medication_system')
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
