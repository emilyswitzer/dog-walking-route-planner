import os
import json
import math
import random
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify
from flask_migrate import Migrate
import requests

from config import Config
from models import db, Walk

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
with app.app_context():
    db.create_all()

migrate = Migrate(app, db)


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


def create_route_coordinates(lat, lon, distance_km, steps=10):
    segment_length = distance_km / steps
    bearing = random.uniform(0, 360)
    coords = [(lat, lon)]

    for _ in range(steps):
        bearing += random.uniform(-45, 45)
        bearing %= 360

        delta_lat = (segment_length / 111) * math.cos(math.radians(bearing))
        delta_lon = (segment_length / (111 * math.cos(math.radians(lat)))) * math.sin(math.radians(bearing))

        lat += delta_lat
        lon += delta_lon
        coords.append((lat, lon))
    return coords


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate-route', methods=['POST'])
def generate_route():
    try:
        data = request.json
        if 'lat' not in data or 'lon' not in data or 'distance' not in data:
            return jsonify({'error': 'Missing required parameters'}), 400

        try:
            lat = float(data['lat'])
            lon = float(data['lon'])
            distance = float(data['distance'])
            duration = float(data.get('duration', 0))
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid parameter types'}), 400

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({'error': 'Invalid coordinates'}), 400

        if not (0.5 <= distance <= 10):
            return jsonify({'error': 'Distance must be between 0.5 and 10 km'}), 400

        duration_seconds = int(duration * 60)

        routes = []
        for i in range(3):
            variation_factor = 0.9 + 0.1 * i
            varied_route = create_route_coordinates(lat, lon, distance * variation_factor)
            if varied_route:
                routes.append(varied_route)

        if not routes:
            return jsonify({"error": "Failed to generate any routes."}), 500

        # Weather
        api_key = os.getenv("OPENWEATHER_API_KEY")
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        try:
            weather_resp = requests.get(weather_url)
            weather_resp.raise_for_status()
            weather_json = weather_resp.json()
            temperature = weather_json['main']['temp']
            condition = weather_json['weather'][0]['main']
            description = weather_json['weather'][0]['description']
        except Exception:
            temperature = condition = description = None

        # Dog spots
        spots = get_dog_friendly_spots(lat, lon)
        dog_parks = [s['name'] for s in spots if s['type'] == 'dog_park']

        difficulty = 'easy' if distance <= 2 else 'medium' if distance <= 4 else 'hard'

        return jsonify({
            "routes": routes,
            "weather": {
                "temperature": temperature,
                "condition": condition,
                "description": description
            },
            "dog_parks": dog_parks,
            "difficulty": difficulty,
            "duration": duration_seconds
        })

    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500


@app.route('/save-walk', methods=['POST'])
def save_walk():
    data = request.json
    try:
        walk = Walk(
            lat=float(data['lat']),
            lon=float(data['lon']),
            distance=float(data['distance']),
            duration=int(data['duration']),
            timestamp=datetime.utcnow(),
            temperature=float(data['temperature']) if data.get('temperature') else None,
            condition=data.get('condition'),
            dog_parks_visited=json.dumps(data.get('dog_parks_visited', [])),
            difficulty=data.get('difficulty', 'medium'),
            route=json.dumps(data.get('route')) if data.get('route') else None
        )
        db.session.add(walk)
        db.session.commit()
        return jsonify({"message": "Walk saved successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Invalid or incomplete data'}), 400


@app.route('/api/walks', methods=['GET'])
def api_walks():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Filters from query params
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    min_distance = request.args.get('min_distance', type=float)
    max_distance = request.args.get('max_distance', type=float)

    query = Walk.query

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        query = query.filter(Walk.timestamp >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(Walk.timestamp < end_date)


    if min_distance is not None:
        query = query.filter(Walk.distance >= min_distance)
    if max_distance is not None:
        query = query.filter(Walk.distance <= max_distance)

    # Order by timestamp desc and paginate
    walks_pagination = query.order_by(Walk.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)

    walks = [{
        'id': w.id,
        'lat': w.lat,
        'lon': w.lon,
        'distance': w.distance,
        'timestamp': w.timestamp.isoformat(),
        'temperature': w.temperature,
        'condition': w.condition,
        'dog_parks_visited': w.dog_parks_visited,
        'difficulty': w.difficulty,
        'duration': w.duration
    } for w in walks_pagination.items]

    return jsonify({
        "page": page,
        "pages": walks_pagination.pages,
        "total": walks_pagination.total,
        "walks": walks
    })
    
@app.route('/walks')
def walks_page():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    walks_pagination = Walk.query.order_by(Walk.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    walks = walks_pagination.items

    return render_template('walks.html', walks=walks, pagination=walks_pagination)


@app.route('/dog-spots', methods=['POST'])
def dog_spots():
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')
    if not lat or not lon:
        return jsonify({"error": "Missing coordinates"}), 400

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
        response = requests.post("http://overpass-api.de/api/interpreter", data={"data": query})
        response.raise_for_status()
        elements = response.json().get("elements", [])
        spots = [{
            "lat": el["lat"],
            "lon": el["lon"],
            "type": el["tags"].get("leisure") or el["tags"].get("shop") or el["tags"].get("amenity") or el["tags"].get("waste"),
            "name": el["tags"].get("name", "Unnamed")
        } for el in elements]
        return jsonify({"spots": spots})
    except Exception as e:
        return jsonify({"error": "Failed to fetch dog-friendly spots"}), 500


@app.route('/weather', methods=['POST'])
def get_weather():
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')
    if not lat or not lon:
        return jsonify({'error': 'Missing coordinates'}), 400

    api_key = app.config.get("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

    try:
        response = requests.get(url)
        response.raise_for_status()
        weather = response.json()
        temp = weather['main']['temp']
        condition = weather['weather'][0]['main']
        description = weather['weather'][0]['description']
        icon = weather['weather'][0]['icon']
        recommendation = (
            "Good" if 10 <= temp <= 25 and condition in ['Clear', 'Clouds'] else
            "Okay" if 5 <= temp <= 30 and condition in ['Drizzle', 'Mist', 'Clouds', 'Rain'] else
            "Skip"
        )
        return jsonify({
            "temperature": temp,
            "condition": condition,
            "description": description,
            "icon": icon,
            "recommendation": recommendation
        })
    except Exception:
        return jsonify({'error': 'Weather API request failed'}), 500


if __name__ == '__main__':
    app.run(debug=True)
