# Related research

Follow-on research across five tracks, run 2026-10-12. Method: direct source and
vendor-documentation research; no hardware was purchased and nothing was measured
first-hand. Anything computed rather than sourced is marked **computed**.

---

## 1. Retail off-the-shelf shortlist

The question: does a ~$100 camera already do this, making the build unnecessary?

| Camera | Sensor / lens | Horizontal FOV | Covers 78" at 34 in? | RTSP | Price |
|---|---|---|---|---|---|
| **Tapo C325WB** | 1/1.88", **4.1 mm** f/1.0 | **106 deg** | **yes** (90.2 in) | yes, port 554, `rtsp://IP/stream1` | ~$60-80 |
| **Reolink FE-P** (PoE) | 6 MP fisheye | 360 deg | **yes** | yes (verified RTSP + Frigate config) | $111.99 |
| **Reolink FE-W** (WiFi) | 6 MP fisheye | 360 deg | **yes** | yes | $110.49 |
| Amcrest IP5M-F1180EW | 5 MP, **1.4 mm** fisheye | 360 deg | **yes** | yes (PoE/ONVIF) | $149.99 |
| Tapo C225 | 1/2.9", **4.3 mm** | ~65-70 deg | no | yes | ~$40 |
| Reolink B800 | 1/2.8", 4.0 mm | 87 deg | no | yes | - |
| Reolink Argus PT | - | 105 deg *diagonal* | no | **no** (battery model) | - |

**Findings**

- **The Tapo C325WB is the cheapest thing that covers the table from 34 in.** 106 deg
  horizontal puts 90.2 in of coverage on a 78 in table, with margin. It is a
  mains-powered WiFi 6 bullet with documented RTSP and ONVIF Profile S.
- **Reolink's fisheye line is a WiFi, RTSP, 360 deg option for ~$110**, with
  on-camera "multiple display modes" (i.e. dewarping done on the device).
- The pattern in the cheap tier holds: **most cameras are 65-90 deg H and simply
  do not fit.** The wide ones are specific SKUs with a short focal length on a
  comparatively large sensor - you must read the datasheet's *horizontal* figure.
- Battery-powered models still never expose RTSP. Unchanged from the main notes.

**Caveats:** the C325WB is an outdoor bullet - bulky on a light fixture. Published
FOV figures in this price class are frequently optimistic; verify on receipt.

---

## 2. RV1106 radio and the OpenIPC alternative

**Radio - confirmed 2.4 GHz only.**
The Luckfox Pico Ultra W uses the **AIC8800DC** module: WiFi 6 (AX) and Bluetooth
5.2, **2.4 GHz only**. There is no 5 GHz option on this board. Mitigations: the
Ultra W exposes an **IPEX antenna connector** (an external antenna is a drop-in),
and 2.4 GHz is entirely adequate for the ~10-15 Mbps this project needs - the risk
is congestion and jitter, not throughput.

**OpenIPC now has RV1106 support.**
- `OpenIPC/firmware` ships a Rockchip RV1106 board config
  (`br-ext-chip-rockchip/board/rv1106/rv1106.generic.config`).
- The OpenIPC firmware explorer lists `rv1103`, `rv1106`, `rv1109`, `rv1126` as
  buildable targets.
- The OpenIPC streamer line-up has expanded: **Majestic**, **Divinus** (new,
  multi-platform), **Mini** and **Venc**.

**Why it matters:** OpenIPC is the mature, low-latency streaming stack from the
FPV/drone world. If it runs on the RV1106, you get a battle-tested RTSP/SRT path
and a large community instead of the vendor SDK. The vendor page classes Rockchip
ports as **"experts only"**, so treat this as a fallback rather than the default.

---

## 3. On-camera AI - ball tracking and automatic scoring

The RV1106 NPU makes on-camera object detection realistic.

**Hardware budget**
| | RV1106 |
|---|---|
| NPU | 0.5 TOPS INT8 (G2) / **1 TOPS** (G3, per datasheet rev 2.0) |
| Memory | 256 MB DDR3L |
| Bandwidth | ~718 MiB/s (published benchmark) |

**Tooling already exists, including for this exact board**
- `rockchip-linux/rknpu2` ships `examples/RV1106_RV1103/rknn_yolov5_demo` -
  an official YOLOv5 demo for RV1106.
- `airockchip/rknn_model_zoo` lists "limited support RV1103, RV1106".
- **`exie1122/luckfox-YOLO-files`** - precompiled YOLO builds for RV1103/RV1106,
  including `rv1106/models/luckfox_pico_rtsp_yolov5_demo/` (RTSP + YOLOv5 + OSD).
- **`LdDl/rv1106-yolov8`** - converts and deploys YOLOv8 on the NPU **on the
  Luckfox Pico Ultra W specifically**, INT8 quantised.
- The vendor ships RKNN Model Zoo deployment docs for its boards.

**Billiards computer-vision prior art**
| Project | Note |
|---|---|
| **PoolMind** | Raspberry Pi, **overhead camera setup** - the closest analogue |
| `sofi-vega/Pool-Table-Tracker` | OpenCV ball tracking + trajectory prediction |
| `fearlessit/pool_coach` | Real-time, per-frame positions, velocities, confidence |
| `thkodin/pool-ball-tracking` | YOLO + multi-camera |
| `jchadwick/billiards-trainer` | AR, projects trajectories onto the table |
| POOLAID (UCSD) | Academic paper |

**Assessment:** ball detection and shot detection on-camera are feasible, and the
published demos target this exact board. The constraint is the **0.5-1 TOPS budget
plus 718 MiB/s of bandwidth** - expect a small model at modest frame rate, and
expect to trade streaming resolution against inference. Treat scoring as a phase-2
feature, not part of the first build.

---

## 4. Image quality

**Depth of field is a non-issue. `computed`**
For a 2.2 mm f/2 lens with a 4.4 um circle of confusion: hyperfocal distance is
~552 mm (21.7 in), so at a 34 in focus distance the near limit is ~13.3 in and the
far limit is infinity. Points on the table sit 34-55 in from the lens (centre to
corner). **Everything is sharp.** The stock 3.95 mm lens is similarly safe
(near limit ~22.9 in). No focus mechanism is required beyond a one-time set.

**Pixels per ball**
| Configuration | px per inch | Ball (2.25 in) |
|---|---|---|
| 1080p, table fills frame | 24.6 | ~55 px |
| 1080p, 2.2 mm fisheye (table ~65% of width) | 16.0 | ~36 px |
| Tapo C325WB at 2K (2688 wide, table 86.5%) | 29.8 | ~67 px |
| Tapo C325WB scaled to 1080p | 21.3 | ~48 px |

A 36-55 px ball is comfortable for a viewer at normal size; the fisheye costs
roughly a third of it unless you dewarp and crop.

**Dewarping**
- `ffmpeg` ships the **`lenscorrection`** filter (since 2.4, frei0r-derived) for
  radial distortion - the standard tool, and the approach Cisco documents for
  dewarping an RTSP fisheye feed.
- OBS has **no built-in lens correction**; live defish needs a shader
  (`obs-shaderfilter`) or an ffmpeg filter upstream.
- `lenscorrection` is **CPU-only** - at 1080p60 expect a real CPU cost, and
  consider dewarping upstream of OBS or accepting the fisheye look.

**Frame rate:** no pool-specific evidence found on 30 vs 60 fps. General guidance
is a shutter near 2x the frame rate for motion clarity. Treated as unverified.

---

## 5. Broadcast operations

**Multi-destination (Facebook + YouTube at once)**
- **`sorayuki/obs-multi-rtmp`** - 5,060 stars, GPL-2.0, actively released
  (v0.7.4.3 tracks OBS 32.2.1). The established answer.
- Forks extend it to **SRT and WHIP** endpoints simultaneously.
- Cloud restream services are the alternative, at the cost of a dependency and
  more latency.

**24/7 and unattended operation**
- **`maioranav/obs-watchdog`** - monitors an OBS 28-32 instance over WebSocket and
  **automatically restarts the stream if it goes offline.** Directly solves the
  unattended case.
- `23langloisj/obs-stream-scheduler` - schedule windows plus reboot recovery.
- **Gotcha, documented:** OBS's automatic reconnect is **unreliable when Dynamic
  Bitrate is enabled** (obs-studio issues #2496 and #6497, the latter closed as
  *not planned*). For a hands-off stream, **do not enable dynamic bitrate** - this
  is the single highest-value reliability finding here.

**Facebook Live API**
- Flow: create a `LiveVideo` object via the Graph API, receive its ID and stream
  URL, point the encoder at it.
- **June 10 2024 requirements:** the Facebook account must be at least **60 days
  old**, and the Page or professional-mode profile must have **at least 100
  followers**, before it can go live.
- A **persistent stream key** is available via `persistent_stream_key_status` -
  useful for automation so the key does not rotate every broadcast.
- Reminder from the main notes: the Live API requires **both audio and video**
  (H.264/AAC), so a silent AAC track is still needed.

---

## 6. Prior art: there is a commercial market for exactly this

Worth knowing before building anything.

| Product | What it does |
|---|---|
| **CUE STREAM** (cueplay.net) | Professional pool broadcasting for venues. Explicitly advertises a **top-down view alongside the end-of-table shot**, with live scoring from match data |
| **RackMatch LIVE** | Billiards scoring + broadcast overlays; connects scoring, cameras and **OBS** into one system |
| **BilliardON** | Turns an Android tablet into a scoreboard with live scoring, YouTube streaming, player stats |
| **EvoSports** | A plug-in appliance ("evobox") with a camera for venue sports streaming |
| **overlays.uno** | Pool/billiards scoreboard overlays for OBS |
| AZBilliards forum | ["Overhead camera for pool table?"](https://forums.azbilliards.com/threads/overhead-camera-for-pool-table.529310/) - the community asking this exact question since 2021 |

The takeaway is not "buy one" - it's that **the overhead-camera-plus-overlay
pattern is proven**, the OBS integration path is established, and there is a
mature overlay/scoring toolchain to plug into rather than build.

---

## What this changes

1. **The retail case got much stronger.** A **~$60-80 Tapo C325WB** at 106 deg
   horizontal covers the table from 34 in and gives RTSP out of the box - no lens
   mounting, no thread uncertainty, no dewarping, no 0.5 TOPS budget. A
   **~$110 Reolink fisheye** guarantees coverage with on-device dewarping.
2. **DIY's remaining advantage is size and weight.** The C325WB is an outdoor
   bullet; nothing cheap is a small, light board you can tuck into a light shade.
   That is the whole remaining argument for the RV1106 build.
3. **The recommended first experiment changed.** Instead of board + camera + a
   lens whose M12 thread is unverified, buy the **$70 Tapo C325WB**, point it down
   from 34 in, and pull the RTSP into OBS. It answers the FOV question for less
   money and with no assembly risk.
4. **Two operational findings worth acting on now:** never enable Dynamic Bitrate
   on an unattended stream, and use `obs-watchdog` to survive disconnects.
5. **On-camera AI is real but phase-2.** Precompiled YOLO demos already exist for
   this exact board; the 0.5-1 TOPS NPU is the constraint, not the software.
