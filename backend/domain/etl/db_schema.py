from __future__ import annotations

import logging
import sqlite3

log = logging.getLogger(__name__)

_DDL = """
    CREATE TABLE IF NOT EXISTS trips_raw (
        pickup_community_area  TEXT,
        year         INTEGER,
        month        INTEGER,
        day          INTEGER,
        hour         INTEGER,
        season       TEXT,
        day_time     TEXT,
        trip_count   INTEGER,
        total_fare   REAL,
        weather_mark INTEGER,
        PRIMARY KEY (pickup_community_area, year, month, day, hour)
    );

    CREATE INDEX IF NOT EXISTS idx_area    ON trips_raw(pickup_community_area);
    CREATE INDEX IF NOT EXISTS idx_season  ON trips_raw(season);
    CREATE INDEX IF NOT EXISTS idx_daytime ON trips_raw(day_time);
    CREATE INDEX IF NOT EXISTS idx_weather ON trips_raw(weather_mark);

    CREATE VIEW IF NOT EXISTS trips_summary AS
    SELECT
        pickup_community_area,
        season,
        day_time,
        weather_mark,
        SUM(trip_count)  AS total_trips,
        ROUND(SUM(total_fare), 2) AS total_fare,
        ROUND(
            CAST(SUM(total_fare) AS REAL) / NULLIF(SUM(trip_count), 0),
            2
        ) AS avg_fare_per_trip
    FROM trips_raw
    GROUP BY pickup_community_area, season, day_time, weather_mark;
"""


def apply_schema(db_path: str) -> sqlite3.Connection:
    """
    Opens (or creates) the SQLite file, applies the full schema,
    and returns an open connection.

    Caller is responsible for closing the connection.
    Safe to call on an already-populated DB — all statements use IF NOT EXISTS.
    """
    conn = sqlite3.connect(db_path)
    conn.executescript(_DDL)
    conn.commit()
    log.info("SQLite schema ready: %s", db_path)
    return conn
