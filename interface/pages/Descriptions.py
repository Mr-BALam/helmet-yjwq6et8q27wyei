import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timezone
import pytz
# Load data from JSON file
DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

# Session authentication check
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.warning("You must Login to view this page.")
    st.stop()

st.title("Helmet Monitoring: Person Descriptions & Status")

# Load and prepare data
data = load_data()
if not data:
    st.info("No data available.")
    st.stop()

df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
df.sort_values('timestamp', inplace=True)

# Unique Person IDs
person_ids = df['person_id'].unique()

# Display status buttons
st.subheader("Person Status")
cols = st.columns(len(person_ids))
tz = pytz.timezone("Africa/Nairobi")
now = datetime.now(tz)
selected_person = None

for i, pid in enumerate(person_ids):
    person_df = df[df['person_id'] == pid]
    latest_time = person_df['timestamp'].max()
    time_diff = (now - latest_time).total_seconds()
    status = "🟢 Online" if time_diff <= 30 else "🔴 Offline"
    if cols[i].button(f"{pid} {status}"):
        selected_person = pid

# Show selected person data
if selected_person:
    st.subheader(f"Sensor Details for Person ID: {selected_person}")
    person_data = df[df['person_id'] == selected_person]
    latest = person_data.iloc[-1]

    # Harmful alerts summary
    harmful_cases = person_data[(person_data['mq7'] == 1) | (person_data['mq2'] == 1)]
    total_harmful = len(harmful_cases)
    mq7_alerts = person_data['mq7'].sum()
    mq2_alerts = person_data['mq2'].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Harmful Detections", value=total_harmful)
    with col2:
        st.metric(label="CO (MQ-7) Alerts", value=mq7_alerts)
    with col3:
        st.metric(label="Smoke (MQ-2) Alerts", value=mq2_alerts)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric(label="Pressure (hPa)", value=f"{latest['pressure']:.2f}")
    with col5:
        st.metric(label="Temperature (°C)", value=f"{latest['temperature']:.2f}")
    with col6:
        st.metric(label="Humidity (%)", value=f"{latest['humidity']:.2f}")

    col7, col8 = st.columns(2)
    with col7:
        st.metric(label="Latitude", value=f"{latest['latitude']:.5f}°")
    with col8:
        st.metric(label="Longitude", value=f"{latest['longitude']:.5f}°")


    st.write(" Behavior Analysis & Urgent Comments")

    latest_entry = person_data.sort_values("timestamp", ascending=False).iloc[0]
    latest_temp = latest_entry["temperature"]
    latest_press = latest_entry["pressure"]
    latest_humidity = latest_entry["humidity"]

    comments = []

    if mq7_alerts > 5:
        comments.append(("error", " Urgent: Elevated Carbon Monoxide (MQ-7) alerts detected. Immediate investigation is required."))
    elif mq7_alerts > 0:
        comments.append(("warning", " Notice: Some CO (MQ-7) alerts recorded. Keep monitoring the air quality."))

    if mq2_alerts > 5:
        comments.append(("error", " Urgent: Multiple Smoke (MQ-2) alerts detected. Possible fire hazard or pollution. Action required."))
    elif mq2_alerts > 0:
        comments.append(("warning", " Notice: Intermittent Smoke (MQ-2) detections. Be alert to changes."))

    if latest_temp > 40:
        comments.append(("error", f" Critical: Current temperature is {latest_temp:.1f}°C — risk of overheating. Ensure cooling and proper airflow."))
    elif latest_temp > 35:
        comments.append(("warning", f" Warning: High temperature at {latest_temp:.1f}°C — may affect comfort and equipment reliability."))

    if latest_press < 300:
        comments.append(("error", f" Critical: Pressure is low ({latest_press:.1f} hPa) — oxygen tank likely empty. Replace immediately."))
    elif 300 < latest_press < 500:
        comments.append(("warning", f" **Warning: Pressure dropping ({latest_press:.1f} hPa). Monitor for declining oxygen supply."))

    if latest_humidity < 20:
        comments.append(("info", f" Dry Conditions: Humidity is low ({latest_humidity:.1f}%) — advise hydration and comfort measures."))
    elif latest_humidity > 80:
        comments.append(("info", f" High Humidity: Reading is {latest_humidity:.1f}% — risk of condensation in electronics. Check waterproofing."))

    if not comments:
        st.success("✅ All sensor readings are within safe and expected ranges.")
    else:
        for level, message in comments:
            if level == "info":
                st.info(message)
            elif level == "warning":
                st.warning(message)
            elif level == "error":
                st.error(message)
