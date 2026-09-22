# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""
Fetch one week of the OMNI 1-minute solar wind, and save the raw reply.

    uv run fetch_omni.py

Why a second fetch script. fetch.py pulls NOAA's live feeds, and those only
hold the last 24 hours: the rolled 7-day files that used to sit beside them
answer 404 now. A week therefore has to come from the archive, and the archive
is NASA's OMNI, which merges what several spacecraft measured at L1 into one
record per minute. It is not live — CDAWeb serves it with a lag of a few weeks —
but it reaches back to 1981, so a week can be chosen rather than waited for.

The week below is 7–14 October 2024: the geomagnetic storm of 10 October, when
Kp reached 8.7. It is also one of the better-covered weeks in the recent archive.

One request, one file, byte for byte. Delete data/ to fetch it again.
"""

from pathlib import Path

import requests

# The server takes these as query parameters; the percent signs are not ours to guess.
PARAMETERS = "F,BZ_GSM,flow_speed,proton_density,T"
START = "2024-10-07T00:00:00Z"
END = "2024-10-14T00:00:00Z"

URL = ("https://cdaweb.gsfc.nasa.gov/hapi/data"
       f"?id=OMNI_HRO_1MIN&time.min={START}&time.max={END}"
       f"&parameters={PARAMETERS}&format=csv")

HERE = Path(__file__).parent
DATA = HERE / "data"
NAME = "omni-hro-1min-2024-10-07-to-10-14.csv"


def main():
    if (DATA / NAME).exists():
        print(f"cached data/{NAME} ({(DATA / NAME).stat().st_size // 1024} KB) — delete it to fetch again")
        return
    print(f"asking {URL}")
    reply = requests.get(URL, timeout=300, headers={"User-Agent": "SD5913 PolyU student"})
    reply.raise_for_status()
    DATA.mkdir(exist_ok=True)
    (DATA / NAME).write_bytes(reply.content)
    rows = len(reply.text.strip().splitlines())
    print(f"saved data/{NAME} ({len(reply.content) // 1024} KB, {rows} rows)")
    print("one row = one UTC minute: time_tag, Bt, Bz(GSM), speed, density, temperature")


if __name__ == "__main__":
    main()
