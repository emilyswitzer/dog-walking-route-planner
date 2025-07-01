import unittest
from unittest.mock import patch, Mock
from app import app, create_route_coordinates
import json


class DogWalkingAppTests(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch("app.requests.post")
    def test_create_route_coordinates_function(self, mock_post):
        # Setup mock response data structure similar to ORS response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [
                            [-122.4194, 37.7749],
                            [-122.41, 37.78],
                            [-122.40, 37.79],
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        lat = 37.7749
        lon = -122.4194
        distance = 3  # km
        route = create_route_coordinates(lat, lon, distance)
        self.assertIsNotNone(route)
        self.assertIsInstance(route, list)
        self.assertGreater(len(route), 0)
        self.assertIsInstance(route[0], tuple)
        self.assertEqual(len(route[0]), 2)

    @patch("app.requests.post")
    def test_generate_route_endpoint_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
        "features": [
            {
                "geometry": {
                    "coordinates": [
                        [-122.4194, 37.7749],
                        [-122.41, 37.78],
                        [-122.40, 37.79],
                    ]
                }
            }
        ]
    }
        mock_post.return_value = mock_response

        data = {"lat": 37.7749, "lon": -122.4194, "distance": 3}
        response = self.app.post(
            "/generate-route", data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)

        # Check 'routes' key (plural)
        self.assertIn("routes", response_data)
        self.assertIsInstance(response_data["routes"], list)

        # Optionally check first route is a list of coordinates
        if response_data["routes"]:
            self.assertIsInstance(response_data["routes"][0], list)
            self.assertIsInstance(response_data["routes"][0][0], list)  # coordinate pair



    def test_generate_route_endpoint_missing_params(self):
        response = self.app.post(
            "/generate-route", data=json.dumps({}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertIn("error", response_data)
        
    @patch("app.requests.post")
    def test_dog_spots_endpoint_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "elements": [
                {
                    "lat": 37.7749,
                    "lon": -122.4194,
                    "tags": {"amenity": "drinking_water", "name": "Fountain Park"},
                },
                {"lat": 37.7750, "lon": -122.4195, "tags": {"leisure": "dog_park"}},
            ]
        }
        mock_post.return_value = mock_response

        data = {"lat": 37.7749, "lon": -122.4194}
        response = self.app.post(
            "/dog-spots", data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn("spots", response_data)
        self.assertIsInstance(response_data["spots"], list)
        self.assertEqual(len(response_data["spots"]), 2)
        self.assertEqual(response_data["spots"][0]["type"], "drinking_water")
        

    def test_dog_spots_missing_params(self):
        response = self.app.post('/dog-spots', data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        
        
    @patch('app.requests.get')
    def test_weather_endpoint_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'main': {'temp': 18.5},
            'weather': [{'main': 'Clear', 'description': 'clear sky', 'icon': '01d'}]
        }
        mock_get.return_value = mock_response

        payload = {
            'lat': 37.7749,
            'lon': -122.4194
        }

        response = self.app.post('/weather', json=payload)
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIn('temperature', data)
        self.assertIn('condition', data)
        self.assertIn('recommendation', data)
        self.assertEqual(data['recommendation'], 'Good')


if __name__ == "__main__":
    unittest.main()
