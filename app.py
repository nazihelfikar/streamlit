import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from datetime import datetime, timedelta

# Konfigurasi
MONGO_URI = "mongodb+srv://teguhgmc:teguh234@capstone.oh1disa.mongodb.net/smartfishing?retryWrites=true&w=majority"
LOKASI = "Tegal"

# Koneksi MongoDB
client = MongoClient(MONGO_URI)
db = client["smartfishing"]

st.set_page_config(layout="wide")
st.title("📊 Dashboard SmartFishing")

# ===== TAB =====
tab1, tab2 = st.tabs(["📈 Harga Ikan", "⛅ Cuaca Harian"])

# ==================== TAB 1: Harga Ikan ====================
with tab1:
    st.subheader("📈 Tren Harga Ikan di Kulon Progo")

    url = "https://ikanku.kulonprogokab.go.id/Landingpage/riwayat_harga/1/2"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.select("tbody tr")
    data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 3:
            tanggal = cols[1].text.strip()
            harga = cols[2].text.strip().replace("Rp", "").replace(".", "").replace(",", "")
            try:
                harga = int(harga)
                tanggal_dt = pd.to_datetime(tanggal).strftime('%Y-%m-%d')
                data.append({"tanggal": tanggal_dt, "harga": harga})
            except:
                continue

    df = pd.DataFrame(data)
    df['tanggal'] = pd.to_datetime(df['tanggal'])
    df = df.sort_values("tanggal").drop_duplicates(subset=["tanggal"])

    # Cek terakhir simpan
    collection = db["harga_ikan"]
    last_record = collection.find_one(sort=[("tanggal", -1)])
    today = datetime.today()
    skip_insert = False

    if last_record:
        last_date = datetime.strptime(last_record["tanggal"], "%Y-%m-%d")
        if today - last_date < timedelta(days=7):
            skip_insert = True

    # Simpan jika perlu
    if not skip_insert:
        for _, row in df.iterrows():
            tgl_str = row["tanggal"].strftime('%Y-%m-%d')
            if not collection.find_one({"tanggal": tgl_str}):
                collection.insert_one({"tanggal": tgl_str, "harga": row["harga"]})
        st.success("✅ Data harga ikan diperbarui.")
    else:
        st.info("✅ Data harga ikan sudah terbaru.")

    # Visualisasi
    st.line_chart(df.set_index("tanggal")["harga"])

# ==================== TAB 2: Cuaca ====================
with tab2:
    st.subheader("⛅ Riwayat Cuaca Harian (Tegal)")

    # Ambil data dari MongoDB
    cuaca_col = db["weather_tegal"]
    days_data = list(cuaca_col.find({}))

    if not days_data:
        st.warning("Data cuaca belum tersedia di database.")
        st.stop()

    df_cuaca = pd.DataFrame(days_data)

    # Pastikan kolom datetime dalam format datetime
    df_cuaca["datetime"] = pd.to_datetime(df_cuaca["datetime"])
    df_cuaca.set_index("datetime", inplace=True)
    df_cuaca = df_cuaca.sort_index()

    col1, col2 = st.columns(2)

    with col1:
        st.write("🌡 Suhu Maksimum (°C)")
        st.line_chart(df_cuaca["tempmax"])

        st.write("💧 Kelembapan (%)")
        st.line_chart(df_cuaca["humidity"])

    with col2:
        st.write("🌡 Suhu Minimum (°C)")
        st.line_chart(df_cuaca["tempmin"])
