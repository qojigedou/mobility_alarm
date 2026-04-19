from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import duckdb

from tools.data_formatter import hour_to_daytime, month_to_season

log = logging.getLogger(__name__)

_AGGREGATE_SQL = """
    SELECT
        pickup_community_area,
        YEAR(trip_start_timestamp::TIMESTAMP)  AS year,
        MONTH(trip_start_timestamp::TIMESTAMP) AS month,
        DAY(trip_start_timestamp::TIMESTAMP)   AS day,
        HOUR(trip_start_timestamp::TIMESTAMP)  AS hour,
        COUNT(*)                               AS trip_count,
        SUM(TRY_CAST(fare AS DOUBLE))          AS total_fare
    FROM read_csv_auto(
        [{file_list}],
        ignore_errors = true,
        columns = {{
            'trip_start_timestamp':  'VARCHAR',
            'pickup_community_area': 'VARCHAR',
            'fare':                  'VARCHAR'
        }}
    )
    WHERE pickup_community_area IS NOT NULL
      AND pickup_community_area != ''
    GROUP BY ALL
"""

_INSERT_SQL = """
    INSERT OR IGNORE INTO trips_raw
        (pickup_community_area, year, month, day, hour,
         season, day_time, trip_count, total_fare, weather_mark)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def transform_and_load(
    csv_paths: list[Path],
    conn: sqlite3.Connection,
    weather: dict[str, int],
) -> int:
    """
    Aggregates CSV files with DuckDB, enriches each row with time/weather
    metadata, and bulk-inserts into trips_raw.

    Args:
        csv_paths: paths to 3-column TNP CSV files
        conn:      open SQLite connection with schema already applied
        weather:   {YYYY-MM-DD: weather_mark} from download_orchestrator

    Returns:
        number of rows inserted

    Raises:
        ValueError: if csv_paths is empty or any path does not exist
    """
    if not csv_paths:
        raise ValueError("csv_paths must not be empty")

    missing = [p for p in csv_paths if not p.exists()]
    if missing:
        raise ValueError(f"CSV files not found: {missing}")

    file_list = ", ".join(f"'{p}'" for p in csv_paths)

    log.info("DuckDB: aggregating %d CSV file(s) ...", len(csv_paths))
    con = duckdb.connect()
    df  = con.execute(_AGGREGATE_SQL.format(file_list=file_list)).fetchdf()
    con.close()
    log.info("DuckDB: %s aggregated rows", f"{len(df):,}")

    rows = []
    for row in df.itertuples(index=False):
        year  = int(row.year)
        month = int(row.month)
        day   = int(row.day)
        hour  = int(row.hour)

        rows.append((
            str(row.pickup_community_area),
            year, month, day, hour,
            month_to_season(month),
            hour_to_daytime(hour),
            int(row.trip_count),
            float(row.total_fare or 0),
            weather.get(f"{year:04d}-{month:02d}-{day:02d}", 0),
        ))

    conn.executemany(_INSERT_SQL, rows)
    conn.commit()
    log.info("SQLite: inserted %s rows into trips_raw", f"{len(rows):,}")
    return len(rows)
