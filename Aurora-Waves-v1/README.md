# Aurora Waves

> **Archived — V01.** A read-only snapshot of the first version: jade-green ranges under a cyan-to-violet curtain, Bz encoded as the curtain's thread hue. The current version is V02 (Emerald Veil), documented in the [repository README](../README.md) and archived in [`Aurora-Waves-v2/`](../Aurora-Waves-v2/). The raw data is not duplicated here — it lives once in `../data/`, so copy it in before re-running these scripts.
>
> **归档说明**：这是第一版的只读快照（青绿山峦 + 青紫色光幕，Bz 用光幕丝的色相表达）。当前版本是第二版 Emerald Veil，见[仓库顶层说明](../README.md)。原始数据不在这里重复存放，统一放在顶层 `data/`。

![Aurora Waves: cyan and violet mountains beneath a curtain of solar-wind measurements](out/aurora-waves.png)

Aurora Waves turns space-weather measurements into a landscape. I chose aurora because I like its flowing light and colour. The visual direction comes from the third reference image I supplied: blue-green mountains, a dark sky and bright yellow-green points. This is data art about the conditions associated with aurora. Auroral light itself comes from interactions in Earth's upper atmosphere [1]; the picture does not measure the light seen from a particular place.

The lower landscape contains 94 complete years of geomagnetic activity, from 1932 to 2025. Each range groups one decade, with shorter ranges at the beginning and end. Its height follows a 45-day mean of daily maximum Kp. The 27 lime markers identify every day that reached Kp 9 within those complete years. The upper curtain uses a separate, recent solar-wind snapshot: 21–22 September 2026 UTC. Its strands and points represent five-minute means from matching active-spacecraft observations. These two sections have different timelines; a point in the sky does not correspond to the historical mountain underneath it.

## The numbers

The raw replies are kept unchanged in `data/`. GFZ supplies the historical Kp file [2]. NOAA SWPC supplies the magnetic field and plasma observations; its raw replies include several spacecraft, so the scripts select records marked `active: true` [3]. These row counts describe the saved snapshot, not the endpoints today.

| Cached file | Rows / grid points | What one row means | Units / use |
|---|---:|---|---|
| `gfz-kp-ap-since-1932.txt` | 276,784 | One three-hour interval, 1932-01-01 to 2026-09-21 | Kp: unitless, 0–9; historical ridges |
| `swpc-solar-wind-mag-1m.json` | 3,496 | One spacecraft's one-minute magnetic measurement | Bt and Bz GSM: nT; curtain |
| `swpc-solar-wind-plasma-1m.json` | 3,374 | One spacecraft's one-minute plasma measurement | Speed: km/s; density: protons/cm³; temperature: K; curtain |
| `swpc-planetary-k-index-1m.json` | 358 | One update of estimated planetary Kp | Unitless; plain first-look plot only |
| `swpc-ovation-aurora-latest.json` | 65,160 | One `[longitude, latitude, aurora]` grid point | Exploration only; not used in the final artwork |

The exact download addresses are recorded in `fetch.py`. Cached files are reused, so plotting requires no internet once Python dependencies are available. The magnetic and plasma records yield 1,362 matching valid active minutes, grouped into 276 usable five-minute bins. Twelve bins have fewer than three matching samples and remain empty. Times are interpreted as UTC, sorted, and joined at the same minute. Missing values, inactive spacecraft and records with nonzero overall quality flags are excluded without changing the raw files.

## Six dimensions

| Measurement | Visual encoding | Display scale |
|---|---|---|
| Historical Kp | Mountain height above each range's baseline | 0–9; identical height scale for all ranges |
| Solar-wind speed | Thread length | 300–380 km/s |
| Bz, GSM north–south component | Thread hue | −5 nT cyan → +5 nT violet |
| Bt, total field strength | Thread opacity | 0–6 nT, faint → bright |
| Proton density | Point area | 0–5 protons/cm³, small → large |
| Proton temperature | Point hue | 20,000–100,000 K, cyan → lime |

Time supplies an additional horizontal dimension. Display scales are fixed in the code and clipped at their limits; the observed ranges appear below the small traces. Thread length and point area include a small visible minimum. The small Kp trace uses 30-day block averages of daily maxima; the other five traces show the same five-minute bins as the curtain, each with its own vertical range.

The picture shows variation at two timescales and how several measurements can share one visual composition. It hides short historical spikes through smoothing, some mountains through overlap, and minute-scale changes through averaging; the original files retain those values. Repeated contour lines and atmospheric glow are drawing effects, and colour is an encoding rather than an observed emission colour. This is not an aurora visibility forecast, an image of real terrain, or a claim that one decade must contain one solar maximum.

## Run

```sh
uv run fetch.py
uv run aurora_data.py
uv run aurora_waves.py
```

`aurora_waves.py` saves `out/aurora-waves.png` and opens the picture. For a machine without a display:

```sh
uv run aurora_waves.py --no-show
```

The plain first look and the regression check are also available:

```sh
uv run plot.py
uv run test_data.py
```

Check the repository with the course checker:

```sh
uv run https://raw.githubusercontent.com/sd5913/pfad/2026/assignments/check.py --assignment 2
```

## References

[1] NOAA Space Weather Prediction Center. Aurora [EB/OL]. [2026-09-22]. https://www.spaceweather.gov/phenomena/aurora

[2] GFZ Helmholtz Centre for Geosciences. Data: Kp index [EB/OL]. [2026-09-22]. https://kp.gfz.de/en/data . Historical file credited to Geomagnetic Observatory Niemegk; CC BY 4.0, as stated in its header.

[3] NOAA Space Weather Prediction Center. Solar Wind [EB/OL]. [2026-09-22]. https://www.spaceweather.gov/products/solar-wind

## 中文说明

我选第三张参考图的青绿山水、深蓝背景和荧光光点作为视觉方向。下方山峦来自 1932—2025 年的 Kp 历史数据，上方光幕来自 2026 年 9 月 21—22 日的太阳风记录，两部分的时间轴不同。作品使用六项测量数据，具体对应关系见上表。颜色是数据编码，并非实际拍到的极光颜色；空白表示缺测，不能理解为活动降到零。运行 `uv run aurora_waves.py` 会保存图片并弹出预览。
