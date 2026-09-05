SELECT
    origin_country,

    count() AS total_flights,

    countIf(on_ground = 0) AS airborne_flights,

    countIf(on_ground = 1) AS grounded_flights,

    round(
        countIf(on_ground = 0) / count() * 100,
        2
    ) AS airborne_percentage,

    round(avg(velocity) * 3.6, 2) AS avg_velocity_kmh,

    round(avg(baro_altitude), 2) AS avg_altitude

FROM {{ ref('silver_flights') }}

GROUP BY origin_country

ORDER BY total_flights DESC