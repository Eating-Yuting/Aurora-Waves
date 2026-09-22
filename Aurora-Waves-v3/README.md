# Aurora Waves · V03 — Emerald Veil in Motion

> **Archived — V03.** A read-only snapshot of the third version. **The final version is V04**, kept at the [repository top level](../README.md) and archived in [`Aurora-Waves-v4/`](../Aurora-Waves-v4/). The raw data is not duplicated here — it lives once in `../data/`, so copy it in before re-running these scripts.
>
> **归档说明**：这是**第三版**的只读快照。**最终版本是第四版（V04）**，在[仓库顶层](../README.md)，也已归档到 `Aurora-Waves-v4/`。原始数据不在这里重复存放，统一放在顶层 `data/`。

![Emerald Veil in motion: the same day of solar wind drawn through a sliding eight-hour window](out/aurora-waves-v03-emerald-veil-in-motion.gif)

The image above is the first version that moves. It plays straight from this page — the file is in `out/`, so opening it shows the animation without running anything.

## What V03 does

V03 takes the measurements V02 already drew and passes them through a window eight hours wide that slides across the day, one frame every ten minutes of the record. Ninety-six frames, played at ten frames a second: the whole day in 9.6 seconds.

Three decisions carried most of the work:

- **The smoothing is computed once, over the full record.** What a given minute looks like never depends on which frame happens to be on screen. Computing it per frame would make the curtain change shape as it moved, which is an artefact, not data.
- **All frames share one 128-colour palette**, built by sampling frames across the loop. GIFs otherwise carry a palette per frame, and the colours visibly flicker as they swap.
- **The mountains do not move.** The 94-year Kp record has no clock, so it cannot slide with the eight-hour window. The bright segment under the time axis marks where the visible window sits inside the day.

It stayed inside one day because its source, NOAA's live feed, serves only the last 24 hours. The first attempt at a week from the OMNI archive looked hopeless and was dropped here; [V04](../Aurora-Waves-v4/) went back and measured it properly. That correction is written up in [`PROCESS.md`](PROCESS.md).

## Files here

| File | What it is |
|---|---|
| `out/aurora-waves-v03-emerald-veil-in-motion.gif` | The animation: 96 frames, 9.6 seconds, about 5 MB. |
| `out/aurora-waves-v03-poster.png` | The poster frame — the window at midday. |
| `aurora_waves_v03.py` | The animation. It imports its drawing from `aurora_waves_v02.py` rather than copying it, so the still and the moving version cannot drift apart. |
| `aurora_waves_v02.py`, `aurora_waves.py`, `aurora_data.py` | The drawing and loading code V03 depends on. |
| `fetch.py`, `plot.py`, `test_data.py`, `test_v02.py` | The original fetcher and the checks, as they stood. |
| `PROCESS.md` | The write-up as it stood when V03 was the current version. |

To run it, copy `../data/` in beside this README first, then:

```sh
uv run aurora_waves_v03.py
uv run aurora_waves_v03.py --window 12 --duration 130
```

## 中文说明

这是**第三版**的归档。它在第二版的基础上加了帧动画：把一天 24 小时的太阳风通过一个 8 小时宽的滑动窗口呈现，让绿色光幕流动起来，山峦保持静止（94 年的 Kp 记录本身没有时间轴）。整个循环 9.6 秒、96 帧、约 5 MB，全部帧共用同一套 128 色调色板，避免颜色闪烁；时间轴下方那条亮绿色的短线，标出当前窗口在一天中的位置。

**最终版本是第四版**：见[仓库顶层](../README.md)或 `Aurora-Waves-v4/`。
