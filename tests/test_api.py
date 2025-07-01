import pytest
from app import app, db
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta

from models import Walk

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.requests.get')   # For weather API
@patch('app.requests.post')  # For route API
def test_generate_route_success(mock_post, mock_get, client):
    # Mock the OpenRouteService route response to simulate multiple routes
    mock_post.return_value = MagicMock(status_code=200)
    mock_post.return_value.json.return_value = {
        "features": [{
            "geometry": {
                "coordinates": [[-122.4194, 37.7749], [-122.418, 37.775]]
            }
        }]
    }

    # Mock the OpenWeather response
    mock_get.return_value = MagicMock(status_code=200)
    mock_get.return_value.json.return_value = {
        "main": {"temp": 20},
        "weather": [{"main": "Clear", "description": "clear sky"}]
    }

    response = client.post('/generate-route', json={
        'lat': 37.7749,
        'lon': -122.4194,
        'distance': 3,
        'duration': 30  # include duration if required by your endpoint
    })

    assert response.status_code == 200
    data = response.get_json()
    
    # Check for multiple routes key (plural)
    assert "routes" in data
    assert isinstance(data["routes"], list)
    assert len(data["routes"]) > 0

    # Optional: Check weather data keys
    assert "weather" in data
    assert "temperature" in data["weather"]
    assert "condition" in data["weather"]

def test_generate_route_missing_params(client):
    response = client.post('/generate-route', json={
        'lat': 37.7749,
        'lon': -122.4194
        # missing distance
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_dog_spots_success(client):
    response = client.post('/dog-spots', json={
        'lat': 37.7749,
        'lon': -122.4194
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'spots' in data
    assert isinstance(data['spots'], list)

def test_dog_spots_missing_params(client):
    response = client.post('/dog-spots', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

@patch('app.requests.get')
def test_weather_success(mock_get, client):
    # Mock JSON response data for weather API
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "main": {"temp": 20.5},
        "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}]
    }
    mock_get.return_value = mock_response

    response = client.post('/weather', json={
        'lat': 37.7749,
        'lon': -122.4194
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['temperature'] == 20.5
    assert data['condition'] == "Clear"
    assert data['recommendation'] == "Good"

def test_weather_missing_params(client):
    response = client.post('/weather', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    


@patch('app.requests.post')
def test_dog_spots_api_failure(mock_post, client):
    # Simulate failure in Overpass API call
    mock_post.side_effect = Exception("API failure")

    response = client.post('/dog-spots', json={
        'lat': 37.7749,
        'lon': -122.4194
    })

    assert response.status_code == 500
    data = response.get_json()
    assert 'error' in data

@patch('app.requests.get')
def test_weather_api_failure(mock_get, client):
    # Simulate failure in OpenWeather API call
    mock_get.side_effect = Exception("API failure")

    response = client.post('/weather', json={
        'lat': 37.7749,
        'lon': -122.4194
    })

    assert response.status_code == 500
    data = response.get_json()
    assert 'error' in data
    
        
def test_api_get_walks(client):
    with app.app_context():
        walk = Walk(
            lat=37.7749,
            lon=-122.4194,
            distance=2,
            duration=900,
            timestamp=datetime.utcnow(),
            temperature=20.0,
            condition='Clear',
            dog_parks_visited='[]',
            difficulty='easy'
        )
        db.session.add(walk)
        db.session.commit()

    response = client.get('/api/walks')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert 'walks' in data
    assert 'page' in data
    assert 'total' in data
    assert isinstance(data['walks'], list)
    assert len(data['walks']) > 0
    
def test_api_walks_pagination(client):
    response = client.get('/api/walks?page=1&per_page=2')
    assert response.status_code == 200
    data = response.get_json()
    assert 'walks' in data
    assert 'page' in data

@patch('app.requests.get')
@patch('app.requests.post')
def test_generate_route_with_duration(mock_post, mock_get, client):
    mock_post.return_value = MagicMock(status_code=200)
    mock_post.return_value.json.return_value = {
        "features": [{
            "geometry": {
                "coordinates": [[-122.4194, 37.7749], [-122.418, 37.775]]
            }
        }]
    }

    mock_get.return_value = MagicMock(status_code=200)
    mock_get.return_value.json.return_value = {
        "main": {"temp": 20},
        "weather": [{"main": "Clear", "description": "clear sky"}]
    }

    response = client.post('/generate-route', json={
        'lat': 37.7749,
        'lon': -122.4194,
        'distance': 3,
        'duration': 45.5  # duration in minutes input
    })

    assert response.status_code == 200
    data = response.get_json()
    assert "duration" in data
    assert data["duration"] == int(45.5 * 60)  # expected in seconds
    

