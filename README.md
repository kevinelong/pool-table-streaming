# Wireless pool-table camera to OBS

Research notes on streaming a **7-foot pool table** overhead into **OBS**, and on to
**Facebook Live / YouTube**, from a small, low-power, wireless camera.

## The short version

- **Facebook Live caps at 1080p**, so 2K and 4K buy nothing for the primary target.
- **Platform latency is measured in seconds**, which makes camera latency irrelevant.
  The usual "low-latency streaming" concerns do not apply here.
- **The binding constraint is optics, not compute.** From the pool light (~31-36 in
  above the cloth) you need roughly **98 deg horizontal FOV**, and no stock camera
  module provides it. Most are 78-90 deg.
- Two ways out: fit a **~2.2 mm M12 fisheye**, or mount the camera **at 55 in or
  higher** - at which point a factory 3.95 mm lens covers the table and the problem
  disappears.
- Everything on the wireless, "small and low power" axis points at a
  **Rockchip RV1106** board (~1 W, hardware H.264, MIPI CSI, WiFi). No microcontroller
  can do this: the ESP32 line tops out at 1080p, and the ESP32-C5 has no video path
  at all.

## Contents

| File | What it is |
|---|---|
| [NOTES.md](NOTES.md) | The engineering brief: FOV math, verified component specs, platform limits, BOM with prices, retail alternatives, rejected options, risks, verification plan |
| [CONVERSATION.md](CONVERSATION.md) | The full conversation record, including the tool calls and the reasoning trail |

## Status

Research and specification only. **No hardware purchased.** The decisive next step is
one ~$79 order (board + camera) and a tape measure - see the verification plan in
NOTES.md section 9.

## Caveat on the numbers

Several vendor FOV figures contradict their own focal lengths and sensor sizes
(noted in NOTES.md section 3). Treat all quoted FOV as approximate and measure real
coverage on the real table before committing to a lens.

## License

Licensed under the **Functional Source License, Version 1.1, MIT Future License**
(SPDX: `FSL-1.1-MIT`) - see [LICENSE.md](LICENSE.md). Source-available today;
converts irrevocably to the MIT license on the second anniversary of each release.
