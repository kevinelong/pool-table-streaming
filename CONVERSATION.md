# Pool table wireless streaming to OBS - conversation record

Session 2026-10-10 .. 2026-10-12 | model deepseek/deepseek-v4-flash-vision-exp
Companion: NOTES.md (distilled engineering brief)

NOTE Plain ASCII. Assistant 'thinking' blocks and tool RESULTS are omitted for size;
tool CALLS are listed with their stated intent. In-body headings are demoted 2 levels so
the [n] USER / [n] ASSISTANT turn markers stay top-level. Generated from a local session
log while it was still running, so the closing assistant message is not included.
Machine-specific paths, usernames and tracking parameters were removed for publication.

---

## [1] USER

which microcontrollers are you familiar with?

*(tools used:)*
- `read`  [.] - Checking working directory context

## [1] ASSISTANT

Empty cwd - answering as general knowledge.

**Strong familiarity (architecture + peripherals + toolchains):**

| Family | Notable parts | Typical stack |
|---|---|---|
| AVR 8-bit | ATmega328P/2560, ATtiny13/85/2313 | avr-gcc, avrdude, Arduino core |
| ARM Cortex-M | STM32 F0/F1/F4/G0/H7, nRF51/52/53, RP2040/RP2350, LPC, SAM D/E, Kinetis, Teensy (i.MX RT) | CMSIS, STM32 HAL/LL + CubeMX, Zephyr, FreeRTOS, embassy (Rust) |
| ESP 32-bit | ESP8266 (Xtensa L106), ESP32/S2/S3 (LX6/LX7), C3/C6/H2 (RISC-V) | ESP-IDF, Arduino-ESP32, MicroPython |
| PIC | PIC10/12/16/18, PIC24/dsPIC, PIC32 | XC8/XC16/XC32, MPLAB |
| MSP430 | FR2xx/FR5xx, G2xx | msp430-gcc, DriverLib, Energia |
| RISC-V MCU | CH32V003, GD32VF103, ESP32-C6, WCH/HPM | riscv-gcc, PlatformIO |
| 8051 lineage | 8051/8052, AT89, STC89/STC8, Nuvoton N76 | SDCC, Keil C51 |
| Others | STM8, Silabs EFM32/Gecko, Renesas RL78/RX, TI CC13xx/26xx, Holtek, XMEGA | varying vendor IDEs |

**Abstractions/frameworks:** Arduino, PlatformIO, Zephyr, FreeRTOS, mbed OS, ESP-IDF, CMSIS-DSP, STM32Cube (HAL/LL), MicroPython/CircuitPython, embedded Rust (`embedded-hal`, `embassy`).

**Honest limits:** solid on *concepts* - clocks/PLL, GPIO, timers/PWM, ADC/DAC, DMA, UART/SPI/IC/CAN/USB, interrupts/NVIC, sleep/power modes, bootloaders, flash/EEPROM, boot/startup code, linker scripts, openocd/J-Link/ST-Link/SWD debug. But exact **register names and bit positions vary per part and silicon revision** - I verify against the datasheet, CMSIS device header, or vendor SDK instead of reciting from memory. Also weaker on proprietary/NDA toolchains (Keil-only parts, some Renesas/PIC32 config) and on analog/PCB-level design.

What's the target? If you name the part, I'll pin registers and write code against its actual SDK rather than a generic sketch.

## [2] USER

what has wifi and can stream 4k video as streaming video to OBS wirelessly is the goal

*(tools used:)*
- `web_search`  [ESP32-P4 H.264 encoder hardware support resolution limit 1080p] - Verifying ESP32-P4 encode limits
- `web_search`  [OBS Studio WHIP input media source WebRTC ingest low latency] - Verifying OBS WHIP input support
- `web_search`  [RK3588 hardware H.265 H.264 encoder 4K60 8K30 mpp ffmpeg rkmpp] - Checking RK3588 encoder capability

## [2] ASSISTANT

Pushing back on the framing first: **no microcontroller can do 4K.** Bandwidth and encode compute put this squarely in SBC/NVENC territory. Let me ground the specifics before recommending.

## [3] ASSISTANT

Grounded now. **Verdict: nobody sells this as a microcontroller.** The ceiling for MCU-class silicon is 1080p - the ESP32-P4's hardware H.264 encoder tops out at 1080p30 ([Espressif esp-h264 docs](https://docs.espressif.com/projects/esp-techpedia/en/latest/esp-friends/solution-introduction/multimedia/component-description/esp-h264.html), [Pyro/P4 benchmark](https://github.com/Metrix187/esp32-p4-h264-benchmark)). 4K needs a board with a real hardware video encoder - that's an SBC, not an MCU.

#### Boards that actually do it

| Board | Encoder | WiFi | Input path | ~Cost | Notes |
|---|---|---|---|---|---|
| **Orange Pi 5 Plus** (RK3588) | H.264/H.265 to 8K@30 | onboard WiFi 6 + 2x 2.5GbE | MIPI CSI (IMX415 4K) via ISP | $120-180 | Best value; `rkmpp` + ffmpeg |
| **Radxa Rock 5B / 5T** (RK3588) | same | WiFi 6 (5B) / 6E (5T) | MIPI CSI x2, no HDMI-in | $150-250 | 5T adds M.2 + 2.5GbE x2 |
| **Jetson Orin Nano Super** | NVENC 4K H.264/H.265 | M.2 Key-E module (verify bundle) | USB3/CSI | $249 | CUDA if you also want CV |
| **Intel N100 mini PC** | Quick Sync | onboard WiFi 6 | USB3 UVC capture (HDMI-in) | $130-220 | Easiest, x86, not ARM |
| ~~Raspberry Pi 5~~ | **none** - H.264 block was removed | WiFi 5/6 | - | - | Cannot encode. Avoid. |
| ~~ESP32-S3 / ESP32-P4~~ | 1080p30 max | yes | MIPI/parallel | $10-40 | Good for a 720p/1080p sub-stream only |

[RK3588 datasheet](https://rockchip.fr/RK3588%20datasheet%20V1.3.pdf): 8K@60 H.265 decode, 8K@30 encode - massive headroom for 4K60.

#### Pipeline

```mermaid
flowchart LR
  A["Camera<br/>MIPI CSI 4K sensor<br/>or HDMI -> USB3 UVC"] --> B["RK3588 board<br/>HW encode H.265 4K<br/>~30-60 Mbps"]
  B -->|"SRT / RTSP over 5-6 GHz WiFi"| C["Ingest server<br/>MediaMTX on your PC"]
  C -->|"SRT or RTSP, localhost"| D["OBS Media Source"]
  C -.->|"WHEP / WebRTC"| E["Browser preview"]
```

**Protocol choice.** OBS 30+ speaks WHIP as an **output** only ([OBS WHIP guide](https://obsproject.com/kb/whip-streaming-guide)) - for *ingest* use a Media Source with `srt://` or `rtsp://`, or the [live-stream-source plugin](https://github.com/xacnio/live-stream-source) for SRT/HLS/WHEP. MediaMTX in the middle is the boring, robust choice: it accepts SRT/RTSP/RTMP/WHIP and republishes locally with sub-100 ms buffering.

**Latency you can expect:** SRT ~150-400 ms, RTSP/UDP ~200-500 ms, WebRTC/WHIP ~100-300 ms glass-to-glass, tuned. WebRTC wins only if you need <200 ms; SRT is far easier to make *stable*.

#### The real failure mode is RF, not silicon

4K60 H.265 at decent quality is 30-80 Mbps. WiFi 5 (2x2, 80 MHz) real-world does 300-500 Mbps, so throughput is never the problem - **jitter, retries and airtime** are. Rules that matter:

- 5 GHz or 6 GHz only; never 2.4. Pin a DFS-free channel, disable auto-channel.
- **OBS PC on Ethernet** to the same AP. Both ends on WiFi halves airtime and doubles jitter.
- SRT with ~3-5x the bitrate as latency buffer beats raw RTSP.
- On-camera transmitters (Hollyland Pyro, Accsoon) are an option *only* if the model exposes RTSP/SRT out - many expose app-only. Verify before buying.

#### To pin an exact build I need two facts

1. **Source:** a bare MIPI camera sensor, or HDMI out of an existing camera? (HDMI changes the answer completely - you need HDMI-in, which no cheap RK3588 board has; you'd add a USB3 capture whose MJPEG/H.264 then gets decoded and re-encoded.)
2. **Constraints:** latency target, budget, and whether the transmitter must be battery-powered/on-camera vs. a static box on a shelf.

Tell me those and I'll spec the board, the ffmpeg/rkmpp command line, and the MediaMTX + OBS config.

## [3] USER

what hardware is small and low power even if we have to drop to 2k

*(tools used:)*
- `web_search`  [Rockchip RV1106 encoder 2560x1440 2K@30 H.265 H.264 power consumption datasheet] - Verifying RV1106 2K encode specs
- `web_search`  [Luckfox Pico Ultra W RV1106 WiFi RTSP stream size power consumption] - Checking Luckfox Pico Ultra W capabilities
- `web_search`  [OpenIPC supported SoC list SSC338Q GK7205 HI3516EV300 Ingenic T31 RTSP] - Checking OpenIPC supported SoCs

## [4] ASSISTANT

2K changes the answer completely - it puts you into **IP-camera SoCs**, which are a whole class smaller and lower-power than any SBC. Verifying the numbers.

## [5] ASSISTANT

#### The class that fits: IP-camera SoCs, not SBCs

Rockchip's **RV1106** is a 5 MP@30 H.265/H.264 encode chip ([RV1106 datasheet](https://rockchip.fr/RV1106%20datasheet%20V2.0.pdf)) - that's above 2K, in a package that idles around 60 mA @ 5 V ~= **0.3 W** ([Luckfox forum measurement](https://forums.luckfox.com/viewtopic.php?t=615)). Nothing in the SBC tier comes close on size or power.

| Option | Max encode | WiFi | Size | Power (est.) | Price | Software |
|---|---|---|---|---|---|---|
| **Luckfox Pico Ultra / Ultra W** (RV1106) | 5 MP@30 H.265/H.264 | onboard WiFi (verify variant) | ~30x65 mm | **~0.5-1.5 W** | $20-35 | Luckfox buildroot SDK + RTSP demos, [wiki](https://wiki.luckfox.com/Luckfox-Pico-Ultra) |
| **RV1126 module** (Firefly Core-1126, etc.) | 4K@30 + 1080p@30 simultaneous | via SDIO/USB module | core-board ~40x40 mm | ~1.5-3 W | $40-90 | rkmedia/RKNN, 2 TOPS NPU |
| **Ingenic T31/T41 or SigmaStar SSC338Q + [OpenIPC](https://openipc.org/cameras/vendors)** | T31 2K/5 MP, SSC338Q 4K | module's own | stick/board cam | ~0.3-1 W | $15-40 | OpenIPC firmware, RTSP/RTMP out of the box |
| Radxa Zero 3W (RK3566) | **1080p60 only** | onboard | 65x30 mm | ~1-2 W | $25-45 | normal Linux; no 2K |
| Orange Pi 5 / Rock 5A (RK3588S) | 8K@30 | onboard WiFi 6 | 62x100 mm | **5-12 W** | $90-160 | overkill unless you need 4K60 |
| ESP32-P4 | 1080p30 (MCU-class) | WiFi 6 | ~25x25 mm | ~0.5 W | $10-25 | ESP-IDF; 2K is out of reach |

#### Why RV1106 is the sweet spot

- **5 MP@30 encode** covers 2560x1440 (3.7 MP) with headroom, and even 2592x1944. 2K H.265 at that resolution is **8-15 Mbps** - trivial for 2.4 GHz, let alone 5 GHz. Wireless link stops being the risk at 2K, which it never stops being at 4K.
- **~1 W** -> runs for many hours on a USB power bank; no heatsink.
- Cameras that match: **SC3336 (3 MP)** or **MIS5001 (5 MP)** - both supported by the Ultra's CSI path ([Luckfox CSI docs](https://wiki.luckfox.com/Luckfox-Pico-Ultra/CSI-Camera)).
- RTSP out is a solved example in the Luckfox SDK/forums, so the OBS leg is unchanged from before: `board -> RTSP/SRT -> MediaMTX -> OBS Media Source`.

#### Honest tradeoffs

- **RV1106/RV1126 SDKs are buildroot + C (RKMedia), poorly documented in English.** Luckfox's wiki is the best of the bunch; the pure-IPC route (OpenIPC on a $20 camera) is cheaper but even more DIY and vendor-warranty-hostile.
- **"WiFi variant" matters** - some Luckfox Pico boards are Ethernet-only. Confirm the W/WiFi SKU before ordering.
- If you later want 4K60, the only path is RK3588S-class silicon, and you pay in watts and volume. 2K is where small and low-power actually coexist.

Two things decide the final pick: do you need **battery/on-camera** (then RV1106 + power bank, or OpenIPC module), and what's your **latency ceiling** (SRT vs RTSP tuning)? Give me those and I'll name the exact SKU and write the RTSP-to-OBS config.

## [4] USER

anyone done this already with recent hardware? research.

*(tools used:)*
- `read`  [(internal skills doc)] - Reading required skills mapping doc
- `web_search`  [Luckfox Pico RV1106 RTSP stream to OBS ffmpeg project github] - Searching Luckfox RV1106 streaming projects
- `web_search`  [OpenIPC camera RTSP stream to OBS Studio low latency setup tutorial] - Searching OpenIPC to OBS streams
- `web_search`  [RK3588 rkmpp ffmpeg HEVC SRT RTSP stream to OBS tutorial wireless] - Searching RK3588 SRT OBS workflow
- `web_search`  [esp32-cam RTSP server esp32cam-rtsp OBS studio project resolution] - Searching ESP32 camera RTSP projects
- `web_search`  [OpenIPC drone 4K wireless video link ground station OBS RubyFPV OpenHD SSC338Q] - Searching drone wireless video to ground station

## [6] ASSISTANT

Doing this directly (no subagents - the workstation rules forbid a second agent). Reading the required skills doc alongside round 1 of the search.

*(tools used:)*
- `web_search`  [Luckfox Pico Ultra RV1106 OBS studio RTSP stream resolution fps test] - Searching Luckfox OBS streaming reports
- `web_search`  [RubyFPV OpenIPC AIO SSC338Q 4K latency ms ground station video quality] - Searching RubyFPV OpenIPC latency figures
- `web_search`  [OpenHD wfb-ng ground station stream video to OBS gstreamer udp pipeline] - Searching OpenHD WFB-NG to OBS
- `web_search`  [wireless camera streaming to OBS SRT mediamtx 4K low latency 2025 setup guide] - Searching wireless camera to OBS latency
- `web_search`  [Orange Pi 5 RK3588 4K video encode SRT streaming test OBS rkmpp benchmark 2025] - Searching RK3588 4K SRT streaming test

## [7] ASSISTANT

Round 1 gave the real projects. Round 2 - hunting actual OBS endpoints and measured latency/quality numbers.

*(tools used:)*
- `web_search`  [luckfox pico ultra webrtc low latency streaming latency ms RTSP alternative] - Searching RV1106 WebRTC latency work
- `web_search`  [openipc majestic streamer SRT output RTSP RTMP stream to OBS from IP camera] - Searching OpenIPC SRT output support
- `web_search`  [Reolink Tapo WiFi IP camera 2K 4K RTSP stream into OBS studio walkthrough] - Searching WiFi IP camera to OBS

## [8] ASSISTANT

One more targeted round - checking the low-latency paths and the OBS-side gotchas.

## [9] ASSISTANT

#### Answer: yes, three separate communities - but nobody has published your exact combo

The pieces all exist and are recent. What's *missing* is a turnkey "2K, ~1 W, WiFi, OBS" box and any published OBS-specific recipe on the RV1106. You'd be assembling known parts, not pioneering.

##### Prior art that's actually shipping

| Project | Hardware | Achieved | Latency | Status |
|---|---|---|---|---|
| [SobolevTim/luckfox-frigate-cam](https://github.com/SobolevTim/luckfox-frigate-cam) | **Luckfox Pico Ultra W (RV1106)** + MIS5001/SC3336 | "stable H.264 RTSP stream" | not stated | Active; built for Frigate/NVR |
| [Luckfox official rkmpi example](https://github.com/LuckfoxTECH/luckfox_pico_rkmpi_example) | RV1106 (Ultra/Pro) | H.264 RTSP + RTMP reference | [~1 s measured](https://forums.luckfox.com/viewtopic.php?t=1828) (OpenCV path) | Official, 74 |
| [OpenIPC](https://openipc.org/) + [RubyFPV](https://rubyfpv.com/) + [waybeam](https://github.com/OpenIPC/waybeam) | **SSC338Q + IMX415** air unit | 1080p120 / 4K, HW H.265, RTSP/RTMP/SRT out | **[~30-32 ms glass-to-glass](https://rubyfpv.com/)** | Very active, drone/teleop |
| [RkCamRtspServer](https://github.com/icetd/RkCamRtspServer) - [MediaMTX Pi-camera doc](https://mediamtx.org/docs/publish/raspberry-pi-cameras) | RK3588S + MIPI (OV13850) | 4K-class HW RTSP server | - | Reference code |
| [Radxa RTSP guide](https://docs.radxa.com/en/rock5/rock5c/app-development/rtsp) | Rock 5C, **5B HDMI-RX** | HW encode -> RTSP | - | Vendor doc; 5B gives HDMI-in |
| [rzeldent/esp32cam-rtsp](https://github.com/rzeldent/esp32cam-rtsp) - [ESP-VISION RTSP](https://docs.espressif.com/projects/esp-vision/en/latest/esp32p4/api-reference/rtsp.html) | ESP32-S3 / **ESP32-P4** | 1080p H.264 RTSP | - | P4 module is official but thin |
| [picamera.live (Pi-WebRTC)](https://picamera.live/) | Pi / Jetson | board->browser WebRTC | **100-200 ms** | Commercial-ish |
| Tapo / Reolink WiFi cams ([Tapo](https://www.tapo.com/uk/faq/34), [Reolink](https://support.reolink.com/articles/900000630706-Introduction-to-RTSP/)) | mains-powered IP cam | 2K-4K RTSP -> any client | seconds unless tuned | **Zero build** |

##### What the research actually tells you

**The RV1106 path is real but unpolished.** SobolevTim's repo is the closest thing to your use case, and it targets *Frigate*, not OBS - consuming RTSP is the same problem either way. The only latency figure I found for a Luckfox RTSP example is **~1 second** ([forum t=1828](https://forums.luckfox.com/viewtopic.php?t=1828)), and it's on the OpenCV example that decodes and re-encodes in userspace. A direct VENC->RTSP path should be far better - `[INFERENCE]`, unmeasured, and that's exactly the number you'd have to establish yourself. Someone is also [pushing WebRTC out of a Pico Ultra W](https://forums.luckfox.com/viewtopic.php?t=1860), which is the low-latency escape hatch.

**The low-latency crown belongs to OpenIPC/SSC338Q** - 30-32 ms glass-to-glass is 30x better than the RV1106 reports. But that ecosystem is built for FPV drones and goggles, is 4K@capable at higher power than RV1106, and expects a WFB-NG radio link ([ground station on Ubuntu](https://docs.openipc.org/use-cases/fpv/wfb-ng/groundstation-ubuntu), [Radxa Zero 3W as GS](https://openfpv.com.ua/en/hardware/vrx/radxa-zero-3w)), not a normal WiFi AP + OBS.

**The OBS side has two documented traps:**
- **WHIP in OBS is output-only.** Ingest must be a Media Source with `rtsp://` or `srt://` ([OBS SRT guide](https://obsproject.com/kb/srt-protocol-streaming-guide)), or the [live-stream-source plugin](https://github.com/xacnio/live-stream-source) for HLS/WHEP/IVS.
- **OBS's SRT *listener* mode is buggy** - it [cannot recreate the socket on reconnect while an output is active](https://github.com/obsproject/obs-studio/issues/13506). Use MediaMTX in the middle, or OBS as caller, not listener.
- OpenIPC's Majestic has a [known RTMP push failure against MediaMTX](https://github.com/OpenIPC/majestic/issues/194) - another argument for RTSP or SRT rather than RTMP.

##### The genuine gap

1. **No published RV1106 -> OBS pipeline at all**, let alone one with measured end-to-end latency. Frigate is the only documented consumer.
2. **No turnkey 1 W battery product with open RTSP.** Battery IP cameras (Argus class) either don't expose RTSP or wake-on-PIR with multi-second standby latency - useless for live OBS.
3. **The 300 ms-vs-30 ms gap is unexplained**: it's unclear how much of the Luckfox ~1 s is the OpenCV example rather than the platform. That's the one measurement worth making before committing to a platform.

##### Concrete next step

Cheapest decisive experiment: **Luckfox Pico Ultra W (~$25) + SC3336**, run the official `rkmpi` RTSP example unmodified, pull it into MediaMTX, and measure glass-to-glass with a phone stopwatch against the OBS preview. That single number decides RV1106-vs-SSC338Q and costs one board. If it lands under ~300 ms, you have your small low-power 2K box; if it's stuck near 1 s, jump to an OpenIPC SSC338Q air unit and accept the bigger power budget.

Want me to write the exact MediaMTX config, the OBS Media Source settings, and a repeatable latency-measurement procedure so the number you get is comparable across boards?

## [5] USER

generate a parts list and summarize consicely your strategy

*(tools used:)*
- `web_search`  [Luckfox Pico Ultra W price buy SC3336 MIS5001 camera kit waveshare] - Checking Luckfox Pico Ultra W pricing
- `web_search`  [Runcam WiFiLink v2 price buy OpenIPC AIO air unit SSC338Q IMX415] - Checking SSC338Q air unit pricing

## [10] ASSISTANT

#### Parts list

##### Tier A - primary build (2K, ~1 W, ~$60 total)

| Qty | Part | Why | ~Price |
|---|---|---|---|
| 1 | **Luckfox Pico Ultra W** (RV1106, onboard WiFi, eMMC) | 5 MP@30 HW H.265, ~0.3 W idle | $20-30 |
| 1 | **SC3336 3 MP Camera (B)** - 2304x1296 | Native 2K, the sensor the RTSP projects target | $15-20 |
| 1 | *or* **MIS5001 5 MP** - 2592x1944 | Headroom above 2K if you want it | [$20-22](https://www.waveshare.com/product/luckfox/cameras.htm) |
| 1 | microSD 16-32 GB | Firmware + local DVR | $5 |
| 1 | 5 V/2 A USB-C PSU or 10 000 mAh power bank | Portability test | $0-20 |
| 1 | USB-TTL serial adapter (CH340) | Console when it doesn't boot | $5 |
| 1 | 5 GHz AP on a dedicated SSID | Camera on WiFi, **OBS PC on Ethernet** | reuse |

CSI cable is bundled. Order the **W** SKU - the non-W boards are Ethernet-only. Board price is unverified against a live listing; confirm at checkout.

##### Host side (free)

MediaMTX (ingest hub) - OBS 30+ - optional [live-stream-source plugin](https://github.com/xacnio/live-stream-source) - ffmpeg (for the latency measurement).

##### Tier B - escalation if the gate fails (low latency)

| Part | Note | ~Price |
|---|---|---|
| **RunCam WiFiLink 2** (OpenIPC, SSC338Q-class, 1080p@90) | Pre-assembled, RTSP/RTMP out, ~30 ms class | $70-100 |
| *or* bare **SSC338Q + IMX415** + WFB-NG ground station ([Radxa Zero 3W](https://openfpv.com.ua/en/hardware/vrx/radxa-zero-3w)) | Mature stack, real build effort | $60-120 |

##### Tier C - only if 4K60 becomes a hard requirement

**Orange Pi 5 Plus 16 GB** ($130-160) + IMX415 MIPI (or Rock 5B for HDMI-in) + 5 V/4 A supply + heatsink. 5-12 W. Not small, not low power.

##### Do not buy

Pi 5 (no hardware encoder) - ESP32-S3 (1080p) - RK3566/Zero 3W (1080p only) - ESP32-P4 (1080p, and thin RTSP support).

#### Strategy

1. **Reduce resolution  change class.** 2K moves you from SBC to IP-camera SoC. RV1106 does 5 MP@30 at ~1 W; the cheapest SBC that beats it draws 5-12 W.
2. **Buy the cheapest decisive experiment, not the final product.** One Pico Ultra W + SC3336, running the official `rkmpi` RTSP example **unmodified**. No custom code until the number exists.
3. **Architecture is fixed:** HW VENC -> RTSP -> MediaMTX -> OBS Media Source. Never OBS as SRT listener ([known bug](https://github.com/obsproject/obs-studio/issues/13506)); WHIP is output-only in OBS.
4. **Single gate: glass-to-glass latency.** <=300 ms  RV1106 wins, proceed to packaging. ~1 s  tune first (no B-frames, GOP ~= 1 s, low-latency flags, UDP vs TCP), then escalate.
5. **Escalate only on a failed gate.** Tier B buys ~30 ms instead of ~1 s at 3-4x price and power. Don't buy it preemptively.
6. **Radio is not the risk at 2K.** H.265 1440p is 8-15 Mbps - trivial for 5 GHz. Jitter is the enemy, hence dedicated SSID + wired PC.
7. **Rejected up front:** no MCU can do this (1080p ceiling), and no battery IP camera exposes usable live RTSP. Both dead ends; don't re-litigate.

Ready to write the MediaMTX config, OBS Media Source settings, and a repeatable latency-measurement procedure for when the board arrives.

## [6] USER

any one stop shopping source where i can get most of not all parts?

*(tools used:)*
- `web_search`  [waveshare.com Luckfox Pico Ultra W product page price buy] - Checking Waveshare Luckfox stock
- `web_search`  [Luckfox Pico Ultra W camera kit bundle buy aliexpress official store price] - Checking Luckfox official store bundles
- `web_search`  ["Luckfox Pico Ultra" buy amazon dfrobot openelab luckfox store RV1106] - Checking Luckfox retail channels

## [11] ASSISTANT

Checking live availability and whether a single vendor actually stocks the whole Tier A BOM.

## [12] ASSISTANT

#### Yes - two genuine one-stop vendors

##### 1. Waveshare - best for a single cart covering the *entire* Tier A list

[waveshare.com/product/luckfox.htm](https://www.waveshare.com/product/luckfox.htm) carries the board, the cameras, **and** the non-Luckfox bits (USB-TTL, microSD, PSU) in one order:

- [Luckfox Pico Ultra RV1106](https://www.waveshare.com/luckfox-pico-ultra.htm) - board, WiFi/PoE variants
- [Cameras](https://www.waveshare.com/product/luckfox/cameras.htm) - MIS5001 5 MP, SC3336 3 MP ([direct](https://www.waveshare.com/sc3336-3mp-camera-b.htm)), IMX415 8 MP ($23.97-24.99), ISG1321
- USB-TTL (CH340) adapter, microSD cards, 5 V supplies, cables - all house brand

Costs more than buying direct (Newegg's Waveshare listing for the Ultra is [$67.19](https://www.newegg.com/lenovo-14-0-8gb-memory-gray/p/1TS-000E-1E5X4?Item=3C6-00U7-00M59); [OpenELAB](https://openelab.com/products/waveshare-luckfox-pico-ultra-linux) $89 for the PoE+wireless variant). You pay ~1.5-2x for one cart and faster shipping.

##### 2. luckfox.com - official store, cheapest, kits bundled

One-stop *for the camera hardware* and it sells ready-made kits:

| SKU at [luckfox.com](https://www.luckfox.com/index.php?page=2&route=product%2Fsearch&tag=LuckFox%2BPico%2BUltra) | Price |
|---|---|
| Luckfox Pico Ultra B | $41.99 |
| Luckfox Pico Ultra B LCD Kit C | $71.99 |
| Luckfox Pico Ultra W LCD Kit C (WiFi + LCD) | $80.99 |
| MIS5001 5 MP Camera | [product page](https://www.luckfox.com/MIS5001-5MP-Camera-A) |
| Pico Mini A/B (no WiFi) | $11.99 |

Same vendor as the [wiki](https://wiki.luckfox.com/Luckfox-Pico-Ultra) and SDK, so firmware/support ambiguity disappears. Ships from China; you still need a USB-TTL adapter from elsewhere.

##### Other single-vendor options

- **OpenELAB** ([openelab.io](https://openelab.io) DE / [openelab.com](https://openelab.com) US) - Waveshare Luckfox line, EU-friendly.
- **Newegg / Amazon** - Waveshare's own marketplace listings, fastest US delivery, highest price.
- **RobotShop** - sells the 3 MP module bundles.

##### Tier B one-stop

FPV dealers carry the whole OpenIPC path in one cart: **[GetFPV](https://www.getfpv.com/runcam-wifilink-2-w-openipc.html)**, **Pyrodrone**, **RaceDayQuads**, **Rotorama** (EU), or [shop.runcam.com](https://shop.runcam.com/runcam-wifilink2) - WiFiLink 2, antennas, and ground-station radios together.

##### Caveats

- **Confirm the WiFi SKU.** Luckfox's own search mixes `Ultra`, `Ultra B` and `Ultra W` - the non-W boards are Ethernet-only, and resellers don't always distinguish. Open the product page and check for "Onboard WiFi 6 & BLE 5.2".
- **Kit contents vary** - verify whether an "LCD Kit" includes the camera, or only the display.
- **Reseller markup is real:** $41.99 direct vs $67-89 through Waveshare/OpenELAB for comparable variants.
- **Firmware and docs come from luckfox.com regardless** of where the hardware ships, so buying the board at the cheapest source costs you nothing but shipping time.

**Recommended:** if you want one cart and it working this week, buy everything from Waveshare. If you want the lowest price and don't mind two orders, board + camera from luckfox.com and a CH340 adapter locally.

## [7] USER

what is the total price difference between amazon and the next best one stop

*(tools used:)*
- `web_search`  [Amazon "Luckfox Pico Ultra" RV1106 board price buy W WiFi] - Checking Amazon Luckfox board price
- `web_search`  [waveshare Luckfox Pico Ultra W price USD onboard WiFi 6 27103] - Checking Waveshare direct price
- `web_search`  [Amazon SC3336 3MP camera module Luckfox Pico price buy] - Checking Amazon camera module price
- `web_search`  [luckfox.com store accessories USB to TTL microSD power supply camera bundle Ultra W kit ] - Checking Luckfox accessory availability

## [13] ASSISTANT

Need real prices on both sides before I can subtract anything.

*(tools used:)*
- `web_search`  [site:amazon.com Luckfox Pico Ultra RV1106 development board] - Checking Amazon Luckfox listings
- `web_search`  [site:amazon.com Waveshare SC3336 3MP camera module Luckfox] - Checking Amazon Waveshare cameras
- `web_search`  [amazon.com Luckfox Pico Ultra W price USD RV1106 WiFi 6 board listing] - Checking Amazon Luckfox prices broadly

## [14] ASSISTANT

Amazon prices aren't surfacing in those results. One focused round on Amazon specifically.

*(tools used:)*
- `read`  [https://www.amazon.com/waveshare-Luckfox-Pico-Ultra-Board/dp/B0D8T54XJR] - Reading Amazon Luckfox Ultra W listing
- `read`  [https://www.waveshare.com/luckfox-pico-ultra.htm?sku=26790] - Reading Waveshare direct product page
- `read`  [https://www.amazon.com/SC3336-3MP-Camera-Sensitivity-Performance/dp/B0CJM7S6F6] - Reading Amazon SC3336 camera listing

## [15] ASSISTANT

Amazon ASINs found but no prices in the snippets. Trying to read the actual pages.

*(tools used:)*
- `bash`  [curl -sL --compressed -m 25 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/53] - Extracting Amazon board price
- `bash`  [curl -sL --compressed -m 25 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/53] - Extracting Amazon camera price
- `bash`  [curl -sL --compressed -m 25 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/53] - Extracting Waveshare prices

## [16] ASSISTANT

Page reads returned scripts, not prices. Extracting the price fields directly.

*(tools used:)*
- `bash`  [command -v curl || echo NOCURL; curl -s -m 15 -o /dev/null -w "example.com=%{http_code}\] - Diagnosing network access
- `bash`  [curl -sL --compressed -m 30 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/53] - Inspecting Amazon page content
- `eval` - Amazon prices

## [17] ASSISTANT

Amazon works - got `priceAmount":62.39`. Pulling all the listings systematically.

*(tools used:)*
- `eval` - Amazon buybox prices

## [18] ASSISTANT

`first=` isn't the buy-box - need the displayed price and the listing title to avoid mixing variants.

*(tools used:)*
- `eval` - Waveshare and Luckfox prices

## [19] ASSISTANT

Amazon: board **$62.39**, camera **$15.99**. Now the comparator prices.

*(tools used:)*
- `eval` - Verify listing identity and Luckfox prices

## [20] ASSISTANT

Waveshare direct is $50.99 / $8.99. Confirming the Amazon board is the same SKU and getting Luckfox's direct board price.

*(tools used:)*
- `bash`  [rm -f amz1.html && ls] - Removing throwaway scratch file

## [21] ASSISTANT

Prices pulled live from each vendor just now.

#### Verdict: Amazon is **~$18 more** on the two items that actually differ (~=31%), before shipping

| Item | Amazon | Waveshare direct | Luckfox direct (floor) |
|---|---|---|---|
| Luckfox Pico Ultra W (RV1106, WiFi 6, 8 GB eMMC) | **$62.39** [B0D8T54XJR](https://www.amazon.com/dp/B0D8T54XJR) | **$50.99** [sku 26790](https://www.waveshare.com/luckfox-pico-ultra.htm?sku=26790) | ~$41.99-50.99 ([Ultra B $41.99](https://www.luckfox.com/)) |
| SC3336 3 MP Camera (B) | **$15.99** [B0CJM7S6F6](https://www.amazon.com/dp/B0CJM7S6F6) | **$8.99** [direct](https://www.waveshare.com/sc3336-3mp-camera-b.htm) | **$8.99** |
| **Subtotal** | **$78.38** | **$59.98** | **~$50.98** |
| microSD 32 GB *(est.)* | ~$9 | ~$9 | - |
| CH340 USB-TTL *(est.)* | ~$9 | ~$7 | - |
| 5 V supply *(est.)* | ~$8 | ~$8 | - |
| **Cart total** | **~$104** | **~$84** | 3 stores, not one cart |

**Per-item markup:** board +$11.40 (+22%), camera +$7.00 (**+78%**). Commodity items are roughly a wash, so the whole Tier A cart runs **~$20 more on Amazon**.

#### Three things that change the answer

1. **Shipping can erase it.** Waveshare ships from China; a $10-15 shipping charge leaves Amazon cheaper *and* two days faster with Prime. `[INFERENCE]` - I didn't quote shipping to your address; it's weight/region-dependent at checkout.
2. **Amazon's SKU naming doesn't match.** B0D8T54XJR is titled "Luckfox Pico **Ultra Micro W**", not "Ultra W" - same RV1106 + onboard WiFi class, but confirm the variant ("Onboard WiFi 6", 8 GB eMMC) before ordering. Amazon also carries three other RV1106 listings at **$74.99** ([B0D6G7Z2BQ](https://www.amazon.com/dp/B0D6G7Z2BQ)), **$87.99** ([B0DB283LHG](https://www.amazon.com/dp/B0DB283LHG)) and **$91.99** ([B0DB23B79S](https://www.amazon.com/dp/B0DB23B79S)) - picking the wrong one can double the delta.
3. **Waveshare's own Newegg storefront sits between the two:** [$67.19](https://www.newegg.com/lenovo-14-0-8gb-memory-gray/p/1TS-000E-1E5X4?Item=3SIC4CTKX40153) for the WiFi board.

**Bottom line:** specialty silicon carries the markup (78% on the camera, 22% on the board); commodity parts don't. If you can tolerate a China-ship board+camera order, buy those two from Waveshare or Luckfox and the rest on Amazon - that combination beats either single vendor by roughly **$18-20**. Prices move; re-check before checkout.

## [8] USER

is luckfox the smallest form factor?

*(tools used:)*
- `web_search`  [Luckfox Pico Ultra W board dimensions mm size outline] - Checking Luckfox Ultra dimensions
- `web_search`  [Luckfox Pico Mini dimensions mm Luckfox Pico Zero W size smallest board] - Checking Luckfox small boards
- `web_search`  [Luckfox Core1106 core board dimensions mm castellated size RV1106] - Checking Core1106 module size
- `web_search`  [smallest 2K H.265 wifi IP camera module 38x38 mm RV1106 Ingenic T31 size] - Checking tiny IP camera modules

## [22] ASSISTANT

Checking actual dimensions - no point guessing.

*(tools used:)*
- `eval` - Board dimensions
- `web_search`  [38x38mm IP camera module wifi H.265 board size Ingenic T31 openipc air unit dimensions m] - Checking tiny camera module sizes

## [23] ASSISTANT

Luckfox Ultra is 50x50 mm - bigger than I implied. Pulling the small-board dimensions.

*(tools used:)*
- `eval` - Small board dimensions
- `web_search`  ["Luckfox Pico Zero" dimensions mm size RV1106G3 wireless board review] - Checking Pico Zero dimensions
- `web_search`  [RV1106 system on module smallest dimensions mm SOM camera module wifi 2K] - Checking RV1106 SoM size

## [24] ASSISTANT

.

*(tools used:)*
- `eval` - Luckfox dimensions retry

## [25] ASSISTANT

Core1106 SoM = 30x30 mm confirmed. My earlier regex missed Luckfox's `(mm)` format - retrying.

## [26] ASSISTANT

**No - and the board in your BOM is the biggest one Luckfox sells.**

Luckfox Pico **Ultra** is **50x50 mm** ([Electronics-Lab](https://www.electronics-lab.com/luckfox-pico-ultra), [CNX](https://www.cnx-software.com/2024/06/21/luckfox-pico-ultra-micro-development-board-features-mipi-csi-wifi-6-ethernet-poe-gpio-headers)). To scale:

```svg
<svg viewBox="0 0 430 175" xmlns="http://www.w3.org/2000/svg">
  <g font-size="11" fill="currentColor" text-anchor="middle">
    <rect x="10" y="40" width="100" height="100" fill="none" stroke="var(--muted)" stroke-width="1.5"/>
    <text x="60" y="32">Ultra W 50x50</text>
    <text x="60" y="158" fill="var(--accent)">WiFi 6 - RJ45 - PoE</text>

    <rect x="130" y="64" width="76" height="76" fill="none" stroke="var(--muted)" stroke-width="1.5"/>
    <text x="168" y="56">T31 IPC 38x38</text>
    <text x="168" y="158" fill="var(--accent)">WiFi opt.</text>

    <rect x="226" y="80" width="60" height="60" fill="none" stroke="var(--muted)" stroke-width="1.5"/>
    <text x="256" y="72">Core1106 30x30</text>
    <text x="256" y="158" fill="var(--accent)">SoM, carrier needed</text>

    <rect x="306" y="98" width="56" height="42" fill="none" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="4 4"/>
    <text x="334" y="90">Mini 28x21</text>
    <text x="334" y="158" fill="var(--error)">no WiFi</text>
  </g>
</svg>
```

| Board | Size | WiFi | 2K encode | Cost |
|---|---|---|---|---|
| **Luckfox Pico Ultra W** (your BOM) | **50x50 mm** | WiFi 6 onboard | 5 MP@30 | $50.99 |
| Ingenic T31 / SigmaStar IPC module | **38x38 mm** | optional | 2-4 MP | $15-30 |
| **Luckfox Core1106** SoM | **30x30 mm** | optional variant | 5 MP@30 | $27-49 |
| **Luckfox Pico Mini** (RV1103) | **28x21 mm** | **none** | 4 MP class | $11.99 |
| Luckfox Pico Zero W | *not published* | WiFi onboard | 5 MP@30 | $31.99 |

#### The three things that actually decide "smallest"

1. **Luckfox's smallest board has no WiFi.** The 28x21 mm Pico Mini is RV1103 (no wireless). Add a USB WiFi dongle and you've added more volume than you saved - a 38x38 mm integrated IPC module with WiFi wins the *assembled* envelope.
2. **Connectors dominate, not the PCB.** The Ultra's RJ45 jack, PoE header, GPIO rows, speaker header and audio jack are most of its bulk - and for your build you want **none** of them. Dropping Ethernet/PoE/GPIO is free size and thickness. That makes **Luckfox Pico Zero W** (RV1106G3, WiFi, 4-lane MIPI CSI, USB-C, no RJ45/PoE/GPIO) the right shape for this job, not the Ultra.
3. **Footprint  system size.** Board + lens barrel (+15-20 mm depth) + antenna + CSI cable is the real envelope. A 28x21 mm board with a USB dongle and cabling is often *larger in hand* than a 38x38 mm module that has the radio and connector onboard.

#### Floor and recommendation

- **Absolute floor:** a custom 2-layer PCB with the RV1106 (QFN package), an SC3336/MIS5001 on CSI, and an SDIO WiFi module. `[INFERENCE]` - size then driven by the camera connector and antenna keep-out, not the SoC.
- **No design work, smallest sensible:** **Pico Zero W**, or **Core1106 SoM** if you'll make a carrier. Both are smaller than the Ultra and lack exactly the connectors you don't need.
- **Verify before ordering:** Luckfox publishes Pico Zero's outline only as an image, so I could not confirm its millimetres - confirm on the product page. Its 4-lane CSI is a bonus over the Ultra's 2-lane.

Net: swap the Ultra for a Pico Zero W and you shrink the board while losing only connectors you weren't going to use.

## [9] USER

what abouyt htis https://www.amazon.com/Seeed-Studio-ESP32-C5-Development-Dual-Band/dp/B0GWQ8K461/ref=sr_1_3

*(tools used:)*
- `eval` - Fetching ESP32-C5 listing
- `web_search`  [ESP32-C5 datasheet camera interface MIPI CSI LCD hardware H.264 encoder video capability] - Checking ESP32-C5 video capability

## [27] ASSISTANT

That's an ESP32-C5 - a *connectivity* MCU. Checking what it actually has for video before I answer.

*(tools used:)*
- `eval` - Checking C5 peripherals

## [28] ASSISTANT

**Wrong chip for this job - it has no video path at all.**

That's the **Seeed XIAO ESP32-C5**, $12.99, 21x17.8 mm, ESP32-C5 (240 MHz RISC-V, 8 MB PSRAM + 8 MB flash), dual-band WiFi 6, BLE 5, Zigbee/Thread, 11 GPIO. It's an excellent *connectivity* MCU. It cannot see.

Evidence: I grepped the [ESP32-C5-MINI-1 datasheet](https://documentation.espressif.com/esp32-c5-mini-1_mini-1u_datasheet_en.html) for `camera`, `CSI`, `DVP`, `JPEG`, `H.264`, `encoder`, `LCD interface` - **zero hits on all seven.** No camera controller, no display interface, no JPEG or video codec block. Not "slow at 2K" - structurally unable to capture a frame.

| Chip | Video input | Encode | Ceiling |
|---|---|---|---|
| **ESP32-C5** | **none** | none | **no video** |
| ESP32-S3 | DVP camera + LCD | software JPEG | ~1080p, low fps |
| ESP32-P4 | MIPI CSI + HW H.264 | hardware | 1080p30 |

ESP32-P4 already only reaches 1080p - and the C5 sits *below* the S3 in this hierarchy because it dropped the video peripherals entirely in favour of dual-band radio.

#### Where it would actually earn a place

- **As a control channel next to the video link.** PTZ, triggers, sync pulses, OSD metadata - a $12.99 XIAO riding alongside the RV1106 video stream. Real use, different job.
- **Its dual-band is a genuine feature your Luckfox board lacks.** Waveshare's own spec says the Pico Ultra W is **2.4 GHz WiFi 6 only** - the C5 does 2.4 *and* 5 GHz. That's the one axis where the C5 is better. But it's irrelevant here: you can't put a video stream on a chip with no encoder.

#### Bottom line

Buying it moves you **zero** distance toward 2K -> OBS. It's the cheapest part in this whole thread and the only one that can't contribute to the goal. If "small + Seeed + camera" is the appeal, the board you're thinking of is the **XIAO ESP32-S3 Sense** (camera, mic, SD, same 21x17.8 mm footprint) - but that's 1080p JPEG-class, still not 2K, still not an OBS-quality source.

Keep the ESP32 line for what it's good at: 1080p at best (P4), control and telemetry (C5). Video stays on the RV1106.

## [10] USER

echo back to me my goal as you understand it

## [29] ASSISTANT

#### Goal as I understand it

Get a **small, low-power wireless camera** that streams live video **into OBS** over WiFi - no capture card, no cable - and keep it small and cheap enough to be practical. You started at **4K** and explicitly traded down to **2K** to buy back size and power.

##### Hard constraints (from you)
- **Wireless** - the whole point.
- **Small form factor** - you pushed back specifically on this, asking whether Luckfox is the smallest.
- **Low power** - the reason 4K was dropped.
- **Destination is OBS** - a live source you can add as an input/scene item.
- **Cost-aware** - you've asked for vendor consolidation and price deltas.

##### Soft constraints (my framing, not yet yours)
- Latency target: I proposed a **<=300 ms glass-to-glass** gate. You never confirmed a number.
- Budget: never stated.
- Quality bar: never stated beyond "2K".

##### The plan we've converged on
**RV1106 IP-camera SoC is the right class** - it encodes 5 MP@30 (covers 2K) at ~1 W, which no SBC matches. Concretely: Luckfox board + SC3336 3MP or MIS5001 5MP camera -> **hardware H.265** -> **RTSP/SRT** -> **MediaMTX** -> **OBS Media Source** (never OBS as SRT listener; WHIP is output-only in OBS).

Escalation path if that fails: OpenIPC/SSC338Q air unit (~30 ms class, 3-4x price and power).

Escalation we rejected: RK3588 SBC (5-12 W, only path to real 4K60), and every pure MCU - ESP32-P4 caps at 1080p, ESP32-C5 has **no video path at all**.

##### What I still don't know - and it changes the answer
1. **What is the actual video source?** A bare MIPI camera sensor, or **HDMI out of a camera you already own**? I've asked twice and never got an answer. If it's HDMI, the whole build changes - you need HDMI-in, and no cheap board has it.
2. **Does it need to be battery-powered and moving** (on a person, drone, rig), or can it be a static box on a shelf?
3. **Range and RF environment** - same room, or across a building?
4. **Latency ceiling** - is 300 ms fine, or do you need <150 ms?
5. **Audio** - needed or not?
6. **Budget cap.**

Nothing has been bought yet. If any of my reading above is wrong, correct it now - items 1 and 2 in particular could still redirect the entire build.

## [11] USER

color sensor to capture a 7 foot pool table from a light a standard height above the table for facebook and youtube audience to watch in realtime

*(tools used:)*
- `web_search`  [Facebook Live maximum resolution 1080p recommended bitrate live video encoder settings] - Checking Facebook Live limits
- `web_search`  [YouTube Live recommended bitrate 1440p 2160p 4K 60fps streaming requirements] - Checking YouTube Live limits
- `web_search`  [7 foot pool table playing surface dimensions inches 78 x 39 regulation] - Checking pool table dimensions
- `web_search`  [pool table light height above playing surface standard inches billiard lamp mounting] - Checking billiard light height

## [30] ASSISTANT

That reframes everything. This is a **fixed overhead broadcast rig**, not a body-worn camera - which changes the optics math, the power situation, and makes latency nearly irrelevant. Grounding the numbers.

## [12] USER

same room

## [31] ASSISTANT

"Same room" kills the RF risk entirely and, combined with the rest, reshapes the problem. My reading: the camera hangs **on the pool light fixture**, ~31-36" above the cloth, looking down.

#### What just changed

| Old assumption | New reality |
|---|---|
| Latency budget ~300 ms | **Irrelevant.** FB/YT add seconds of platform latency - "real-time" to an audience means 5-30 s end-to-end regardless. Even the ~1 s Luckfox RTSP path is fine. |
| Battery / low power | **Moot.** The fixture has mains power. Low power now only buys you small size and no heatsink. |
| RF is the risk | **Gone.** Same room, OBS PC on Ethernet. |
| Resolution is the hard part | **Wrong.** Optics are. |

#### The real constraint: field of view

7-foot table playing surface = **78" x 39"** ([WPA-style](https://solvetutor.com/pool-table-room-size)), standard light height = **31-36"** above the cloth ([Blatt](https://blattbilliards.com/blogs/news/how-bright-should-the-lighting-be-over-a-pool-table)). Camera co-located with the light:

| Camera height above cloth | HFOV needed | VFOV needed | **Min diagonal FOV** |
|---|---|---|---|
| 31" (low end of standard) | 103deg | 71deg | **~111deg** |
| 36" (high end of standard) | 95deg | 63deg | **~102deg** |
| 48" | 78deg | 49deg | ~86deg |
| 60" (ceiling) | 66deg | 40deg | ~73deg |

**Headline: your default camera is too narrow.** The SC3336 is specified at **98.3deg FOV** - at or below the ~102deg minimum at 36", and clearly short at 31". Either verify whether that figure is horizontal or diagonal (it's listed ambiguously), or plan on a **2.8 mm or wider M12 lens** on an M12-mount sensor module. The MIS5001 is sold as "wide-angle" but its DFOV isn't published in anything I've found - check before ordering.

**Mounting higher is the cheat code.** At 60" the requirement drops to a normal ~73deg lens and the corner distortion all but disappears. If the camera can hang from the ceiling *beside* the light rather than on it, this gets dramatically easier and cheaper.

#### Platform ceilings - this decides your resolution

| | Max | Practical target |
|---|---|---|
| **Facebook Live** | **1080p** ([caps at 1080p](https://gyre.pro/blog/hd-vs-sd-vs-k-streaming-what-to-consider-when-choosing)); FB wants a 1080p envelope, 3-6 Mbps @30fps | 1080p30, ~6 Mbps |
| **YouTube Live** | up to 4K60 | 1440p60 ~=24 Mbps, 1440p30 ~=15 Mbps, 1080p60 ~=12 Mbps |

**2K pays off only on YouTube.** Facebook will downscale 1440p to 1080p. If both platforms are required, **1080p is the common denominator** and the "drop to 2K" decision buys you nothing on FB - it only helps YT.

For pool specifically, I'd weigh **1080p60 over 1440p30**: break shots are the only fast motion, and 60 fps tracks the balls far better. The RV1106 does either.

#### Revised pick

1. **Best fit (camera stays on the light):** RV1106 board + **an M12-mount sensor with a lens you choose** (~2.8 mm or wider). You need lens freedom and a small body that tucks into a fixture - off-the-shelf IP cameras are bulky and mostly ~100-110deg with no lens choice.
2. **Best if it can hang higher:** any 2K WiFi IP camera (Reolink/Tapo class) with RTSP -> OBS Media Source. Mains power, PoE option, proper optics, zero build. Same-room WiFi makes it trivially reliable.
3. **Dead:** ESP32-C5 (no video), and 4K anything - FB can't use it and the optics at 36" get worse, not better.

#### Four traps specific to this setup

- **LED flicker banding.** Pool lights are often LED now. Rolling-shutter sensors band badly under PWM drivers. Set anti-flicker to your mains frequency (60 Hz US) or confirm the fixture uses flicker-free drivers - otherwise you'll ship a stream with rolling dark bars.
- **The lamp is in your exposure.** With the camera on the fixture, the light source dominates the frame and the cloth blows out. Shield the lens or bias exposure for the cloth.
- **Corner stretch.** At 50deg off-axis, balls near the table corners look stretched. A 110deg lens covering a 7-footer at 36" is a *very* wide look - acceptable for overhead pool, but not pretty.
- **OBS output settings, not camera settings, drive the platform.** Camera -> RTSP at 8-15 Mbps into OBS; OBS then encodes per platform. Use a **2 s keyframe interval** (both FB and YT expect <=2 s) and 1080p60 ~=6-9 Mbps for FB.

#### Still open

- Confirm **on-fixture vs ceiling** - that single answer changes the lens from "wide M12" to "whatever it came with".
- Is **Facebook mandatory**, or is YouTube the primary? That decides whether you need 2K at all.
- Exact fixture model / can you tap its power, and how much room is inside the shade.

Answer those two and I'll spec the exact board, lens and OBS settings.

## [13] USER

audio not required

*(tools used:)*
- `web_search`  [Facebook Live stream without audio video only encoder no microphone allowed requirements] - Checking video-only live streams
- `web_search`  [YouTube live stream video only no audio track encoder settings required] - Checking YouTube Live audio requirement

## [32] ASSISTANT

Noted - and it removes a real failure mode, but with one correction you need before you build.

#### Good news: no camera-side audio

The RV1106 path gets simpler. There's a [known Luckfox RV1103 audio-over-RTSP problem](https://github.com/LuckfoxTECH/luckfox-pico/issues/263) you'd otherwise have had to solve - now irrelevant. No mic, no audio codec, no sync work. Nothing changes in the BOM.

#### Correction: YouTube is fine, **Facebook is not**

- **YouTube:** audio is optional. Video-only ingest works.
- **Facebook:** their ingest spec says otherwise. The [Live Video API reference](https://developers.secure.facebook.com/docs/live-video-api/reference) states live video **"must: Include both audio and video data"** and must be **H264/AAC**, and Meta's [requirements page](https://www.facebook.com/business/help/162540111070395) repeats "H264 encoded video and AAC encoded audio only."

So "audio not required" is true for YouTube and **risky-to-false for Facebook**. The fix costs nothing:

- **Mux a silent AAC track.** In OBS, keep one audio source enabled so an AAC track is always emitted (a muted input is enough); if you're encoding with ffmpeg, add `-f lavfi -i anullsrc=r=48000:cl=stereo -c:a aac`.
- **No hardware.** Zeros hardware cost, zero camera change. It only exists to satisfy FB's container requirement.

Worth verifying your own FB ingest once before relying on it - documented requirements and observed behaviour don't always match.

#### Spec impact

None on purchase. One line of OBS configuration when you go live. The camera stays a pure video source at 8-15 Mbps into OBS.

*(Aside, once: pool viewers notice the ball clack and pocket thuds. A cheap USB mic into the OBS PC would add it later, decoupled from the camera - but that's a separate decision, not a blocker.)*

#### Still blocking the final spec

1. **On the fixture, or ceiling-mounted?** This alone decides whether you need a wide M12 lens (~102-111deg DFOV) or the stock one.
2. **Is Facebook mandatory, or YouTube-primary?** Decides whether 2K is worth anything at all.

Those two answers and I'll write the exact board, lens, and OBS output settings.

## [14] USER

hangin from the shop light like fixture. FB is first.

*(tools used:)*
- `web_search`  [Luckfox RV1106 supported camera sensors list SDK SC3336 MIS5001 IMX415 driver] - Checking Luckfox supported sensors
- `web_search`  [MIPI CSI camera module M12 lens mount interchangeable wide angle 2.8mm 1/2.8 sensor RV11] - Checking M12 lens modules
- `web_search`  [SC3336 3MP camera module FOV 98.3 degree diagonal or horizontal field of view lens] - Checking SC3336 FOV spec

## [33] ASSISTANT

Light-fixture mount + Facebook-primary settles it: **1080p is the target, and the lens becomes the entire engineering problem.** Verifying the lens/sensor constraint before I spec it.

## [34] ASSISTANT

Decisive finding - I'll lead with it.

#### The stock camera cannot shoot your table

The Luckfox SC3336 module is a **3.95 mm** lens on a 1/2.8" sensor ([spec](https://www.robotics.org.za/W25553)). Working that through a 1/2.8" (5.6 mm-wide active area) sensor:

- HFOV ~= **70deg**, DFOV ~= 78deg
- At 36" above the cloth that frames **50.4" of table length** - you'd see **65% of a 78" table**

The "98.3deg FOV" in Waveshare's listing is **inconsistent** with the listed 3.95 mm focal length - those two numbers can't both be right for a 1/2.8" sensor. Don't trust either; compute from focal length.

#### Locked decisions

| Decision | Value | Why |
|---|---|---|
| Resolution | **1080p** | FB caps at 1080p. 2K buys nothing for your primary platform. |
| Frame rate | 60 fps if you have the headroom, else 30 | Break shots are the only fast motion |
| SoC | **RV1106** | HW H.264 + ISP + MIPI CSI + WiFi in one chip. ESP32-P4 has **no WiFi** (it pairs with a C6/C5), and the C5 has no video |
| Audio | camera: none / stream: silent AAC | FB's ingest requires an audio track |

#### Lens selection - the whole problem

Required FOV from camera height `h` above the cloth (table = 78" x 39"):

| `h` | HFOV needed | VFOV needed | **Lens on 1/2.8"** |
|---|---|---|---|
| 31" (low end of standard) | 103deg | 71deg | **~=2.2 mm** |
| 36" (high end of standard) | 95deg | 63deg | **~=2.6 mm** |
| 48" | 78deg | 49deg | ~=3.4 mm |
| 60" (hanging at ceiling) | 66deg | 40deg | ~=4.3 mm  *the stock lens* |

**Buy a 2.2-2.6 mm M12 lens** (formula: `f = (sensor_width/2) / tan(HFOV/2)`, using width - not the marketed diagonal FOV). Two constraints:

- **Swap the lens, not the sensor.** The RV1106 ISP tuning is sensor-specific; only SC3336 / MIS5001 / IMX415 / ISG1321 have drivers. An arbitrary M12 module won't work.
- **Verify the module is M12-threaded** before ordering. If the stock lens is glued, get an M12-mount module carrying a supported sensor (IMX415 is 1/2.8" too, so the same lens gives the same view).
- Accept barrel distortion - a 2.2 mm lens on a 7-footer at 36" bows the rails. `ffmpeg lenscorrection` or the obs-shaderfilter plugin can dewarp if it bothers you.

#### Final BOM

| Qty | Part | Note |
|---|---|---|
| 1 | Luckfox Pico Zero W (RV1106G3, WiFi, 4-lane CSI) | Confirm outline on the product page; or Pico Ultra W if you want the better-documented board |
| 1 | MIPI CSI module, supported sensor, **M12 mount** | SC3336 is cheapest |
| 1 | **M12 lens 2.2-2.6 mm** | The critical part - this is what makes or breaks it |
| 1 | 5 V supply / USB-C, tapped at the fixture | Mains is already at the light |
| 1 | Mount bracket + light shield | Keep the lamp out of frame and off the lens |
| - | OBS + MediaMTX | Free |

#### OBS -> Facebook settings

- **1920x1080**, 60 fps (or 30)
- **Bitrate 3,000-6,000 kbps** @30 - up to ~9,000 @60 ([FB sits in a narrow 1080p envelope](https://streamneo.com/blog/what-bitrate-does-facebook-live-actually-accept))
- **Keyframe 2 s**
- **H.264 High, Level 4.1** @30 fps / **4.2** @60
- **Add one muted audio source** so OBS emits the AAC track FB's ingest requires ([video must include audio](https://developers.secure.facebook.com/docs/live-video-api/reference))
- Camera -> MediaMTX -> OBS Media Source at 8-12 Mbps; OBS does the platform encode

#### Two setup traps

- **LED/fluorescent flicker.** A shop light is almost certainly a switched driver. Rolling-shutter sensors band under PWM - set anti-flicker to 60 Hz and check for rolling bars across the cloth before you commit.
- **The lamp is in your exposure.** Camera on the fixture means the light source dominates the frame. Bias exposure for the cloth, shield the lens from the tubes.

*(If you ever move the camera to the ceiling above the fixture, `h` goes 60"+, the lens becomes a stock 4.3 mm, and the distortion disappears. Worth knowing you have that escape hatch.)*

#### Do this before buying

Tape-measure the actual height from cloth to where the camera will sit. That single number picks the lens - 31" needs 2.2 mm, 36" needs 2.6 mm. Get it wrong by 5" and you either lose the corner pockets or shoot half the table.

## [15] USER

what is the standard height range for classic pool table lights

## [35] ASSISTANT

**31-36 inches above the playing surface**, measured from the **bottom of the fixture** (bottom of the shade, not the canopy or chain anchor) - roughly **60-66 inches above the floor**.

| Source | Stated height |
|---|---|
| [Billight Pool](https://www.billightpool.com/post/how-high-to-hang-a-pool-table-light) | 31-36" above playing surface / 60-66" above floor |
| [Blatt Billiards](https://blattbilliards.com/blogs/news/how-bright-should-the-lighting-be-over-a-pool-table) | 31-36", measured from the bottom of the fixture |
| [Blatt (product guide)](https://blattbilliards.com/collections/pool-table-lights) | "Hang the bottom of the shade roughly 32-36 inches above the cloth" |

Notes on the convention:
- Measured **surface-to-fixture**, not floor-to-fixture - table beds sit 29.25-31" off the floor, which is where the 60-66" figure comes from.
- **Lower bound** is set by shadow control: below ~31" you get glare and hot spots on the cloth.
- **Upper bound** is set by coverage: above ~36" the light no longer spans the table evenly and shadows creep back in.
- Taller tables and rooms trend toward the top of the range; the "classic" multi-shade billiard lamp on chains is the fixture this range was written for.

#### Why this matters for your build

"Hanging **from** the fixture" means the camera sits at or **below** the bottom-of-shade line - so your working height is likely **<=31"**, not the flattering 36".

At 31" the lens math gets worse:

| `h` | Required HFOV | **Lens on 1/2.8"** |
|---|---|---|
| 31" | 103deg | ~=2.2 mm |
| 26" (camera slung 5" below the shade) | 113deg | **~=1.85 mm** |
| 36" | 95deg | ~=2.6 mm |

So plan for **<=2.2 mm, and possibly ~1.9 mm** - a genuinely fisheye-class lens, with heavy rail distortion that you'd want to dewarp in OBS.

That pushes one decision forward: **mount the camera level with the shades or at the fixture's top**, not dangling below it. Every inch you claw back up shortens the lens you need and cuts the distortion. If the fixture body can host the camera at its top edge, you're at 36"+ and back to a comfortable 2.6 mm.

## [16] USER

assume 34

*(tools used:)*
- `eval` - SC3336 lens variants

## [36] ASSISTANT

h = 34" is workable. Let me nail the exact lens - and check whether the two SC3336 variants differ, because the "(B)" module claims 98.3deg FOV.

*(tools used:)*
- `eval` - MIS5001 spec and h=34 geometry

## [37] ASSISTANT

Authoritative: **(A) and (B) are identical - 3.95 mm, F2.0, 98.3deg diagonal, <33% distortion.** Checking the one remaining wide colour option.

## [38] ASSISTANT

h = 34" gives clean targets, and Luckfox's own wiki settles the module question.

#### What 34" requires

At 34" above the cloth, framing the full 78" x 39" surface:

| Requirement | Value |
|---|---|
| Horizontal FOV | **97.8deg** |
| Vertical FOV | 59.7deg |
| Diagonal FOV | **105.5deg** |
| Lens (1/2.8", rectilinear) | **~=2.4 mm** |

#### No stock Luckfox module reaches it

From the [Luckfox camera wiki](https://wiki.luckfox.com/Cameras/) - these are their own published figures:

| Module | Colour | HFOV | Covers at 34" | Verdict |
|---|---|---|---|---|
| **SC3336 3MP** | yes | ~90.5deg | **68.6"** (88%) | Closest - and only **$8.99** |
| MIS5001 5MP, 2.88 mm "distortion-free" | yes | 87.5deg | 65.1" (83%) | Short |
| IMX415-98 (8MP) | yes | 84deg | 61.2" (78%) | Short |
| MIS5001 5MP, 4.15 mm | yes | 78.2deg | 55.3" (71%) | Way short |
| *required* | - | *97.8deg* | *78"* | - |

**(A) and (B) SC3336 variants are identical** - 3.95 mm, F2.0, 98.3deg diagonal, <33% distortion, manual focus. No wide version hiding in the lineup.

So at 34" you would lose **the corner pockets** - exactly where the games are won.

#### Datasheet warning (correcting my earlier advice)

Luckfox's focal lengths and their FOV figures **contradict each other**. 3.95 mm on a 6.43 mm-diagonal sensor geometrically yields ~78deg diagonal, yet they publish 98deg. Their HFOV/VFOV columns aren't internally consistent with 16:9 either. **Do not plan off the datasheet numbers** - the 5-minute test at the real height is definitive.

#### The real lever is height, not lens

The stock 3.95 mm lens covers **1.41 inches of table per inch of height**:

- **55.2"** -> covers exactly 78"
- **60.9"** -> covers 78" with 10% margin

**Hang the camera at ~60" and the $8.99 stock camera shoots the whole table with no lens hunting.** At 34" you'd need a ~2.4 mm lens - essentially a fisheye, with 40-60% barrel distortion that bows the rails and would need lossy dewarping in OBS. At 34" a clean, rectilinear full-table shot on a 16:9 sensor isn't really achievable.

#### Recommendation

1. **Buy the SC3336 ($8.99).** Cheapest module, widest stock lens, manual focus - it's also your cheapest test article.
2. **Mount it and look.** At 34" expect ~88% coverage. If the corner pockets are clipped by a few inches, you have two fixes, in order of preference: raise the camera (free, and improves distortion), or source a 2.2-2.4 mm M12 lens.
3. **Before ordering a lens**, verify the SC3336's lens is M12-threaded rather than glued - "manual focus" suggests threaded, but confirm on arrival.

If the fixture physically allows the camera **above** the shades rather than below them, take it. Every inch up is free image quality.

## [17] USER

is there a fisheye wide angle alternative?how does the new xio sense camera do?

*(tools used:)*
- `web_search`  [M12 fisheye lens 1.8mm 180 degree 1/2.8" sensor MIPI CSI wide angle module] - Checking fisheye M12 options
- `web_search`  [Luckfox camera fisheye 180 wide angle RV1106 option SC3336 lens swap M12 thread] - Checking Luckfox fisheye option
- `web_search`  [Seeed XIAO Sense camera 2026 new OV5640 wide angle field of view specification] - Checking XIAO Sense camera
- `web_search`  [XIAO ESP32S3 Sense camera MJPEG stream fps resolution quality RTSP not supported] - Checking XIAO Sense streaming quality

## [39] ASSISTANT

Two separate questions - checking both.

*(tools used:)*
- `read`  [https://files.seeedstudio.com/Bazaar/product_pdf/114993115.pdf] - Reading Seeed OV5640 datasheet
- `web_search`  [XIAO ESP32S3 Sense camera field of view degrees OV2640 OV3660 OV5640 FOV specification] - Checking XIAO Sense camera FOV

## [40] ASSISTANT

Fisheye route is real and cheap. Checking the Seeed camera's actual FOV before judging it.

## [41] ASSISTANT

#### 1. Fisheye: yes - and it's the cheap fix

The right choice is a **mild fisheye, not a 180deg**. A 2.2 mm M12 fisheye delivers roughly **121deg H x 76deg V (146deg D)** ([Commonlands, measured on a 6.4 mm-class sensor](https://commonlands.com/pages/image-sensors/mt9v034)) - comfortably past the **97.8deg** you need at 34", with the extra ~23deg serving as dewarp headroom rather than wasted pixels.

| Lens | Format | HFOV | Coverage at 34" | Note |
|---|---|---|---|---|
| **2.2 mm M12 fisheye** | 1/3"-1/2.5" | ~121deg | **~120"** (154% of table) | **Sweet spot** - mild distortion, dewarpable |
| 1.85 mm M12 fisheye | 1/1.8" | 185deg | over-covers | High quality, pricier; wastes pixels |
| 1.7 mm M12 fisheye | 1/2.5" | 180deg | over-covers | [Pi Hut ~$25](https://thepihut.com/products/m12-lens-180-degree-fisheye-1-2-5-optical-format-1-7mm-focal-length) |
| Arducam M12 lens set | 1/2.7-1/2.9" | 20deg-180deg kit | pick a FL | [Includes fisheye + holder](https://www.arducam.com/arducam-m12-lens-set-arducam-lens-for-usb-camera1-2-7-1-2-8-1-2-9-telephoto-macro-wide-angle-fisheye-lens-kit-20-180-with-m12-lens-holder-and-cleaning-cloth-optical-all-in-one.html) - good if you want to experiment |

**Four gotchas before you buy a lens:**

1. **M12 thread must exist on the module.** Luckfox's SC3336 is listed as "manual focus," which implies a threaded barrel - but confirm before ordering. If it's glued, source a bare 1/2.8" M12 sensor board with an RV1106-supported sensor (SC3336/IMX415).
2. **IR-cut filter location.** If the IR-cut sits *in* the stock lens, swapping it off gives you warm/green colour shift on the cloth. Check where the filter lives; many lenses have none.
3. **Image circle >= sensor diagonal.** Buy a lens rated 1/2.7"-1/2.5" for a 1/2.8" sensor, or you'll vignette the corners - where the pockets are.
4. **The real cost is resolution.** A 121deg lens puts the 78" table across only ~65% of the frame. On a 1080p output that's **~1,250 px across the table -> a 2.25" ball renders ~36 px**. Fill-the-frame would give ~55 px. Dewarp-and-crop recovers most of it, at the price of corner softness. A 180deg lens makes this much worse.

There's no fisheye in Luckfox's own line - the widest thing they sell is the mono ISG1321 at 95.5deg, which is useless to you on colour.

#### 2. XIAO Sense camera (OV5640): no, and it isn't close

The current module is the **OV5640 for XIAO ESP32S3 Sense - $11.99, 1/4" sensor, 1.4 um pixels, 2592x1944, autofocus** ([datasheet](https://files.seeedstudio.com/Bazaar/product_pdf/114993115.pdf)).

**The datasheet does not publish a field of view** - I checked. Typical for this lens class is ~65-72deg, i.e. **~44" of your 78" table at 34" (57%)**. Worse than every stock Luckfox module.

But FOV isn't what kills it - **the platform does**:

| | XIAO ESP32-S3 Sense | RV1106 |
|---|---|---|
| Video encoder | **none** - sensor-side JPEG only | **hardware H.264/H.265** |
| Compression | intraframe JPEG | interframe |
| 1080p30 bitrate | ~36-72 Mbps | 8-15 Mbps |
| Realistic WiFi throughput (2.4 GHz) | 10-20 Mbps | - |
| **Achievable 1080p** | **~4-6 fps** | 1080p60 |

A 1080p JPEG frame is 150-300 KB. At 30 fps that's 36-72 Mbps - two to four times what the ESP32-S3's radio can carry, with no interframe compression to help. The OV5640 itself does 1080p30 (sensor-side), but the board cannot ship it. Seeed's own forum threads land on the same wall: the 8-bit DVP interface plus web-server path is the bottleneck.

Add the 4:3 sensor against a 2:1 table, and 1.4 um pixels on a 1/4" sensor (worse low light than the SC3336's 1/2.8"), and it's the wrong tool on **four** axes.

It's a fine board for edge AI, stills, and low-res monitoring. It is not a broadcast source.

#### Bottom line

- **Buy the SC3336 ($8.99)** - cheapest, closest stock FOV, and the module to hang a lens on.
- **Add a 2.2 mm M12 fisheye** - solves 34" coverage with room to spare, ~$15-60.
- **Skip the XIAO Sense path entirely** for this build; no lens swap fixes a radio that can't carry 1080p30.

Still the strongest move available: if the fixture lets the camera sit **at or above the shades (~55-61")**, the stock 3.95 mm lens covers the table and you skip the fisheye, the distortion, and the dewarping altogether.

## [18] USER

what else do i need to make this truly wireless? power source recomendations for the sc3336? specific camera source? are all on amazon for quick delivery?

*(tools used:)*
- `eval` - Amazon sourcing check

## [42] ASSISTANT

Four questions - let me get the sourcing and power facts straight.

*(tools used:)*
- `eval` - Lens and pairing check

## [43] ASSISTANT

Board confirmed (RV1106 + onboard 2.4 GHz WiFi 6). Fixing the lens search and checking the camera/board pairing.

## [44] ASSISTANT

#### Short answer: yes - everything is on Amazon

| Item | Amazon | Price | Note |
|---|---|---|---|
| **Luckfox Pico Ultra (WiFi)** | [B0D8T54XJR](https://www.amazon.com/dp/B0D8T54XJR) | **$62.39** | Confirmed RV1106 + **onboard 2.4 GHz WiFi 6** + BT5.2. 8 GB eMMC |
| **SC3336 3MP Camera (B)** | [B0CJM7S6F6](https://www.amazon.com/dp/B0CJM7S6F6) | **$15.99** | Matched to the Ultra/Waveshare line |
| **M12 fisheye lens** | search "M12 fisheye" | ~$12-100 | Generic ones from ~$12; Arducam kits & IR-corrected ~$50-100 |
| **Always-on power bank** | Voltaic V50 13,400 mAh / 48 Wh USB-C PD | verify | See power section |
| USB-C cable, clamp, shield | - | ~$15 | - |

**No microSD needed** - the Ultra boots from its 8 GB eMMC. **No separate camera supply needed** - the SC3336 runs off the board's 3.3 V over the CSI connector (pins 19/20).

#### What else you need for "truly wireless"

Only **one wire remains: power.** Three ways to kill it:

| Option | Runtime | Wires | Verdict |
|---|---|---|---|
| **Battery bank on the fixture** | 15-24 h | **none** | Truly wireless |
| Tap the fixture's mains -> 5 V USB | unlimited | one short lead | Best if allowed; see gotcha |
| PoE module + Ethernet | unlimited | one cable | Not wireless, but bulletproof |

**The gotcha that will bite you:** a shop light is usually on a **wall switch**. Tap its power and the camera **dies every time someone turns the lights off**. Never tap a dimmed circuit - a dimmer will brown-out or destroy the 5 V supply.

#### Power recommendations

Budget for the board + camera:

| State | Draw | Source |
|---|---|---|
| Idle | **22 mA @ 5 V ~= 0.11 W** | [measured, Luckfox forum](https://forums.luckfox.com/viewtopic.php?t=1822) |
| Streaming (WiFi + HW H.264) | **~1.5-2.5 W** `[INFERENCE]` | estimate |

| Bank | Capacity | Runtime @ 2 W | 
|---|---|---|
| 10,000 mAh | ~37 Wh | ~12 h |
| **13,400 mAh (Voltaic V50)** | ~48 Wh | ~19 h |
| 20,000 mAh | ~74 Wh | ~30 h |

**Buy an "always-on" bank specifically.** Most power banks auto-shutoff below ~50-100 mA - and at **0.11 W idle your board sits far below that threshold**, so a normal bank will cut out on you. Voltaic markets explicitly for this (`V50`, `V75`); otherwise look for a bank with a **low-current mode** button.

Two more:
- **Don't strap Li-ion to the fixture.** Fluorescent/LED tubes run warm; heat plus a pouch cell in an enclosed shade is a bad combination.
- Bank -> USB-C into the board's Type-C port. That's it.

#### Specific camera source

**Buy the SC3336 3MP Camera (B).** Luckfox's own compatibility table lists **(B)** for the **Ultra** and **Mini A/B**, and **(A)** for the **Pro/Max** - they differ by FPC/connector, not optics (both are 3.95 mm, 98.3deg, <33% distortion). Match the variant to your board.

Sources, cheapest first:

| Vendor | Price |
|---|---|
| [Waveshare direct](https://www.waveshare.com/sc3336-3mp-camera-b.htm) | **$8.99** |
| [Luckfox direct](https://www.luckfox.com/EN-SC3336-3MP-Camera-B) | **$8.99** |
| Amazon (quick delivery) | $15.99 |

**Do not substitute:** the MIS5001 (HFOV 87.5deg) and IMX415-98 (HFOV 84deg) are both *narrower* than the SC3336's ~90.5deg - you'd be paying more for a worse view.

Then add the **2.2 mm M12 fisheye** to cover 78" from 34".

#### Order of operations

1. Buy the board + SC3336 (B) + fisheye lens + always-on bank. ~$100-130 all-in.
2. **Power it and point it down from 34" before buying anything else.** Confirm the four corner pockets are in frame and check for flicker banding under the actual fixture.
3. Only then commit to the mount, the shield, and the lens.

That step 2 costs you nothing extra and is the only thing that proves the FOV math - every published FOV figure in this chain contradicted its own focal length.

## [19] USER

what are the amazon links to the board and camera and anything else required for true wireless streaming off the device

*(tools used:)*
- `eval` - Amazon ASINs

## [45] ASSISTANT

Pulling the actual ASINs and links.

*(tools used:)*
- `eval` - Verifying power bank and lens ASINs

## [46] ASSISTANT

All verified live.

#### The complete Amazon list

| # | Item | Link | Price |
|---|---|---|---|
| 1 | **Luckfox Pico Ultra (WiFi 6)** - RV1106, 8 GB eMMC, MIPI CSI | [amazon.com/dp/B0D8T54XJR](https://www.amazon.com/dp/B0D8T54XJR) | **$62.39** |
| 2 | **SC3336 3MP Camera (B)** | [amazon.com/dp/B0CJM7S6F6](https://www.amazon.com/dp/B0CJM7S6F6) | **$15.99** |
| 3 | **Commonlands 2.2 mm M12 lens** - low distortion, 1/2.3", IP67, IR-corrected | [amazon.com/dp/B0F3KZJKVQ](https://www.amazon.com/dp/B0F3KZJKVQ) | **$47.00** |
| 4 | **Voltaic Always On V50** - 13,400 mAh / 48 Wh, USB-C PD | [amazon.com/dp/B00XZ7YU4M](https://www.amazon.com/dp/B00XZ7YU4M) | **$74.00** |
| | **Total** | | **$199.38** |

**Upgrade option:** Voltaic **V75** Always On, 20,100 mAh - [B084BPSFKH](https://www.amazon.com/dp/B084BPSFKH) - **$89.00** (~30 h runtime instead of ~19).

**Cheaper swaps** (both degrade something real):

| Instead of | Swap | Price | Cost of the swap |
|---|---|---|---|
| #3 | [2 mm M12 fisheye, 190deg, IR-corrected](https://www.amazon.com/dp/B0F1QRXTQP) | $35.00 | Wider than needed -> wastes ~30% of your pixels on ceiling |
| #4 | Any 20,000 mAh bank (~$20-25) | ~$25 | **Will auto-shutoff** - at 0.11 W idle you're below the cutout threshold |

#### If you'd rather not use a battery

Tap the fixture instead - one short hidden lead, infinite runtime:

| Item | Link | Price |
|---|---|---|
| DC 12/24 V -> 5 V USB-C buck converter, 5 A | [amazon.com/dp/B0CRVW7N2J](https://www.amazon.com/dp/B0CRVW7N2J) | **$8** |
| Waterproof version, 3 A | [amazon.com/dp/B09DGDQ48H](https://www.amazon.com/dp/B09DGDQ48H) | verify |

! **Only if the fixture's circuit is not the wall switch.** If flipping the light switch kills the fixture, it kills the camera. Never tap a dimmed circuit.

#### Not required

- **microSD** - the Ultra boots from its 8 GB eMMC
- **USB-C cable** - a Type-A->Type-C cable ships in the box, and the V50 has USB-A outputs
- **Audio hardware** - none on the camera; you just need a muted source in OBS to satisfy FB's ingest
- **USB-serial adapter** - flashing is over USB-C
- **Mount** - a clamp and a 1/4"-20 ball head; hardware-store generic, no specific ASIN needed

#### Two things to confirm at checkout

1. **Select the WiFi variant.** That ASIN has siblings - [B0D6G7Z2BQ](https://www.amazon.com/dp/B0D6G7Z2BQ) ($74.99, PoE) and [B0DB23B79S](https://www.amazon.com/dp/B0DB23B79S) ($91.99). The bullets must say *"Onboard 2.4GHz WiFi 6"*.

2. **The lens mount is the one unverified risk in this list.** The SC3336 lists "manual focus," which implies a threaded barrel, but I could not confirm **M12 vs M8** - and a $47 lens is scrap if it's the wrong thread. **Buy the camera first, look at the mount, then order the lens.** Everything else on the list is safe to order today.

## [20] USER

any prebuilt off the shelf retail options

*(tools used:)*
- `web_search`  [Mevo Start wireless live streaming camera RTMP SRT OBS field of view price battery] - Checking Mevo Start specs
- `web_search`  [NDI HX Camera app Android iOS wireless to OBS plugin latency ultra wide lens] - Checking phone NDI to OBS
- `web_search`  [Reolink Tapo 2K IP camera RTSP field of view degrees 2.8mm lens wide angle spec] - Checking IP camera FOV specs
- `web_search`  [fisheye 360 IP camera RTSP ONVIF dewarp 180 degree ceiling mount PoE budget] - Checking fisheye IP cameras

## [47] ASSISTANT

Fair question - let me check what actually exists retail.

*(tools used:)*
- `web_search`  [Tapo C225 C220 indoor 2K camera field of view diagonal degrees RTSP ONVIF support price] - Checking indoor IP camera FOV and RTSP
- `web_search`  [Mevo Core 4K wireless streaming camera interchangeable lens NDI OBS price specs] - Checking Mevo Core details

## [48] ASSISTANT

Real options exist - including one purpose-built. Verifying a concrete model.

## [49] ASSISTANT

Yes - several, and one is purpose-built for exactly this.

#### Retail options

| Option | Product | Price | Wireless | Path to OBS | FOV at 34" |
|---|---|---|---|---|---|
| **Purpose-built** | **[Mevo Core](https://www.logitech.com/en-us/shop/p/mevo-core)** - 4K MFT, **interchangeable lens**, 6 h battery, WiFi 6E | **$949** / **$699 [refurb](https://www.logitech.com/en-us/shop/p/mevo-core-camera-refurbished)** | yes | **Native NDI + SRT** (also RTMP) -> obs-ndi plugin | **You choose the lens** |
| Purpose-built 1080p | [Mevo Start](https://www.logitech.com/en-ca/shop/p/mevo-start) - 1080p, 4 h battery, native FB/YT | ~$600 (was $299) | yes | RTMP / USB webcam / PoE adapter | fixed lens |
| WiFi IP camera | Tapo (non-battery) / Reolink, 2K-4K | $40-120 | WiFi | **RTSP** -> OBS Media Source | **only if HFOV >=98deg** |
| Spare phone | NDI Camera / NDI HX app | $0-30 | WiFi | NDI -> obs-ndi plugin | ultra-wide ~= 100-110deg OK |
| Pro fisheye | Hikvision DS-2CD6365 / Dahua fisheye, 6 MP, **on-board dewarp** | $300-600 | PoE (wired) | RTSP - dewarped stream | 360deg, trivially covers |

#### The one that actually solves your problem

**Mevo Core.** It's Micro Four Thirds with an **interchangeable lens**, so the FOV problem you've been fighting for six messages simply disappears - fit a wide MFT lens, get a *rectilinear* 100deg+ view, no fisheye, no dewarping, no lens-mount guessing. Add native NDI/SRT straight into OBS, a 6-hour battery, and WiFi 6E.

That's ~$700-950, which is 3.5-5x the DIY build. What you're buying is the elimination of every risk we've hit: lens compatibility, published-spec contradictions, fisheye distortion, and RTSP plumbing.

#### Traps in the cheap tier

- **Battery-powered cameras don't do RTSP.** TP-Link's own FAQ: most Tapo cameras *excluding battery-powered models* support RTSP/ONVIF. Buy a mains-powered model.
- **Most IP cameras are narrower than you'd assume.** The Tapo C225 is a **4.3 mm** lens on a 1/2.9" sensor - roughly 65-70deg HFOV, nowhere near the 98deg you need. The genuinely wide ones (2.8-3.17 mm, 111deg HFOV) are specific SKUs. **Read the datasheet's horizontal FOV before buying.**
- **They're all bulky.** Nothing in the retail column hangs elegantly off a shop-light shade.

#### So: buy or build?

| If... | Then |
|---|---|
| The camera can be **big** or go on the **ceiling** | **Buy retail.** A $50-120 RTSP camera on the ceiling is the best value in this whole conversation - at 60" even a stock lens covers the table. |
| It must hang **on the light fixture** | **Build the RV1106 rig.** At 34" every retail option is either too narrow, too bulky, or $700+ |

That's the honest bottom line: **retail wins on effort and optics; DIY wins only on size.** Your original "small and low power" constraint is what keeps the DIY build alive - everything else has been resolved away.

If you can put the camera on the **ceiling** instead of the fixture and run power up there, I'd stop building and buy a Tapo/Reolink with a documented >=98deg HFOV. That's a ~$100 answer to a problem we've spent a lot of effort engineering around.

## [21] USER

save this conversation and your notes here in this folder (micro)

*(tools used:)*
- `read`  [(repo root)] - Confirming target folder state
- `glob`  [~/.omp] - Looking for a session transcript store
- `glob`  [~/.omp/**/sessions/-micro/*] - Locating the micro session transcript
- `bash`  [find "~/.omp" -maxdepth 4 -name "*.jsonl" -path "*micro*" -printf "%p  %s b] - Finding session jsonl size

## [50] ASSISTANT

Session transcript exists on disk. Locating and inspecting it.

*(tools used:)*
- `eval` - Inspecting session schema

## [51] ASSISTANT

Found it - 2.1 MB session log. Inspecting the schema so I can extract faithfully rather than retype.

*(tools used:)*
- `eval` - Message structure stats
- `eval` - Generating conversation record

## [52] ASSISTANT

Schema confirmed: 21 user turns, 51 assistant text blocks, 92 tool calls. Generating the transcript from the raw log.

*(tools used:)*
- `write`  [(repo root)/NOTES.md] - Writing engineering notes

## [53] ASSISTANT

Now the notes.

*(tools used:)*
- `bash`  [cd "(repo root)" && ls -l && echo "--- non-ascii check ---" && for f in CONVERS] - Verifying saved files
- `eval` - Regenerating conversation record

## [54] ASSISTANT

Two fixes: my own in-body headings collide with the turn markers, and tool-only turns skip numbering. Regenerating.

*(tools used:)*
- `read`  [(repo root)/CONVERSATION.md:1-40] - Spot-checking conversation file head
- `read`  [(repo root)/CONVERSATION.md:-22] - Spot-checking conversation file tail
- `eval` - Inspecting tool call shape

## [55] ASSISTANT

The tool intents are empty - they live in a separate event, not in `args`. Fixing.

*(tools used:)*
- `eval` - Final conversation record

## [56] ASSISTANT

`arguments`, not `args` - my key was wrong. Regenerating with intents.

*(tools used:)*
- `eval` - Checking for duplication

## [57] ASSISTANT

56 replies but only 51 text parts - that doesn't add up. Checking for duplication.

*(tools used:)*
- `eval` - Checking heading numbering

## [58] ASSISTANT

Counts moved because the session log is live (this is the current session). Checking the numbering anomaly.

*(tools used:)*
- `eval` - Final regeneration

## [59] ASSISTANT

Numbering is clean (my check was buggy). Final regeneration with a capture footer.

---

END OF RECORD - 21 user turns, 59 assistant replies. Captured 2026-10-12.
