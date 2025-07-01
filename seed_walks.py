from models import Walk, db
from datetime import datetime, timedelta
import random

# Clear previous walks if needed
Walk.query.delete()

# Generate 10 sample walks
for i in range(11):
    walk = Walk(
        lat=37.77 + random.uniform(-0.01, 0.01),
        lon=-122.42 + random.uniform(-0.01, 0.01),
        distance=round(random.uniform(1.0, 5.0), 2),
        timestamp=datetime.utcnow() - timedelta(days=i),
        temperature=random.randint(15, 30),
        condition=random.choice(['Sunny', 'Cloudy', 'Rainy']),
        dog_parks_visited=random.choice(['["Park A"]', '["Park B"]', '["Park A", "Park C"]']),
        difficulty=random.choice(['Easy', 'Moderate', 'Hard']),
        duration=random.randint(1200, 5400)
    )
    db.session.add(walk)

db.session.commit()
print("Seeded 10 walks.")
