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
- **What is left is two purchase decisions, not engineering** - the camera budget
  and mains power at the table. Both are costed, with a recommendation, in
  [NOTES.md](NOTES.md) section 0.

## Contents

| File | What it is |
|---|---|
| [NOTES.md](NOTES.md) | The engineering brief: FOV math, verified component specs, platform limits, BOM with prices, retail alternatives, rejected options, risks, verification plan |
| [RESEARCH.md](RESEARCH.md) | Follow-on research: retail camera shortlist, RV1106 radio and OpenIPC, on-camera AI, dewarping, broadcast ops, commercial prior art |
| [CONVERSATION.md](CONVERSATION.md) | The full conversation record, including the tool calls and the reasoning trail |
| [test_claims.py](test_claims.py) | Recomputes the FOV table and its thresholds from the stated geometry and fails if any published figure disagrees — the guard on the numbers the purchase rests on |

## Status

Research and specification only. **No hardware purchased, nothing ordered.** Two
decisions pick the route, and both are stated in [NOTES.md](NOTES.md) section 0
with a cost and a recommendation:

- **Budget: build, buy only stage 1 now.** The DIY build is **$199.38** as
  itemised, but it is bought in two stages: the board plus the SC3336 camera
  first - **$78.38** on Amazon, or **$59.98** for the same two parts direct from
  the vendors - and the **$47.00** fisheye lens, the mount and the shield only
  after stage 1 shows the real table fits from the real height. That first stage
  is the cheapest way to test the one unverified assumption in the design. The
  turnkey alternative is the **$699.99 refurb / $949.99 new Mevo Core**, 3.5x-4.8x
  as much, and worth it only if the camera may be big or may sit above the shades.
- **Power: mains at the table, about $8.** The RV1106 idles at a measured
  **0.11 W (22 mA at 5 V)**, so any 5 V supply is ample - and a 5 W one has 45x
  headroom over idle. A battery has to be an "always on" bank (**$74**), because
  22 mA sits below an ordinary bank's auto-shutoff; it is the answer only if the
  fixture is on the wall switch or no socket is in reach. The streaming PC stays
  on mains either way.

The cheapest single decisive test of the optics is still a **~$70 Tapo C325WB**
(106 deg horizontal, 90.2 in of coverage at 34 in) aimed down from 34 in and
pulled into OBS over RTSP - no assembly risk and no unverified lens mount. Buy it
with its firmware requirement in mind: the V2 advisories
(CVE-2026-105672/673/674) are fixed in `V2_1.3.3 Build 260914`, and the RTSP route
needs the Camera Account feature that one of them targets, so the update is
mandatory rather than hygiene (NOTES.md section 8, risk 7). The DIY board + camera
build remains the option if the camera must be small enough to hang on the light
fixture. Details in [RESEARCH.md](RESEARCH.md) section 1.

## Caveat on the numbers

Several vendor FOV figures contradict their own focal lengths and sensor sizes
(noted in NOTES.md section 3). Treat all quoted FOV as approximate and measure real
coverage on the real table before committing to a lens.

## Checking the numbers

The figures above are what the hardware decision rests on, so they are checked
rather than trusted. `test_claims.py` recomputes the field-of-view table and the
thresholds it implies from the stated geometry, and the decision packet's own
arithmetic - the staged subtotals and totals against the priced BOM, the C325WB's
coverage at 34 in, and the power numbers that pick the bank - and fails when any
published figure disagrees, at the precision it claims:

    python3 test_claims.py

Standard library only, no dependencies. It also refuses the figures that were
superseded (the corrected FOV cells, the pre-audit coverage per inch, and the bank
runtime that assumed a different conversion from its siblings), so a wrong number
cannot quietly return.

## License

Licensed under the **Functional Source License, Version 1.1, MIT Future License**
(SPDX: `FSL-1.1-MIT`) - see [LICENSE.md](LICENSE.md). Source-available today;
converts irrevocably to the MIT license on the second anniversary of each release.

## Third-party images

`images/sc3336-b-*.jpg` are product photographs and a dimension drawing from
**Waveshare**, reproduced **temporarily** as illustrative reference for the
SC3336 camera module, with attribution and a link to the source product page.

**They are not covered by this repository's FSL-1.1-MIT license.** Copyright in
those files remains with Waveshare; the FSL grant applies only to our own text and
to `sc3336-dimensions.svg`.

They are placeholders, and will be replaced with photographs of our own hardware
once it is in hand.
