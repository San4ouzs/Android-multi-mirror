# Android Multi‑Mirror (Bluetooth/Wi‑Fi via ADB)

This tool displays multiple Android screens on one computer monitor. It works by pulling screenshots from each phone via **ADB** and showing them in a live grid (configurable FPS).

> ⚠️ Bluetooth note: classic Bluetooth is low‑bandwidth. For smoother mirroring use Wi‑Fi (ADB over TCP) or USB. If you **must** use Bluetooth, enable **Bluetooth tethering (PAN)** on each phone so your PC gets an IP route to the phone, then connect ADB over TCP using that PAN IP. Expect ~1–5 FPS.

## What you get
- `multi_mirror.py` — Python app (OpenCV) that shows a grid of all connected devices.
- `config.json` — Configure device serials/IPs and grid/FPS settings.
- `start_windows.bat` — One‑click launcher on Windows (assumes Python 3.10+ and ADB in PATH).
- `requirements.txt` — Python deps.
- This README.

## Prerequisites
1. **ADB** installed and in PATH (Android platform tools).  
2. **Python 3.10+** installed.
3. **On each phone**: enable *Developer Options* → *USB debugging*.
4. For Bluetooth PAN use: enable **Bluetooth tethering** on the phone; pair the phone with your PC.

## Quick start (Wi‑Fi / USB recommended)
### Option A — USB (no network)
- Plug each phone by USB. Run: `adb devices` and confirm all serials are `device`.
- You can use the USB serials directly in `config.json` (e.g., `R58M...`).

### Option B — Wi‑Fi (fastest)
- For each phone (just once): plug by USB and run:
  ```bash
  adb tcpip 5555
  adb shell ip route
  # find the phone's IP (e.g., 192.168.1.23)
  adb connect 192.168.1.23:5555
  ```
- Put those IP:port values into `config.json` under `devices`.

### Option C — **Bluetooth PAN (experimental)**
- On the phone: **Settings → Tethering & portable hotspot → Bluetooth tethering** (enable).
- Pair phone with the PC over Bluetooth.
- On Windows: open **Settings → Bluetooth & devices** and ensure the phone shows as *Connected via Bluetooth* with *Access the internet via this device* allowed (wording varies by vendor).
- Find the phone's IP reachable via PAN; one way:
  ```powershell
  adb tcpip 5555
  # Temporarily keep USB to run the above if needed
  # Now over PAN, try:
  adb connect <phone_pan_ip>:5555
  ```
- If `adb connect` succeeds, add that IP:port to `config.json`.

> Tip: If you can’t find the PAN IP, open a terminal on the phone (`adb shell ip addr`) while USB is connected to see addresses; often PAN uses a 172.20.x.x or 192.168.44.x range on Android.

## Run
1. Edit `config.json`:
   - List all `devices` (ADB serials or `ip:port` from `adb connect`).
   - Set `fps` (default 5), `cols` for grid columns, and `max_width` to limit individual view width.
2. Windows: double‑click `start_windows.bat` (or run `python multi_mirror.py`).  
   Linux/macOS: `python3 -m pip install -r requirements.txt && python3 multi_mirror.py`.

## Controls
- Press **Q** in the window or focus the console and press **Ctrl+C** to exit.
- The app attempts to reconnect if a device temporarily drops.

## Known limits
- This is **pull‑based** (grabs PNG frames using `adb exec-out screencap -p`). Expect ~1–8 FPS depending on link (USB/Wi‑Fi good, Bluetooth PAN slow).
- For true high‑FPS mirroring, use `scrcpy` (ADB video encoder) over USB/Wi‑Fi. You can still use this tool for a simple multi‑grid, or adapt it to launch `scrcpy` windows with pre‑positioning.

## Optional: scrcpy multi‑window helper
If you install **scrcpy**, you can run multiple instances (one per device) and arrange them with Windows FancyZones or similar. Example per device:
```bash
scrcpy -s <serial> --max-size 800 --window-title <serial>
```
Then tile windows in a grid.

---

## Troubleshooting
- **`adb` not found** → install platform-tools and add to PATH; reopen terminal.
- **`device unauthorized`** → check the phone screen for the USB debugging authorization prompt.
- **High CPU** → lower `fps` in config, reduce `max_width`, or reduce number of devices.
- **Black tiles** → device temporarily unavailable; the app retries automatically.
