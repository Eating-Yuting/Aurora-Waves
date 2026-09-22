# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///

"""
Read the files in data/, make one plain picture, save it to out/.

    uv run plot.py

This is the ugly first version, on purpose: does the pipeline work, and what
do yesterday's numbers actually look like? Two panels, one day, minute by
minute - Kp on top (how strong the disturbance was), Bz below (which way the
solar wind's magnetic field pointed). The beautiful version comes later.
"""

import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "out"

PICTURE = "aurora-first-look.png"


def main():
    kp = json.loads((DATA / "swpc-planetary-k-index-1m.json").read_text())
    mag = json.loads((DATA / "swpc-solar-wind-mag-1m.json").read_text())

    def series(rows, key):
        """time_tag text -> datetime, keep only rows where the key is numeric."""
        xs, ys = [], []
        for row in rows:
            value = row.get(key)
            if isinstance(value, (int, float)):
                xs.append(datetime.fromisoformat(row["time_tag"]))
                ys.append(value)
        return xs, ys

    print(f"kp: {len(kp)} rows, mag: {len(mag)} rows")

    kp_x, kp_y = series(kp, "estimated_kp")
    bz_x, bz_y = series(mag, "bz_gsm")
    print(f"Kp from {min(kp_y)} to {max(kp_y)}, Bz from {min(bz_y)} to {max(bz_y)} nT")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    ax1.plot(kp_x, kp_y, color="#1f77b4")
    ax1.set_ylabel("estimated Kp")
    ax1.set_title("Aurora first look - last 24 hours, one minute per point")
    ax1.grid(True, alpha=0.3)

    ax2.plot(bz_x, bz_y, color="#d62728")
    ax2.set_ylabel("Bz, nT")
    ax2.set_xlabel("time (UTC)")
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / PICTURE, dpi=150)
    print(f"saved out/{PICTURE}")
    plt.show()


if __name__ == "__main__":
    main()
