# Slower approach compared to current

import requests
import csv
import time

URL = "https://data.cityofchicago.org/api/views/6dvr-xwnh/rows.csv?accessType=DOWNLOAD"

KEEP_COLS = {"trip_start_timestamp", "pickup_community_area", "fare"}

start = time.time()

with requests.get(URL, stream=True) as r:
    r.raise_for_status()

    lines = (line.decode('utf-8') for line in r.iter_lines())

    reader = csv.DictReader(lines)

    with open("filtered.csv", "w", newline="") as f:
        writer = None

        for i, row in enumerate(reader):
            filtered = {k: row[k] for k in KEEP_COLS if k in row}

            if writer is None:
                writer = csv.DictWriter(f, fieldnames=filtered.keys())
                writer.writeheader()

            writer.writerow(filtered)

            if i % 1_000_000 == 0:
                print("Processed:", i)

end = time.time()
print("Done in", end - start)