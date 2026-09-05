SELECT
    event_time,
    icao24,
    callsign,
    origin_country,
    longitude,
    latitude,
    baro_altitude,
    geo_altitude,
    velocity,
    heading,
    vertical_rate,
    on_ground,
    ingested_at
FROM {{ source('flight', 'raw_flights') }}
WHERE latitude IS NOT NULL
  AND longitude IS NOT NULL
  AND baro_altitude IS NOT NULL
  AND geo_altitude IS NOT NULL
  AND velocity IS NOT NULL
  AND heading IS NOT NULL
  AND vertical_rate IS NOT NULL