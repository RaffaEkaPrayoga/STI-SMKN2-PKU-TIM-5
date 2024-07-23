import streamlit as st
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import sqlite3
import pandas as pd

# Memuat variabel lingkungan dari .env
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Menginisialisasi model AI
llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)

# Koneksi ke database SQLite
db_name = 'kualitas_udara_data.db'
table_name = 'sensor_data'

def fetch_latest_data(db_name, table_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Ambil data terbaru dari tabel
    query = f"SELECT suhu, kelembapan, ppm FROM {table_name} ORDER BY timestamp DESC LIMIT 1"
    cursor.execute(query)
    result = cursor.fetchone()

    conn.close()
    
    if result:
        return result
    else:
        raise ValueError("No data found in the database")

def fetch_predictions(db_name, table_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Ambil prediksi terbaru dari tabel
    query = f"SELECT prediksi_suhu, prediksi_kelembapan, prediksi_ppm FROM {table_name} ORDER BY timestamp DESC LIMIT 1"
    cursor.execute(query)
    result = cursor.fetchone()

    conn.close()
    
    if result:
        return result
    else:
        raise ValueError("No prediction data found in the database")

# Fungsi untuk menghasilkan rekomendasi menggunakan AI
def generate_recommendations(temperature, humidity, aqi, predicted_temperature, predicted_humidity, predicted_aqi):
    input_prompt = f"""
    Berikut adalah data terbaru dari sensor ESP32:
    - Temperature: {temperature} °C
    - Humidity: {humidity} %
    - AQI: {aqi} ppm

    Berikut adalah data prediksi untuk 24 jam ke depan:
    - Prediksi Temperature: {predicted_temperature} °C
    - Prediksi Humidity: {predicted_humidity} %
    - Prediksi AQI: {predicted_aqi} ppm

    Berdasarkan data di atas, buatlah beberapa saran dan rekomendasi untuk kepala sekolah, guru, dan siswa terkait kualitas udara:
    - Apakah kualitas udara saat ini baik atau buruk?
    - Apa yang harus dilakukan jika kualitas udara buruk?
    - Saran-saran lainnya terkait kesehatan dan tindakan yang harus diambil?
    """
    result = llm.invoke(input_prompt)
    return result.content

# Streamlit App
st.title('Sistem Pemantauan dan Peringatan Dini Kualitas Udara')

# Ambil data terbaru dan data prediksi dari database
temperature, humidity, aqi = fetch_latest_data(db_name, table_name)
predicted_temperature, predicted_humidity, predicted_aqi = fetch_predictions(db_name, table_name)

# Tampilkan data terbaru
st.header('Data Terbaru')
st.write(f'Temperature: {temperature} °C')
st.write(f'Humidity: {humidity} %')
st.write(f'AQI: {aqi} ppm')

# Tampilkan data prediksi
st.header('Data Prediksi untuk 24 Jam ke Depan')
st.write(f'Prediksi Temperature: {predicted_temperature} °C')
st.write(f'Prediksi Humidity: {predicted_humidity} %')
st.write(f'Prediksi AQI: {predicted_aqi} ppm')

# Tampilkan saran dan rekomendasi dari AI
recommendations = generate_recommendations(temperature, humidity, aqi, predicted_temperature, predicted_humidity, predicted_aqi)
st.header('Saran dan Rekomendasi dari AI')
st.write(recommendations)

# Chatbot untuk interaksi pengguna
st.header('Chatbot Kualitas Udara')
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input('Masukkan pertanyaan atau komentar Anda tentang kualitas udara:')
if user_input:
    st.session_state.chat_history.append({'user': user_input})
    response = llm.invoke(user_input)
    st.session_state.chat_history.append({'ai': response.content})

for chat in st.session_state.chat_history:
    if 'user' in chat:
        st.chat_message('user').write(chat['user'])
    else:
        st.chat_message('assistant').write(chat['ai'])