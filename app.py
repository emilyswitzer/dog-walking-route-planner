import os
from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify
from flask_migrate import Migrate
from config import Config
import requests
import traceback
import polyline
import math, random
import json 
from datetime import datetime, timedelta

load_dotenv()


app = Flask(__name__)
app.config.from_object(Config)


from models import db, Walk
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
        # Slightly randomize bearing to simulate natural turns
        bearing += random.uniform(-45, 45)
        bearing %= 360

        # Approximate conversion: 1° lat ≈ 111 km
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
        lat = data.get('lat')
        lon = data.get('lon')
        distance = data.get('distance')
        duration = data.get('duration', 0)

        if lat is None or lon is None or distance is None:
            return jsonify({"error": "Latitude, longitude, and distance are required"}), 400

        try:
            lat = float(lat)
            lon = float(lon)
            distance = float(distance)
        except ValueError:
            return jsonify({'error': 'Invalid data types'}), 400

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({'error': 'Invalid latitude or longitude'}), 400

        if not (0.5 <= distance <= 10):
            return jsonify({'error': 'Distance must be between 0.5 and 10 km'}), 400

        duration_seconds = None
        if duration is not None:
            try:
                duration_seconds = int(float(duration) * 60)  # float to seconds
                if duration_seconds < 0:
                    return jsonify({'error': 'Duration must be non-negative'}), 400
            except Exception:
                return jsonify({'error': 'Invalid duration value'}), 400

      
        routes = []
        for i in range(3):
            variation_factor = 0.9 + 0.1 * i  # 90%, 100%, 110% of base distance
            varied_route = create_route_coordinates(lat, lon, distance * variation_factor)
            if varied_route:
                routes.append(varied_route)

        if not routes:
            return jsonify({"error": "Failed to generate any routes."}), 500

        # Weather fetch
        api_key = os.getenv("OPENWEATHER_API_KEY")
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        try:
            weather_resp = requests.get(weather_url)
            weather_resp.raise_for_status()
            weather_json = weather_resp.json()
            temperature = weather_json['main']['temp']
            condition = weather_json['weather'][0]['main']
            description = weather_json['weather'][0]['description']
        except Exception as e:
            print("Weather API fetch error:", e)
            temperature = None
            condition = None
            description = None

        # Dog spots
        spots = get_dog_friendly_spots(lat, lon)
        dog_parks = [s['name'] for s in spots if s['type'] == 'dog_park']

        # Difficulty
        difficulty = 'easy' if distance <= 2 else 'medium' if distance <= 4 else 'hard'

        # Duration in seconds
        duration_seconds = None
        try:
            duration_seconds = int(float(duration) * 60)
        except:
            pass

        print("Returning routes:", routes)

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
        print(f"Error in /generate-route: {e}")
        return jsonify({"error": "Internal server error. Please try again later."}), 500


@app.route('/dog-spots', methods=['POST'])
def dog_spots():
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')

    if lat is None or lon is None:
        return jsonify({"error": "Missing latitude or longitude"}), 400

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
    except Exception as e:
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
        weather_data = response.json()

        temp = weather_data['main']['temp']
        condition = weather_data['weather'][0]['main']
        description = weather_data['weather'][0]['description']
        icon = weather_data['weather'][0]['icon']

        if 10 <= temp <= 25 and condition in ['Clear', 'Clouds']:
            recommendation = 'Good'
        elif 5 <= temp <= 30 and condition in ['Drizzle', 'Mist', 'Clouds', 'Rain']:
            recommendation = 'Okay'
        else:
            recommendation = 'Skip'

        return jsonify({
            'temperature': temp,
            'condition': condition,
            'description': description,
            'icon': icon,
            'recommendation': recommendation
        })

    except Exception:
        return jsonify({'error': 'Weather API request failed'}), 500
    
@app.route('/walk-history', methods=['GET'])
def walk_history():
    walks = Walk.query.order_by(Walk.timestamp.desc()).all()
    history = []
    for walk in walks:
        history.append({
            "id": walk.id,
            "lat": walk.lat,
            "lon": walk.lon,
            "distance": walk.distance,
            "timestamp": walk.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": walk.temperature,
            "condition": walk.condition,
            "dog_parks_visited": json.loads(walk.dog_parks_visited or "[]"),
            "difficulty": walk.difficulty
        })
    return jsonify(history)


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

@app.route('/save-walk', methods=['POST'])
def save_walk():
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    distance = data.get('distance')
    duration = data.get('duration')

    # Required fields check
    if lat is None or lon is None or distance is None or duration is None:
        return jsonify({"error": "Missing walk data"}), 400

    # Optional fields
    temperature = data.get('temperature')
    condition = data.get('condition')
    dog_parks_visited = data.get('dog_parks_visited', [])
    difficulty = data.get('difficulty', 'medium')
    route = data.get('route')  # New: Persist full route coordinates

    try:
        lat = float(lat)
        lon = float(lon)
        distance = float(distance)
        duration = int(duration)

        if temperature is not None:
            temperature = float(temperature)

        if not isinstance(condition, (str, type(None))):
            raise ValueError("Condition must be a string")

        if not isinstance(dog_parks_visited, list):
            raise ValueError("dog_parks_visited must be a list")

        if difficulty not in ['easy', 'medium', 'hard']:
            raise ValueError("Invalid difficulty")

        if route is not None:
            if not isinstance(route, list) or not all(
                isinstance(coord, list) and len(coord) == 2 for coord in route
            ):
                raise ValueError("Invalid route format")

    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid data types or values: {str(e)}'}), 400

    # Range checks
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return jsonify({'error': 'Latitude or longitude out of range'}), 400
    if not (0.5 <= distance <= 50):
        return jsonify({'error': 'Distance out of acceptable range'}), 400
    if duration < 0:
        return jsonify({'error': 'Duration must be non-negative'}), 400

    # Serialize optional fields
    dog_parks_json = json.dumps(dog_parks_visited)
    route_json = json.dumps(route) if route else None

    # Create and save walk record
    walk = Walk(
        lat=lat,
        lon=lon,
        distance=distance,
        duration=duration,
        timestamp=datetime.utcnow(),
        temperature=temperature,
        condition=condition,
        dog_parks_visited=dog_parks_json,
        difficulty=difficulty,
        route=route_json  # Ensure your model has this column
    )

    try:
        db.session.add(walk)
        db.session.commit()
        return jsonify({"message": "Walk saved successfully"}), 201
    except Exception as e:
        db.session.rollback()
        print("Database error:", e)
        return jsonify({"error": "Failed to save walk to database"}), 500


if __name__ == '__main__':
    app.run(debug=True)
