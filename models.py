from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Walk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    distance = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    temperature = db.Column(db.Float)
    condition = db.Column(db.String(50))
    dog_parks_visited = db.Column(db.Text)  # Storing as json
    difficulty = db.Column(db.String(20))  # easy, medium, hard

    def __repr__(self):
        return f"<Walk {self.id} at ({self.lat}, {self.lon})>"