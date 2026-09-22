# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy", "pillow"]
# ///
"""Aurora Waves v03 — Emerald Veil in motion.

The same 24 hours of NOAA solar wind as V02, drawn through a moving window so
the green curtain flows past instead of standing still. One frame every few
minutes of the record. The mountain ranges do not move: the 94-year Kp record
is fixed, and only the sky has a clock.

    uv run aurora_waves_v03.py                 # the GIF and a poster frame
    uv run aurora_waves_v03.py --frames 64     # shorter loop, smaller file
    uv run aurora_waves_v03.py --window 12     # wider window, calmer motion

Every drawing decision comes from aurora_waves_v02.py, which is imported rather
than copied, so the still and the moving version cannot drift apart. Only the
window, the frame loop and the GIF assembly are new here.
"""
import argparse
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
from matplotlib.colors import to_rgb
from PIL import Image

from aurora_waves import load_landscape, load_wind, scaled

# Reused, not re-implemented: the still and the animation must agree.
from aurora_waves_v02 import (
    BG, GREEN, MUTED, POINT_MAP, TEXT,
    curtain_samples, draw_key, draw_memory, veil_geometry,
)

ROOT = Path(__file__).resolve().parent
GIF_NAME = "aurora-waves-v03-emerald-veil-in-motion.gif"
POSTER_NAME = "aurora-waves-v03-poster.png"
FIG = (18, 12)          # same canvas as V02, so the layout is the same layout
FRAME_DPI = 65          # 1170 x 780, sized for a looping GIF
POSTER_DPI = 150        # the still that goes in the README
PALETTE_COLOURS = 128   # one palette for the whole loop, so colours cannot flicker
PICKS = 7               # frames sampled when building that shared palette
LEGAL = 'NOAA SWPC   ·   GFZ CC BY 4.0   /   cached observations   /   all times UTC'
NOTE = 'DATA ART   ·   aurora-inspired colour, not a photographic or visibility reconstruction'


def veil_window(ax, dense_t, dense, times, values, smooth, t_start, t_span, t0, span):
    """Draw only the part of the curtain that falls inside [t0, t0 + span]."""
    inside = (dense_t >= t0) & (dense_t <= t0 + span)
    t, v = dense_t[inside], dense[inside]
    good = np.isfinite(v).all(axis=1)
    # NaN only for the arithmetic; missing columns are masked out before drawing.
    edge, reach, brightness = veil_geometry(np.nan_to_num(v))
    xx = .055 + .89 * (t - t0) / span
    yy = np.linspace(.36, .89, 1100)[:, None]
    height = yy - edge[None, :]
    u = height / reach[None, :]
    # Texture is tied to the data's own clock, so it travels with the curtain
    # instead of shimmering underneath it. Drawing texture, not measurement.
    phase = ((t - t_start) / t_span)[None, :]
    filaments = (.68 + .22 * np.sin(phase * 1350 + u * 1.2) ** 2
                 + .10 * np.sin(phase * 2390 - u * .9) ** 2)
    core = np.exp(-((height - .009) / .019) ** 2)
    body = np.exp(-np.maximum(u, 0) * 3.4) * (1 / (1 + np.exp(np.clip(-height * 450, -50, 50))))
    cap = 1 / (1 + np.exp(np.clip((u - .97) * 25, -50, 50)))
    green_light = (core * .45 + body * .76) * filaments * cap * brightness[None, :]
    # The purple hem and red upper glow are colour styling, not measured emissions.
    red_light = .075 * np.exp(-((u - .86) / .28) ** 2) * brightness[None, :]
    purple_light = .25 * np.exp(-((height + .013) / .007) ** 2) * brightness[None, :]
    for layer in (green_light, red_light, purple_light):
        layer[:, ~good] = 0
    rgb = (green_light[..., None] * np.array([.30, 1, .39]) +
           red_light[..., None] * np.array([1, .15, .33]) +
           purple_light[..., None] * np.array([.68, .28, 1]))
    alpha = np.clip(np.max(rgb, axis=2), 0, 1)
    colour = np.clip(rgb / np.maximum(alpha[..., None], 1e-6), 0, 1)
    ax.imshow(np.dstack([colour, alpha]), extent=[.055, .945, .36, .89], origin='lower',
              aspect='auto', zorder=3, interpolation='bilinear')
    y = np.where(good, edge + .003, np.nan)
    for lw, a in ((10, .025), (4, .08), (.6, .5)):
        ax.plot(xx, y, color=GREEN, lw=lw, alpha=a, zorder=4)

    # One light point per five-minute observation inside the window.
    m = (times >= t0) & (times <= t0 + span)
    valid = np.isfinite(values[m]).all(axis=1)
    px = .055 + .89 * (times[m] - t0) / span
    point_y = veil_geometry(np.nan_to_num(smooth[m]))[0] - .043
    area = 1.5 + 4 * np.clip(values[m][:, 1], 0, 5)
    pc = POINT_MAP(scaled(values[m][:, 2], 20000, 100000))
    ax.scatter(px[valid], point_y[valid], s=area[valid] * 5, c=pc[valid], alpha=.045, lw=0, zorder=8)
    ax.scatter(px[valid], point_y[valid], s=area[valid], c=pc[valid], alpha=.8, lw=0, zorder=9)

    ax.text(.055, .866, '01   /   A DAY IN THE SOLAR WIND   ·   IN MOTION', color=MUTED, fontsize=7.5)
    start = datetime.fromtimestamp(t0, timezone.utc)
    end = datetime.fromtimestamp(t0 + span, timezone.utc)
    ax.text(.945, .866, f'{start:%d %b %H:%M} → {end:%H:%M} UTC   ·   SOLAR1 ACTIVE',
            ha='right', color=MUTED, fontsize=7.5)
    for f in (0, .25, .5, .75, 1):
        tx = .055 + .89 * f
        dt = datetime.fromtimestamp(t0 + f * span, timezone.utc)
        ax.plot([tx, tx], [.427, .433], color=MUTED, alpha=.5, lw=.5, zorder=50)
        ax.text(tx, .413, dt.strftime('%d %b  %H:%M'), color=MUTED, fontsize=6.5,
                ha='center', zorder=50)
    # Where this window sits inside the whole day: the bright segment is the window.
    ax.plot([.055, .945], [.4005, .4005], color=MUTED, lw=.8, alpha=.3, zorder=60)
    wa = .055 + .89 * (t0 - t_start) / t_span
    wb = .055 + .89 * (t0 + span - t_start) / t_span
    ax.plot([wa, wb], [.4005, .4005], color=GREEN, lw=1.8, alpha=.85, zorder=61,
            solid_capstyle='round')


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
    fig.text(.057, .920, 'EMERALD VEIL IN MOTION   /   SIX MEASUREMENTS, ONE DAY LANDSCAPE',
             fontsize=8, color=MUTED)
    fig.text(.945, .959, 'V.03', fontsize=14, color=GREEN, ha='right')
    fig.text(.945, .936, '21–22 SEP 2026  /  NOAA SWPC', fontsize=7.5, color=MUTED, ha='right')
    fig.text(.945, .919, '1932–2025  /  GFZ NIEMEGK', fontsize=7.5, color=MUTED, ha='right')
    fig.text(.055, .019, LEGAL, fontsize=6, color=MUTED)
    fig.text(.945, .019, NOTE, fontsize=6, color=MUTED, ha='right')
    counter = fig.text(.5, .019, '', fontsize=6, color=MUTED, ha='center')
    return fig, ax, counter


def compose(ax, dense_t, dense, times, values, smooth, ranges, t_start, t_span, t0, span):
    """Everything that changes from frame to frame, on the axes only."""
    clean_axes(ax)
    veil_window(ax, dense_t, dense, times, values, smooth, t_start, t_span, t0, span)
    draw_memory(ax, ranges)
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--frames', type=int, default=96, help='frames in the loop (default 96)')
    ap.add_argument('--window', type=float, default=8.0, help='hours visible at once (default 8)')
    ap.add_argument('--duration', type=int, default=100, help='milliseconds per frame (default 100)')
    ap.add_argument('--dither', action='store_true', help='dither the shared palette (larger file)')
    args = ap.parse_args()

    import matplotlib.pyplot as plt

    _, _, ranges = load_landscape()
    times, values, paired = load_wind()
    bins = int(np.isfinite(values).all(axis=1).sum())
    t_start, t_end = times[0], times[-1]
    t_span = t_end - t_start
    span = args.window * 3600
    if not 0 < span < t_span:
        raise SystemExit(f'--window must be between 0 and {t_span/3600:.1f} hours')
    if args.frames < 2:
        raise SystemExit('--frames must be at least 2')

    # Smooth once, over the whole record, so a given moment never depends on which
    # frame happens to be on screen.
    dense_t, dense, smooth = curtain_samples(times, values, width=2880)
    travel = t_span - span
    steps = args.frames
    fig, ax, counter = build_figure()
    draw_key(fig, values)

    frames = []
    for i in range(steps):
        t0 = t_start + travel * (i / (steps - 1))
        compose(ax, dense_t, dense, times, values, smooth, ranges, t_start, t_span, t0, span)
        counter.set_text(f'FRAME {i+1:02d} / {steps}')
        frames.append(to_image(fig, FRAME_DPI))
        print(f'  frame {i+1:3d}/{steps}   {datetime.fromtimestamp(t0, timezone.utc):%d %b %H:%M}')

    # The still that goes in the README: the middle of the run, at print size.
    mid = t_start + travel * .5
    compose(ax, dense_t, dense, times, values, smooth, ranges, t_start, t_span, mid, span)
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
    print(f'{paired} paired minutes; {bins} valid five-minute bins; '
          f'mid-frame {datetime.fromtimestamp(mid, timezone.utc):%d %b %H:%M} UTC')


if __name__ == '__main__':
    main()
