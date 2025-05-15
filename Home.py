
import streamlit as st
import json
import os
import time
import pandas as pd
import plotly.express as px
from flask import Flask, request, jsonify
from threading import Thread
from streamlit_autorefresh import st_autorefresh
import folium
from streamlit_folium import st_folium
from streamlit_echarts import st_echarts
from datetime import datetime
import pytz
st.set_page_config(page_title="Gas Monitoring Dashboard", layout="wide")

# Automatically refresh every 5 seconds
st_autorefresh(interval=5000, key="autorefresh")

# ---------- Flask Setup ---------- #
app = Flask(__name__)
DATA_FILE = 'data.json'

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)


@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    if data:
        person_id = data.get("person_id", None)
        if not person_id:
            return jsonify({"error": "No person ID provided"}), 400

        # Add timestamp in Africa/Nairobi timezone (UTC+3)
        nairobi_tz = pytz.timezone("Africa/Nairobi")
        timestamp = datetime.now(nairobi_tz).isoformat()
        data["timestamp"] = timestamp

        with open(DATA_FILE, 'r+') as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

            existing.append(data)
            f.seek(0)
            json.dump(existing, f, indent=2)
            f.truncate()
        return jsonify({"message": "Data saved"}), 200
    return jsonify({"error": "No data received"}), 400


def run_flask():
    app.run(debug=False, port=5000, use_reloader=False)

# ---------- Streamlit App ---------- #
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

# ---------- Gauge Chart Function ---------- #
def gauge_chart(title, value, min_val, max_val, unit=""):
    option = {
        "series": [{
            "type": "gauge",
            "startAngle": 180,
            "endAngle": 0,
            "min": min_val,
            "max": max_val,
            "axisLine": {"lineStyle": {"width": 10}},
            "pointer": {"show": True},
            "detail": {
                "valueAnimation": True,
                "formatter": f"{value} {unit}",
                "fontSize": 18
            },
            "data": [{"value": value, "name": title}]
        }]
    }
    st_echarts(options=option, height="400px")

# Start Flask in a background thread
flask_thread = Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# ---------- Streamlit Dashboard ---------- #
st.title("Helmet Monitoring Dashboard")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid credentials")
else:
    st.success("Logged in as admin")
    data = load_data()
    st.write(f" Total Records: {len(data)}")
    if data:
        df = pd.DataFrame(data)

        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.sort_values('timestamp', inplace=True)

        person_ids = df['person_id'].unique()
        person_id = st.sidebar.selectbox("Select Person", person_ids)
        person_data = df[df['person_id'] == person_id]

        st.write(f"Showing data for Person ID: {person_id}")
        latest_row = person_data.iloc[-1]

        harmful_cases = person_data[(person_data['mq7'] == 1) | (person_data['mq2'] == 1)]
        total_harmful = len(harmful_cases)
        mq7_alerts = harmful_cases['mq7'].sum()
        mq2_alerts = harmful_cases['mq2'].sum()

        temperature = round(latest_row['temperature'], 2)
        pressure = round(latest_row['pressure'], 2)
        humidity = round(latest_row['humidity'], 2)
        altitude = round(latest_row['altitude'], 2)

        st.subheader(" Helmet Sensor Summary")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Harmful Detections", value=total_harmful)
        with col2:
            st.metric(label="CO (MQ-7) Alerts", value=mq7_alerts)
        with col3:
            st.metric(label="Smoke (MQ-2) Alerts", value=mq2_alerts)

        g1, g2, g3, g4 = st.columns(4)
        with g1:
            gauge_chart("Temperature", temperature, min_val=-40, max_val=85, unit="°C")
        with g2:
            gauge_chart("Pressure", pressure, min_val=300, max_val=1100, unit="hPa")
        with g3:
            gauge_chart("Humidity", humidity, min_val=0, max_val=100, unit="%")
        with g4:
            gauge_chart("Altitude", altitude, min_val=-10, max_val=100, unit="m")

        chart_cols = st.columns(3)
        with chart_cols[0]:
            st.plotly_chart(px.line(person_data, x='timestamp', y='mq7', title='MQ-7 (CO)'))
            st.plotly_chart(px.line(person_data, x='timestamp', y='temperature', title='Temperature'))

        with chart_cols[1]:
            st.plotly_chart(px.line(person_data, x='timestamp', y='mq2', title='MQ-2 (Smoke)'))
            st.plotly_chart(px.line(person_data, x='timestamp', y='pressure', title='Pressure'))

        with chart_cols[2]:
            st.plotly_chart(px.line(person_data, x='timestamp', y='altitude', title='Altitude'))
            st.plotly_chart(px.line(person_data, x='timestamp', y='humidity', title='Humidity'))

        df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
        latest_lat = df.iloc[-1]['lat']
        latest_lon = df.iloc[-1]['lon']
        m = folium.Map(location=[latest_lat, latest_lon], zoom_start=13)
        path_coords = list(zip(df['lat'], df['lon']))

        folium.PolyLine(path_coords, color="blue", weight=2.5, opacity=0.8).add_to(m)
        folium.Marker(
            location=[latest_lat, latest_lon],
            popup=f"Person: {latest_row['person_id']}<br>Temperature: {latest_row['temperature']}°C",
            icon=folium.Icon(color='red', icon='user', prefix='fa')
        ).add_to(m)

        st.subheader("Helmet Position Map")
        st_folium(m, width=1000, height=700)
