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
