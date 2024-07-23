import streamlit as st
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import sqlite3
import pandas as pd
from datetime import timedelta
import numpy as np
import plotly.express as px
import pickle
import streamlit.components.v1 as components

# Memuat variabel lingkungan dari .env
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Menginisialisasi model AI
llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)

# Koneksi ke database SQLite
db_name = 'kualitas_udara_data.db'
table_name = 'sensor_data'

# Load models
temp_model = pickle.load(open('temperature_model.sav', 'rb'))
hum_model = pickle.load(open('humidity_model.sav', 'rb'))
aqi_model = pickle.load(open('aqi_model.sav', 'rb'))

# Load scalers
temp_scaler = pickle.load(open('temperature_scaler.sav', 'rb'))
hum_scaler = pickle.load(open('humidity_scaler.sav', 'rb'))
aqi_scaler = pickle.load(open('aqi_scaler.sav', 'rb'))


def load_and_prepare_data(db_name, table_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    data_columns = ['id', 'kelembapan', 'suhu', 'ppm', 'kualitas', 'tahun', 'bulan', 'tanggal', 'jam', 'menit', 'timestamp']
    cursor.execute(f"SELECT {', '.join(data_columns)} FROM {table_name}")
    rows = cursor.fetchall()
    data = pd.DataFrame(rows, columns=data_columns)
    conn.close()
    return data

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

def prepare_input_data(data, target):
    window_length = 240  # Jumlah langkah waktu yang digunakan untuk prediksi
    X = []

    for i in range(window_length, len(data)):
        window_features = data.iloc[i - window_length:i][target].to_list()
        X.append(window_features)

    return np.array(X)

data = load_and_prepare_data('kualitas_udara_data.db', 'sensor_data')
data['timestamp'] = pd.to_datetime(data['timestamp'])

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

    Berdasarkan data di atas, buatlah beberapa saran dan rekomendasi untuk kepala sekolah, guru, dan siswa di sekolah pedesaan terkait kualitas udara:
    - Apakah kualitas udara saat ini baik atau buruk?
    - Apa yang harus dilakukan jika ada kualitas udara buruk?
    - Saran-saran lainnya terkait kesehatan dan tindakan yang harus diambil?
    - Apakah kualitas udara saat ini bisa untuk siswa bersekolah?
    """
    result = llm.invoke(input_prompt)
    return result.content

# Fungsi untuk prediksi
def predict_values(data, model, scaler, feature, hours_ahead=1):
    if len(data) < 300:
        return None, 'Data tidak cukup untuk melakukan prediksi. Harap kumpulkan lebih banyak data.'
    
    X_feature = prepare_input_data(data, feature)
    X_feature = scaler.transform(X_feature)
    current_window = X_feature[-1].reshape(1, -1)  # Start with the last available data window

    # Predicting the next 'hours_ahead' hours (points at 60-minute intervals)
    predictions = []
    for _ in range(hours_ahead):
        next_value = model.predict(current_window)[0]
        predictions.append(next_value)

        # Update the current_window to include the new prediction
        current_window = np.roll(current_window, -1)
        current_window[0, -1] = next_value

    # Persiapkan data untuk plot
    future_timestamps = [data['timestamp'].iloc[-1] + timedelta(hours=i) for i in range(1, hours_ahead + 1)]
    future_data = pd.DataFrame({'Waktu': future_timestamps, f'Prediksi {feature.capitalize()}': predictions})
    
    return future_data, None

# Fungsi untuk menampilkan prediksi dengan grafik yang memiliki border radius
def display_predictions(data, model, scaler, feature, color):
    st.header(f'Prediksi {feature.capitalize()}')

    future_data, warning = predict_values(data, model, scaler, feature, 24)

    if warning:
        st.warning(warning)
    else:
        st.subheader('Hasil Prediksi')
        st.write(f'Prediksi {feature.capitalize()} untuk 24 jam ke depan dimulai dari {future_data["Waktu"].iloc[0]} sampai {future_data["Waktu"].iloc[-1]}')


        st.subheader(f'Grafik Prediksi {feature.capitalize()} 24 Jam ke Depan')
        fig = px.line(future_data, x='Waktu', y=f'Prediksi {feature.capitalize()}', title=f'Prediksi {feature.capitalize()} 24 Jam ke Depan', line_shape='linear', color_discrete_sequence=[color])
        
        # Render Plotly chart with custom CSS for border radius
        html_string = f"""
        <style>
        .plotly-chart {{
            border-radius: 15px;
            overflow: hidden;
            background-color: black;
        }}
        </style>
        <div class="plotly-chart">
        {fig.to_html(include_plotlyjs='cdn')}
        </div>
        """
        components.html(html_string, height=600)

# Fungsi mengatur latar belakang
def set_bg(url: str):
    '''
    URL: Link atau alamat website untuk gambar latar belakang
    '''
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: linear-gradient(rgba(0, 0, 0, 0.95), rgba(0, 0, 0, 0.5)), url({url});
             background: url({url});
             background-size: cover;
             background-repeat: no-repeat;
             background-opacity: 0.3;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )
    return
    
set_bg("https://cdn.gencraft.com/prod/user/14e836fe-1fce-4f67-b5f3-fa2f86c26b7c/83b9d223-ff81-47a5-8e7e-9d9b29f9b8b1/image/image1_0.jpg?Expires=1721814032&Signature=fo9zMVldq1bBGP2NYuf14ybKWvOmebtLkrNNg0IKILYorNxt-6lWv32KT14PLeOrPc9s5SWwge5dXTdHR51Vlh2UOhvtZBtktA2u-3rMno6~CbxLqmHxPE6Bz-euli4SiPpbt6nhIjhHRUGJFzlKg~2ceOM3Az7GDcL57KZ5C472s5WdpGd5RVcFVAzKSE5VJ383HWQR9LKusD4mMFKf51-6q4keSc69a2rpxTtFdRzLO7rKpHL0DVykao--reWuwSqYi6IG6UVXFwmoZYs6neg28LsRGqVjup4wg8xKOmFL~de1CYB4Db2mclF9biVXz~Uab~PbtIg~xBFRwsKjdw__&Key-Pair-Id=K3RDDB1TZ8BHT8")

# Streamlit App
st.title('Sistem Pemantauan dan Peringatan Dini Kualitas Udara Untuk Sekolah Pedesaan')

# Navigasi halaman di sidebar
page = st.sidebar.radio('Pilih Halaman', ['Data Terbaru', 'Prediksi Suhu', 'Prediksi Kelembapan', 'Prediksi AQI', 'Saran dan Rekomendasi', 'Chatbot Kualitas Udara'])

# Ambil data terbaru dan data prediksi dari database
temperature, humidity, aqi = fetch_latest_data(db_name, table_name)

if page == 'Data Terbaru':
    st.header('Data Terbaru')
    st.write(f'Temperature: {temperature} °C')
    st.write(f'Humidity: {humidity} %')
    st.write(f'AQI: {aqi} ppm')

    st.write(data)

elif page == 'Prediksi Suhu':
    display_predictions(data, temp_model, temp_scaler, 'suhu', 'red')

elif page == 'Prediksi Kelembapan':
    display_predictions(data, hum_model, hum_scaler, 'kelembapan', 'blue')

elif page == 'Prediksi AQI':
    display_predictions(data, aqi_model, aqi_scaler, 'ppm', 'green')

elif page == 'Saran dan Rekomendasi':
    predicted_temperature, predicted_humidity, predicted_aqi = fetch_latest_data(db_name, table_name)
    recommendations = generate_recommendations(temperature, humidity, aqi, predicted_temperature, predicted_humidity, predicted_aqi)
    st.header('Saran dan Rekomendasi dari AI')
    st.write(recommendations)

elif page == 'Chatbot Kualitas Udara':
    st.header('Chatbot Kualitas Udara')
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.chat_input('Masukkan pertanyaan atau komentar Anda tentang kualitas udara:')
    if user_input:
        st.session_state.chat_history.append({'user': user_input})
        response = llm.invoke(user_input)
        st.session_state.chat_history.append({'ai': response.content})

        # Check if user is asking for predictions
        if 'prediksi' in user_input.lower():
            # Tentukan jam ke depan berdasarkan input pengguna
            hours_ahead = [1, 3, 6, 12, 24]
            selected_hours = None
            for hour in hours_ahead:
                if f'{hour} jam' in user_input.lower():
                    selected_hours = hour
                    break

            if selected_hours is None:
                response_content = "Mohon sebutkan durasi prediksi dalam jam: 1, 3, 6, 12, atau 24 jam."
            else:
                if 'suhu' in user_input.lower():
                    pred_data, warning = predict_values(data, temp_model, temp_scaler, 'suhu', selected_hours)
                    if warning:
                        response_content = warning
                    else:
                        prediction = pred_data[f'Prediksi Suhu'].iloc[selected_hours-1]
                        response_content = f'Prediksi Suhu untuk {selected_hours} jam ke depan: {prediction:.2f} °C'
                elif 'kelembapan' in user_input.lower():
                    pred_data, warning = predict_values(data, hum_model, hum_scaler, 'kelembapan', selected_hours)
                    if warning:
                        response_content = warning
                    else:
                        prediction = pred_data[f'Prediksi Kelembapan'].iloc[selected_hours-1]
                        response_content = f'Prediksi Kelembapan untuk {selected_hours} jam ke depan: {prediction:.2f} %'
                elif 'aqi' in user_input.lower() or 'kualitas udara' in user_input.lower():
                    pred_data, warning = predict_values(data, aqi_model, aqi_scaler, 'ppm', selected_hours)
                    if warning:
                        response_content = warning
                    else:
                        prediction = pred_data[f'Prediksi Ppm'].iloc[selected_hours-1]
                        response_content = f'Prediksi AQI untuk {selected_hours} jam ke depan: {prediction:.2f} ppm'
                else:
                    response_content = "Mohon sebutkan apakah Anda ingin prediksi suhu, kelembapan, atau AQI."

            st.session_state.chat_history.append({'ai': response_content})

    for chat in st.session_state.chat_history:
        if 'user' in chat:
            st.chat_message('user').write(chat['user'])
        else:
            st.chat_message('assistant').write(chat['ai'])
