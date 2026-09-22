# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""
Fetch the numbers once, save the raw replies to data/, and never fetch again.

    uv run fetch.py

Phenomenon: the aurora. Four raw replies from NOAA's Space Weather Prediction
Center and one historical Kp file from GFZ, covering different time spans. They are saved
byte for byte, as they arrived, because the machine that marks this may have
no network: if the file is not in the repository, nothing happened.

    swpc-planetary-k-index-1m.json    Kp, one value per minute  -> how strong
    swpc-solar-wind-mag-1m.json       Bt, Bx, By, Bz            -> which way
    swpc-solar-wind-plasma-1m.json    speed, density, temp      -> how hard
    swpc-ovation-aurora-latest.json   probability on a 1 deg grid -> where
    gfz-kp-ap-since-1932.txt          Kp every three hours since 1932 -> how long

Delete a file in data/ to fetch it again.
"""

from pathlib import Path

import requests

SOURCES = [
    ("https://services.swpc.noaa.gov/json/planetary_k_index_1m.json",
     "swpc-planetary-k-index-1m.json"),
    ("https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json",
     "swpc-solar-wind-mag-1m.json"),
    ("https://services.swpc.noaa.gov/json/rtsw/rtsw_wind_1m.json",
     "swpc-solar-wind-plasma-1m.json"),
    ("https://services.swpc.noaa.gov/json/ovation_aurora_latest.json",
     "swpc-ovation-aurora-latest.json"),
    ("https://kp.gfz.de/app/files/Kp_ap_since_1932.txt",
     "gfz-kp-ap-since-1932.txt"),
]

HERE = Path(__file__).parent
DATA = HERE / "data"


def fetch(url, path):
    """Ask for the file once. If it is already in data/, do nothing."""
    if path.exists():
        print(f"cached data/{path.name} ({path.stat().st_size // 1024} KB)")
        return path
    DATA.mkdir(exist_ok=True)
    print(f"asking {url}")
    reply = requests.get(url, timeout=90, headers={"User-Agent": "SD5913 PolyU student"})
    reply.raise_for_status()
    path.write_bytes(reply.content)      # the raw reply, byte for byte: what arrived is what gets committed
    print(f"saved data/{path.name} ({path.stat().st_size // 1024} KB).")
    return path


if __name__ == "__main__":
    for url, name in SOURCES:
        fetch(url, DATA / name)
    print("Now: git add data")

