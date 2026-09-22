# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///
"""The plain first-look chart, with the same corrected parsing as the artwork.

    uv run plot.py
    uv run plot.py --no-show
"""
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import matplotlib
from aurora_data import read_swpc


def series(rows):
    """Insert breaks rather than drawing a line through missing minutes."""
    xs, ys = [], []
    previous = None
    for t, (v,) in rows.items():
        if previous and t - previous > timedelta(minutes=1):
            xs.append(previous + timedelta(seconds=30)); ys.append(float("nan"))
        xs.append(t); ys.append(v); previous = t
    return xs, ys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-show", action="store_true")
    no_show = parser.parse_args().no_show
    if no_show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    kp = read_swpc("swpc-planetary-k-index-1m.json", ("estimated_kp",))
    # Include Bt in validation to reject impossible |Bz| > Bt.
    mag = read_swpc("swpc-solar-wind-mag-1m.json", ("bt", "bz_gsm"))
    bz = {t: (v[1],) for t,v in mag.items()}
    fig, axes = plt.subplots(2,1,figsize=(11,6),sharex=True)
    for ax, rows, name, color in zip(axes, [kp,bz], ["estimated Kp (unitless)","Bz GSM (nT)"], ["#6457aa","#1b9a94"]):
        ax.plot(*series(rows),color=color,lw=1)
        ax.set_ylabel(name); ax.grid(alpha=.2)
    axes[1].axhline(0,color="gray",lw=.5)
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%H:%M",tz=timezone.utc))
    axes[1].set_xlabel("Time (UTC) · active spacecraft · gaps left empty")
    axes[0].set_title("Aurora first look · cached NOAA observations")
    fig.tight_layout()
    out = Path(__file__).resolve().parent / "out"
    out.mkdir(exist_ok=True)
    fig.savefig(out/"aurora-first-look.png",dpi=150)
    print("saved out/aurora-first-look.png")
    if not no_show: plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
