import os
from dotenv import load_dotenv
import requests
from flask import Flask, request, render_template

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

@app.route('/', methods=['GET', 'POST'])
def home():
    routes = None
    weather = None
    if request.method == 'POST':
        location = request.form['location']
        distance = float(request.form['distance'])
        weather = get_weather(location)
        routes = [
            f"Scenic park in {location}, approx {distance} km",
            f"Lake loop near {location}, approx {distance * 1.2:.1f} km",
            f"Neighborhood trail in {location}, approx {distance * 0.8:.1f} km"
        ]
    return render_template('index.html', routes=routes, weather=weather)

if __name__ == '__main__':
    app.run(debug=True)
