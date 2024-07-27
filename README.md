# Sistem Pemantauan dan Peringatan Dini Kabut Asap Berbasis AI untuk Sekolah di Pedesaan

## Deskripsi Proyek
Proyek ini bertujuan untuk mengembangkan sistem pemantauan kualitas udara dan peringatan dini kabut asap berbasis AI yang dirancang khusus untuk sekolah-sekolah di pedesaan. Sistem ini menggunakan perangkat IoT untuk mengumpulkan data lingkungan, yang kemudian dianalisis menggunakan model AI untuk memberikan prediksi dan rekomendasi guna menjaga kesehatan dan keselamatan siswa serta staf sekolah.

## Fitur Utama
- **Pemantauan Real-time**: Memantau kualitas udara secara langsung menggunakan sensor yang terpasang di lingkungan sekolah.
- **Prediksi Kualitas Udara**: Menggunakan model AI untuk memprediksi Air Quality Index (AQI), suhu, dan kelembapan.
- **Rekomendasi Kesehatan**: Memberikan rekomendasi berbasis AI untuk tindakan pencegahan kesehatan.
- **Layar LCD**: Menampilkan data kualitas udara real-time dengan indikator warna (merah, kuning, hijau).
- **Website Streamlit**: Memungkinkan pengguna untuk mengakses data terbaru, prediksi, dan rekomendasi dari jarak jauh.
- **Chatbot Kualitas Udara**: Chatbot yang terintegrasi dengan API OpenAI untuk menjawab pertanyaan terkait kualitas udara.

## Teknologi yang Digunakan

### Hardware
- **ESP32**: Microcontroller untuk mengumpulkan dan memproses data dari sensor.
- **Panel Surya**: Sumber daya untuk perangkat di lokasi terpencil.
- **Sensor MQ-135**: Sensor kualitas udara untuk mendeteksi gas berbahaya.
- **Sensor DHT11**: Sensor untuk mengukur suhu dan kelembapan.

### Software
- **Arduino IDE**: Untuk pemrograman ESP32.
- **Wokwi**: Simulator untuk menguji rangkaian IoT.
- **VS Code**: Editor kode untuk pengembangan perangkat lunak.
- **Python**: Bahasa pemrograman untuk analisis data dan pengembangan model AI.
- **Streamlit**: Framework untuk membuat aplikasi web interaktif.
- **Scikit-Learn**: Library untuk pengembangan model machine learning.
- **SQLite**: Database untuk menyimpan data sensor.

## Cara Mengoperasikan Sistem

### Di Sekolah
1. **Pantau Kualitas Udara**: Lihat data kualitas udara real-time di layar LCD.
2. **Indikator Warna**: Perhatikan indikator warna untuk status kualitas udara.

### Dari Jarak Jauh
1. **Akses Website Streamlit**: Masuk ke website Streamlit yang telah disediakan.
2. **Lihat Data Terbaru**: Periksa data terkini mengenai kualitas udara di sekolah.
3. **Prediksi AQI, Suhu, dan Kelembapan**: Cek prediksi untuk kondisi udara mendatang.
4. **Rekomendasi AI**: Terima saran dari AI mengenai langkah-langkah yang bisa diambil.
5. **Gunakan Chatbot**: Tanyakan pertanyaan terkait kualitas udara kepada chatbot yang diintegrasikan dengan API OpenAI.

## Instalasi
1. **Clone Repository**:
   ```bash
   git clone https://github.com/username/project-name.git
