# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Six measured variables as a landscape. Offline, deterministic, no synthetic data.

    uv run aurora_waves.py             # save PNG and open a window
    uv run aurora_waves.py --no-show   # save only, including on GitHub

Edit the palette / figure constants below to change the design.
"""
import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from aurora_data import read_gfz, read_swpc

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
BG, INK, MUTED = "#060b25", "#e8f4ee", "#97a8bd"
CYAN, LIME, PURPLE = "#26ead8", "#e4ff69", "#a17aff"
BINS_MINUTES, MIN_SAMPLES, SMOOTH_DAYS = 5, 3, 45
BZ_MAP = LinearSegmentedColormap.from_list("bz", [CYAN, "#83bdf4", PURPLE])
TEMP_MAP = LinearSegmentedColormap.from_list("temp", ["#4bdbea", LIME])
RIDGE_MAP = LinearSegmentedColormap.from_list("ridges", ["#073e52", "#087985", "#193a79", "#342a7a"])


def load_landscape():
    """Complete calendar years only; no fake 366th day in non-leap years."""
    raw_count, daily = read_gfz()
    latest_year = max(daily).year
    years = []
    for y in range(min(daily).year, latest_year + 1):
        expected = (date(y + 1, 1, 1) - date(y, 1, 1)).days
        if sum(d.year == y for d in daily) == expected:
            years.append(y)
    allowed = set(years)
    grouped = defaultdict(list)
    for d, kp in daily.items():
        if d.year in allowed:
            grouped[d.year // 10 * 10].append((d, kp))
    if not grouped:
        raise ValueError("No complete calendar years in GFZ data")
    return raw_count, years, list(grouped.values())


def load_wind():
    """Join valid active plasma and magnetic observations at EXACT UTC minutes.

    Five-minute means require >=3 paired minutes. Empty bins remain NaN;
    no interpolation over telemetry gaps and no endpoint extrapolation.
    """
    plasma = read_swpc("swpc-solar-wind-plasma-1m.json", ("proton_speed", "proton_density", "proton_temperature"))
    mag = read_swpc("swpc-solar-wind-mag-1m.json", ("bt", "bz_gsm"))
    times = sorted(plasma.keys() & mag.keys())
    if len(times) < MIN_SAMPLES:
        raise ValueError("Not enough matching active plasma / magnetic minutes")
    seconds = BINS_MINUTES * 60
    bucket = defaultdict(list)
    for t in times:
        bucket[int(t.timestamp()) // seconds].append(plasma[t] + mag[t])
    keys = np.arange(min(bucket), max(bucket) + 1)
    values = np.full((len(keys), 5), np.nan)
    for i, k in enumerate(keys):
        if len(bucket[k]) >= MIN_SAMPLES:
            values[i] = np.mean(bucket[k], axis=0)
    if not np.isfinite(values).any():
        raise ValueError("No five-minute bin has enough matching observations")
    return (keys + .5) * seconds, values, len(times)


def scaled(values, low, high):
    return np.clip((values - low) / (high - low), 0, 1)


def glow_line(ax, x, y, color, width=.6, z=5):
    for w, a in [(width * 10, .025), (width * 4, .08), (width, .8)]:
        ax.plot(x, y, color=color, lw=w, alpha=a, zorder=z)


def draw_curtain(ax, times, values):
    x = .06 + .88 * (times - times[0]) / (times[-1] - times[0])
    speed, density, temp, bt, bz = values.T
    height = .06 + .20 * scaled(speed, 300, 380)
    colors = BZ_MAP(scaled(bz, -5, 5))
    colors[:, 3] = .2 + .8 * scaled(bt, 0, 6)
    floor = .645
    # Every strand = one observed five-minute bin. Same time on all sky layers.
    valid = np.isfinite(values).all(axis=1)
    segments = [np.array([[xi, floor], [xi, floor + hi]]) for xi, hi in zip(x[valid], height[valid])]
    for lw, fade in [(12, .035), (5, .10), (1.3, .65), (.4, 1)]:
        c = colors[valid].copy()
        c[:, 3] *= fade
        ax.add_collection(LineCollection(segments, colors=c, linewidths=lw, zorder=3))
    top = np.where(valid, floor + height, np.nan)
    glow_line(ax, x, top, CYAN, .65)
    # A point sits just above each thread. Its AREA is linear in density;
    # its hue follows proton temperature. Point count does not encode density.
    point_y = top + .018
    point_colors = TEMP_MAP(scaled(temp, 20000, 100000))
    areas = 2 + 12 * np.clip(density, 0, 5)
    ax.scatter(x[valid], point_y[valid], s=areas[valid] * 4, c=point_colors[valid], alpha=.05, lw=0, zorder=7)
    ax.scatter(x[valid], point_y[valid], s=areas[valid], c=point_colors[valid], alpha=.8, lw=0, zorder=8)
    ax.plot([.06, .94], [.632, .632], color=MUTED, lw=.5, alpha=.4)
    for f in np.linspace(0, 1, 5):
        t = datetime.fromtimestamp(times[0] + f * (times[-1] - times[0]), timezone.utc)
        xx = .06 + .88 * f
        ax.text(xx, .618, t.strftime("%d %b · %H:%M"), ha="center", color=MUTED, fontsize=7)
    ax.text(.06, .864, "01 / SOLAR WIND", color=CYAN, fontsize=8, weight="bold")
    ax.text(.94, .864, "UTC  /  FIVE-MINUTE MEANS  /  GAPS LEFT EMPTY", color=MUTED, fontsize=7, ha="right")


def draw_ridges(ax, ranges):
    x = np.linspace(.06, .94, 1500)
    all_peaks = 0
    for i, rows in enumerate(ranges):
        dates, v = zip(*rows)
        v = np.asarray(v)
        # Edge padding for the centred 45-day mean; no extra dates are created.
        smooth = np.convolve(np.pad(v, SMOOTH_DAYS // 2, mode="edge"), np.ones(SMOOTH_DAYS) / SMOOTH_DAYS, mode="valid")
        xx = np.linspace(.06, .94, len(v))
        crest = np.interp(x, xx, smooth) / 9
        base = .481 - .027 * i
        y = base + .19 * crest
        color = RIDGE_MAP(i / max(1, len(ranges) - 1))
        ax.fill_between(x, .253, y, color=color, zorder=20+i*2)
        # Contours repeat the measured silhouette; repetitions are texture,
        # not more measurements or imaginary topography.
        lines = [np.column_stack([x, np.where(y - j * .0025 >= .253, y - j * .0025, np.nan)]) for j in range(17)]
        ax.add_collection(LineCollection(lines, colors=CYAN if i < 6 else "#8193ff", linewidths=.35, alpha=.20, zorder=21+i*2))
        ax.plot(x, y, color=CYAN if i < 6 else "#90a4ff", lw=.65, alpha=.95, zorder=21+i*2)
        # Highlight ALL Kp=9 days, not an arbitrarily selected "strongest" one.
        extreme = np.flatnonzero(v == 9)
        all_peaks += len(extreme)
        px = xx[extreme]
        py = base + .19 * smooth[extreme] / 9
        ax.scatter(px, py, s=8, c=LIME, lw=0, zorder=60)
        ax.text(.045, base+.06, f"{dates[0].year}\n{dates[-1].year}", color=MUTED, ha="right", fontsize=6.2, linespacing=1.0, zorder=80)
    ax.text(.06, .591, "02 / GEOMAGNETIC MEMORY", color=CYAN, fontsize=8, weight="bold")
    ax.text(.94, .591, f"{all_peaks} DAYS REACHED Kp 9  /  LIME MARKERS", color=LIME, fontsize=7, ha="right")
    ax.text(.06, .231, "START OF EACH RANGE", color=MUTED, fontsize=6.5)
    ax.text(.94, .231, "END OF EACH RANGE  →", color=MUTED, fontsize=6.5, ha="right")
    ax.text(.50, .231, "45-day mean of daily maximum Kp · equal height scale · each range has its own years", color=MUTED, fontsize=6.5, ha="center")


def draw_legend(fig, times, values, ranges):
    # Small quantitative traces anchor the artwork in units and real ranges.
    history = np.array([v for rows in ranges for _, v in rows])
    specs = [
        ("01  Kp", "RIDGE HEIGHT", "0–9 · unitless", history, CYAN),
        ("02  SPEED", "THREAD LENGTH", "300–380 km/s", values[:, 0], CYAN),
        ("03  Bz · GSM", "THREAD HUE", "−5 nT cyan → +5 nT violet", values[:, 4], PURPLE),
        ("04  Bt", "THREAD OPACITY", "0–6 nT · faint → bright", values[:, 3], "#b6b5ff"),
        ("05  DENSITY", "POINT AREA", "0–5 protons/cm³", values[:, 1], LIME),
        ("06  TEMPERATURE", "POINT HUE", "20–100 kK · cyan → lime", values[:, 2], LIME),
    ]
    for j, (title, encoding, scale, v, color) in enumerate(specs):
        left = .055 + j * .15
        fig.text(left, .183, title, color=color, fontsize=9, weight="bold")
        fig.text(left, .163, encoding, color=INK, fontsize=6.8)
        fig.text(left, .145, scale, color=MUTED, fontsize=6.4)
        ax = fig.add_axes([left, .085, .125, .043], facecolor="none")
        if j == 0:
            # Monthly-like 30-day block means only in this compact overview.
            vv = history[:len(history)//30*30].reshape(-1,30).mean(axis=1)
            xx = np.linspace(0,1,len(vv))
        else:
            vv, xx = v, times
        ax.plot(xx, vv, color=color, lw=.6)
        ax.set_xlim(xx[0], xx[-1])
        ax.set_ylim((0,9) if j == 0 else (min(vv[np.isfinite(vv)]), max(vv[np.isfinite(vv)])))
        ax.axis("off")
        good = v[np.isfinite(v)]
        label = f"observed {min(good):.2f}–{max(good):.2f}"
        if j == 5:
            label = f"observed {min(good)/1000:.1f}–{max(good)/1000:.1f} kK"
        fig.text(left, .069, label, color=MUTED, fontsize=6.4)


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--no-show", action="store_true", help="save PNG without opening a window")
    no_show = args.parse_args().no_show
    if no_show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    count, years, ranges = load_landscape()
    times, values, paired = load_wind()
    start, end = [datetime.fromtimestamp(t, timezone.utc) for t in (times[0]-150, times[-1]+150)]
    print(f"GFZ: {count:,} raw rows; {len(years)} complete years {years[0]}–{years[-1]}")
    print(f"SWPC: {paired:,} paired active minutes; {np.isfinite(values).all(axis=1).sum()} valid five-minute bins / {len(times)}")
    print(f"UTC bin edges: {start.isoformat()} → {end.isoformat()}")
    fig = plt.figure(figsize=(18, 12), facecolor=BG)
    ax = fig.add_axes([0,0,1,1])
    ax.set(xlim=(0,1), ylim=(0,1)); ax.axis("off")
    # Atmospheric background is layout, not a measurement.
    yy, xx = np.mgrid[0:1:800j, 0:1:1200j]
    rgba = np.zeros((*yy.shape,4))
    rgba[:,:,:3] = to_rgb("#293977")
    rgba[:,:,3] = .45 * np.exp(-((yy-.59)/.26)**2) * (.6+.4*np.sin(xx*np.pi))
    ax.imshow(rgba, extent=(0,1,0,1), origin="lower", aspect="auto")
    fig.text(.055,.945,"AURORA WAVES",color=INK,fontsize=34,weight="normal")
    fig.text(.058,.916,"A landscape made from six measurements of space weather",color=MUTED,fontsize=10)
    fig.text(.945,.951,"94 YEARS / ONE DAY" if len(years)==94 else f"{len(years)} YEARS / SOLAR WIND",color=LIME,fontsize=10,ha="right")
    fig.text(.945,.928,f"GFZ {years[0]}–{years[-1]}  ·  NOAA {start:%d}–{end:%d %b %Y}",color=MUTED,fontsize=8,ha="right")
    draw_curtain(ax, times, values)
    draw_ridges(ax, ranges)
    ax.plot([.055,.945],[.208,.208],color=MUTED,lw=.5,alpha=.35)
    draw_legend(fig,times,values,ranges)
    fig.text(.055,.033,"GFZ Niemegk · CC BY 4.0  /  NOAA SWPC · active spacecraft  /  cached 22 September 2026",color=MUTED,fontsize=7)
    fig.text(.945,.033,"DATA ART  ·  colours are encodings, not observed auroral colours",color=MUTED,fontsize=7,ha="right")
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT/"aurora-waves.png",dpi=200,facecolor=BG)
    print("saved out/aurora-waves.png")
    if not no_show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
