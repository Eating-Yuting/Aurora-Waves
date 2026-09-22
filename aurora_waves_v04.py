# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy", "pillow"]
# ///
"""Aurora Waves v04 — a week in the solar wind.

V03 moved a window across ONE day of the live NOAA feed. The live feed only
holds 24 hours, so a week has to come from somewhere else: NASA's OMNI archive,
which merges the L1 spacecraft into one record per minute and reaches back to
1981. The week drawn here is 7–14 October 2024 — the storm of 10 October, when
Kp reached 8.7 and Bz fell to −46 nT.

    uv run aurora_waves_v04.py                    # GIF and a poster frame
    uv run aurora_waves_v04.py --frames 80        # shorter loop, smaller file
    uv run aurora_waves_v04.py --window 12        # wider window, calmer motion

The drawing is V02's, imported rather than copied, so the still, the one-day
animation and the week animation cannot drift apart. What is new here: the
loader for the archive file, the encoding scales (V02's were set for a quiet
day and would saturate on a storm), and a strip that shows the whole week with
the moving window marked on it.

The five-minute rule is different from V02's, on purpose. V02 required three
minutes where BOTH instruments reported; here each instrument is averaged over
its own valid minutes inside the same clock bin, and a bin exists when both are
present. OMNI's two instruments drop out at different times (the magnetometer
95.8% of minutes, the plasma 79.6%), so demanding they agree to the minute
would discard a fifth of the week for no physical reason — at most five minutes
of alignment sits inside one bin. Nothing is interpolated across a gap.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
from matplotlib.colors import to_rgb
from PIL import Image

from aurora_waves import load_landscape, scaled

# Reused, not re-implemented: the still and both animations must agree.
from aurora_waves_v02 import (
    BG, GREEN, MUTED, POINT_MAP, TEXT,
    curtain_samples, draw_memory, runs,
)

ROOT = Path(__file__).resolve().parent
CSV_NAME = "omni-hro-1min-2024-10-07-to-10-14.csv"
GIF_NAME = "aurora-waves-v04-week-in-motion.gif"
POSTER_NAME = "aurora-waves-v04-poster.png"

BIN_SECONDS = 300                          # five-minute clock bins, as in V02
FILL = np.array([9999.99, 9999.99, 99999.9, 999.99, 9999999.0])   # OMNI's fill values
# Scales read off this week's own five-minute bins, not guessed (see PROCESS.md).
SPEED_LO, SPEED_HI = 380, 800              # km/s
BT_LO, BT_HI = 0, 45                       # nT
BZ_FULL = 45                               # nT, the clip on the lower-edge position
DENSITY_FULL = 30                          # protons/cm^3, the clip on point area
TEMP_LO, TEMP_HI = 20000, 500000           # K

FIG = (18, 12)
FRAME_DPI = 60          # 1080 x 720, sized for a looping GIF held entirely in memory
POSTER_DPI = 150
PALETTE_COLOURS = 128   # one palette for the whole loop, so colours cannot flicker
PICKS = 9               # frames sampled when building that shared palette
LEGAL = ('NASA OMNI / CDAWeb   ·   GFZ CC BY 4.0   /   archived observations   '
         '/   all times UTC')
NOTE = ('DATA ART   ·   aurora-inspired colour, not a photographic or '
        'visibility reconstruction')
STRIP_BASE = .3915      # the week strip: whole-week reach, with the window marked
STRIP_TOP = .404


# ---------------------------------------------------------------------------
# The archive file.
# ---------------------------------------------------------------------------

def read_omni(path):
    """One row per UTC minute. Fill values become NaN; nothing else is touched."""
    stamp, rows = [], []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split(",")
        stamp.append(int(np.datetime64(parts[0].rstrip("Z"), "s").astype("int64")))
        rows.append([float(x) for x in parts[1:6]])
    minute = np.where(np.abs(np.array(rows) - FILL) < 1, np.nan, np.array(rows))
    return np.array(stamp), minute


def load_omni_week():
    """Five-minute means, one instrument at a time, into (time, values, paired).

    Column order matches V02 — speed, density, temperature, Bt, Bz — so the
    drawing code receives what it was written for.
    """
    stamp, minute = read_omni(ROOT / "data" / CSV_NAME)
    mag_ok = np.isfinite(minute[:, 0]) & np.isfinite(minute[:, 1])
    plasma_ok = np.isfinite(minute[:, 2]) & np.isfinite(minute[:, 3]) & np.isfinite(minute[:, 4])
    buckets = defaultdict(list)
    for i, second in enumerate(stamp):
        buckets[int(second) // BIN_SECONDS].append(i)
    keys = np.arange(min(buckets), max(buckets) + 1)
    values = np.full((len(keys), 5), np.nan)
    for i, key in enumerate(keys):
        rows = buckets.get(key)
        if not rows:
            continue
        rows = np.array(rows)
        mag, plasma = rows[mag_ok[rows]], rows[plasma_ok[rows]]
        if len(mag) == 0 or len(plasma) == 0:
            continue                                   # one instrument absent: the bin stays empty
        values[i] = np.r_[minute[plasma][:, 2:5].mean(axis=0),
                          minute[mag][:, 0:2].mean(axis=0)]
    if not np.isfinite(values).any():
        raise ValueError("No five-minute bin has both instruments")
    return (keys + .5) * BIN_SECONDS, values, int((mag_ok & plasma_ok).sum())


FEATHER_MINUTES = 12  # glow fades this far into a gap; the line and dots still break.
                      # Wide enough that a single five-minute hole dims instead of
                      # cutting a black stripe through a bright curtain.


def feather(present, dense_t, minutes=FEATHER_MINUTES):
    """Soft shoulders on a data gap, so a hole reads as thinning, not as a cut.

    Only interior boundaries are feathered — the edges of the window are the
    edge of the viewport, not missing data, and they stay hard. The mask itself
    is returned unchanged: callers keep breaking the edge line and dropping the
    light points on the real gaps, so the hole is still there to be seen.
    """
    w = present.astype(float).copy()
    ramp = max(1, int(minutes * 60 / (dense_t[1] - dense_t[0])))
    interior = (dense_t[0] + 1, dense_t[-1] - 1)
    for a, b in runs(present):
        n = min(ramp, (b - a) // 2)
        if a > 0 and dense_t[a] > interior[0]:
            w[a:a + n] *= np.linspace(0, 1, n)
        if b < len(w) and dense_t[b - 1] < interior[1]:
            w[b - n:b] *= np.linspace(1, 0, n)
    return w


def veil_geometry_week(v):
    """V02's encodings, re-scaled for a storm.

    V02 clamped Bz at ±5 nT and Bt at 6 nT, which is right for a quiet day and
    useless for this week: Bz reached −46 nT and Bt 48 nT, so every frame would
    have been pinned to one colour. Same three encodings, wider rulers.
    """
    speed, density, temp, bt, bz = v.T
    edge = .60 + .15 * np.clip(bz / BZ_FULL, -1, 1)
    reach = .095 + .21 * scaled(speed, SPEED_LO, SPEED_HI)
    brightness = .18 + .82 * scaled(bt, BT_LO, BT_HI)
    return edge, reach, brightness


# ---------------------------------------------------------------------------
# The frames.
# ---------------------------------------------------------------------------

def veil_window(ax, dense_t, dense, times, values, smooth, t_start, t_span, t0, span):
    """Draw only the part of the curtain that falls inside [t0, t0 + span]."""
    inside = (dense_t >= t0) & (dense_t <= t0 + span)
    t, v = dense_t[inside], dense[inside]
    good = np.isfinite(v).all(axis=1)
    edge, reach, brightness = veil_geometry_week(np.nan_to_num(v))
    xx = .055 + .89 * (t - t0) / span
    yy = np.linspace(.36, .89, 1100)[:, None]
    height = yy - edge[None, :]
    u = height / reach[None, :]
    phase = ((t - t_start) / t_span)[None, :]
    filaments = (.68 + .22 * np.sin(phase * 1350 + u * 1.2) ** 2
                 + .10 * np.sin(phase * 2390 - u * .9) ** 2)
    core = np.exp(-((height - .009) / .019) ** 2)
    body = np.exp(-np.maximum(u, 0) * 3.4) * (1 / (1 + np.exp(np.clip(-height * 450, -50, 50))))
    cap = 1 / (1 + np.exp(np.clip((u - .97) * 25, -50, 50)))
    green_light = (core * .45 + body * .76) * filaments * cap * brightness[None, :]
    red_light = .075 * np.exp(-((u - .86) / .28) ** 2) * brightness[None, :]
    purple_light = .25 * np.exp(-((height + .013) / .007) ** 2) * brightness[None, :]
    for layer in (green_light, red_light, purple_light):
        layer[:, ~good] = 0
    # The glow gets soft shoulders at a gap; the line below still breaks, so the
    # hole stays visible without reading as a rendering fault.
    shoulder = feather(good, t)[None, :]
    rgb = (green_light[..., None] * np.array([.30, 1, .39]) +
           red_light[..., None] * np.array([1, .15, .33]) +
           purple_light[..., None] * np.array([.68, .28, 1]))
    alpha = np.clip(np.max(rgb, axis=2), 0, 1) * shoulder
    colour = np.clip(rgb / np.maximum(alpha[..., None], 1e-6), 0, 1)
    ax.imshow(np.dstack([colour, alpha]), extent=[.055, .945, .36, .89], origin='lower',
              aspect='auto', zorder=3, interpolation='bilinear')
    y = np.where(good, edge + .003, np.nan)
    for lw, a in ((10, .025), (4, .08), (.6, .5)):
        ax.plot(xx, y, color=GREEN, lw=lw, alpha=a, zorder=4)

    # One light point per five-minute observation inside the window. Density is
    # still the only thing driving AREA; temperature still only drives hue.
    m = (times >= t0) & (times <= t0 + span)
    valid = np.isfinite(values[m]).all(axis=1)
    px = .055 + .89 * (times[m] - t0) / span
    point_y = veil_geometry_week(np.nan_to_num(smooth[m]))[0] - .043
    area = 1.5 + .9 * np.clip(values[m][:, 1], 0, DENSITY_FULL)
    pc = POINT_MAP(scaled(values[m][:, 2], TEMP_LO, TEMP_HI))
    ax.scatter(px[valid], point_y[valid], s=area[valid] * 5, c=pc[valid], alpha=.045, lw=0, zorder=8)
    ax.scatter(px[valid], point_y[valid], s=area[valid], c=pc[valid], alpha=.8, lw=0, zorder=9)

    ax.text(.055, .866, '01   /   A WEEK IN THE SOLAR WIND   ·   IN MOTION', color=MUTED, fontsize=7.5)
    start = datetime.fromtimestamp(t0, timezone.utc)
    end = datetime.fromtimestamp(t0 + span, timezone.utc)
    ax.text(.945, .866, f'{start:%d %b %H:%M} → {end:%d %b %H:%M} UTC   ·   8-HOUR WINDOW',
            ha='right', color=MUTED, fontsize=7.5)
    for f in (0, .25, .5, .75, 1):
        tx = .055 + .89 * f
        dt = datetime.fromtimestamp(t0 + f * span, timezone.utc)
        ax.plot([tx, tx], [.427, .433], color=MUTED, alpha=.5, lw=.5, zorder=50)
        ax.text(tx, .413, dt.strftime('%d %b  %H:%M'), color=MUTED, fontsize=6.5,
                ha='center', zorder=50)


def week_strip(ax, times, values, t_start, t_span, t0, span, peaks):
    """The whole week at once, with the moving window marked on it.

    A bare progress line says where you are; this says where you are AND what
    the rest of the week looked like — the same curtain reach, compressed, with
    a square-root lift so a quiet day is still visible under a storm. Empty
    bins leave a hole here exactly as they do in the sky above.
    """
    good = np.isfinite(values).all(axis=1)
    x = .055 + .89 * (times - t_start) / t_span
    reach = veil_geometry_week(np.nan_to_num(values))[1]
    lift = np.clip((reach - .095) / .21, 0, 1) ** .5
    top = np.where(good, STRIP_BASE + (STRIP_TOP - STRIP_BASE) * lift, np.nan)
    ax.fill_between(x, STRIP_BASE, np.where(np.isfinite(top), top, STRIP_BASE),
                    color=GREEN, alpha=.17, lw=0, zorder=80)
    inside = (times >= t0) & (times <= t0 + span)
    bright = np.isfinite(top) & inside
    ax.fill_between(x, STRIP_BASE, np.where(bright, top, STRIP_BASE),
                    color=GREEN, alpha=.6, lw=0, zorder=81)
    ax.plot([.055, .945], [STRIP_BASE, STRIP_BASE], color=MUTED, lw=.4, alpha=.35, zorder=82)

    wa = .055 + .89 * (t0 - t_start) / t_span
    wb = .055 + .89 * (t0 + span - t_start) / t_span
    for edge in (wa, wb):
        ax.plot([edge, edge], [STRIP_BASE - .002, STRIP_TOP + .001], color=GREEN,
                lw=.7, alpha=.9, zorder=83)

    for when, kp in peaks:
        px = .055 + .89 * (when - t_start) / t_span
        ax.plot([px, px], [STRIP_BASE, STRIP_BASE - .007], color='#caff93',
                lw=.8, alpha=.8, zorder=83)
    if peaks:
        worst = max(peaks, key=lambda p: p[1])
        px = .055 + .89 * (worst[0] - t_start) / t_span
        ax.text(px + .008, STRIP_BASE - .010,
                f'{datetime.fromtimestamp(worst[0], timezone.utc):%d %b} · Kp {worst[1]:.1f}'
                ' · the week\'s storm',
                color='#caff93', fontsize=6, va='top', zorder=84)


def shade(ax):
    """Unchanged background: a low-contrast atmospheric wash, purely composition."""
    yy, xx = np.mgrid[0:1:900j, 0:1:1300j]
    glow = np.exp(-((yy - .46) / .20) ** 2) * np.exp(-((xx - .50) / .6) ** 2)
    wash = np.empty((*yy.shape, 4))
    wash[:, :, :3] = to_rgb('#0e463e')
    wash[:, :, 3] = glow * .26
    ax.imshow(wash, origin='lower', extent=[0, 1, 0, 1], aspect='auto', zorder=0)


def clean_axes(ax):
    ax.cla()
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis('off')
    shade(ax)


def build_figure():
    """Canvas and everything that is identical in every frame."""
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=FIG, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    clean_axes(ax)
    fig.text(.055, .949, 'Aurora Waves', fontfamily='DejaVu Serif', fontsize=35, color=TEXT)
    fig.text(.057, .920, 'EMERALD VEIL IN MOTION   /   SEVEN DAYS OF MEASURED SOLAR WIND',
             fontsize=8, color=MUTED)
    fig.text(.945, .959, 'V.04', fontsize=14, color=GREEN, ha='right')
    fig.text(.945, .936, '7–14 OCT 2024  /  NASA OMNI', fontsize=7.5, color=MUTED, ha='right')
    fig.text(.945, .919, '1932–2025  /  GFZ NIEMEGK', fontsize=7.5, color=MUTED, ha='right')
    fig.text(.055, .019, LEGAL, fontsize=6, color=MUTED)
    fig.text(.945, .019, NOTE, fontsize=6, color=MUTED, ha='right')
    counter = fig.text(.5, .019, '', fontsize=6, color=MUTED, ha='center')
    return fig, ax, counter


def draw_key_week(fig):
    """Same six encodings as V02, with this week's rulers printed under them."""
    specs = [('01 / Kp', 'RIDGE HEIGHT', '0–9 · unitless', GREEN),
             ('02 / SPEED', 'CURTAIN REACH', f'{SPEED_LO}–{SPEED_HI} km/s', GREEN),
             ('03 / Bz', 'LOWER-EDGE POSITION', f'±{BZ_FULL} nT · lower → higher', '#1bebad'),
             ('04 / Bt', 'GLOW INTENSITY', f'{BT_LO}–{BT_HI} nT · faint → bright', '#1bebad'),
             ('05 / DENSITY', 'POINT AREA', f'0–{DENSITY_FULL} protons/cm³', '#c1e7b3'),
             ('06 / TEMPERATURE', 'POINT COLOUR',
              f'{TEMP_LO // 1000}–{TEMP_HI // 1000} kK · green → mauve', '#d998da')]
    for i, (title, enc, scale, col) in enumerate(specs):
        left = .055 + i * .15
        fig.text(left, .079, title, color=col, fontsize=8.5)
        fig.text(left, .061, enc, color=TEXT, fontsize=6.5)
        fig.text(left, .044, scale, color=MUTED, fontsize=6)


def compose(ax, dense_t, dense, times, values, smooth, ranges, peaks,
            t_start, t_span, t0, span):
    """Everything that changes from frame to frame, on the axes only."""
    clean_axes(ax)
    veil_window(ax, dense_t, dense, times, values, smooth, t_start, t_span, t0, span)
    week_strip(ax, times, values, t_start, t_span, t0, span, peaks)
    draw_memory(ax, ranges, label_dy=-.014)
    ax.plot([.055, .945], [.097, .097], color=MUTED, lw=.45, alpha=.3, zorder=80)


def to_image(fig, dpi):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, facecolor=BG)
    buf.seek(0)
    return Image.open(buf).convert('RGB')


def shared_palette(frames):
    """One palette for the whole loop, sampled across it, so nothing flickers."""
    picks = np.linspace(0, len(frames) - 1, min(PICKS, len(frames))).astype(int)
    w, h = frames[0].size
    strip = Image.new('RGB', (w, h * len(picks)))
    for k, i in enumerate(picks):
        strip.paste(frames[i], (0, k * h))
    return strip.quantize(colors=PALETTE_COLOURS, method=Image.MEDIANCUT)


def storm_days(ranges, start, end):
    """Every day in the week whose daily maximum Kp reached 6, from the GFZ record.

    `start` is a bin centre, not midnight, so the first day is matched with a
    day's slack rather than dropped.
    """
    daily = {d: v for rows in ranges for d, v in rows}
    out = []
    for day, kp in sorted(daily.items()):
        when = datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp()
        if start - 86400 <= when <= end and kp >= 6:
            out.append((when, kp))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--frames', type=int, default=161, help='frames in the loop (default 161)')
    ap.add_argument('--window', type=float, default=8.0, help='hours visible at once (default 8)')
    ap.add_argument('--duration', type=int, default=110, help='milliseconds per frame (default 110)')
    ap.add_argument('--dither', action='store_true', help='dither the shared palette (larger file)')
    args = ap.parse_args()

    import matplotlib.pyplot as plt

    _, _, ranges = load_landscape()
    times, values, paired = load_omni_week()
    bins = int(np.isfinite(values).all(axis=1).sum())
    t_start, t_end = times[0], times[-1]
    t_span = t_end - t_start
    span = args.window * 3600
    if not 0 < span < t_span:
        raise SystemExit(f'--window must be between 0 and {t_span/3600:.1f} hours')
    if args.frames < 2:
        raise SystemExit('--frames must be at least 2')
    peaks = storm_days(ranges, t_start, t_end)

    # Smooth once, over the whole week, so a given moment never depends on which
    # frame happens to be on screen. Same samples per hour as V03.
    dense_t, dense, smooth = curtain_samples(times, values, width=2880 * 7)
    travel = t_span - span
    steps = args.frames
    fig, ax, counter = build_figure()
    draw_key_week(fig)

    frames = []
    for i in range(steps):
        t0 = t_start + travel * (i / (steps - 1))
        compose(ax, dense_t, dense, times, values, smooth, ranges, peaks,
                t_start, t_span, t0, span)
        counter.set_text(f'FRAME {i+1:03d} / {steps}')
        frames.append(to_image(fig, FRAME_DPI))
        print(f'  frame {i+1:3d}/{steps}   {datetime.fromtimestamp(t0, timezone.utc):%d %b %H:%M}')

    # The poster is the frame that contains the deepest Bz of the week, snapped
    # to the loop's own grid so the still is exactly one of the frames.
    deepest = times[int(np.nanargmin(values[:, 4]))]
    cover = np.clip(deepest - span / 2, t_start, t_start + travel)
    mid = t_start + travel * round((cover - t_start) / travel * (steps - 1)) / (steps - 1)
    compose(ax, dense_t, dense, times, values, smooth, ranges, peaks,
            t_start, t_span, mid, span)
    counter.set_text('')
    out = ROOT / 'out'
    if not out.is_dir():
        out.mkdir(parents=True)
    fig.savefig(out / POSTER_NAME, dpi=POSTER_DPI, facecolor=BG)

    palette = shared_palette(frames)
    dither = Image.FLOYDSTEINBERG if args.dither else Image.NONE
    quantised = [f.quantize(palette=palette, dither=dither) for f in frames]
    gif = out / GIF_NAME
    quantised[0].save(gif, save_all=True, append_images=quantised[1:], duration=args.duration,
                      loop=0, optimize=True, disposal=1)
    plt.close(fig)

    print(f'saved out/{GIF_NAME}  ({steps} frames, {args.window:g} h window, '
          f'{gif.stat().st_size // 1024} KB)')
    print(f'saved out/{POSTER_NAME}')
    print(f'{paired} paired minutes; {bins} of {len(times)} five-minute bins usable '
          f'({100*bins/len(times):.1f}%); poster at '
          f'{datetime.fromtimestamp(mid, timezone.utc):%d %b %H:%M} UTC')


if __name__ == '__main__':
    main()
