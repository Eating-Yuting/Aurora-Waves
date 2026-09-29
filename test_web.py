# /// script
# requires-python = ">=3.10"
# dependencies = ["plotly", "numpy", "matplotlib", "pillow"]
# ///
"""Check that time frames move the curtain and measurements, not the overview."""
from aurora_waves_web import build, CURTAIN_ROW, ROWS


def main():
    figure, stats = build()
    expected = {f"xaxis{row}" for row in range(CURTAIN_ROW, ROWS + 1)}
    assert len(figure.frames) == stats["frames"] > 1
    for frame in figure.frames:
        axes = frame.layout.to_plotly_json()
        assert set(axes) == expected, "Only the curtain and measurement axes should move"
        ranges = [axes[key]["range"] for key in expected]
        assert all(value == ranges[0] for value in ranges), "Panels must share one clock"
    assert figure.frames[0].layout.xaxis2.range != figure.frames[-1].layout.xaxis2.range
    print("PASS: curtain and all six measurements share each frame; overview stays fixed")


if __name__ == "__main__":
    main()
