# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///
"""One small regression check for the real cached data and missing-minute rules."""
import json
from datetime import date, timezone
import numpy as np
from aurora_data import DATA, read_gfz, read_swpc, utc
from aurora_waves import load_landscape, load_wind


def main():
    assert utc("2026-09-22T03:18:00").tzinfo == timezone.utc
    # A hand-checked raw GFZ day: catches the old wrong-column error.
    _, daily = read_gfz()
    assert daily[date(1932,1,1)] == 3.333
    _, years, ranges = load_landscape()
    represented = [d for rows in ranges for d,_ in rows]
    assert len(represented) == len(set(represented))
    assert all((date(y+1,1,1)-date(y,1,1)).days == sum(d.year==y for d in represented) for y in years)
    raw = json.loads((DATA/'swpc-solar-wind-plasma-1m.json').read_text())
    selected = read_swpc('swpc-solar-wind-plasma-1m.json', ('proton_speed','proton_density','proton_temperature'))
    inactive = [r for r in raw if not r['active'] and utc(r['time_tag']) in selected and r['proton_speed'] is not None]
    assert inactive and any(selected[utc(r['time_tag'])][0] != r['proton_speed'] for r in inactive)
    assert list(selected) == sorted(selected)
    t,v,n = load_wind()
    assert np.all(np.diff(t)==300)
    assert v.shape == (len(t),5) and n >= 3*np.isfinite(v[:,0]).sum()
    assert np.isnan(v).any(), 'Expected real telemetry gaps in this cached snapshot'
    assert np.all(np.isnan(v).sum(axis=1) % 5 == 0)
    ov = json.loads((DATA/'swpc-ovation-aurora-latest.json').read_text())
    assert ov['Data Format'] == '[Longitude, Latitude, Aurora]'
    assert all(0 <= c[2] <=100 for c in ov['coordinates'])
    print('PASS: GFZ column/date handling, UTC sorting, active selection, gaps, OVATION schema')


if __name__ == '__main__':
    main()
