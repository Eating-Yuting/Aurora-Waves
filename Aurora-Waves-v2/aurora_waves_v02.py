# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Aurora Waves v02 — Emerald Veil. Same real data, a different visual treatment.

uv run aurora_waves_v02.py             # save and show
uv run aurora_waves_v02.py --no-show   # save only

Shared data handling lives in aurora_data.py and aurora_waves.py.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgb, LinearSegmentedColormap
from aurora_waves import load_landscape, load_wind, scaled

ROOT = Path(__file__).resolve().parent
BG, TEXT, MUTED = '#030b10', '#e6f0de', '#89a89e'
GREEN, JADE, PINK = '#98ff75', '#1bebad', '#d998da'
SMOOTH_BINS = 9  # 45 minutes; only inside contiguous valid stretches
OUTNAME = 'aurora-waves-v02-emerald-veil.png'
POINT_MAP = LinearSegmentedColormap.from_list('temperature', [GREEN, '#c1e7b3', PINK])


def runs(mask):
    """Contiguous valid slices. A missing bin always separates two ribbons."""
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def curtain_samples(times, values, width=2200):
    """Smooth within valid runs, interpolate only inside their time support.

    Output columns outside observations stay NaN, including missing intervals.
    The data count does not increase when the image gets more pixels.
    """
    dense_t = np.linspace(times[0], times[-1], width)
    dense = np.full((width, 5), np.nan)
    smoothed = np.full_like(values, np.nan)
    for a, b in runs(np.isfinite(values).all(axis=1)):
        n = min(SMOOTH_BINS, b-a)
        n -= (n + 1) % 2  # odd, including a single observation
        n = max(1, n)
        v = np.column_stack([np.convolve(np.pad(values[a:b,j], n//2, mode='edge'), np.ones(n)/n, mode='valid') for j in range(5)])
        smoothed[a:b] = v
        m = (dense_t >= times[a]) & (dense_t <= times[b-1])
        if b-a == 1:
            m = np.abs(dense_t-times[a]) <= min(150, (dense_t[1]-dense_t[0])/2)
        for j in range(5):
            dense[m,j] = np.interp(dense_t[m], times[a:b], v[:,j])
    return dense_t, dense, smoothed


def veil_geometry(v):
    speed, density, temp, bt, bz = v.T
    # Bz is a POSITION encoding here, freeing the palette to stay auroral green.
    edge = .60 + .15 * np.clip(bz/5, -1, 1)
    reach = .095 + .21 * scaled(speed, 300, 380)
    brightness = .18 + .82 * scaled(bt, 0, 6)
    return edge, reach, brightness


def draw_veil(ax, times, values):
    t, v, smooth = curtain_samples(times, values)
    good = np.isfinite(v).all(axis=1)
    # Fill NaN for array arithmetic only; missing columns are masked afterward.
    vv = np.nan_to_num(v)
    edge, reach, brightness = veil_geometry(vv)
    xx = np.linspace(.055,.945,len(t))
    yy = np.linspace(.36,.89,1100)[:,None]
    height = yy-edge[None,:]
    u = height / reach[None,:]
    # Fine filaments are a declared drawing texture, not additional data.
    phase = np.linspace(0,1,len(t))[None,:]
    filaments = .68 + .22*np.sin(phase*1350 + u*1.2)**2 + .10*np.sin(phase*2390-u*.9)**2
    core = np.exp(-((height-.009)/.019)**2)
    body = np.exp(-np.maximum(u,0)*3.4) * (1/(1+np.exp(np.clip(-height*450,-50,50))))
    cap = 1/(1+np.exp(np.clip((u-.97)*25,-50,50)))
    green_light = (core*.45 + body*.76)*filaments*cap*brightness[None,:]
    # Faint red upper glow and a thin purple lower hem reference colour structure,
    # but are NOT a spectroscopic model or inferred local atmospheric altitude.
    red_light = .075*np.exp(-((u-.86)/.28)**2)*brightness[None,:]
    purple_light = .25*np.exp(-((height+.013)/.007)**2)*brightness[None,:]
    green_light[:,~good] = 0; red_light[:,~good] = 0; purple_light[:,~good] = 0
    rgb = (green_light[...,None]*np.array([.30,1,.39]) +
           red_light[...,None]*np.array([1,.15,.33]) +
           purple_light[...,None]*np.array([.68,.28,1]))
    alpha = np.clip(np.max(rgb,axis=2),0,1)
    colour = np.clip(rgb/np.maximum(alpha[...,None],1e-6),0,1)
    rgba = np.dstack([colour,alpha])
    ax.imshow(rgba,extent=[.055,.945,.36,.89],origin='lower',aspect='auto',zorder=3,interpolation='bilinear')
    y = np.where(good, edge+.003, np.nan)
    for lw,alpha in [(10,.025),(4,.08),(.6,.5)]:
        ax.plot(xx,y,color=GREEN,lw=lw,alpha=alpha,zorder=4)
    # Each light point is one valid five-minute observation; no random stars.
    orig_x = .055+.89*(times-times[0])/(times[-1]-times[0])
    smooth_edge,_,_ = veil_geometry(smooth)
    valid = np.isfinite(values).all(axis=1)
    area = 1.5 + 4*np.clip(values[:,1],0,5)
    pc = POINT_MAP(scaled(values[:,2],20000,100000))
    point_y = smooth_edge-.043
    ax.scatter(orig_x[valid],point_y[valid],s=area[valid]*5,c=pc[valid],alpha=.045,lw=0,zorder=8)
    ax.scatter(orig_x[valid],point_y[valid],s=area[valid],c=pc[valid],alpha=.8,lw=0,zorder=9)
    # Discreet labels separate the solar-wind clock from the historical ranges.
    ax.text(.055,.866,'01   /   A DAY IN THE SOLAR WIND',color=MUTED,fontsize=7.5)
    ax.text(.945,.866,'SOLAR1 ACTIVE RECORDS  ·  UTC',ha='right',color=MUTED,fontsize=7.5)
    for f in [0,.25,.5,.75,1]:
        tx=.055+.89*f
        dt=datetime.fromtimestamp(times[0]+f*(times[-1]-times[0]),timezone.utc)
        ax.plot([tx,tx],[.427,.433],color=MUTED,alpha=.5,lw=.5,zorder=50)
        ax.text(tx,.413,dt.strftime('%d %b  %H:%M'),color=MUTED,fontsize=6.5,ha='center',zorder=50)
    return smooth


def draw_memory(ax, ranges):
    x=np.linspace(.055,.945,1800)
    cmap=LinearSegmentedColormap.from_list('night_ridges',['#134336','#0c3433','#0a232c','#07151e'])
    peaks=0
    for i, rows in enumerate(ranges):
        dates, vals=zip(*rows); vals=np.asarray(vals)
        avg=np.convolve(np.pad(vals,22,mode='edge'),np.ones(45)/45,mode='valid')
        source_x=np.linspace(.055,.945,len(vals))
        base=.292-i*.019
        y=base+.16*np.interp(x,source_x,avg)/9
        z=20+i*2
        ax.fill_between(x,.115,y,color=cmap(i/9),zorder=z,lw=0)
        lines=[np.column_stack([x,np.where(y-j*.0022>.115,y-j*.0022,np.nan)]) for j in range(14)]
        ax.add_collection(LineCollection(lines,colors=JADE,linewidths=.25,alpha=.13,zorder=z+1))
        ax.plot(x,y,color=GREEN if i<3 else JADE,lw=.45,alpha=.46,zorder=z+1)
        extreme=np.flatnonzero(vals==9); peaks+=len(extreme)
        ax.scatter(source_x[extreme],base+.16*avg[extreme]/9,s=5,color='#caff93',alpha=.85,zorder=z+1,lw=0)
        ax.text(.045,base+.052,f'{dates[0].year}\n{dates[-1].year}',ha='right',va='center',fontsize=5.5,color=MUTED,linespacing=1.1,zorder=60)
    ax.text(.055,.387,'02   /   94 YEARS OF GEOMAGNETIC MEMORY',fontsize=7.5,color=MUTED,zorder=70)
    ax.text(.945,.387,f'{peaks} Kp-9 DAYS  ·  45-DAY SMOOTHING',ha='right',fontsize=7.5,color=MUTED,zorder=70)
    ax.text(.055,.112,'EACH RIDGE HAS ITS OWN YEARS: START → END',fontsize=6,color=MUTED,zorder=70)
    ax.text(.945,.112,'EQUAL Kp HEIGHT SCALE  /  LANDSCAPE COLOURS ARE DECORATIVE',ha='right',fontsize=6,color=MUTED,zorder=70)


def draw_key(fig, values):
    specs=[('01 / Kp','RIDGE HEIGHT','0–9 · unitless',GREEN),
           ('02 / SPEED','CURTAIN REACH','300–380 km/s',GREEN),
           ('03 / Bz','LOWER-EDGE POSITION','−5 to +5 nT · lower → higher',JADE),
           ('04 / Bt','GLOW INTENSITY','0–6 nT · faint → bright',JADE),
           ('05 / DENSITY','POINT AREA','0–5 protons/cm³', '#c1e7b3'),
           ('06 / TEMPERATURE','POINT COLOUR','20–100 kK · green → mauve',PINK)]
    for i,(title,enc,scale,col) in enumerate(specs):
        left=.055+i*.15
        fig.text(left,.079,title,color=col,fontsize=8.5)
        fig.text(left,.061,enc,color=TEXT,fontsize=6.5)
        fig.text(left,.044,scale,color=MUTED,fontsize=6)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-show',action='store_true')
    no_show=parser.parse_args().no_show
    if no_show: matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    count,years,ranges=load_landscape()
    times,values,paired=load_wind()
    fig=plt.figure(figsize=(18,12),facecolor=BG)
    ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    # Low-contrast atmospheric wash is purely background composition.
    yy,xx=np.mgrid[0:1:900j,0:1:1300j]
    glow=np.exp(-((yy-.46)/.20)**2)*np.exp(-((xx-.50)/.6)**2)
    wash=np.empty((*yy.shape,4));wash[:,:,:3]=to_rgb('#0e463e');wash[:,:,3]=glow*.26
    ax.imshow(wash,origin='lower',extent=[0,1,0,1],aspect='auto',zorder=0)
    fig.text(.055,.949,'Aurora Waves',fontfamily='DejaVu Serif',fontsize=35,color=TEXT)
    fig.text(.057,.920,'EMERALD VEIL   /   SIX MEASUREMENTS, ONE NIGHT LANDSCAPE',fontsize=8,color=MUTED)
    fig.text(.945,.959,'V.02',fontsize=14,color=GREEN,ha='right')
    fig.text(.945,.936,'21–22 SEP 2026  /  NOAA SWPC',fontsize=7.5,color=MUTED,ha='right')
    fig.text(.945,.919,'1932–2025  /  GFZ NIEMEGK',fontsize=7.5,color=MUTED,ha='right')
    draw_veil(ax,times,values)
    draw_memory(ax,ranges)
    ax.plot([.055,.945],[.097,.097],color=MUTED,lw=.45,alpha=.3,zorder=80)
    draw_key(fig,values)
    fig.text(.055,.019,'NOAA SWPC  ·  GFZ CC BY 4.0  /  cached observations  /  all times UTC',fontsize=6,color=MUTED)
    fig.text(.945,.019,'DATA ART  ·  aurora-inspired colour, not a photographic or visibility reconstruction',fontsize=6,color=MUTED,ha='right')
    out=ROOT/'out';out.mkdir(exist_ok=True)
    fig.savefig(out/OUTNAME,dpi=220,facecolor=BG)
    print(f'saved out/{OUTNAME}')
    print(f'{len(years)} complete years; {paired} paired minutes; {np.isfinite(values).all(axis=1).sum()} valid bins')
    if not no_show: plt.show()
    plt.close(fig)


if __name__=='__main__': main()
