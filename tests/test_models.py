import pytest
from app import app, db
from models import Walk
from datetime import datetime

@pytest.fixture
def test_app():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory DB for testing
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_create_walk(test_app):
    with test_app.app_context():
        walk = Walk(
            lat=40.7128,
            lon=-74.0060,
            distance=5.0,
            timestamp=datetime.utcnow(),
            temperature=22.5,
            condition="Clear",
            dog_parks_visited='[]',
            difficulty="easy"
        )
        db.session.add(walk)
        db.session.commit()

        saved_walk = Walk.query.filter_by(lat=40.7128, lon=-74.0060).first()
        assert saved_walk is not None
        assert saved_walk.lat == 40.7128
        assert saved_walk.distance == 5.0
        assert saved_walk.condition == "Clear"

def test_update_walk(test_app):
    with test_app.app_context():
        walk = Walk(
            lat=40,
            lon=-70,
            distance=3.0,
            difficulty="medium"
        )
        db.session.add(walk)
        db.session.commit()

        walk_to_update = Walk.query.first()
        walk_to_update.distance = 4.5
        walk_to_update.difficulty = "hard"
        db.session.commit()

        updated_walk = Walk.query.first()
        assert updated_walk.distance == 4.5
        assert updated_walk.difficulty == "hard"

def test_delete_walk(test_app):
    with test_app.app_context():
        walk = Walk(
            lat=50,
            lon=-80,
            distance=2.5,
            difficulty="easy"
        )
        db.session.add(walk)
        db.session.commit()

        walk_to_delete = Walk.query.first()
        db.session.delete(walk_to_delete)
        db.session.commit()

        assert Walk.query.count() == 0

def test_walk_validation(test_app):
    with test_app.app_context():
        # Missing required fields lat, lon, distance should raise error when committing
        walk = Walk()
        db.session.add(walk)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()
        
def test_walk_model_duration(test_app):
    with app.app_context():
        walk = Walk(
            lat=37.7749,
            lon=-122.4194,
            distance=3.5,
            duration=3600,  # 1 hour in seconds
            timestamp=datetime.utcnow(),
            temperature=20.0,
            condition='Clear',
            dog_parks_visited='[]',
            difficulty='medium'
        )
        db.session.add(walk)
        db.session.commit()

        saved_walk = Walk.query.first()
        assert saved_walk.duration == 3600
        assert saved_walk.distance == 3.5
        
