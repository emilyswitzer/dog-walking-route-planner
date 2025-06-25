import os
from dotenv import load_dotenv
import requests
from flask import Flask, request, render_template, jsonify
from typing import List, Optional, Tuple
import polyline

load_dotenv()  # Loads the .env file

API_KEY = os.getenv('OPENWEATHER_API_KEY')
ORS_API_KEY = os.getenv("ORS_API_KEY")

app = Flask(__name__)

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        return f"{temp}°C, {description}"
    else:
        return "Weather data not available"
    
def get_coordinates(city: str) -> Optional[Tuple[float, float]]:
    """
    Get latitude and longitude for a city name using Nominatim API.


    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "dog-walking-route-planner/1.0"
    }
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return float(data["lat"]), float(data["lon"])
    else:
        return None


def get_dog_friendly_shops(lat: float, lon: float, radius: int = 2000) -> List[str]:
    """
    Query Overpass API to find dog-friendly shops within radius.

    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      node["shop"="pet"](around:{radius},{lat},{lon});
      node["shop"="dog"](around:{radius},{lat},{lon});
      node["leisure"="dog_park"](around:{radius},{lat},{lon});
    );
    out center;
    """
    response = requests.get(overpass_url, params={'data': query})
    places = []
    if response.status_code == 200:
        data = response.json()
        for element in data.get('elements', []):
            name = element.get('tags', {}).get('name')
            if name:
                places.append(name)
    return places

def generate_circular_route(lat, lon, distance_km):
    target_distance = distance_km * 1000  
    url = "https://api.openrouteservice.org/v2/directions/foot-walking/geojson"

    offset = distance_km * 0.009  
    coords = [[lon, lat], [lon + offset, lat]]

    body = {
        "coordinates": coords,
        "instructions": False,
        "units": "m"
    }

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=body, headers=headers)
    if response.status_code != 200:
        return None

    data = response.json()
    route_coords = data["features"][0]["geometry"]["coordinates"]
    route_latlon = [(coord[1], coord[0]) for coord in route_coords]

    return route_latlon


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-route', methods=['POST'])
def generate_route():
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    distance = data.get('distance')

    if lat is None or lon is None or distance is None:
        return jsonify({"error": "Missing parameters"}), 400

    route = generate_circular_route(lat, lon, distance)
    if route is None:
        return jsonify({"error": "Failed to generate route"}), 500

    return jsonify({"route": route})

if __name__ == '__main__':
    app.run(debug=True)
