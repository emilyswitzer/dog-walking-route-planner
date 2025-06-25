from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    routes = None
    if request.method == 'POST':
        location = request.form['location']
        distance = float(request.form['distance'])
        # For now, just create dummy routes based on input
        routes = [
            f"Scenic park in {location}, approx {distance} km",
            f"Lake loop near {location}, approx {distance * 1.2:.1f} km",
            f"Neighborhood trail in {location}, approx {distance * 0.8:.1f} km"
        ]
    return render_template('index.html', routes=routes)

if __name__ == '__main__':
    app.run(debug=True)
