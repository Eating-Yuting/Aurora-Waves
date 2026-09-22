# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Look at the numbers before drawing them. Print what each file in data/
actually contains: how many records, which fields, what the first and
last rows look like, and the range of the interesting columns.

    uv run aurora_data.py
"""

import json
from pathlib import Path

DATA = Path(__file__).parent / "data"


def hr(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def show(name, rows, fields, time_key="time_tag"):
    """Print span, fields, and value ranges for a list of dicts."""
    span = f"{rows[0][time_key]}  ->  {rows[-1][time_key]}"
    print(f"\n{name}: {len(rows):,} records, {span}")
    for label, key, unit in fields:
        values = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
        if values:
            print(f"  {label:<28} {key:<18} min {min(values):>10.2f}   "
                  f"max {max(values):>10.2f}   ({unit})")
        else:
            print(f"  {label:<28} {key:<18} (no numeric values)")


def main():
    hr("swpc-planetary-k-index-1m.json  (NOAA SWPC, Kp every minute)")
    kp = json.loads((DATA / "swpc-planetary-k-index-1m.json").read_text())
    print(f"first row: {kp[0]}")
    show("kp", kp, [("Kp index (0-9)", "kp_index", "unitless"),
                    ("estimated Kp", "estimated_kp", "unitless")])

    hr("swpc-solar-wind-mag-1m.json  (NOAA SWPC, magnetic field)")
    mag = json.loads((DATA / "swpc-solar-wind-mag-1m.json").read_text())
    show("mag", mag, [("total field", "bt", "nT"),
                      ("north-south", "bz_gsm", "nT"),
                      ("east-west", "by_gsm", "nT")])

    hr("swpc-solar-wind-plasma-1m.json  (NOAA SWPC, solar wind)")
    wind = json.loads((DATA / "swpc-solar-wind-plasma-1m.json").read_text())
    show("plasma", wind, [("proton speed", "proton_speed", "km/s"),
                          ("proton density", "proton_density", "1/cm3"),
                          ("temperature", "proton_temperature", "K")])

    hr("swpc-ovation-aurora-latest.json  (NOAA SWPC, aurora probability)")
    ov = json.loads((DATA / "swpc-ovation-aurora-latest.json").read_text())
    coords = ov["coordinates"]
    probs = [c[1] for c in coords]
    print(f"\nObservation Time: {ov['Observation Time']}")
    print(f"Forecast   Time: {ov['Forecast Time']}")
    print(f"grid: {len(coords):,} points  (lon, aurora probability 0-100)")
    print(f"  aurora probability          min {min(probs):>10.2f}   "
          f"max {max(probs):>10.2f}   (percent)")

    hr("gfz-kp-ap-since-1932.txt  (GFZ, Kp every 3 hours since 1932)")
    lines = [l for l in (DATA / "gfz-kp-ap-since-1932.txt").read_text().splitlines()
             if l and not l.startswith("#")]
    first, last = lines[0].split(), lines[-1].split()
    # columns: YYYY MM DD hh.h hh._m days days_m Kp ap D  ->  Kp is index 7
    kps = [float(l.split()[7]) for l in lines]
    print(f"\ngfz: {len(lines):,} records,  {first[0]}-{first[1]}-{first[2]}  ->  "
          f"{last[0]}-{last[1]}-{last[2]}")
    print("  columns: YYYY MM DD hh.h hh._m days days_m Kp ap D")
    print(f"  Kp (0-9, 3-hourly)          min {min(kps):>10.2f}   "
          f"max {max(kps):>10.2f}   (unitless)")
    print("\nDone. Now we know what every number means - time to draw.")


if __name__ == "__main__":
    main()
