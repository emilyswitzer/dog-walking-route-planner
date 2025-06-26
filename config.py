import os


basedir = os.path.abspath(os.path.dirname(__file__))
class Config:
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance', 'dog_walks.sqlite3')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ORS_API_KEY = os.getenv("ORS_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
