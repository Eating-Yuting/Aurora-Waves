# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///

"""
Aurora Waves - the picture.

Two data sets, one landscape:

  * Ninety-four years of geomagnetic activity (Kp, 1932-2025, GFZ) become
    mountain ranges in the blue-green mineral pigments of Chinese
    landscape painting. One range per decade: its silhouette is the daily
    maximum Kp of those years, so every decade grows exactly one grand
    summit - the solar maximum that lived inside it. Old ranges recede
    into dark azurite mist, the 2020s stand close in bright malachite.

  * The solar wind of the last ~56 hours (NOAA SWPC, one minute per
    point) becomes threads of light rising out of the range: the faster
    the wind, the longer the thread; a southward-pointing magnetic field
    makes it glow.

A gold dot marks the strongest storm in the whole record.

    uv run aurora_waves.py   ->   out/aurora-waves.png
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "out"
if not OUT.exists():
    OUT.mkdir()

# ---------------------------------------------------------------- palette
# 墨 ink -> 石青 azurite -> 石绿 malachite: far ranges are dark and blue,
# near ranges bright and green.
RIDGE_CMAP = LinearSegmentedColormap.from_list(
    "qinglv",
    ["#06141C", "#0B2530", "#123B44", "#1B565B",
     "#2A7268", "#3B8F74", "#4FA97D", "#63BD87"],
)
SKY_TOP = "#030C14"
SKY_HORIZON = "#16404F"
THREAD_CMAP = LinearSegmentedColormap.from_list(
    "threads", ["#1B4E5E", "#2E7F7A", "#63B79B", "#A8E6CB", "#E4FBF0"]
)
TEXT = "#AEDCC9"
GOLD = "#D4AF4E"

GAP = 0.66      # horizon line: ranges stack below, light rises above


# ------------------------------------------------------------------ data
def load_yearly_kp():
    """One silhouette per year (daily maximum Kp), plus the worst storm."""
    rows = [l.split() for l in (DATA / "gfz-kp-ap-since-1932.txt")
            .read_text().splitlines() if l.strip() and not l.startswith("#")]
    # YYYY MM DD hh.h hh._m days days_m Kp ap D
    year = np.array([int(r[0]) for r in rows])
    yday = np.array([date(int(r[0]), int(r[1]), int(r[2])).timetuple().tm_yday
                     for r in rows])
    kp = np.array([float(r[7]) for r in rows])          # 0-9, thirds

    key = year * 1000 + yday
    uniq, inv = np.unique(key, return_inverse=True)
    daily = np.zeros(uniq.shape)
    np.maximum.at(daily, inv, kp)                       # 8 samples -> 1 day

    uy, ud = uniq // 1000, uniq % 1000
    grid = np.arange(1, 367)
    years, profiles = [], []
    for y in np.unique(uy):
        m = uy == y
        if m.sum() < 340:                               # drop partial years
            continue
        profiles.append(np.interp(grid, ud[m], daily[m],
                                  left=daily[m][0], right=daily[m][-1]))
        years.append(y)

    worst = int(np.argmax(daily))
    wy, wd = int(uy[worst]), int(ud[worst])
    storm = {"date": date(wy, 1, 1) + timedelta(days=wd - 1),
             "kp": float(daily[worst])}
    return np.array(years), np.array(profiles), storm


def load_series(filename, key):
    """Read a NOAA SWPC json list and return (epoch seconds, values).

    SWPC serves the newest minute first, so put the series back in
    chronological order before anything is drawn from it.
    """
    rows = json.loads((DATA / filename).read_text())
    t, v = [], []
    for r in rows:
        val = r.get(key)
        if isinstance(val, (int, float)):
            t.append(datetime.fromisoformat(r["time_tag"]).timestamp())
            v.append(float(val))
    t, v = np.array(t), np.array(v)
    order = np.argsort(t)
    return t[order], v[order]


def decade_ranges(years, profiles):
    """Group the years into decades; each decade becomes one range."""
    ranges, cy, cp = [], [], []
    for y, p in zip(years, profiles):
        if cy and int(y) % 10 == 0:
            ranges.append((cy, np.concatenate(cp)))
            cy, cp = [], []
        cy.append(int(y))
        cp.append(p)
    if cy:
        ranges.append((cy, np.concatenate(cp)))
    return ranges


# ------------------------------------------------------------- the ranges
def draw_ridges(ax, ranges, storm):
    n = len(ranges)
    x = np.linspace(0, 1, 1200)
    base = np.linspace(0.60, 0.05, n)       # oldest far away, newest up front
    marked = False

    for i, (yrs, prof) in enumerate(ranges):
        d = i / (n - 1)                     # 0 = farthest, 1 = nearest
        amp = 0.12 + 0.18 * d               # perspective: near peaks taller
        kernel = np.ones(45) / 45           # storm-days -> rolling hills
        padded = np.pad(prof, 22, mode="edge")
        smooth = np.convolve(padded, kernel, mode="valid")[: prof.size]
        crest = np.interp(x, np.linspace(0, 1, smooth.size), smooth) / 9.0
        y = base[i] + amp * crest
        colour = RIDGE_CMAP(d)

        ax.fill_between(x, -0.05, y, color=colour, lw=0,
                        zorder=10 + i)
        pale = tuple(0.5 * np.array(colour[:3]) + 0.5 * np.array([0.85, 0.97, 0.90]))
        ax.plot(x, y, color=pale, lw=0.5, alpha=0.4, zorder=10 + i)
        ax.text(0.013, base[i] + 0.015, f"{yrs[0]}-{str(yrs[-1])[2:]}",
                color=pale, fontsize=5.5, alpha=0.85, ha="left", zorder=300)

        # the strongest storm of the record, if it lives in this range
        if not marked and yrs[0] <= storm["date"].year <= yrs[-1]:
            idx = ((storm["date"].year - yrs[0]) * 366
                   + storm["date"].timetuple().tm_yday - 1)
            idx = min(idx, prof.size - 1)
            sx = idx / (prof.size - 1)
            sy = base[i] + amp * np.interp(sx, np.linspace(0, 1, smooth.size),
                                           smooth) / 9.0
            ax.scatter([sx], [sy + 0.006], s=16, color=GOLD, zorder=300)
            ax.plot([sx, sx + 0.025], [sy + 0.010, 0.845], color=GOLD, lw=0.6,
                    alpha=0.8, zorder=300)
            ha = "left" if sx < 0.55 else "right"
            tx = sx + 0.030 if ha == "left" else sx - 0.030
            ax.text(tx, 0.835,
                    f"{storm['date']:%d %b %Y}  ·  Kp {storm['kp']:.1f}\n"
                    "the strongest storm in the record",
                    color=GOLD, fontsize=6.2, alpha=0.9, ha=ha, va="top",
                    zorder=300, linespacing=1.5)
            marked = True


# ------------------------------------------------------- the light curtain
def draw_aurora(ax):
    """The solar wind of the last ~56 hours as a curtain of light.

    Brightness follows a mix of wind speed and southward Bz; the glow
    fades exponentially with height and is broken into vertical rays.
    """
    tp, speed = load_series("swpc-solar-wind-plasma-1m.json", "proton_speed")
    tz, bz = load_series("swpc-solar-wind-mag-1m.json", "bz_gsm")

    t0, t1 = tp.min(), tp.max()
    grid = np.linspace(t0, t1, 1400)
    sp = np.interp(grid, tp, speed)
    bz_g = np.interp(grid, tz, bz)

    x = (grid - t0) / (t1 - t0)
    lo, hi = np.percentile(sp, 2), np.percentile(sp, 98)
    s = np.clip((sp - lo) / max(hi - lo, 1e-6), 0, 1)
    south = np.clip(-bz_g / 6.0, 0, 1)                  # southward = aurora
    env = np.convolve(0.45 * s + 0.55 * south, np.ones(41) / 41, mode="same")
    env = np.clip(env, 0, 1)

    # irregular vertical striations, like the rays of a real curtain
    rng = np.random.default_rng(7)
    noise = rng.random(x.size)
    kern = np.hanning(31)
    kern /= kern.sum()
    stria = np.convolve(np.pad(noise, 15, mode="edge"), kern, mode="valid")
    stria = 0.55 + 0.45 * (stria - stria.min()) / np.ptp(stria)

    h = np.linspace(0, 1, 260)[:, None]                 # 0 = horizon, 1 = top
    glow = env[None, :] ** 1.35 * np.exp(-h / 0.13) * stria[None, :]
    t = np.clip(glow * 1.7, 0, 1)
    low = np.array([0.10, 0.31, 0.37])                  # deep teal
    high = np.array([0.89, 0.98, 0.94])                 # pale jade-white
    col = low * (1 - t[..., None]) + high * t[..., None]
    rgba = np.concatenate([col, np.clip(glow, 0, 1)[..., None]], axis=-1)
    ax.imshow(rgba, extent=[0, 1, GAP - 0.01, 1], origin="lower",
              aspect="auto", zorder=3)

    # a few silk strands drifting through the glow, scattered like the
    # curtain's rays, not in an even row
    picks = rng.choice(x.size, size=110, replace=False)
    for xi, si in sorted(zip(x[picks], env[picks])):
        rise = 0.03 + 0.16 * si
        tt = np.linspace(0, 1, 24)
        bow = 0.008 * np.sin(np.pi * tt) * (si - 0.5)
        pts = np.column_stack([xi + bow, GAP - 0.01 + rise * tt])
        ax.add_collection(LineCollection(
            [pts], colors=[THREAD_CMAP(min(1.0, 0.35 + 0.65 * si))],
            linewidths=0.5, alpha=0.32, zorder=4))


def draw_kp_stars(ax):
    """The last hours of planetary Kp, one minute each, as stars."""
    t, kp = load_series("swpc-planetary-k-index-1m.json", "estimated_kp")
    rng = np.random.default_rng(11)                     # fixed seed, same sky
    x = np.linspace(0.04, 0.96, kp.size)
    y = GAP + 0.06 + rng.random(kp.size) * 0.24
    ax.scatter(x, y, s=0.6 + 3.0 * (kp / 3.0) ** 2, color="#D6F5E6",
               alpha=0.12 + 0.35 * np.clip(kp / 3.0, 0, 1), lw=0, zorder=5)


# ------------------------------------------------------------------ main
def main():
    years, profiles, storm = load_yearly_kp()
    ranges = decade_ranges(years, profiles)
    print(f"gfz: {len(years)} years in {len(ranges)} ranges, "
          f"strongest storm {storm['date']} Kp {storm['kp']:.2f}")

    fig = plt.figure(figsize=(13.0, 7.4), facecolor=SKY_TOP)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # sky: teal at the horizon fading to ink overhead - the gradient is
    # pinned so the horizon colour lands right at the horizon line
    grad = np.linspace(0, 1, 600).reshape(-1, 1)
    ax.imshow(grad, extent=[0, 1, GAP - 0.45, 1], origin="lower", aspect="auto",
              cmap=LinearSegmentedColormap.from_list("sky", [SKY_HORIZON, SKY_TOP]),
              zorder=0)

    draw_aurora(ax)
    draw_kp_stars(ax)
    draw_ridges(ax, ranges, storm)

    # a thin gold horizon, the one warm note in a cold picture
    ax.plot([0.04, 0.96], [GAP, GAP], color=GOLD, lw=0.7, alpha=0.4,
            zorder=200)

    ax.text(0.05, 0.945, "A U R O R A   W A V E S", color=TEXT, fontsize=13,
            alpha=0.92, zorder=300, ha="left", va="center")
    ax.text(0.05, 0.905,
            f"{len(years)} years of geomagnetic weather, in one range",
            color=TEXT, fontsize=8, alpha=0.55, zorder=300, ha="left",
            va="center", style="italic")

    ax.text(0.97, 0.955,
            f"RANGES  daily maximum Kp, one range per decade, {years[0]}-{years[-1]}"
            "  ·  GFZ Niemegk, CC BY 4.0\n"
            "THREADS  solar wind speed and southward Bz, one minute per point, "
            "2026-09-20 to 2026-09-22  ·  NOAA SWPC",
            color=TEXT, fontsize=6.4, alpha=0.62, zorder=300, ha="right",
            va="top", linespacing=1.8)

    out = OUT / "aurora-waves.png"
    fig.savefig(out, dpi=200, facecolor=SKY_TOP)
    print(f"saved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
