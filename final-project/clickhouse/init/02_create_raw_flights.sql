CREATE TABLE IF NOT EXISTS flight.raw_flights
(
    event_time DateTime,
    icao24 String,
    callsign String,
    origin_country String,

    longitude Nullable(Float64),
    latitude Nullable(Float64),

    baro_altitude Nullable(Float64),
    geo_altitude Nullable(Float64),
    velocity Nullable(Float64),
    heading Nullable(Float64),
    vertical_rate Nullable(Float64),

    on_ground UInt8,

    ingested_at DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_time, icao24);