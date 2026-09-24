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

## V03 — in motion

I asked for the green curtain to move, ideally across a week. The honest answer turned out to be a day, and the reason is worth recording. NOAA's free one-minute solar-wind feed serves only the last 24 hours — the seven-day `products/solar-wind` endpoints that used to exist now return 404. NASA's OMNI archive (HAPI `OMNI_HRO_1MIN` and `OMNI_HRO_5MIN`) does hold a week, so I downloaded two candidate weeks and measured them: the stronger one was missing 18 per cent of its five-minute samples and 36 per cent of its one-minute samples, in runs averaging under eight minutes, which would cut the curtain into roughly 850 separate ribbons. Bridging only the short gaps still left about 14 per cent of the week blank. I rejected the thinner week and kept the same complete day as the still.

The animation reuses V02's drawing code by importing it, so the still and the moving version cannot drift apart — the only new code is the window, the frame loop and the GIF assembly. Three decisions matter. The smoothing is computed once over the whole record, so what a minute looks like never depends on which frame is on screen. The filament texture is keyed to the data's own clock, so it travels with the curtain instead of shimmering underneath it. And every frame shares one 128-colour palette sampled across the loop, which prevents the colour flicker that per-frame palettes cause in GIFs.

The mountains are deliberately static: the 94-year Kp record has no clock, and moving it would have implied one. A bright segment under the time axis marks where the visible eight-hour window sits inside the day, which is what makes the span of the loop readable. The result loops through 24 hours in 9.6 seconds at 96 frames and about 5 MB.

第三版想要光幕动起来，最好是一周。诚实的答案是一天：NOAA 免费的 1 分钟太阳风只保留 24 小时（原来的 7 天接口已经 404），NASA OMNI 档案虽然有一周，但实测这一周缺测 18–36%，缺口平均不到 8 分钟一段，会把光幕切成约 850 段碎片；只桥接短缺口后仍有约 14% 空白。所以拒绝了更薄的一周，保留了和静态版相同的完整一天。动画直接复用第二版的绘图代码，平滑只算一次、纹理绑定数据时钟、全帧共用一套 128 色调色板；山峦刻意不动，因为 94 年的 Kp 记录没有时间轴，时间轴下的亮线标出当前窗口的位置。

## V04 — a week, and a correction

The week came back. The honest thing to record first is that V03's rejection of it was based on a mismeasurement, and V04 is what fixed it.

V03 counted a minute as available only when *all five quantities* were valid *in the same minute* — the rule V02 uses for its live feed, where both instruments report nearly always. Under that rule the archive looked 18–36 per cent empty. But OMNI's two instruments do not fail together: over the week drawn here the magnetometer reports 95.8 per cent of minutes and the plasma instrument 79.6, and their outages only rarely overlap. Demanding minute-level agreement between two independently failing instruments throws away real data to protect a rule that only made sense when it cost nothing. V04 instead averages each instrument over its own valid minutes inside a shared five-minute bin, and keeps a bin only when both are present. Measured properly, 1,921 of 2,016 bins are usable — 95.3 per cent of the week, with one three-hour hole on 13 October and 48 shorter ones.

That change is a correction, not a convenience, and it is bounded: at most five minutes of alignment error sits inside one bin, the same width as the bin itself. The week chosen is 7–14 October 2024 — picked by ranking every seven-day window since 2015 in the GFZ Kp record, then comparing the top candidates' gap structure. The G5 storm of May 2024 was more famous but had a seven-hour hole; this week has the storm of 10 October (Kp 8.7, Bz −46 nT) and the best coverage of the strong candidates.

Two things were rejected on the way. A per-column fill that would have raised coverage further by interpolating plasma across its gaps was rejected: it invents the very minutes the archive does not have, and the strip and the light points would have hidden it. And simply accepting the harsh mask was rejected after seeing it rendered — a single five-minute hole cut a full-height black stripe through a bright curtain, which read as a rendering fault rather than as missing data. The compromise: the glow fades over twelve minutes into each gap (it is a smoothed field anyway), while the edge line still breaks and the light points still stop, so the hole stays visible in the two layers that are drawn straight from observations.

V04 also re-scaled the encodings. V02's rulers — Bz ±5 nT, Bt 0–6 nT, speed 300–380 km/s — are calibrated to a quiet day; this week reached −46 nT, 48 nT and 810 km/s, so every frame would have been pinned. The new scales were read off this week's own percentiles rather than chosen by eye. The poster frame is the loop's own frame containing the deepest Bz, not an arbitrary midpoint, so the still and the animation cannot disagree about what the storm looked like. And the week strip under the axis replaces V03's bare progress line: the whole week's curtain reach at once, with the window marked, because a week is too long to hold in your head from a moving segment alone.

第四版把一周找了回来，首先要记录的是：第三版拒绝一周，是因为测错了。V03 沿用了 V02「同一分钟内五个量全部有效」的口径，在那个口径下档案看起来缺了 18–36%；但 OMNI 的两台仪器并不同时故障——这一周里磁强计有 95.8% 的分钟在场，等离子体仪有 79.6%。要求两台独立故障的仪器逐分钟对齐，等于为了一个在旧数据上毫无代价的规则扔掉真实数据。第四版改为「各自在自己有效的分钟内取平均、共享同一个五分钟时钟窗口」，2016 个窗口里 1921 个可用（95.3%）。这一版还按本周自身的分布重新标定了三条编码的刻度（否则整场磁暴会被压成一种颜色）、用「含最深 Bz 的那一帧」做海报静帧、并把光幕辉光在缺口处做 12 分钟渐隐——同时边线和光点仍然断开，缺口如实可见。选周的办法是先把 2015 年以来每个七天窗口按 Kp 排名，再比较候选周的缺口结构：2024 年 5 月的 G5 更有名，但那周有一个七小时的洞。

## V04 again — the page, and a size that had to change

Two things came out of showing the finished picture to somebody who had not built it, and both are corrections rather than additions.

**The lettering was sized for a poster and read at a link.** The poster is 2,700 pixels wide, which is right for a file you open and wrong for a README: GitHub's column is about 880. At the size the picture was drawn, a 6 pt caption left that downscale as roughly 4 pixels and could not be read. The fix is not a new layout — it is noticing that font size, line width and point size are measured in *points*, meaning relative to the physical figure and not to the pixel count. The canvas went from 18 × 12 inches to 11.25 × 7.5, and every dpi went up by the same 1.6: frames 60 → 96, poster 150 → 240. Both pictures keep exactly the pixels they had — 1080 × 720 frames, a 2,700 × 1,800 poster — while everything measured in points is now 1.6 times larger relative to the picture. Nothing moved: the drawing is in relative coordinates and the curtain is a raster, so the same picture came back with legible lettering.

**A page, with one control and not six.** The page is `aurora_waves_web.py` writing `site/index.html`: the same week, with one slider for time, so a moment can be stopped on and its six numbers read. The brief allows this and explicitly does not reward it, so it is here for the other reason it gives — the group project will demand a page that builds itself in November, and this is the cheapest place to learn it. What it keeps is that the numbers, the smoothing, the geometry and the colour map are imported from `aurora_waves_v04.py` and `aurora_waves_v02.py` rather than re-implemented, so the page cannot drift away from the poster.

Two things were rejected. Six sliders, one per measurement, would let each be scrubbed on its own clock — which is precisely what makes a picture say six things at once, and this drawing only ever had one clock. And the mountains, for the reason they never move in the GIF either: 94 years of Kp have no clock to slide, so the first row carries this week's own three-hour Kp instead, the same index the ridges are built from. The glow could not be carried over as it is in the poster — a browser will not hold a 2,700-pixel raster for every moment at a usable size — so it became five stacked bands; and because a filled band cannot carry an opacity that varies along time, a faint aurora is now drawn short as well as faint. That is a re-reading of the encoding rather than a copy of it, and it is the one place where the page and the poster are not the same picture.

Two faults were found by rendering the page and looking at it, which was the only way either could have been found. Plotly thins its own slider step labels once there are enough steps, so seven day labels that were present in the generated HTML never painted; the page now draws its own time ruler, in the same coordinates the slider handle travels along. And the annotation meant to caption a panel produced no visible text at all, because `add_annotation(row=3)` resolves to that row's *axis* rather than to its panel — so `x = −.007` meant seven thousandths of a second before 1970, and the caption was drawn there. The axes have to be named explicitly.

中文：把成品拿给没做过这张图的人看了一遍之后，改了两件事，都是修正而不是新增。一是**字号**——海报 2700 像素宽，挂在 README 里只有约 880 像素，原尺寸下 6 pt 的注记缩到约 4 像素，读不出来。修法不是重排版面，而是发现字号、线宽、点径都是按「点」计量的，也就是相对图幅而不是相对像素：画布从 18×12 英寸改成 11.25×7.5，所有 dpi 同比例乘 1.6（帧 60→96、海报 150→240），两张图仍是原来的像素尺寸（1080×720 与 2700×1800），而所有以点计量的元素相对图幅放大了 1.6 倍，构图没有移动。二是**只有一条滑块的网页**：`aurora_waves_web.py` 写出 `site/index.html`，用一条时间滑块把同一周重新读一遍，可以停在某一刻读那六个数字；数据、平滑、几何与配色全部从 `aurora_waves_v04.py`、`aurora_waves_v02.py` 导入，所以网页不会和海报走散。拒绝了「六个维度各一条滑块」——每个量按自己的时钟拖动，正是让一张图同时说六件事的做法；也拒绝了山峦，因为 94 年的 Kp 没有时钟可拖，改用本周自己的三小时 Kp 放在最上一行。光幕改成五层堆叠色带（浏览器托不住每个时刻一张 2700 像素的贴图），色带的透明度无法随时间变化，所以「越暗的极光画得越短」，这是对编码的重新解读，不是照抄。另外两处只有渲染出来才会发现的毛病：Plotly 在步数多时会自动抽稀滑块自身的标签，HTML 里明明有七个日标签却没有画出来，于是页面自己画了一把时间尺；以及 `add_annotation(row=3)` 解析到的是那一行的**坐标轴**而不是面板，`x=−.007` 变成了 1970 年之前，注解一个字都看不见，必须显式指定坐标轴。

## Repository layout — four versions, one copy each

This repository is a single submission, but it carries four versions of the picture, so each one has its own folder — `Aurora-Waves-v1/` to `Aurora-Waves-v4/` — holding that version's scripts, its README, its still and its animation as they stood at the time. Two reasons. A version can be read and seen without checking out an old commit, and the order of decisions stays visible in one place: v1 the first landscape, v2 the quieter palette and the re-encoded Bz, v3 a day in motion, v4 the week — which is both the correction of v3 and the version submitted.

The only thing kept in one place is the raw data: it lives once in `data/`, and all four read it from there, which is why each archive README says to copy it in before re-running a script. Everything else is copied rather than linked, so that a folder is self-contained — open it and you have the whole version. Each picture therefore exists twice: once inside the folder that produced it, and once at the top level in `out/`, which is where the main README's links point. The pairs are written by the same run and are byte-identical; the duplication costs about 9 MB and buys the reader not having to follow a link out of a folder to see what it is about.

One exception, recorded because it is one. `Aurora-Waves-v4/` was re-synced after the type-size revision above, so that the folder claiming to be the submitted version holds the submitted version — same script, same two pictures, byte for byte. The other three folders hold what they held. Their pictures are drawn at the older type size, which is why V03's lettering is visibly smaller than V04's at the same displayed width; that is the honest thing for a frozen stage to show, and it is the clearest way to see what the revision changed.

The archive folders therefore add files the brief does not ask for, which is why the course checker prints one line reading `note  15 file(s) beyond the ones the brief asks for`. It is a `note`, not a `fail`. The check's own source keeps `FAIL` and the softer `note` separate and only a `FAIL` turns the GitHub run red; this run is green. The fifteen are the four archive READMEs, the four archive copies of this document, and the seven pictures in the archive folders. Scripts are not counted — the checker exempts any `.py` file — but they are there anyway, which is the point of an archive. The folders are kept on purpose: they are the evidence of how the picture got to its final state, which is what this document is marked on.

中文：仓库是同一个提交，但里面装了四个版本，所以每一版都有自己的文件夹（`Aurora-Waves-v1/` 到 `Aurora-Waves-v4/`），放着那一版当时的脚本、说明、静帧和动画。这样不用翻旧提交就能读代码、也能直接看到成品，而且能一眼看出决策的顺序：第一版是最早的风景画，第二版换了更安静的配色并改掉 Bz 的编码方式，第三版让一天动起来，第四版回到一周——第四版既是对第三版的纠正，也是最终提交的版本。

只有原始数据是单份的：它只存在顶层 `data/`，四个版本都从那里读，所以每个归档 README 都写了「重跑脚本前先把 `data/` 拷进来」。其余文件是复制而不是链接，这样每个文件夹自带全部内容：每一版文件夹里 `out/` 放的是那一版自己的成品图，顶层 `out/` 里另有一份完全相同的副本（主 README 的链接指向顶层那一份）。两份由同一次运行产出、逐字节一致；重复大约多占 9 MB，换来的是打开一个文件夹就等于打开一个完整版本。

有一个例外，写在这里因为它是例外：`Aurora-Waves-v4/` 在改字号之后重新同步过一次，好让「装着最终版本的那个文件夹」里真的就是最终版本——同一个脚本、同样两张图，逐字节一致。另外三个文件夹保持原样，它们的图仍是旧字号画的，所以同一显示宽度下第三版的字明显比第四版小；对一份冻结的阶段记录来说，这才是诚实的呈现，也是看清这次改了什么的最直接方式。

归档文件夹因此比作业要求多出一些文件，课程检查脚本那句 `note`（"15 file(s) beyond the ones the brief asks for"）说的就是它们——那是 `note` 不是 `fail`，只有 `FAIL` 才会让 GitHub 变红叉，而这次运行是绿的。这 15 个是四份归档 README、四份归档的本文档副本、以及归档文件夹里的七张图；脚本不计入（检查脚本放行所有 `.py`），但脚本本来就在里面，那才是归档的意义。多出来的正是「过程分」要看的证据。

