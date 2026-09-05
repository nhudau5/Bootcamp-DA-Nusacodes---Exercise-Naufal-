import requests
import clickhouse_connect
from datetime import datetime, timezone

# =========================
# 1. Ambil data dari OpenSky
# =========================

URL = "https://opensky-network.org/api/states/all"

response = requests.get(URL, timeout=30)
response.raise_for_status()

data = response.json()

states = data.get("states", [])

print(f"Jumlah data dari API: {len(states)}")


# =========================
# 2. Connect ke ClickHouse
# =========================

client = clickhouse_connect.get_client(
    host="localhost",
    port=8124,
    username="default",
    password="admin123",
    database="flight",
)

print("Berhasil terhubung ke ClickHouse")


# =========================
# 3. Mapping data API
# =========================

rows = []

for state in states:
    row = [
        datetime.fromtimestamp(state[4], tz=timezone.utc).replace(tzinfo=None)
        if state[4] is not None
        else None,
        state[0],
        state[1].strip() if state[1] else "",
        state[2],
        state[5],
        state[6],
        state[7],
        state[13],
        state[9],
        state[10],
        state[11],
        1 if state[8] else 0,
    ]

    rows.append(row)


# =========================
# 4. Insert ke ClickHouse
# =========================

client.insert(
    "raw_flights",
    rows,
    column_names=[
        "event_time",
        "icao24",
        "callsign",
        "origin_country",
        "longitude",
        "latitude",
        "baro_altitude",
        "geo_altitude",
        "velocity",
        "heading",
        "vertical_rate",
        "on_ground",
    ],
)

print(f"Berhasil memasukkan {len(rows)} data ke ClickHouse")
