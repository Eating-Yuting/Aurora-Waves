# Aurora Waves

![Emerald Veil: a green auroral curtain with a purple lower hem above dark geomagnetic mountain ranges](out/aurora-waves-v02-emerald-veil.png)

This second version takes the mountain-and-curtain composition from the earlier Aurora Waves picture and gives it a quieter night palette. Pale green carries the brightest light, jade sits in the shadows, and a small purple border runs beneath the curtain. NOAA describes pale green as the most common auroral colour and notes that some auroras have a purple lower edge [1]. That informed the palette. The colours here are a design choice, not a reconstruction of what an observer would have seen.

I kept the same published data so the two versions can be compared without changing both the numbers and the design at once. The upper curtain uses NOAA solar-wind observations from 21–22 September 2026 UTC [2]. The lower mountain ranges use 94 complete years of GFZ Kp data, 1932–2025 [3]. The sky and mountains have separate timelines: horizontal position in the sky is recent UTC time, while each mountain runs from the beginning to the end of its labelled years.

## Three versions in this repository

![Aurora Waves V01: cyan and violet mountains beneath a curtain of solar-wind measurements](out/aurora-waves.png)

The picture above the line is V01, the one at the top of this page is V02, and V03 below sets the same day in motion. V01 and V02 each keep a read-only archive folder holding that version's scripts, README and picture as they stood; V03 is the current version and lives at the top level. The raw data is kept once, in `data/`, and every version reads it from there.

| Version | Where it lives | How it differs |
|---|---|---|
| **V01** | [`Aurora-Waves-v1/`](Aurora-Waves-v1/) | Jade-green ranges under a cyan-to-violet curtain. Bz is encoded as the curtain's thread hue, and the strands are hard vertical bars. |
| **V02** | [`Aurora-Waves-v2/`](Aurora-Waves-v2/) | Emerald Veil. Bz moves to the position of the curtain's lower edge, the bars become a fading light field softened only inside valid runs, and the palette follows the auroral colours NOAA describes. |
| **V03** | the top level of this repository | The same day as V02, drawn through a window eight hours wide that slides across it: the curtain flows, the mountains hold still. |

## V03 — the curtain in motion

![Emerald Veil in motion: the same day of solar wind drawn through a sliding eight-hour window](out/aurora-waves-v03-emerald-veil-in-motion.gif)

*The loop covers the whole day in 9.6 seconds, one frame every ten minutes of the record.*

![Emerald Veil in motion, poster frame: the window at midday](out/aurora-waves-v03-poster.png)

V03 draws the same measurements as V02, but through a window instead of the whole day at once. The smoothing is computed once over the full record, so what a given minute looks like never depends on which frame happens to be on screen. The fine filament texture is tied to the data's own clock, so it travels with the curtain rather than shimmering underneath it, and the bright segment under the time axis shows where the visible window sits inside the day. The mountain ranges do not move: the 94-year Kp record has no clock. The GIF carries one shared 128-colour palette built from frames sampled across the loop, so the colours cannot flicker between frames.

Why the animation stays inside one day rather than spanning a week: NOAA's free one-minute solar-wind feed serves only the last 24 hours, and NASA's OMNI archive — the standard week-long alternative — is missing between 18 and 36 per cent of its samples for these dates, with gaps long enough to cut the curtain into separate ribbons. A thinner week would have been less honest than the same day, complete.

## What the six measurements do

| Measurement | V02 encoding | Display scale |
|---|---|---|
| Historical Kp | Mountain height above its baseline | 0–9, unitless; same height scale on every range |
| Solar-wind speed | Vertical reach of the curtain | 300–380 km/s; longer for faster wind |
| Bz, GSM north–south component | Position of the curtain's lower edge | −5 to +5 nT; lower to higher |
| Bt, total magnetic field | Glow intensity | 0–6 nT; faint to bright |
| Proton density | Area of each light point | 0–5 protons/cm³; small to large |
| Proton temperature | Colour of each light point | 20,000–100,000 K; green to mauve |

The fixed display scales clip values outside their limits. Curtain reach, glow intensity and point area include small visible minimums. The Bz encoding is a graphic position on the page, not a geographic position or altitude. The purple hem and faint red upper glow are colour styling; their presence does not prove particular emissions were measured. Fine vertical filaments and repeated mountain contours are drawing textures, not additional data points.

## Data and transformations

The original replies remain unchanged in `data/`. The source addresses are in `fetch.py`.

| Saved file | Raw records | Meaning and use |
|---|---:|---|
| `gfz-kp-ap-since-1932.txt` | 276,784 | One three-hour Kp record; Kp is column eight. Daily maxima become historical ridges. |
| `swpc-solar-wind-mag-1m.json` | 3,496 | One spacecraft's one-minute magnetic measurement; Bt and Bz in nT. |
| `swpc-solar-wind-plasma-1m.json` | 3,374 | One spacecraft's one-minute speed, density and temperature measurement. |
| `swpc-planetary-k-index-1m.json` | 358 | Estimated Kp updates; retained for the plain first-look plot, not this image. |
| `swpc-ovation-aurora-latest.json` | 65,160 grid points | An exploratory aurora grid; retained but not used in this image. |

The NOAA files contain several spacecraft. The parser selects active records, interprets timestamps as UTC, sorts them and joins valid plasma and magnetic measurements at exactly matching minutes. This snapshot supplies 1,362 paired minutes from SOLAR1, forming 276 usable five-minute bins. Twelve bins have fewer than three matching samples and remain empty.

For the curtain's shape and brightness, V02 adds a centred nine-bin moving mean, equivalent to 45 minutes in a full valid run. Short runs use a smaller odd window; edges use endpoint padding. Interpolation adds drawing pixels only within each valid run. It never connects across a missing interval. Light-point area and colour retain the unsmoothed five-minute density and temperature values, while their positions follow the softened Bz edge. Each point represents one valid bin, not one physical particle.

Each historical ridge uses the same centred 45-day mean of daily maximum Kp as V01. Only complete calendar years enter the ranges; no extra leap days are invented. All 27 days reaching Kp 9 in those years are marked, although overlap can obscure some markers. Smoothing removes short fluctuations, overlap hides parts of the history, and the colour treatment does not predict aurora visibility. These are deliberate limits of a data artwork.

## Run V02

```sh
uv run aurora_waves_v02.py
```

This saves `out/aurora-waves-v02-emerald-veil.png` and opens a preview. To save without opening a window:

```sh
uv run aurora_waves_v02.py --no-show
```

Check the data and the new gap-handling logic:

```sh
uv run aurora_data.py
uv run test_data.py
uv run test_v02.py
```

`fetch.py` reuses the cached files. The plotting scripts work offline once their dependencies are installed. The original `aurora_waves.py` is retained because V02 reuses its data-loading functions; running it still creates the separate V01 filename `out/aurora-waves.png`. Everything works the same from inside the archive folders, except that they share the single `data/` kept at the top level.

## Run V03

```sh
uv run aurora_waves_v03.py
```

This writes `out/aurora-waves-v03-emerald-veil-in-motion.gif` and the poster frame `out/aurora-waves-v03-poster.png`; it does not open a window. The window width, the loop length and the frame rate are adjustable:

```sh
uv run aurora_waves_v03.py --window 12        # wider window, calmer motion
uv run aurora_waves_v03.py --frames 64        # shorter loop, smaller file
uv run aurora_waves_v03.py --duration 130     # slower playback
```

Rendering imports the drawing code from `aurora_waves_v02.py` instead of copying it, so the still and the moving version cannot drift apart. About a minute for 96 frames on a laptop; the GIF lands around 5 MB.

## References

[1] NOAA Space Weather Prediction Center. Aurora Tutorial [EB/OL]. [2026-09-22]. https://www.spaceweather.gov/content/aurora-tutorial

[2] NOAA Space Weather Prediction Center. Solar Wind [EB/OL]. [2026-09-22]. https://www.spaceweather.gov/products/solar-wind

[3] GFZ Helmholtz Centre for Geosciences. Data: Kp index [EB/OL]. [2026-09-22]. https://kp.gfz.de/en/data . Historical data: Geomagnetic Observatory Niemegk, CC BY 4.0, as credited in the raw file.

## 中文说明

这是单独保存的第二版：`aurora_waves_v02.py` 对应 `aurora-waves-v02-emerald-veil.png`，不会覆盖第一版。新版保留六项数据，把极光绿作为主色，辅以青绿、少量紫色下缘和红色辉光。Bz 改为控制光幕下缘的位置，让主体颜色更接近极光观感。光幕经过 45 分钟柔化，但缺测位置仍留空；光点面积和颜色保留五分钟数据的变化。这里呈现的是数据艺术，不是实拍照片或极光可见性预测。

仓库里两个版本各有一个归档文件夹：`Aurora-Waves-v1/` 是第一版（青绿山峦、青紫光幕），`Aurora-Waves-v2/` 是第二版（Emerald Veil）。原始数据只保存一份，放在顶层 `data/`，两个版本共用。

第三版 `aurora_waves_v03.py` 在第二版的基础上加了帧动画：把一天 24 小时的太阳风通过一个 8 小时宽的滑动窗口呈现，让绿色光幕流动起来，山峦保持静止（94 年的 Kp 记录本身没有时间轴）。整个循环 9.6 秒、96 帧、约 5 MB，全部帧共用同一套 128 色调色板，避免颜色闪烁；光幕纹理绑定在数据自己的时钟上，会随光幕一起移动。时间轴下方那条亮绿色的短线，标出当前窗口在一天中的位置。之所以没有做成一整周：NOAA 免费的 1 分钟太阳风数据只保留 24 小时，而 NASA OMNI 档案在这几周缺测 18–36%、且缺口足以把光幕切成碎片——用残缺的一周，不如完整的一天诚实。
