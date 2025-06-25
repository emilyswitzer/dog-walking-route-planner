import os
from dotenv import load_dotenv
import requests
from flask import Flask, request, render_template
from typing import List, Optional, Tuple

load_dotenv()  # Loads the .env file

API_KEY = os.getenv('OPENWEATHER_API_KEY')

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

@app.route('/', methods=['GET', 'POST'])
def home():
    routes = None
    weather = None
    if request.method == 'POST':
        location = request.form['location']
        distance = float(request.form['distance'])
        weather = get_weather(location)
        coordinates = get_coordinates(location)
        dog_shops = []
        if coordinates:
            dog_shops = get_dog_friendly_shops(*coordinates)
        routes = [
            f"Scenic park in {location}, approx {distance} km",
            f"Lake loop near {location}, approx {distance * 1.2:.1f} km",
            f"Neighborhood trail in {location}, approx {distance * 0.8:.1f} km"
        ]
    return render_template('index.html', routes=routes, weather=weather, dog_shops=dog_shops)

if __name__ == '__main__':
    app.run(debug=True)
