import requests

URL = "https://opensky-network.org/api/states/all"

response = requests.get(URL, timeout=30)

print("Status code:", response.status_code)

data = response.json()

states = data["states"]

print("Jumlah pesawat:", len(states))

print("\n5 data pesawat pertama:\n")

for state in states[:5]:
    print(
        {
            "icao24": state[0],
            "callsign": state[1],
            "origin_country": state[2],
            "longitude": state[5],
            "latitude": state[6],
            "baro_altitude": state[7],
            "on_ground": state[8],
            "velocity": state[9],
            "heading": state[10],
        }
    )
