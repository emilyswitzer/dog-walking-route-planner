import os
from dotenv import load_dotenv
import requests
from flask import Flask, request, render_template, jsonify
from typing import List, Optional, Tuple
from flask import render_template
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
    

def get_dog_friendly_spots(lat, lon, radius=1500):
    overpass_url = "http://overpass-api.de/api/interpreter"

    query = f"""
    [out:json];
    (
      node["leisure"="dog_park"](around:{radius},{lat},{lon});
      node["shop"="pet"](around:{radius},{lat},{lon});
      node["amenity"="drinking_water"](around:{radius},{lat},{lon});
      node["amenity"="waste_basket"](around:{radius},{lat},{lon});
    );
    out body;
    """

    response = requests.post(overpass_url, data={"data": query})
    if response.status_code != 200:
        return []

    data = response.json()
    spots = []
    for element in data.get("elements", []):
        spot = {
            "lat": element["lat"],
            "lon": element["lon"],
            "type": element["tags"].get("leisure") or
                    element["tags"].get("shop") or
                    element["tags"].get("amenity"),
            "name": element["tags"].get("name", "Unnamed")
        }
        spots.append(spot)

    return spots

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

@app.route('/dog-spots', methods=['POST'])
def dog_spots():
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')

    if lat is None or lon is None:
        return jsonify({"error": "Missing latitude or longitude"}), 400

    # Overpass QL query to get dog-friendly places within 2km radius
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (
      node["leisure"="dog_park"](around:2000,{lat},{lon});
      node["shop"="pet"](around:2000,{lat},{lon});
      node["amenity"="drinking_water"](around:2000,{lat},{lon});
      node["waste"="dog_waste_bin"](around:2000,{lat},{lon});
    );
    out body;
    """

    try:
        response = requests.post(overpass_url, data=query)
        response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": "Failed to fetch dog-friendly spots", "details": str(e)}), 500

    data = response.json()
    spots = []
    for element in data.get('elements', []):
        tags = element.get('tags', {})
        spot_type = (
            tags.get('leisure') or
            tags.get('shop') or
            tags.get('amenity') or
            tags.get('waste') or
            "unknown"
        )
        spots.append({
            "id": element.get('id'),
            "lat": element.get('lat'),
            "lon": element.get('lon'),
            "type": spot_type,
            "name": tags.get('name', 'Unnamed')
        })

    return jsonify({"spots": spots})


if __name__ == '__main__':
    app.run(debug=True)
