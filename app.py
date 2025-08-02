from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import os
import sqlite3
import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# --- Database setup ---
def init_db():
    with sqlite3.connect('db.sqlite3') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            category TEXT,
            latitude REAL,
            longitude REAL,
            images TEXT,
            anonymous INTEGER,
            status TEXT,
            created_at TEXT
        )''')
        conn.commit()

init_db()

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        anonymous = int(request.form.get('anonymous', 0))
        images = []

        for i in range(1, 4):
            img = request.files.get(f'image{i}')
            if img:
                filename = secure_filename(img.filename)
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                img.save(img_path)
                images.append(img_path)

        with sqlite3.connect('db.sqlite3') as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO reports 
                         (title, description, category, latitude, longitude, images, anonymous, status, created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, 'Reported', ?)''',
                      (title, description, category, latitude, longitude, ';'.join(images), anonymous, datetime.datetime.now()))
            conn.commit()
        return redirect(url_for('index'))
    return render_template('report.html')

@app.route('/api/issues')
def issues_api():
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    distance = float(request.args.get('distance', 5))  # in km

    def within_distance(lat1, lon1, lat2, lon2, km):
        from geopy.distance import geodesic
        return geodesic((lat1, lon1), (lat2, lon2)).km <= km

    with sqlite3.connect('db.sqlite3') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM reports WHERE status != 'Hidden'")
        data = []
        for row in c.fetchall():
            if within_distance(lat, lon, row[4], row[5], distance):
                data.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'category': row[3],
                    'lat': row[4],
                    'lon': row[5],
                    'images': row[6].split(';'),
                    'anonymous': bool(row[7]),
                    'status': row[8],
                    'created_at': row[9]
                })
        return jsonify(data)

@app.route('/admin')
def admin():
    with sqlite3.connect('db.sqlite3') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM reports")
        issues = c.fetchall()
    return render_template('admin.html', issues=issues)

if __name__ == '__main__':
    app.run(debug=True)
