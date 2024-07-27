from flask import Flask, request, Response
import json
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = 'kualitas_udara_data.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kelembapan REAL NOT NULL,
                suhu REAL NOT NULL,
                ppm REAL,
                kualitas TEXT,
                timestamp TEXT NOT NULL
            )
        ''')
    conn.close()

create_table()

@app.route('/sensor/data', methods=["POST"])
def sensor():
    if request.method == 'POST':
        try:
            data = request.json
            app.logger.info(f"Data diterima: {data}")
            kelembapan = data["kelembapan"]
            suhu = data["suhu"]
            ppm = data.get("ppm", None)
            kualitas = data.get("kualitas", "Tidak diketahui")
            
            # Ambil waktu saat ini dalam format YYYY-MM-DD HH:MM:SS
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            conn = get_db_connection()
            with conn:
                conn.execute('''
                    INSERT INTO sensor_data (kelembapan, suhu, ppm, kualitas, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (kelembapan, suhu, ppm, kualitas, timestamp))
            conn.close()

            response_data = {
                'pesan': 'Data berhasil disimpan'
            }

            response = Response(
                json.dumps(response_data),
                status=200,
                mimetype='application/json'
            )

            return response

        except Exception as e:
            app.logger.error(f"Kesalahan dalam memproses permintaan: {e}")
            response_data = {
                'pesan': 'Gagal memproses permintaan',
                'error': str(e)
            }
            response = Response(
                json.dumps(response_data),
                status=400,
                mimetype='application/json'
            )
            return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8502)
