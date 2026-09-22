# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Inspect the untouched GFZ / NOAA replies; share the parsing rules with plots."""
import json
import math
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


def utc(text):
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def read_swpc(filename, fields):
    """Sort UTC, select active spacecraft, skip flagged / incomplete rows.

    Do not combine several spacecraft at the same minute. Missing records
    stay absent; plotting code must decide explicitly how to show gaps.
    """
    raw = json.loads((DATA / filename).read_text())
    rows = {}
    for r in raw:
        if not r.get("active", True) or r.get("overall_quality", 0) != 0:
            continue
        values = [r.get(k) for k in fields]
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
            continue
        if any(v < 0 for k, v in zip(fields, values) if k != "bz_gsm"):
            continue
        if "estimated_kp" in fields and r["estimated_kp"] > 9:
            continue
        if "bz_gsm" in fields and "bt" in fields and abs(r["bz_gsm"]) > r["bt"] + 0.02:
            continue
        t = utc(r["time_tag"])
        if t in rows:
            raise ValueError(f"Multiple active records at {t}: {filename}")
        rows[t] = tuple(float(v) for v in values)
    if not rows:
        raise ValueError(f"No valid active observations in {filename}")
    return dict(sorted(rows.items()))


def read_gfz():
    """Kp is the EIGHTH column (index 7). Keep real dates and valid 0..9 Kp."""
    days = defaultdict(list)
    raw_count = 0
    for line in (DATA / "gfz-kp-ap-since-1932.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        r = line.split()
        raw_count += 1
        kp = float(r[7])
        if 0 <= kp <= 9:
            days[date(*map(int, r[:3]))].append(kp)
    # Require eight intervals so an incomplete day cannot look artificially quiet.
    daily = {d: max(v) for d, v in sorted(days.items()) if len(v) == 8}
    if not daily:
        raise ValueError("GFZ file contains no complete days")
    return raw_count, daily


def main():
    for filename, fields in [
        ("swpc-solar-wind-plasma-1m.json", ("proton_speed", "proton_density", "proton_temperature")),
        ("swpc-solar-wind-mag-1m.json", ("bt", "bz_gsm")),
        ("swpc-planetary-k-index-1m.json", ("estimated_kp",)),
    ]:
        raw = json.loads((DATA / filename).read_text())
        rows = read_swpc(filename, fields)
        print(f"{filename}: {len(raw):,} raw / {len(rows):,} selected complete rows")
        print(f"  {min(rows).isoformat()} -> {max(rows).isoformat()}")
        for j, field in enumerate(fields):
            v = [r[j] for r in rows.values()]
            print(f"  {field}: {min(v):g} .. {max(v):g}")
    raw_count, daily = read_gfz()
    print(f"GFZ: {raw_count:,} raw 3-hour records / {len(daily):,} complete days")
    print(f"  {min(daily)} -> {max(daily)}; Kp range {min(daily.values())} .. {max(daily.values())}")
    ov = json.loads((DATA / "swpc-ovation-aurora-latest.json").read_text())
    vals = [c[2] for c in ov["coordinates"]]
    print(f"OVATION (exploration only): {len(vals):,} [longitude, latitude, aurora] grid points")
    print(f"  third-field range {min(vals)} .. {max(vals)}; forecast {ov['Forecast Time']}")


if __name__ == "__main__":
    main()
