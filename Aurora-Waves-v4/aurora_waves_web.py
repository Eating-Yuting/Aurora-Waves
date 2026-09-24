# /// script
# requires-python = ">=3.10"
# dependencies = ["plotly", "numpy", "matplotlib", "pillow"]
# ///
"""Aurora Waves, read again — the same week, with ONE slider for time.

    uv run aurora_waves_web.py          # writes site/index.html — open it in a browser
    uv run aurora_waves_web.py --window 12   # a wider window, calmer motion

No window opens and no picture is drawn. Python writes one HTML file and the
browser draws it, exactly as `week03/currents_web.py` does for the tidal streams.
The page is the reading instrument for the picture, not a second picture: the
poster and the GIF are the artwork, and this is where you can stop on a moment and
read the six numbers that produced it.

Why the layout is what it is
----------------------------
The picture has one message — a week of measured solar wind, seen through a window
that moves. The page keeps that message and adds one control. Six sliders would have
let each measurement be scrubbed on its own clock, which is exactly the thing that
makes a picture say six things at once; one slider for time keeps every measurement
on the same moment, which is the only way the drawing was ever made.

What the drawing reuses, and what it does not
---------------------------------------------
The numbers, the smoothing, the geometry and the colours are imported from
`aurora_waves_v04.py` and `aurora_waves_v02.py` rather than re-implemented, so the
page cannot drift away from the poster. Two things are deliberately different:

  * The glow is five stacked bands instead of V04's raster. A browser cannot hold a
    2700-pixel glow for every moment at a usable file size, and the fine filament
    texture belongs to the still picture's resolution. The three encodings of the
    sky survive intact: Bz sets the lower edge, speed the reach, Bt how far the
    light climbs. A filled band cannot carry an opacity that varies along time, so
    a faint aurora is drawn SHORT as well as faint — the honest reading of
    "brightness scales the amplitude" once the alpha is fixed.

  * The mountains are absent. They have no clock — 94 years of Kp on their own
    timeline — so they cannot move with a slider. Row 01 shows this week's own Kp
    instead, one value per three-hour interval, which is the same index the ridges
    are built from and is the one part of the picture that does have a clock.
"""

import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from aurora_data import DATA as DATA_DIR
from aurora_waves import load_landscape, scaled
from aurora_waves_v02 import GREEN, JADE, PINK, POINT_MAP, curtain_samples
from aurora_waves_v04 import (
    BT_HI, BT_LO, BZ_FULL, DENSITY_FULL, ROOT, SPEED_HI, SPEED_LO, TEMP_HI,
    TEMP_LO, load_omni_week, storm_days, veil_geometry_week,
)

BG, TEXT, MUTED = '#030b10', '#e6f0de', '#89a89e'
PALE = '#c1e7b3'
RULE = 'rgba(137,168,158,.20)'
STORM = '#caff93'
HOUR = 3600
WINDOW_HOURS = 8.0        # the width of the window, as in V03 and V04
STEP_HOURS = 1.0          # one hour per frame, so the page and the GIF keep pace
PLAY_MS = 110             # the GIF's own frame duration
POINT_SCALE = 1.35        # light-point diameter, points -> screen pixels
SITE = ROOT / 'site'
PAGE = SITE / 'index.html'
KP_FILE = 'gfz-kp-ap-since-1932.txt'

# The canvas and its margins, named rather than written into the layout call, because
# the time ruler under the slider has to place its ticks in the same coordinates the
# rail travels along — and that arithmetic needs the width of the drawing area, which
# is the width of the page minus two margins, not the width of the page.
WIDTH, HEIGHT = 1240, 1180
MARGIN = dict(l=272, r=36, t=152, b=124)
PLOT_W = WIDTH - MARGIN['l'] - MARGIN['r']
PLOT_H = HEIGHT - MARGIN['t'] - MARGIN['b']
PLOT_BOTTOM = MARGIN['t'] + PLOT_H    # the pixel row that paper y = 0 sits on

# The slider, and where the rail it draws ends up. Plotly puts the rail seven and a
# half pixels below the slider's own origin, five pixels tall, and insets it eight
# pixels from each end of the drawing area. Those three offsets are fixed, so they are
# written down here and the ruler is computed from them rather than eyeballed.
SLIDER_Y = -.056
SLIDER_PAD = 6
RAIL_OFFSET, RAIL_HEIGHT, RAIL_PAD = 7.5, 5, 8
RAIL_BOTTOM = (PLOT_BOTTOM + (-SLIDER_Y) * PLOT_H + SLIDER_PAD + RAIL_OFFSET + RAIL_HEIGHT)


def below_rail(pixels):
    """Paper y, `pixels` below the bottom of the slider's rail."""
    return -(RAIL_BOTTOM + pixels - PLOT_BOTTOM) / PLOT_H


def rail_x(step, count):
    """Paper x of the slider handle once it has reached `step` of `count`."""
    span = PLOT_W - 2 * RAIL_PAD
    return (RAIL_PAD + span * step / (count - 1)) / PLOT_W

# Rows, top to bottom: the whole week, the curtain, then the six measurements.
ROWS = 8
CURTAIN_ROW = 2
FIRST_KEY_ROW = 3
ROW_HEIGHTS = [.095, .275, .087, .087, .087, .087, .087, .087]
VERTICAL_SPACING = .015
# The sky band of V04's drawing runs .36 to .89 of its canvas. The row keeps those
# proportions and adds headroom at each end: below, for the light points that sit 43
# thousandths under the edge; above, for a storm glow that climbs past the band the
# way V04's does, and for the caption that has to sit clear of both the glow and the
# day labels of the row above.
SKY_RANGE = [.34, 1.02]
# Row 1 owns the whole week and the window marker, so its empty space has to hold two
# lines of text without either landing on the silhouette.
WEEK_RANGE = [0, 1.9]

# What each measurement drives in the picture. This is the page's real content:
# the drawing says the same thing, but only here is it written down.
KEY = [
    ('01', 'Kp', 'unitless', 'ridge height', GREEN,
     'this week, 3-hourly \u00b7 the index behind the 94-year ridges'),
    ('02', 'speed', 'km/s', 'curtain reach', GREEN,
     f'how high the light climbs \u00b7 ruler {SPEED_LO}\u2013{SPEED_HI}'),
    ('03', 'Bz', 'nT', 'lower edge', JADE,
     f'GSM north\u2013south \u00b7 more negative, lower \u00b7 clips at \u00b1{BZ_FULL} nT'),
    ('04', 'Bt', 'nT', 'glow intensity', JADE,
     f'the total field \u00b7 how bright the glow gets \u00b7 clips at {BT_HI} nT'),
    ('05', 'density', 'protons/cm\u00b3', 'point area', PALE,
     f'the area of each light point \u00b7 clips at {DENSITY_FULL}'),
    ('06', 'temperature', 'K', 'point colour', PINK,
     f'green \u2192 pale \u2192 mauve \u00b7 {TEMP_LO // 1000}\u2013{TEMP_HI // 1000} kK, on a log axis'),
]


# ---------------------------------------------------------------------------
# This week's own Kp, at the resolution the file actually carries.
# ---------------------------------------------------------------------------


def kp_three_hourly(start, end):
    """One Kp value per three-hour interval, for the week the slider covers.

    `aurora_data.read_gfz()` keeps only each day's maximum, because that is what the
    ridges are built from. The slider needs the inside of a day as well, so this reads
    the same file and the same column, and keeps the same two rules: Kp is column 8,
    and a day only counts when all eight intervals are present. Nothing is invented
    for a day that is short.
    """
    per_day = defaultdict(list)
    for line in (DATA_DIR / KP_FILE).read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        record = line.split()
        per_day[date(int(record[0]), int(record[1]), int(record[2]))].append(float(record[7]))
    rows = []
    for day in sorted(per_day):
        values = per_day[day]
        if len(values) != 8:
            continue
        for interval, kp in enumerate(values):
            when = datetime(day.year, day.month, day.day, interval * 3, tzinfo=timezone.utc)
            # One interval of slack at the start: the OMNI week begins at 00:02:30, and
            # the 00:00 Kp interval still covers it.
            if start - timedelta(hours=3) <= when <= end and 0 <= kp <= 9:
                rows.append((when, kp))
    return rows


# ---------------------------------------------------------------------------
# Small helpers.
# ---------------------------------------------------------------------------


def blank(values):
    """NaN becomes null: Plotly breaks the line and closes the fill, as the picture does."""
    return [None if not np.isfinite(v) else round(float(v), 4) for v in values]


def hexes(colours):
    """Matplotlib colours into the hex strings a browser wants. Same map, not a copy."""
    return ['#%02x%02x%02x' % tuple(int(round(c * 255)) for c in row[:3]) for row in colours]


def domain_ref(row):
    """The `x3 domain` / `y3 domain` form Plotly wants for a caption on one panel.

    `add_annotation(..., row=3)` looks like the obvious way to do this, and it is the
    wrong one: it resolves the reference to the row's AXIS, so x=-.007 means seven
    thousandths of a second before the epoch rather than just left of the panel, and
    the caption lands in 1970 where nobody will see it.
    """
    suffix = '' if row == 1 else str(row)
    return f'x{suffix} domain', f'y{suffix} domain'


def paper_rows():
    """Each row's top and bottom in figure coordinates, so rules can be placed
    without guessing. Plotly scales the heights to fit the figure, so this mirrors it."""
    free = 1 - (ROWS - 1) * VERTICAL_SPACING
    scale = free / sum(ROW_HEIGHTS)
    out, top = [], 1.0
    for height in ROW_HEIGHTS:
        bottom = top - height * scale
        out.append((top, bottom))
        top = bottom - VERTICAL_SPACING
    return out


# ---------------------------------------------------------------------------
# The page.
# ---------------------------------------------------------------------------


def build(window_hours=WINDOW_HOURS, step_hours=STEP_HOURS):
    times, values, paired = load_omni_week()
    _, _, ranges = load_landscape()
    peaks = storm_days(ranges, times[0], times[-1])

    good = np.isfinite(values).all(axis=1)          # a bin with both instruments
    speed, density, temp, bt, bz = values.T
    stamp = [datetime.fromtimestamp(t, timezone.utc) for t in times]

    # The curtain's geometry comes from the smoothed bins, exactly as in V04, so the
    # edge on the page runs through the same points the poster's edge runs through.
    _, _, smoothed = curtain_samples(times, values, width=len(times))
    sky = np.isfinite(smoothed).all(axis=1)
    edge, reach, brightness = veil_geometry_week(np.nan_to_num(smoothed))
    for field in (edge, reach, brightness):
        field[~sky] = np.nan

    # V04 lets Bt set the amplitude. With the alpha fixed at 1, that becomes height:
    # a faint aurora is drawn short, a bright one climbs the full reach.
    amplitude = .45 + .55 * np.clip((brightness - .18) / .82, 0, 1)
    bands = [edge + reach * amplitude * (k / 5) for k in range(1, 6)]

    figure = make_subplots(
        rows=ROWS, cols=1,
        row_heights=ROW_HEIGHTS,
        vertical_spacing=VERTICAL_SPACING,
    )

    # --- Row 1 · the whole week, with the window marked on it -----------------
    strip_reach = veil_geometry_week(np.nan_to_num(values))[1]
    lift = np.where(good, np.clip((strip_reach - .095) / .21, 0, 1) ** .5, np.nan)
    figure.add_trace(go.Scatter(
        x=stamp, y=blank(lift), fill='tozeroy',
        fillcolor='rgba(152,255,117,.20)', line=dict(color=GREEN, width=1),
        name='curtain reach, whole week', hoverinfo='skip', showlegend=False,
    ), row=1, col=1)

    if peaks:
        ticks_x, ticks_y = [], []
        for when, _ in peaks:
            ticks_x += [when, when, None]
            ticks_y += [0, .085, None]
        figure.add_trace(go.Scatter(
            x=ticks_x, y=ticks_y, mode='lines', line=dict(color=STORM, width=1),
            hoverinfo='skip', showlegend=False,
        ), row=1, col=1)

    # Two traces the frames rewrite: the window on the strip, and its dates beside it.
    marker_rect = go.Scatter(
        x=[stamp[0], stamp[0], stamp[0], stamp[0], stamp[0]], y=[0, 0, 1, 1, 0],
        fill='toself', fillcolor='rgba(152,255,117,.16)',
        line=dict(color=GREEN, width=1), mode='lines',
        hoverinfo='skip', showlegend=False,
    )
    figure.add_trace(marker_rect, row=1, col=1)
    rect_index = len(figure.data) - 1
    marker_text = go.Scatter(
        x=[stamp[0]], y=[1.30], mode='text', text=[''],
        textfont=dict(color=GREEN, size=11), hoverinfo='skip', showlegend=False,
    )
    figure.add_trace(marker_text, row=1, col=1)
    text_index = len(figure.data) - 1

    # --- Row 2 · the curtain --------------------------------------------------
    # The purple hem first: a filled band always closes onto the trace before it,
    # so the order the traces are added in IS the order the layers are drawn in.
    figure.add_trace(go.Scatter(
        x=stamp, y=blank(edge - .014), line=dict(width=0), showlegend=False,
        hoverinfo='skip',
    ), row=CURTAIN_ROW, col=1)
    figure.add_trace(go.Scatter(
        x=stamp, y=blank(edge - .004), fill='tonexty', fillcolor='rgba(217,152,218,.30)',
        line=dict(width=0), hoverinfo='skip', showlegend=False,
    ), row=CURTAIN_ROW, col=1)
    figure.add_trace(go.Scatter(
        x=stamp, y=blank(edge), line=dict(color=GREEN, width=1.6),
        customdata=np.array([bz, speed, bt]).T,
        hovertemplate=('%{x|%d %b %H:%M} UTC<br><b>lower edge</b> — Bz %{customdata[0]:.1f} nT'
                       '<br>reach %{customdata[1]:.0f} km/s · Bt %{customdata[2]:.1f} nT'
                       '<extra></extra>'),
        showlegend=False,
    ), row=CURTAIN_ROW, col=1)
    alphas = (.34, .24, .16, .10, .05)
    for level, alpha in zip(bands, alphas):
        figure.add_trace(go.Scatter(
            x=stamp, y=blank(level), fill='tonexty',
            fillcolor=f'rgba(152,255,117,{alpha})', line=dict(width=0),
            hoverinfo='skip', showlegend=False,
        ), row=CURTAIN_ROW, col=1)

    # One light point per valid five-minute bin — never a random star. Area is density,
    # colour is temperature; both are the raw bin values, not the smoothed ones.
    solid = np.flatnonzero(good)
    point_y = edge - .043
    area = np.sqrt(1.5 + .9 * np.clip(density, 0, DENSITY_FULL)) * 1.333 * POINT_SCALE
    point_colour = hexes(POINT_MAP(scaled(temp, TEMP_LO, TEMP_HI)))
    sample = np.array([density, temp / 1000]).T
    for size, opacity, hover in ((area * 2.2, .06, 'skip'), (area, .85, 'text')):
        figure.add_trace(go.Scatter(
            x=[stamp[i] for i in solid], y=point_y[solid], mode='markers',
            marker=dict(size=size[solid], color=[point_colour[i] for i in solid],
                        line=dict(width=0)),
            opacity=opacity,
            customdata=sample[solid],
            hovertemplate=('each point is one five-minute bin<br>density %{customdata[0]:.1f} '
                           'protons/cm\u00b3<br>temperature %{customdata[1]:,.0f} kK<extra></extra>'
                           if hover == 'text' else None),
            showlegend=False,
        ), row=CURTAIN_ROW, col=1)

    # --- Rows 3..8 · the six measurements ------------------------------------
    kp_rows = kp_three_hourly(stamp[0], stamp[-1])
    # The y ranges are the picture's own rulers, not the data's own extent. A reader
    # who checks a row against the poster is looking at the same scale, and the two
    # numbers that run past their ruler — Bz at −46 nT against a ±45 clip, density at
    # 41 against a clip of 30 — run past it in the picture too. Hovering gives the
    # exact value either way.
    #
    # Temperature is the exception: it climbs from 13 kK in the quiet stretches to
    # 1,860 kK in the storm, so on a linear axis half the week lies in the bottom tenth
    # of the row and reads as a flat line at the floor. The row keeps the picture's
    # 20–500 kK ruler and spaces it logarithmically instead. The point COLOUR in the
    # picture stays linear in temperature, exactly as V04 draws it.
    specs = [
        ([when for when, _ in kp_rows], [kp for _, kp in kp_rows], [0, 9], False),
        (stamp, blank(speed), [SPEED_LO, SPEED_HI], False),
        (stamp, blank(bz), [-BZ_FULL, BZ_FULL], False),
        (stamp, blank(bt), [BT_LO, BT_HI], False),
        (stamp, blank(density), [0, DENSITY_FULL], False),
        (stamp, blank(temp / 1000),
         [np.log10(TEMP_LO / 1000), np.log10(TEMP_HI / 1000)], True),
    ]
    for offset, ((number, name, unit, drives, colour, note), spec) in enumerate(zip(KEY, specs)):
        x, y, limits, logarithmic = spec
        row = FIRST_KEY_ROW + offset
        figure.add_trace(go.Scatter(
            x=x, y=y, mode='lines',
            line=dict(color=colour, width=1.6, shape='hv' if number == '01' else 'linear'),
            hovertemplate=f'%{{x|%d %b %H:%M}} UTC<br>{name} %{{y:,.1f}} {unit}<extra></extra>',
            showlegend=False,
        ), row=row, col=1)
        figure.update_yaxes(range=limits, type='log' if logarithmic else 'linear',
                            row=row, col=1)

    # --- The one control ------------------------------------------------------
    start = times[0]
    end = times[-1]
    span = window_hours * HOUR
    step = step_hours * HOUR
    count = int(round((end - start - span) / step)) + 1
    day_steps = max(1, int(round(24 / step_hours)))
    # The window's own label is centred on the window, so it is pulled back from the
    # ends of the record — otherwise its first half would fall off the left edge.
    frames, steps = [], []
    for i in range(count):
        opened = start + i * step
        closed = opened + span
        opened_dt = datetime.fromtimestamp(opened, timezone.utc)
        closed_dt = datetime.fromtimestamp(closed, timezone.utc)
        middle = min(max(opened_dt + (closed_dt - opened_dt) / 2,
                         stamp[0] + timedelta(hours=15)),
                     stamp[-1] - timedelta(hours=15))
        frame_layout = {('xaxis' if row == CURTAIN_ROW else f'xaxis{row}'): dict(range=[opened_dt, closed_dt])
                        for row in range(CURTAIN_ROW, ROWS + 1)}
        frames.append(go.Frame(
            name=str(i),
            data=[
                go.Scatter(x=[opened_dt, closed_dt, closed_dt, opened_dt, opened_dt],
                           y=[0, 0, 1, 1, 0]),
                go.Scatter(x=[middle], y=[1.30],
                           text=[f'{opened_dt:%d %b %H:%M}  →  {closed_dt:%H:%M} UTC']),
            ],
            traces=[rect_index, text_index],
            layout=go.Layout(**frame_layout),
        ))
        # The rail carries no labels of its own, and the ruler under it is drawn
        # further down. Plotly thins the slider's label row to one label per forty
        # pixels or so — at 161 steps that is every seventh one — and a label written
        # on a day boundary simply does not land on one of those, so it is dropped in
        # silence. Seven day labels went in and one came out. The ruler is drawn by
        # hand instead, at the coordinates the handle itself travels along.
        steps.append(dict(
            method='animate',
            label='',
            args=[[str(i)], dict(mode='immediate', frame=dict(duration=0, redraw=True),
                                 transition=dict(duration=0))],
        ))
    figure.frames = frames

    # --- Frame, axes, captions -----------------------------------------------
    rows = paper_rows()
    figure.update_layout(
        template='none',
        font=dict(family='Helvetica Neue, Helvetica, Arial, sans-serif', size=12, color=TEXT),
        paper_bgcolor=BG, plot_bgcolor=BG,
        width=WIDTH, height=HEIGHT,
        margin=MARGIN,
        bargap=0,
        hovermode='closest',
        hoverlabel=dict(bgcolor='#0a1a20', bordercolor=RULE, font=dict(color=TEXT, size=11)),
        dragmode=False,
        title=dict(
            text=(f'<b>Aurora Waves</b>   ·   7\u201314 October 2024, read again'
                  f'<br><span style="font-size:13px;color:{MUTED}">'
                  f'the six measurements behind the picture \u00b7 one slider for time '
                  f'\u00b7 drag it, or press play</span>'),
            x=.006, xanchor='left', y=.985, yanchor='top',
            font=dict(size=23, color=TEXT, family='Georgia, DejaVu Serif, serif'),
        ),
        annotations=[],
        sliders=[dict(
            active=0, x=0, y=SLIDER_Y, len=1, pad=dict(t=SLIDER_PAD, b=0),
            bgcolor='rgba(137,168,158,.10)', bordercolor=RULE,
            tickcolor='rgba(0,0,0,0)', font=dict(color=MUTED, size=10), ticklen=0,
            currentvalue=dict(visible=False),
            steps=steps,
        )],
        updatemenus=[dict(
            type='buttons', direction='left', showactive=False,
            x=1, y=1.005, xanchor='right', yanchor='bottom', pad=dict(t=0, r=0),
            bgcolor='rgba(152,255,117,.12)', bordercolor=RULE,
            font=dict(color=GREEN, size=11),
            buttons=[
                dict(label='\u25b6  PLAY', method='animate', args=[None, dict(
                    mode='immediate', fromcurrent=True,
                    frame=dict(duration=PLAY_MS, redraw=True), transition=dict(duration=0))]),
                dict(label='\u275a\u275a  PAUSE', method='animate', args=[[None], dict(
                    mode='immediate', frame=dict(duration=0, redraw=False))]),
            ],
        )],
    )

    # The window is a fixed width, so the page opens on the first one rather than on
    # whatever Plotly would have auto-ranged. The frames then move it; it never zooms.
    first = datetime.fromtimestamp(start, timezone.utc)
    opening = [first, datetime.fromtimestamp(start + span, timezone.utc)]
    for row in range(1, ROWS + 1):
        if row == 1:
            figure.update_xaxes(row=row, col=1, range=[stamp[0], stamp[-1]],
                                dtick=86400000, tickformat='%d %b', ticks='outside',
                                tickcolor=RULE, ticklen=3, fixedrange=True)
            figure.update_yaxes(row=row, col=1, range=WEEK_RANGE, showticklabels=False,
                                showgrid=False, zeroline=False)
        else:
            figure.update_xaxes(row=row, col=1, range=opening, fixedrange=True, showgrid=True,
                                gridcolor='rgba(137,168,158,.13)', gridwidth=1,
                                ticks='outside', tickcolor=RULE, ticklen=3,
                                tickformat='%d %b %H:%M',
                                showticklabels=row in (CURTAIN_ROW, ROWS),
                                tickfont=dict(size=10, color=MUTED))
            if row == CURTAIN_ROW:
                figure.update_yaxes(row=row, col=1, range=SKY_RANGE, showticklabels=False,
                                    showgrid=False, zeroline=False)
            else:
                figure.update_yaxes(row=row, col=1, showgrid=True,
                                    gridcolor='rgba(137,168,158,.10)',
                                    zeroline=row == FIRST_KEY_ROW + 2,
                                    zerolinecolor=RULE, zerolinewidth=1,
                                    tickfont=dict(size=10, color=MUTED), ticks='')
    # The six measurements are labelled beside their rows, not on the y axes. A y-axis
    # title is drawn rotated, and a rotated sentence is taller than an 80-pixel row —
    # six of them stacked overlapped into a single unreadable column.
    for offset, (number, name, unit, drives, colour, note) in enumerate(KEY):
        xref, yref = domain_ref(FIRST_KEY_ROW + offset)
        figure.add_annotation(
            xref=xref, yref=yref, x=-.018, y=.5, xanchor='right', yanchor='middle',
            align='right', showarrow=False,
            text=(f'<b>{number} \u00b7 {name}</b> <span style="color:{MUTED}">({unit})</span>'
                  f'   \u2192   <span style="color:{colour}">{drives}</span>'
                  f'<br><span style="font-size:9.5px">{note}</span>'),
            font=dict(size=11, color=TEXT))

    for top, _ in rows[:CURTAIN_ROW + 1]:
        figure.add_shape(type='rect', xref='paper', yref='paper', x0=0, x1=1,
                         y0=top - .0005, y1=top, line=dict(width=0), fillcolor=RULE,
                         layer='below')

    # Captions sit inside their own panel, where there is room: the strip is a
    # silhouette along the floor of its row, and the curtain's glow stops well short
    # of the top of the sky. Placing them above the panels instead dropped them into
    # the gap between rows, where fifteen pixels cannot hold a line of text.
    for row, top, text in (
        (1, .99, (f'<b>THE WHOLE WEEK</b> \u00b7 curtain reach, one point per five-minute bin '
                  f'\u00b7 <span style="color:{STORM}">10 October, Kp 8.7</span>')),
        (CURTAIN_ROW, .94, (f'<b>THE CURTAIN</b> \u00b7 Bz sets the lower edge, speed its reach, '
                            f'Bt how far the light climbs \u00b7 each light point is one five-minute '
                            f'bin: area is density, colour is temperature')),
    ):
        xref, yref = domain_ref(row)
        figure.add_annotation(xref=xref, yref=yref, x=.004, y=top, xanchor='left',
                              yanchor='top', text=text, showarrow=False,
                              font=dict(size=11, color=MUTED))
    figure.add_annotation(x=0, y=-.038, xanchor='left', yanchor='top', showarrow=False,
                          xref='paper', yref='paper',
                          text=(f'<b>TIME</b>  \u00b7  one slider: it moves the window and it never '
                                f'zooms  \u00b7  drag it, or press play  \u00b7  every measurement '
                                f'moves to the same moment'),
                          font=dict(size=11, color=MUTED))

    # --- The time ruler under the slider ---------------------------------------
    # Drawn here rather than left to the slider, for the reason given where the steps
    # are built: Plotly drops a slider label that does not land on one of its own
    # thinned positions. These ticks are placed at the paper x the handle reaches for
    # the same step, so a tick and the handle that comes to rest on it agree pixel for
    # pixel. Three-hourly ticks, and a date on every day boundary.
    minor_stride = max(1, int(round(3 / step_hours)))
    for at in range(0, count, minor_stride):
        major = at % day_steps == 0
        figure.add_shape(
            type='line', xref='paper', yref='paper',
            x0=rail_x(at, count), x1=rail_x(at, count),
            y0=below_rail(13 if major else 8), y1=below_rail(0),
            line=dict(color='rgba(137,168,158,.55)' if major else RULE, width=1),
            layer='below',
        )
    for at in range(0, count, day_steps):
        figure.add_annotation(
            x=rail_x(at, count), y=below_rail(16), xref='paper', yref='paper',
            xanchor='center', yanchor='top', showarrow=False,
            text=f'{datetime.fromtimestamp(start + at * step, timezone.utc):%d %b}',
            font=dict(size=10.5, color=MUTED))

    return figure, {
        'bins': int(good.sum()), 'total': len(times), 'paired': paired,
        'frames': count, 'span_hours': (end - start) / HOUR,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--window', type=float, default=WINDOW_HOURS,
                        help='hours visible at once (default 8)')
    parser.add_argument('--step', type=float, default=STEP_HOURS,
                        help='hours the window advances per frame (default 1)')
    args = parser.parse_args()

    figure, stats = build(args.window, args.step)
    if not SITE.exists():
        SITE.mkdir(parents=True)
    figure.write_html(PAGE, include_plotlyjs='cdn', auto_open=False,
                      config={'displaylogo': False, 'responsive': True})
    print(f'wrote site/index.html — {PAGE.stat().st_size // 1024} KB, '
          f'{stats["frames"]} frames of {args.window:g} h, {stats["span_hours"]:.0f} h of record')
    print(f'{stats["paired"]} paired minutes; {stats["bins"]} of {stats["total"]} five-minute bins '
          f'usable ({100 * stats["bins"] / stats["total"]:.1f}%)')
    for number, name, unit, drives, _, _ in KEY:
        print(f'  {number}  {name:<12} {unit:<14} -> {drives}')


if __name__ == '__main__':
    main()
