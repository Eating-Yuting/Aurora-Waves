# Process

## Tools and decisions

I chose aurora as the subject and supplied three visual references. I wanted colour and more than five data dimensions. I used AI assistance for the Python scripts and asked Codex to continue the existing `Aurora-Waves` repository after its first landscape version. Codex selected the third reference for its blue-green mountains and luminous points, then revised the plotting code and drafted this documentation. Most of the revised code was written by AI. The final image is drawn by Matplotlib from the saved data, without an AI-generated image layer.

The repository already contained a fetch script, data inspection, a plain first plot and a landscape version. Those stages are retained. This revision uses NumPy for numerical processing, Matplotlib for the image, and Python's standard library for parsing. The download script uses Requests. The raw NOAA and GFZ replies remain unchanged.

## Kept

The revision keeps the historical mountain ranges and the recent solar-wind curtain. This gives the long record a landscape form while leaving room for the newer measurements. It also keeps the plain first-look plot, which makes it easier to inspect the estimated Kp and Bz without the artwork's visual effects. The final curtain adds separate encodings for speed, Bz, Bt, proton density and proton temperature instead of describing several decorative effects as additional data dimensions.

## Rejected and corrected

I passed on two concrete warnings from the previous work: GFZ Kp is in the eighth column, and the SWPC records need sorting before plotting. Codex's inspection also found that the magnetic and plasma files contain multiple spacecraft at the same minute. The revision rejects the earlier approach of mixing those records: it selects active records, validates values, and joins observations at matching UTC minutes. It leaves gaps rather than drawing a smooth continuation through missing telemetry.

The earlier artwork called one point “the strongest storm in the record.” The revision removes that claim because several days share the maximum Kp value. All 27 Kp-9 days in the complete historical years are now marked. It also removes the claim that every decade must have one grand solar-maximum summit. The inspection script's OVATION summary used the latitude column as if it were the aurora field; that was corrected to the third column. OVATION remains an explored source, not an extra dimension claimed for the final picture.

## Checks in this revision

Codex ran the inspection script, rendered the artwork from the existing cached data, and inspected the resulting image. A small regression script checks the known first GFZ day, calendar-year lengths, UTC interpretation, active-spacecraft selection and empty time bins. The final documentation records smoothing, clipping, overlap and the two separate timelines so the image does not imply more than the measurements support.

## 中文记录

我确定了极光主题，提供三张参考图，并要求画面有色彩、包含五个以上的数据维度。Codex 接着已有仓库修改脚本，选择第三张图作为视觉方向，也协助起草了说明。新版保留山峦和光幕，但修正了卫星记录混用、时间排序、缺测处理、Kp 列号及“最强风暴”的说法。图像由真实缓存数据生成，主体代码由 AI 协助完成。

## V02 — Emerald Veil

I asked for another version using the previous image as a reference, with more natural auroral colours and clearly different filenames. Codex kept the same verified datasets, reused the existing parsers, and created `aurora_waves_v02.py` rather than overwriting V01. NOAA's Aurora Tutorial informed the green main light, purple lower border and faint red upper glow. These colours remain a visual treatment rather than measured emissions.

This version keeps the six measurements but changes Bz from thread colour to lower-edge position. That leaves the main curtain green instead of forcing its colour to swing between cyan and violet. The hard vertical bars were replaced with a fading light field, with 45-minute smoothing inside valid runs. The revision rejects filling the missing intervals simply to make a continuous ribbon. The density and temperature points still use the five-minute means, so their numerical detail is not lost in the softened curtain. AI wrote the new rendering code and documentation; it did not generate a photographic background.

The rendered result was inspected, the light points were moved clear of the time labels, and the mountains were lowered to leave room for the section heading. A regression check covers missing runs, isolated bins and the direction of the three curtain encodings. The original V01 files are kept separately and unchanged.

第二版的要求是更贴近真实极光的色感，并且不要覆盖上一版。Codex 保留原始数据，主要修改光幕、配色和层次，也补了新版的图例与说明。为了让主体保持绿色，Bz 改用光幕下缘的位置表达；空白缺测没有补成连续数据。
