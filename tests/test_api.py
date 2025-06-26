import pytest
from app import app
from unittest.mock import patch, Mock, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.requests.get')
@patch('app.requests.post')
def test_generate_route_success(mock_post, mock_get, client):
    # Mock the OpenRouteService route response
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
        'distance': 3
    })

    assert response.status_code == 200
    data = response.get_json()
    assert "route" in data
    assert "weather" in data

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
